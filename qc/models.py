import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

class Entity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    class Meta:
        abstract = True

class Organization(models.Model):
    code = models.CharField(max_length=16, unique=True)
    name = models.CharField(max_length=120)
    self_approval_allowed = models.BooleanField(default=True)
    policy_version = models.PositiveIntegerField(default=1)
    def __str__(self): return self.name

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT)
    is_owner = models.BooleanField(default=False)
    is_senior = models.BooleanField(default=False)
    def __str__(self): return self.user.get_full_name() or self.user.username

ACTIONS = [('enter', 'Enter QC records'), ('coupon_accept', 'Accept coupon results'), ('procedure_approve', 'Approve WPS / PQR / plans'), ('qualification_approve', 'Approve operator / equipment qualification'), ('readiness', 'Approve Gate 1 readiness'), ('hold_close', 'Close process hold'), ('disposition', 'Approve hardware disposition'), ('ncr_close', 'Close verified NCR'), ('continue_pending', 'Authorize in-process continuation'), ('release', 'Authorize conforming release'), ('at_risk', 'Authorize pending-coupon shipment'), ('ship', 'Record shipment'), ('impact_clear', 'Resolve evidence-impact review')]

class AuthorityGrant(Entity):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT)
    action = models.CharField(max_length=40, choices=ACTIONS)
    scope = models.CharField(max_length=120, default='LANDER')
    evidence = models.CharField(max_length=240)
    starts_at = models.DateTimeField(default=timezone.now)
    ends_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    granted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='grants_made', null=True)

class Person(Entity):
    name = models.CharField(max_length=100)
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, blank=True, null=True)
    def __str__(self): return self.name

class Machine(Entity):
    identifier = models.CharField(max_length=60, unique=True)
    model = models.CharField(max_length=100)
    serial = models.CharField(max_length=100, unique=True)
    def __str__(self): return f'{self.identifier} · {self.model}'

class WorkOrder(Entity):
    number = models.CharField(max_length=60, unique=True)
    title = models.CharField(max_length=180)
    customer_reference = models.CharField(max_length=160, blank=True)
    traveler_reference = models.CharField(max_length=180, blank=True)
    notes = models.TextField(blank=True)
    def __str__(self): return self.number
    class Meta:
        ordering = ['-created_at']

class HardwareUnit(Entity):
    serial = models.CharField(max_length=60, unique=True)
    work_order = models.ForeignKey(WorkOrder, on_delete=models.PROTECT, related_name='units')
    part_number = models.CharField(max_length=80)
    drawing_revision = models.CharField(max_length=120)
    def __str__(self): return self.serial

KINDS = [('wps', 'WPS'), ('pqr', 'PQR'), ('plan', 'Verification / acceptance plan'), ('inspection', 'Inspection'), ('proof', 'Assembly proof test'), ('development', 'Development trial'), ('maintenance', 'Equipment event'), ('source', 'Source document')]

class ControlledRecord(Entity):
    number = models.CharField(max_length=70, unique=True)
    kind = models.CharField(max_length=24, choices=KINDS)
    title = models.CharField(max_length=180)
    unit = models.ForeignKey(HardwareUnit, on_delete=models.PROTECT, null=True, blank=True, related_name='records')
    machine = models.ForeignKey(Machine, on_delete=models.PROTECT, null=True, blank=True)
    current_revision = models.ForeignKey('Revision', on_delete=models.PROTECT, null=True, blank=True, related_name='+')
    def __str__(self): return self.number
    class Meta:
        ordering = ['-created_at']

