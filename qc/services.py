"""Explicit, transactional prototype decisions. Engineering TBDs never count as acceptance."""
import calendar
import hashlib
from datetime import date
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q, F
from django.utils import timezone
from .models import *

CUSTOMER_ACTIONS = {'procedure_approve', 'disposition', 'at_risk'}
CONE_ACTIONS = {'qualification_approve', 'readiness', 'coupon_accept', 'hold_close', 'ncr_close', 'release', 'ship'}

def profile(user):
    if not user.is_authenticated or not user.is_active:
        raise PermissionDenied('Sign in with an active program account.')
    try:
        return user.profile
    except Profile.DoesNotExist:
        raise PermissionDenied('This account has no program membership.')

def authorize(user, action, capacity='organization', scope='LANDER', performer=None):
    p = profile(user)
    if capacity == 'owner':
        if not p.is_owner:
            raise PermissionDenied('Owner capacity is available only to the designated owner.')
        return None
    if capacity not in ('organization', 'picogrid'):
        raise PermissionDenied('Choose a recognized acting capacity.')
    code = 'PICOGRID' if capacity == 'picogrid' else p.organization.code
    if action in CUSTOMER_ACTIONS and code != 'PICOGRID':
        raise PermissionDenied('This decision requires recorded Picogrid authority.')
    if action in CONE_ACTIONS and code != 'CONE':
        raise PermissionDenied('This ordinary decision belongs to Cone designated personnel.')
    now = timezone.now()
    grants = AuthorityGrant.objects.filter(user=user, organization__code=code, action=action, revoked_at__isnull=True, starts_at__lte=now).filter(Q(ends_at__isnull=True) | Q(ends_at__gt=now)).filter(Q(scope='LANDER') | Q(scope=scope))
    grant = grants.order_by('-created_at').first()
    if not grant:
        raise PermissionDenied('No effective authority grant covers this action and scope.')
    policy = grant.organization
    if performer and performer.user_id == user.pk and not policy.self_approval_allowed:
        raise PermissionDenied('The effective organizational policy requires a different approver.')
    return grant

def audit(user, action, target, **detail):
    profile(user)
    return AuditEvent.objects.create(actor=user, action=action, target=str(target), detail=detail)

def decision(user, action, target, reason, capacity='organization', performer=None, revision=None, outcome='approved'):
    if not reason.strip():
        raise ValidationError('Record the decision basis or reason.')
    grant = authorize(user, action, capacity, performer=performer)
    p = profile(user)
    approval = Approval.objects.create(actor=user, action=action, capacity=capacity, grant=grant, policy_version=grant.organization.policy_version if grant else p.organization.policy_version, target_label=str(target), target_id=target.pk, revision=revision, decision=outcome, reason=reason)
    audit(user, action, target, capacity=capacity, decision=outcome, approval=str(approval.pk))
    return approval

def resolved(revision):
    return bool(revision and revision.state == 'approved' and revision.requirements_resolved and revision.basis.strip())

def active_holds(unit):
    machine_ids = unit.operations.values_list('machine_id', flat=True)
    return Hold.objects.filter(Q(unit=unit) | Q(machine_id__in=machine_ids)).exclude(status='closed')

def blocked(unit):
    return active_holds(unit).exists() or unit.ncrs.exclude(status='closed').exists() or unit.impacts.filter(status='open').exists()

def ensure_unrestricted(unit):
    if blocked(unit):
        raise ValidationError('An applicable process hold, hardware NCR or evidence-impact review is still open.')

def lock_unit(unit):
    # Global prototype decision lock serializes machine-wide and unit-level restrictions.
    # Narrower lock ordering can replace this after measured scale requirements.
    Organization.objects.select_for_update().get(code='CONE')
    return HardwareUnit.objects.select_for_update().get(pk=unit.pk)