class Revision(Entity):
    record = models.ForeignKey(ControlledRecord, on_delete=models.PROTECT, related_name='revisions')
    number = models.PositiveIntegerField(default=1)
    body = models.TextField()
    payload = models.JSONField(default=dict)
    requirements_resolved = models.BooleanField(default=False)
    basis = models.CharField(max_length=240, blank=True)
    state = models.CharField(max_length=24, choices=[('draft', 'Draft'), ('submitted', 'Awaiting approval'), ('approved', 'Approved in prototype'), ('rejected', 'Returned for correction')], default='draft')
    performed_by = models.ForeignKey(Person, on_delete=models.PROTECT, null=True, blank=True)
    performed_at = models.DateTimeField(null=True, blank=True)
    entered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='revisions_entered')
    frozen_at = models.DateTimeField(null=True, blank=True)
    amendment_reason = models.TextField(blank=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['record', 'number'], name='unique_record_revision')]
        ordering = ['-number']
    def __str__(self): return f'{self.record.number} · Rev {self.number}'
    def save(self, *args, **kwargs):
        if not self._state.adding:
            previous = type(self).objects.get(pk=self.pk)
            if previous.frozen_at:
                raise ValidationError('Frozen evidence cannot be overwritten. Create an amendment.')
        super().save(*args, **kwargs)

class Operation(Entity):
    unit = models.ForeignKey(HardwareUnit, on_delete=models.PROTECT, related_name='operations')
    joint_family = models.CharField(max_length=40, choices=[('tts', 'Tube to sheet'), ('corner', 'Enclosure outside corner')])
    operator = models.ForeignKey(Person, on_delete=models.PROTECT)
    machine = models.ForeignKey(Machine, on_delete=models.PROTECT)
    wps = models.ForeignKey(Revision, on_delete=models.PROTECT, related_name='wps_operations')
    plan = models.ForeignKey(Revision, on_delete=models.PROTECT, related_name='plan_operations')
    material_lot = models.CharField(max_length=100)
    filler_lot = models.CharField(max_length=100)
    fixture_reference = models.CharField(max_length=140)
    state = models.CharField(max_length=40, default='start')
    version = models.PositiveIntegerField(default=1)
    def __str__(self): return f'{self.unit.serial} · {self.get_joint_family_display()}'

class WorkflowRun(Entity):
    operation = models.ForeignKey(Operation, on_delete=models.PROTECT, related_name='runs')
    section = models.CharField(max_length=1)
    caller = models.ForeignKey('self', null=True, blank=True, on_delete=models.PROTECT)
    return_to = models.CharField(max_length=40)
    state = models.CharField(max_length=40, default='open')
    originating_gate = models.CharField(max_length=20, default='gate1')

class Qualification(Entity):
    kind = models.CharField(max_length=20, choices=[('operator', 'Operator'), ('machine', 'Equipment'), ('procedure', 'Procedure')])
    person = models.ForeignKey(Person, on_delete=models.PROTECT, null=True, blank=True)
    machine = models.ForeignKey(Machine, on_delete=models.PROTECT, null=True, blank=True)
    wps = models.ForeignKey(Revision, on_delete=models.PROTECT, null=True, blank=True, related_name='qualification_wps')
    joint_family = models.CharField(max_length=40)
    evidence = models.ForeignKey(Revision, on_delete=models.PROTECT, related_name='qualification_evidence')
    status = models.CharField(max_length=24, default='pending')
    last_activity = models.DateField(null=True, blank=True)
    activity_source = models.CharField(max_length=200, blank=True)
    class Meta:
        constraints = [models.CheckConstraint(condition=(Q(kind='operator', person__isnull=False, machine__isnull=True) | Q(kind='machine', machine__isnull=False, person__isnull=True) | Q(kind='procedure', wps__isnull=False, machine__isnull=True, person__isnull=True)), name='qualification_typed_subject')]

class CouponSet(Entity):
    number = models.CharField(max_length=70, unique=True)
    purpose = models.CharField(max_length=24, choices=[('development', 'Development'), ('qualification', 'Qualification'), ('production', 'Production verification')])
    joint_family = models.CharField(max_length=40, choices=[('tts', 'Tube to sheet'), ('corner', 'Enclosure outside corner')])
    operation = models.ForeignKey(Operation, on_delete=models.PROTECT, null=True, blank=True, related_name='coupons')
    plan = models.ForeignKey(Revision, on_delete=models.PROTECT)
    operator = models.ForeignKey(Person, on_delete=models.PROTECT)
    machine = models.ForeignKey(Machine, on_delete=models.PROTECT)
    material_lot = models.CharField(max_length=100)
    status = models.CharField(max_length=24, default='pending')
    coverage = models.ManyToManyField(HardwareUnit, blank=True, related_name='coupon_coverage')
    notes = models.TextField(blank=True)
    def __str__(self): return self.number
    class Meta:
        ordering = ['-created_at']