@transaction.atomic
def create_record(user, *, number, kind, title, body, unit=None, machine=None, performed_by=None, performed_at=None, requirements_resolved=False, basis='', payload=None):
    authorize(user, 'enter', 'owner' if profile(user).is_owner else 'organization')
    record = ControlledRecord.objects.create(number=number, kind=kind, title=title, unit=unit, machine=machine)
    rev = Revision.objects.create(record=record, body=body, payload=payload or {}, requirements_resolved=requirements_resolved, basis=basis, performed_by=performed_by, performed_at=performed_at, entered_by=user)
    record.current_revision = rev
    record.save(update_fields=['current_revision'])
    if unit and kind in ('inspection','proof') and (payload or {}).get('result') == 'fail':
        lock_unit(unit)
        hold = Hold.objects.create(number=f'H-{str(rev.pk)[:10]}',unit=unit,origin='gate2',issue=f'Failed {kind} evidence: {number}',hardware_affected=True,containment='Identify and contain affected serial population; review last acceptable verification.',raised_by=user)
        NCR.objects.create(number=f'NCR-{str(rev.pk)[:10]}',unit=unit,hold=hold,description=f'Failed {kind} evidence {number}; customer disposition required.')
    audit(user, 'record_created', record, revision=str(rev.pk))
    return record

@transaction.atomic
def amend_record(user, record, *, body, reason, requirements_resolved=False, basis='', payload=None):
    authorize(user, 'enter', 'owner' if profile(user).is_owner else 'organization')
    Organization.objects.select_for_update().get(code='CONE')
    record = ControlledRecord.objects.select_for_update().get(pk=record.pk)
    old = record.current_revision
    if not reason.strip():
        raise ValidationError('An amendment reason is required.')
    rev = Revision.objects.create(record=record, number=old.number + 1, body=body, payload=payload if payload is not None else old.payload, requirements_resolved=requirements_resolved, basis=basis, performed_by=old.performed_by, performed_at=old.performed_at, entered_by=user, amendment_reason=reason)
    record.current_revision = rev
    record.save(update_fields=['current_revision'])
    if old.state == 'approved':
        flag_impact(user, old, reason)
    audit(user, 'amendment', record, prior=str(old.pk), revision=str(rev.pk), reason=reason)
    return rev

@transaction.atomic
def approve_revision(user, revision, reason, capacity='organization', reject=False):
    Organization.objects.select_for_update().get(code='CONE')
    rev = Revision.objects.select_for_update(of=('self',)).select_related('record', 'performed_by').get(pk=revision.pk)
    if rev.frozen_at or rev.record.current_revision_id != rev.pk:
        raise ValidationError('Only the current, unfrozen revision can receive a new approval.')
    action = 'procedure_approve' if rev.record.kind in ('wps', 'pqr', 'plan') else 'coupon_accept'
    if rev.record.unit_id:
        unit = lock_unit(rev.record.unit)
        if unit.impacts.filter(status='open').exists():
            raise ValidationError('Resolve the evidence-impact review before further affected approvals.')
    authorize(user, action, capacity, performer=rev.performed_by)
    if not reject and (not rev.requirements_resolved or not rev.basis.strip()):
        raise ValidationError('Unresolved / TBD requirements cannot be approved as acceptance evidence, including in owner capacity.')
    if not reject and rev.record.kind == 'wps':
        pqr = Revision.objects.filter(pk=rev.payload.get('pqr_id'),record__kind='pqr').first() if rev.payload.get('pqr_id') else None
        if not resolved(pqr): raise ValidationError('A WPS needs its separate approved PQR evidence; a successful trial is not procedure qualification.')
    if not reject and rev.record.kind == 'pqr':
        cs = CouponSet.objects.filter(pk=rev.payload.get('coupon_set_id'),purpose='qualification',status='accepted').first() if rev.payload.get('coupon_set_id') else None
        if not cs or not rev.payload.get('section_c_complete'): raise ValidationError('PQR approval requires complete Section C scope and accepted B qualification-coupon evidence.')
    a = decision(user, action, rev.record, reason, capacity, rev.performed_by, rev, outcome='rejected' if reject else 'approved')
    Revision.objects.filter(pk=rev.pk).update(state='rejected' if reject else 'approved', frozen_at=timezone.now())
    return a