class CouponAssembly(Entity):
    coupon_set = models.ForeignKey(CouponSet, on_delete=models.PROTECT, related_name='assemblies')
    identifier = models.CharField(max_length=80, unique=True)
    drawing_reference = models.CharField(max_length=180)
    nde_complete = models.BooleanField(default=False)
    def __str__(self): return self.identifier

class CouponWeld(Entity):
    assembly = models.ForeignKey(CouponAssembly, on_delete=models.PROTECT, related_name='welds')
    side = models.CharField(max_length=32)
    observations = models.TextField(blank=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['assembly', 'side'], name='unique_assembly_weld')]
    def __str__(self): return f'{self.assembly.identifier}-{self.side}'

class PassActual(Entity):
    weld = models.ForeignKey(CouponWeld, on_delete=models.PROTECT, related_name='passes')
    ordinal = models.PositiveIntegerField()
    preset = models.CharField(max_length=80, blank=True)
    raw_parameters = models.TextField()
    observations = models.TextField(blank=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['weld', 'ordinal'], name='unique_weld_pass')]

class Specimen(Entity):
    identifier = models.CharField(max_length=90, unique=True)
    assembly = models.ForeignKey(CouponAssembly, on_delete=models.PROTECT, related_name='specimens')
    welds = models.ManyToManyField(CouponWeld, related_name='specimens')
    layout_reference = models.CharField(max_length=180)
    integrity = models.CharField(max_length=20, choices=[('pending', 'Not evaluated'), ('valid', 'Acceptable preparation'), ('invalid', 'Preparation concern')], default='pending')
    def __str__(self): return self.identifier

class TestAttempt(Entity):
    specimen = models.ForeignKey(Specimen, on_delete=models.PROTECT, related_name='tests')
    method = models.CharField(max_length=24, choices=[('macroetch', 'Macroetch'), ('pull', 'Pull test')])
    provider = models.CharField(max_length=120)
    method_reference = models.CharField(max_length=200)
    validity = models.CharField(max_length=20, choices=[('pending', 'Not evaluated'), ('valid', 'Valid evidence'), ('invalid', 'Invalid evidence')], default='pending')
    result = models.CharField(max_length=16, choices=[('pending', 'Pending'), ('pass', 'Meets stated basis'), ('fail', 'Does not meet stated basis')], default='pending')
    observations = models.TextField()
    reason = models.TextField(blank=True)
    report = models.ForeignKey(Revision, on_delete=models.PROTECT, null=True, blank=True)
    entered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    prior_attempt = models.ForeignKey('self', on_delete=models.PROTECT, null=True, blank=True)
    def __str__(self): return f'{self.specimen} · {self.get_method_display()}'

class Hold(Entity):
    number = models.CharField(max_length=70, unique=True)
    unit = models.ForeignKey(HardwareUnit, on_delete=models.PROTECT, related_name='holds')
    machine = models.ForeignKey(Machine, null=True, blank=True, on_delete=models.PROTECT, related_name='holds')
    origin = models.CharField(max_length=20, choices=[('gate1', 'Gate 1 / other origin'), ('gate2', 'Gate 2')])
    issue = models.TextField()
    hardware_affected = models.BooleanField(default=False)
    containment = models.TextField(blank=True)
    notification = models.TextField(blank=True)
    corrective_action = models.TextField(blank=True)
    problem_resolved = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default='open')
    raised_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='holds_raised')
    verification = models.ForeignKey(Revision, on_delete=models.PROTECT, null=True, blank=True)
    requires_bc = models.BooleanField(default=False)
    coupon_evidence = models.ForeignKey(CouponSet, on_delete=models.PROTECT, null=True, blank=True)
    qualification_evidence = models.ForeignKey(Qualification, on_delete=models.PROTECT, null=True, blank=True)
    class Meta:
        ordering = ['-created_at']
    def __str__(self): return self.number

class HoldCheck(Entity):
    hold = models.ForeignKey(Hold, on_delete=models.PROTECT, related_name='checks')
    operator = models.ForeignKey(Person, on_delete=models.PROTECT)
    machine = models.ForeignKey(Machine, on_delete=models.PROTECT)
    result = models.CharField(max_length=8, choices=[('pass', 'PASS'), ('fail', 'FAIL')])
    performed_at = models.DateTimeField()
    corrective_action_reference = models.CharField(max_length=240)
    entered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

class NCR(Entity):
    number = models.CharField(max_length=70, unique=True)
    unit = models.ForeignKey(HardwareUnit, on_delete=models.PROTECT, related_name='ncrs')
    hold = models.ForeignKey(Hold, on_delete=models.PROTECT, null=True, blank=True, related_name='ncrs')
    description = models.TextField()
    proposed_disposition = models.TextField(blank=True)
    disposition = models.TextField(blank=True)
    execution = models.TextField(blank=True)
    verification = models.ForeignKey(Revision, on_delete=models.PROTECT, null=True, blank=True)
    status = models.CharField(max_length=24, default='open')
    def __str__(self): return self.number

class ImpactCase(Entity):
    revision = models.ForeignKey(Revision, on_delete=models.PROTECT, related_name='impacts')
    units = models.ManyToManyField(HardwareUnit, related_name='impacts')
    reason = models.TextField()
    status = models.CharField(max_length=20, default='open')
    resolution = models.TextField(blank=True)
    raised_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

class EvidenceDependency(Entity):
    source = models.ForeignKey(Revision, on_delete=models.PROTECT, related_name='downstream_links')
    target = models.ForeignKey(Revision, on_delete=models.PROTECT, related_name='upstream_links')
    class Meta:
        constraints = [models.UniqueConstraint(fields=['source', 'target'], name='unique_evidence_dependency'), models.CheckConstraint(condition=~Q(source=models.F('target')), name='no_self_dependency')]

class Approval(Entity):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=40)
    capacity = models.CharField(max_length=20, choices=[('organization', 'Organizational authority'), ('picogrid', 'Picogrid delegation'), ('owner', 'System owner')])
    grant = models.ForeignKey(AuthorityGrant, on_delete=models.PROTECT, null=True, blank=True)
    policy_version = models.PositiveIntegerField(default=1)
    target_label = models.CharField(max_length=180)
    target_id = models.UUIDField()
    revision = models.ForeignKey(Revision, on_delete=models.PROTECT, null=True, blank=True, related_name='approvals')
    decision = models.CharField(max_length=32)
    reason = models.TextField()
    class Meta:
        ordering = ['-created_at']

class Release(Entity):
    unit = models.ForeignKey(HardwareUnit, on_delete=models.PROTECT, related_name='releases')
    approval = models.OneToOneField(Approval, on_delete=models.PROTECT)
    route = models.CharField(max_length=20, choices=[('normal', 'Conforming'), ('pending', 'Pending coupon authorization'), ('owner', 'Owner action; requirements shown')])
    evidence_manifest = models.JSONField(default=dict)
    outstanding = models.JSONField(default=list)
    pending_authorization = models.ForeignKey(Approval, on_delete=models.PROTECT, null=True, blank=True, related_name='pending_releases')
    class Meta:
        ordering = ['-created_at']

class Shipment(Entity):
    unit = models.ForeignKey(HardwareUnit, on_delete=models.PROTECT, related_name='shipments')
    release = models.ForeignKey(Release, on_delete=models.PROTECT)
    reference = models.CharField(max_length=140)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    shipped_at = models.DateTimeField(default=timezone.now)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['unit'], name='single_prototype_shipment')]

class Attachment(Entity):
    revision = models.ForeignKey(Revision, on_delete=models.PROTECT, related_name='attachments')
    file = models.FileField(upload_to='private/%Y/%m/')
    original_name = models.CharField(max_length=180)
    sha256 = models.CharField(max_length=64)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    signed_paper = models.BooleanField(default=False)

class AuditEvent(Entity):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=80)
    target = models.CharField(max_length=180)
    detail = models.JSONField(default=dict)
    class Meta:
        ordering = ['-created_at']