@transaction.atomic
def add_attachment(user, revision, upload, signed_paper=False):
    authorize(user, 'enter', 'owner' if profile(user).is_owner else 'organization')
    Organization.objects.select_for_update().get(code='CONE')
    rev = Revision.objects.select_for_update().get(pk=revision.pk)
    if rev.frozen_at:
        raise ValidationError('Approved/frozen evidence requires an amendment before attaching new material.')
    allowed = {'.pdf': b'%PDF-', '.png': b'\x89PNG\r\n\x1a\n', '.jpg': b'\xff\xd8\xff', '.jpeg': b'\xff\xd8\xff'}
    from pathlib import Path
    extension = Path(upload.name).suffix.lower()
    if extension not in allowed or upload.size > 10 * 1024 * 1024:
        raise ValidationError('Attach PDF, PNG or JPEG evidence, up to 10 MB.')
    signature = upload.read(16)
    upload.seek(0)
    if not signature.startswith(allowed[extension]):
        raise ValidationError('The attachment content does not match its file type.')
    digest = hashlib.sha256()
    for chunk in upload.chunks(): digest.update(chunk)
    upload.seek(0)
    attachment = Attachment.objects.create(revision=rev, file=upload, original_name=Path(upload.name).name[:180], sha256=digest.hexdigest(), signed_paper=signed_paper, uploaded_by=user)
    audit(user, 'evidence_attached', rev.record, sha256=attachment.sha256, signed_paper=signed_paper)
    return attachment

def qualification_current(op, kind):
    qs = Qualification.objects.filter(kind=kind, status='qualified', joint_family=op.joint_family, wps=op.wps)
    qs = qs.filter(person=op.operator) if kind == 'operator' else qs.filter(machine=op.machine)
    for award in qs.select_related('evidence'):
        if not resolved(award.evidence): continue
        if kind == 'operator':
            if not award.last_activity or not award.activity_source.strip(): continue
            today = timezone.localdate()
            month = today.month - 6
            year = today.year
            if month <= 0: year, month = year - 1, month + 12
            boundary = date(year, month, min(today.day, calendar.monthrange(year, month)[1]))
            if award.last_activity < boundary: continue
        return True
    return False

def readiness_issues(op):
    issues = []
    if not resolved(op.wps): issues.append('Approved, resolved WPS revision is missing.')
    if not resolved(op.plan): issues.append('Approved verification / acceptance plan is missing; requirements remain TBD.')
    for kind in ('operator', 'machine'):
        if not qualification_current(op, kind): issues.append(f'Current scoped {kind} qualification evidence is missing.')
    if not all((op.material_lot.strip(), op.filler_lot.strip(), op.fixture_reference.strip())):
        issues.append('Actual materials, filler and fixture references are incomplete.')
    if blocked(op.unit): issues.append('An applicable hold, NCR or evidence-impact review is open.')
    return issues

@transaction.atomic
def open_hold(user, *, unit, number, origin, issue, hardware_affected=False, containment='', notification='', machine=None):
    authorize(user, 'enter', 'owner' if profile(user).is_owner else 'organization')
    lock_unit(unit)
    if hardware_affected and not containment.strip():
        raise ValidationError('Describe containment and the potentially affected population; unknown impact is not acceptance.')
    hold = Hold.objects.create(number=number, unit=unit, machine=machine, origin=origin, issue=issue, hardware_affected=hardware_affected, containment=containment, notification=notification, raised_by=user)
    audit(user, 'hold_opened', hold, unit=str(unit.pk), origin=origin)
    return hold

@transaction.atomic
def close_hold(user, hold, reason, capacity='organization'):
    lock_unit(hold.unit)
    h = Hold.objects.select_for_update().get(pk=hold.pk)
    if h.status == 'closed': raise ValidationError('The hold is already closed.')
    checks = h.checks.order_by('-performed_at', '-created_at')
    if not h.problem_resolved or not h.corrective_action.strip() or not checks.exists() or checks.first().result != 'pass':
        raise ValidationError('Record corrective action, a passing H-required strike-plate check and confirmation that the problem is resolved.')
    if h.requires_bc and not ((h.coupon_evidence_id and h.coupon_evidence.status == 'accepted') or (h.qualification_evidence_id and h.qualification_evidence.status == 'qualified')):
        raise ValidationError('This hold came from failed coupon/qualification evidence. Complete the applicable B/C verification before closure.')
    if not resolved(h.verification):
        raise ValidationError('The required verification / hold-closure basis is unresolved or unapproved.')
    if h.hardware_affected and not h.notification.strip():
        raise ValidationError('Record the required Picogrid notification evidence.')
    decision(user, 'hold_close', h, reason, capacity)
    h.status = 'closed'
    h.save(update_fields=['status'])
    h.unit.operations.update(state='gate2' if h.origin == 'gate2' else 'gate1', version=F('version') + 1)
    return h

@transaction.atomic
def approve_disposition(user, ncr, text, reason, capacity='organization'):
    lock_unit(ncr.unit)
    ncr = NCR.objects.select_for_update().get(pk=ncr.pk)
    if ncr.status != 'open' or not text.strip(): raise ValidationError('An open NCR and explicit disposition are required.')
    decision(user, 'disposition', ncr, reason, capacity)
    ncr.disposition, ncr.status = text, 'action_required'
    ncr.save(update_fields=['disposition', 'status'])

@transaction.atomic
def close_ncr(user, ncr, reason, capacity='organization'):
    lock_unit(ncr.unit)
    ncr = NCR.objects.select_for_update().get(pk=ncr.pk)
    if ncr.status != 'action_required' or not ncr.execution.strip() or not resolved(ncr.verification):
        raise ValidationError('Complete approved disposition actions and accepted reinspection/retest evidence before NCR closeout.')
    if not Approval.objects.filter(target_id=ncr.pk, action='disposition', decision='approved').exists():
        raise ValidationError('Disposition authorization is missing.')
    decision(user, 'ncr_close', ncr, reason, capacity)
    ncr.status = 'closed'
    ncr.save(update_fields=['status'])

@transaction.atomic
def record_test(user, *, specimen, method, provider, method_reference, validity, result, observations, reason='', report=None, prior_attempt=None):
    authorize(user, 'enter', 'owner' if profile(user).is_owner else 'organization')
    specimen = Specimen.objects.select_related('assembly__coupon_set__operation', 'assembly__coupon_set__plan').get(pk=specimen.pk)
    cs = specimen.assembly.coupon_set
    if cs.operation_id: lock_unit(cs.operation.unit)
    if cs.status == 'accepted': raise ValidationError('An accepted set is frozen for this prototype. Record corrected report evidence and flag its impact instead of adding an unreviewed attempt.')
    if not specimen.assembly.nde_complete:
        raise ValidationError('Document pre-cut visual/dimensional inspection before destructive testing.')
    if method == 'pull' and cs.joint_family == 'corner':
        raise ValidationError('Pull testing does not apply to Lander enclosure outside-corner verification.')
    if validity == 'invalid' and not reason.strip(): raise ValidationError('Record why this evidence is invalid; this is not a weld-failure decision.')
    if validity == 'valid' and specimen.integrity != 'valid': raise ValidationError('Specimen preparation integrity has not been accepted.')
    if result != 'pending' and (not resolved(cs.plan) or not resolved(report)):
        raise ValidationError('Unresolved criteria/report evidence cannot produce a recorded passing or failing acceptance result. Save raw observations as pending.')
    if prior_attempt and prior_attempt.specimen_id != specimen.pk:
        raise ValidationError('A repeat attempt must reference the same specimen; replacement specimens need their own traceability.')
    test = TestAttempt.objects.create(specimen=specimen, method=method, provider=provider, method_reference=method_reference, validity=validity, result=result, observations=observations, reason=reason, report=report, prior_attempt=prior_attempt, entered_by=user)
    if validity == 'valid' and result == 'fail':
        cs.status = 'rejected'
        cs.save(update_fields=['status'])
        units = list(cs.coverage.all())
        if cs.operation_id and cs.operation.unit not in units: units.append(cs.operation.unit)
        for unit in units:
            number = f'H-{str(test.pk)[:8]}-{unit.serial}'[:70]
            hold = Hold.objects.create(number=number, unit=unit, origin='gate1', issue=f'Valid failed coupon {cs.number}: {observations}', hardware_affected=True, requires_bc=True, containment='Contain affected population; determine last acceptable verification.', raised_by=user)
            NCR.objects.create(number=f'NCR-{str(test.pk)[:8]}-{unit.serial}'[:70], unit=unit, hold=hold, description=f'Valid failed coupon {cs.number}; Picogrid disposition required.')
    audit(user, 'test_recorded', cs, test=str(test.pk), validity=validity, result=result)
    return test

@transaction.atomic
def accept_coupon(user, coupon, reason, capacity='organization'):
    Organization.objects.select_for_update().get(code='CONE')
    cs = CouponSet.objects.select_for_update(of=('self',)).select_related('plan').get(pk=coupon.pk)
    if cs.operation_id: lock_unit(cs.operation.unit)
    if cs.status == 'rejected': raise ValidationError('A rejected coupon cannot be accepted by choosing a later favorable test. Resolve the nonconformance.')
    if not resolved(cs.plan): raise ValidationError('Acceptance criteria remain TBD or unapproved.')
    count = cs.plan.payload.get('coupon_count')
    methods = cs.plan.payload.get('required_tests')
    if not isinstance(count, int) or count < 1 or not isinstance(methods, list) or not methods:
        raise ValidationError('Approved plan must explicitly define physical coupon count and required test coverage.')
    if cs.assemblies.count() < count: raise ValidationError('Required physical coupon assemblies are incomplete; A/B are welds, not separate coupons.')
    for assembly in cs.assemblies.all():
        if not assembly.nde_complete or not assembly.welds.exists(): raise ValidationError('Pre-cut NDE or weld identity is incomplete.')
        for weld in assembly.welds.all():
            if not weld.passes.exists(): raise ValidationError(f'{weld}: actual pass evidence is incomplete.')
            for method in methods:
                tests = TestAttempt.objects.filter(specimen__welds=weld, method=method)
                if tests.filter(validity='valid', result='fail').exists(): raise ValidationError('A valid failed result remains in the evidence history.')
                if not tests.filter(validity='valid', result='pass', report__state='approved', report__requirements_resolved=True).exists(): raise ValidationError(f'{weld}: required valid accepted {method} evidence is incomplete.')
    if cs.operation_id and cs.operation.unit.impacts.filter(status='open').exists(): raise ValidationError('Resolve the evidence-impact review before accepting affected evidence.')
    decision(user, 'coupon_accept', cs, reason, capacity, performer=cs.operator)
    cs.status = 'accepted'
    cs.save(update_fields=['status'])

@transaction.atomic
def award_qualification(user, award, reason, capacity='organization'):
    Organization.objects.select_for_update().get(code='CONE')
    award = Qualification.objects.select_for_update().get(pk=award.pk)
    action = 'procedure_approve' if award.kind == 'procedure' else 'qualification_approve'
    if not resolved(award.evidence): raise ValidationError('Approved, complete qualification evidence is required.')
    if not award.evidence.payload.get('section_c_complete') or not award.evidence.payload.get('coupon_set_id'):
        raise ValidationError('Section C qualification requires accepted Section B coupon evidence and scope.')
    cs = CouponSet.objects.filter(pk=award.evidence.payload['coupon_set_id'], status='accepted', purpose='qualification').first()
    if not cs or cs.joint_family != award.joint_family:
        raise ValidationError('An accepted qualification coupon set for this joint family is required.')
    if award.kind == 'operator' and cs.operator_id != award.person_id: raise ValidationError('Coupon operator does not match the qualification subject.')
    if award.kind == 'machine' and cs.machine_id != award.machine_id: raise ValidationError('Coupon machine does not match the unique qualification subject.')
    if cs.operation_id and award.wps_id and cs.operation.wps_id != award.wps_id:
        raise ValidationError('Coupon evidence does not cover this WPS revision.')
    decision(user, action, award, reason, capacity, performer=award.person, revision=award.evidence)
    award.status = 'qualified'
    award.save(update_fields=['status'])

def release_checklist(unit):
    issues, pending = [], []
    ops = list(unit.operations.select_related('wps', 'plan', 'operator', 'machine'))
    if not ops: issues.append('No scoped welding operations are defined.')
    if active_holds(unit).exists(): issues.append('An applicable process hold is open.')
    if unit.ncrs.exclude(status='closed').exists(): issues.append('A hardware NCR remains open.')
    if unit.impacts.filter(status='open').exists(): issues.append('An evidence-impact review is open.')
    manifest = {'revisions': [], 'coupons': [], 'operations': []}
    for op in ops:
        issues.extend(f'{op.get_joint_family_display()}: {msg}' for msg in readiness_issues(op))
        if op.state not in ('gate2', 'released'): issues.append(f'{op.get_joint_family_display()}: final / Gate 2 checkpoint is not complete.')
        manifest['operations'].append(str(op.pk))
        manifest['revisions'].extend([str(op.wps_id), str(op.plan_id)])
        manifest['revisions'].extend(str(x) for x in Qualification.objects.filter(status='qualified',joint_family=op.joint_family,wps=op.wps).filter(Q(person=op.operator)|Q(machine=op.machine)).values_list('evidence_id',flat=True))
        coupons = CouponSet.objects.filter(Q(operation=op) | Q(coverage=unit), joint_family=op.joint_family, purpose='production').distinct()
        if not coupons.exists(): issues.append(f'{op.get_joint_family_display()}: required coupon evidence is missing.')
        for cs in coupons:
            manifest['coupons'].append(str(cs.pk))
            manifest['revisions'].extend(str(x) for x in TestAttempt.objects.filter(specimen__assembly__coupon_set=cs).exclude(report=None).values_list('report_id',flat=True))
            if cs.machine_id != op.machine_id or cs.operator_id != op.operator_id or cs.material_lot != op.material_lot or cs.plan_id != op.plan_id:
                issues.append(f'{cs.number}: context does not cover the actual operation.')
            if cs.status == 'rejected': issues.append(f'{cs.number}: known failed coupon; not eligible for pending-results shipment.')
            elif cs.status != 'accepted':
                tests = TestAttempt.objects.filter(specimen__assembly__coupon_set=cs)
                if tests.filter(validity='invalid').exists(): issues.append(f'{cs.number}: invalid evidence needs review; not treated as merely pending.')
                else: pending.append(cs)
        proof = op.plan.payload.get('proof_applicable')
        if not isinstance(proof, bool): issues.append('Proof-test applicability remains TBD.')
        required_stages = ['pre_finish', 'post_finish', 'final'] if op.joint_family == 'corner' else ['final']
        if proof: required_stages.append('proof')
        for stage in required_stages:
            records = unit.records.filter(kind='proof' if stage == 'proof' else 'inspection', current_revision__state='approved', current_revision__requirements_resolved=True, current_revision__payload__stage=stage)
            record = records.first()
            if not record or record.current_revision.payload.get('result') != 'pass':
                issues.append(f'Required {stage.replace("_", " ")} evidence is not accepted.')
            else: manifest['revisions'].append(str(record.current_revision_id))
    for key in manifest: manifest[key]=sorted(set(manifest[key]))
    return list(dict.fromkeys(issues)), list({c.pk:c for c in pending}.values()), manifest

@transaction.atomic
def authorize_pending(user, unit, reason, capacity='organization'):
    lock_unit(unit)
    issues, pending, manifest = release_checklist(unit)
    if issues or not pending: raise ValidationError('Only genuinely pending coupon results may be deferred; every other applicable requirement must be satisfied.')
    approval = decision(user, 'at_risk', unit, reason, capacity, outcome='pending_coupon_authorized')
    audit(user, 'pending_scope', unit, approval=str(approval.pk), coupons=sorted(str(c.pk) for c in pending), manifest=manifest)
    return approval

@transaction.atomic
def release_unit(user, unit, reason, capacity='organization', route='normal'):
    unit = lock_unit(unit)
    issues, pending, manifest = release_checklist(unit)
    pending_auth = None
    if route == 'owner':
        if capacity != 'owner': raise PermissionDenied('Select explicit owner capacity for owner intervention.')
        action = 'release'
    else:
        if issues: raise ValidationError(issues)
        action = 'release'
        if pending:
            if route != 'pending': raise ValidationError('Coupon results are still pending. Normal conforming release is unavailable.')
            pending_auth = Approval.objects.filter(target_id=unit.pk, action='at_risk', decision='pending_coupon_authorized').order_by('-created_at').first()
            if not pending_auth: raise ValidationError('Explicit scoped Picogrid pending-coupon authorization is missing.')
            scope_event = AuditEvent.objects.filter(action='pending_scope', target=str(unit), detail__approval=str(pending_auth.pk)).first()
            if not scope_event or scope_event.detail['coupons'] != sorted(str(c.pk) for c in pending) or scope_event.detail['manifest'] != manifest:
                raise ValidationError('Pending-coupon authorization does not cover the current evidence and coupon population.')
        elif route == 'pending': raise ValidationError('No coupon results are pending; use the normal route.')
    approval = decision(user, action, unit, reason, capacity, outcome='owner_action' if route == 'owner' else 'prototype_release')
    return Release.objects.create(unit=unit, approval=approval, route=route, evidence_manifest=manifest, outstanding=issues + [f'{c.number}: coupon results pending' for c in pending], pending_authorization=pending_auth)

@transaction.atomic
def record_shipment(user, release, reference, reason, capacity='organization'):
    unit = lock_unit(release.unit)
    if not reference.strip(): raise ValidationError('Record the shipment / CoC reference.')
    if unit.shipments.exists(): raise ValidationError('This prototype serial already has a shipment record.')
    issues, pending, manifest = release_checklist(unit)
    if release.route == 'owner':
        if capacity != 'owner': raise PermissionDenied('Shipping under an owner action requires explicit owner capacity.')
    elif issues or (pending and release.route != 'pending') or manifest != release.evidence_manifest:
        raise ValidationError('Requirements, restrictions or evidence changed since release. Reassess Gate 2 before shipment.')
    decision(user, 'ship', unit, reason, capacity)
    return Shipment.objects.create(unit=unit, release=release, reference=reference, recorded_by=user)

@transaction.atomic
def flag_impact(user, revision, reason):
    authorize(user, 'enter', 'owner' if profile(user).is_owner else 'organization')
    Organization.objects.select_for_update().get(code='CONE')
    if not reason.strip(): raise ValidationError('Describe the evidence concern.')
    ids, queue = set(), [revision.pk]
    while queue:
        pk = queue.pop()
        if pk in ids: continue
        ids.add(pk)
        queue.extend(EvidenceDependency.objects.filter(source_id=pk).values_list('target_id', flat=True))
    units = set(ControlledRecord.objects.filter(revisions__pk__in=ids).exclude(unit=None).values_list('unit_id', flat=True))
    units.update(Operation.objects.filter(Q(wps_id__in=ids) | Q(plan_id__in=ids)).values_list('unit_id', flat=True))
    awards = Qualification.objects.filter(Q(evidence_id__in=ids) | Q(wps_id__in=ids))
    for award in awards:
        qs = Operation.objects.filter(joint_family=award.joint_family)
        if award.person_id: qs = qs.filter(operator_id=award.person_id)
        if award.machine_id: qs = qs.filter(machine_id=award.machine_id)
        units.update(qs.values_list('unit_id', flat=True))
    tests = TestAttempt.objects.filter(report_id__in=ids)
    for test in tests.select_related('specimen__assembly__coupon_set__operation'):
        cs = test.specimen.assembly.coupon_set
        units.update(cs.coverage.values_list('pk', flat=True))
        if cs.operation_id: units.add(cs.operation.unit_id)
    for release in Release.objects.all():
        if set(release.evidence_manifest.get('revisions', [])) & {str(i) for i in ids}: units.add(release.unit_id)
    case = ImpactCase.objects.create(revision=revision, reason=reason, raised_by=user)
    case.units.set(HardwareUnit.objects.filter(pk__in=units))
    audit(user, 'evidence_flagged', revision.record, revision=str(revision.pk), units=[str(u) for u in units])
    return case

@transaction.atomic
def clear_impact(user, case, resolution, capacity='organization'):
    Organization.objects.select_for_update().get(code='CONE')
    case = ImpactCase.objects.select_for_update().get(pk=case.pk)
    if case.status != 'open': raise ValidationError('This review is already resolved.')
    if not resolution.strip(): raise ValidationError('Document scope, investigation and authorized resolution.')
    grant = authorize(user,'impact_clear',capacity)
    if case.units.exists() and capacity != 'owner' and grant.organization.code != 'PICOGRID':
        raise PermissionDenied('Hardware-impact clearance needs recorded Picogrid authority; Cone process review alone does not disposition hardware.')
    decision(user, 'impact_clear', case, resolution, capacity)
    case.status, case.resolution = 'resolved', resolution
    case.save(update_fields=['status', 'resolution'])

@transaction.atomic
def change_policy(user, organization, allow):
    Organization.objects.select_for_update().get(code='CONE')
    p = profile(user)
    if not p.is_owner and (not p.is_senior or p.organization_id != organization.pk):
        raise PermissionDenied('Only the organization senior approver may change its policy.')
    organization = Organization.objects.select_for_update().get(pk=organization.pk)
    organization.self_approval_allowed = allow
    organization.policy_version += 1
    organization.save(update_fields=['self_approval_allowed', 'policy_version'])
    audit(user, 'approval_policy_changed', organization, self_approval_allowed=allow, version=organization.policy_version)

@transaction.atomic
def grant_authority(user, target_user, organization, action, scope, evidence):
    Organization.objects.select_for_update().get(code='CONE')
    p = profile(user)
    if not p.is_owner and (not p.is_senior or p.organization_id != organization.pk): raise PermissionDenied('You may manage only your organization\'s grants.')
    if not p.is_owner and target_user.profile.organization_id != organization.pk: raise PermissionDenied('Cross-organization delegation is reserved for explicit designation by the owner in this prototype.')
    if organization.code != 'PICOGRID' and action in CUSTOMER_ACTIONS: raise PermissionDenied('This organization cannot grant Picogrid authority.')
    if organization.code != 'CONE' and action in CONE_ACTIONS: raise PermissionDenied('This ordinary action belongs to Cone.')
    if not evidence.strip(): raise ValidationError('Record designation/delegation evidence.')
    grant = AuthorityGrant.objects.create(user=target_user, organization=organization, action=action, scope=scope, evidence=evidence, granted_by=user)
    audit(user, 'authority_granted', target_user.username, grant=str(grant.pk), action_type=action, organization=organization.code)
    return grant

@transaction.atomic
def advance_operation(user, operation, action, reason='', capacity='organization', version=None):
    lock_unit(operation.unit)
    op = Operation.objects.select_for_update().select_related('unit', 'wps', 'plan', 'operator', 'machine').get(pk=operation.pk)
    if version is not None and op.version != version:
        raise ValidationError('This operation changed. Reload before making a decision.')
    authorize(user, 'enter', capacity if capacity == 'owner' else 'organization')
    if action == 'review_wps' and op.state == 'start':
        if not resolved(op.wps):
            WorkflowRun.objects.create(operation=op, section='D', return_to='start', state='development')
            op.state = 'development'
        else: op.state = 'readiness'
    elif action == 'gate1' and op.state in ('readiness', 'gate1'):
        issues = readiness_issues(op)
        if issues: raise ValidationError(issues)
        decision(user, 'readiness', op, reason, capacity, performer=op.operator)
        op.state = 'triggers'
    elif action in ('call_b', 'call_c') and op.state in ('readiness', 'gate1', 'triggers', 'verification'):
        section = 'B' if action == 'call_b' else 'C'
        WorkflowRun.objects.create(operation=op, section=section, return_to='gate1' if section == 'B' else 'start')
        op.state = 'verification'
    elif action == 'start_welding' and op.state == 'triggers':
        issues = readiness_issues(op)
        if issues: raise ValidationError(issues)
        if not op.coupons.filter(status='accepted', purpose='production',joint_family=op.joint_family,machine=op.machine,operator=op.operator,material_lot=op.material_lot,plan=op.plan).exists():
            raise ValidationError('Complete the applicable verification before ordinary production. Pending-result continuation needs a defined authorization and is not enabled by default.')
        op.state = 'welding'
    elif action == 'checkpoint' and op.state == 'welding': op.state = 'triggers'
    elif action == 'final_inspection' and op.state == 'welding': op.state = 'gate2'
    elif action == 'return_b' and op.state == 'verification':
        if not op.coupons.filter(status='accepted').exists(): raise ValidationError('Accepted coupon evidence is required before returning.')
        WorkflowRun.objects.filter(operation=op, section='B', state='open').update(state='completed')
        op.state = 'gate1'
    elif action == 'return_c' and op.state == 'verification':
        if not qualification_current(op, 'operator') or not qualification_current(op, 'machine') or not resolved(op.wps):
            raise ValidationError('Complete the applicable Section C awards and approved procedure before returning to M START.')
        WorkflowRun.objects.filter(operation=op, section='C', state='open').update(state='completed')
        op.state = 'start'
    else: raise ValidationError('That transition is not available from this checkpoint. Reload the operation.')
    op.version += 1
    op.save(update_fields=['state', 'version'])
    audit(user, 'workflow_transition', op, action_type=action, state=op.state, version=op.version)
    return op


@transaction.atomic
def revoke_authority(user, grant):
    Organization.objects.select_for_update().get(code='CONE')
    grant=AuthorityGrant.objects.select_for_update().get(pk=grant.pk)
    p=profile(user)
    if not p.is_owner and (not p.is_senior or p.organization_id!=grant.organization_id):
        raise PermissionDenied("You may revoke only your organization's grants.")
    grant.revoked_at=timezone.now()
    grant.save(update_fields=['revoked_at'])
    audit(user,'authority_revoked',grant.user.username,grant=str(grant.pk))
