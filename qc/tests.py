"""Synthetic software fixtures only; none of these limits/approvals are engineering evidence."""
from datetime import timedelta
from io import BytesIO
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from .models import *
from . import services as s

@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class PrototypeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cone=Organization.objects.create(code='CONE',name='Cone')
        cls.pg=Organization.objects.create(code='PICOGRID',name='Picogrid')
        cls.amk=Organization.objects.create(code='AMK',name='AM Kreations')
        cls.owner=cls.make_user('owner',cls.amk,owner=True,senior=True)
        cls.approver=cls.make_user('cone',cls.cone,senior=True)
        cls.customer=cls.make_user('customer',cls.pg,senior=True)
        cls.worker=cls.make_user('worker',cls.cone)
        cls.viewer=cls.make_user('viewer',cls.pg)
        for u in [cls.owner,cls.approver,cls.worker,cls.customer]: cls.grant(u,'enter',u.profile.organization)
        for action in ['coupon_accept','qualification_approve','readiness','hold_close','ncr_close','release','ship','impact_clear']: cls.grant(cls.approver,action,cls.cone)
        for action in ['procedure_approve','disposition','at_risk','impact_clear']: cls.grant(cls.customer,action,cls.pg)
        cls.person=Person.objects.create(name='Synthetic worker',organization=cls.cone,user=cls.worker)
        cls.machine=Machine.objects.create(identifier='M1',model='Test model',serial='MACHINE-1')
        cls.job=WorkOrder.objects.create(number='TEST-WO',title='Synthetic test job')
        cls.unit=HardwareUnit.objects.create(serial='TEST-001',work_order=cls.job,part_number='TEST',drawing_revision='SYNTHETIC')
        cls.other_unit=HardwareUnit.objects.create(serial='TEST-002',work_order=cls.job,part_number='TEST',drawing_revision='SYNTHETIC')
        cls.plan=cls.fixture_revision('PLAN','plan',{'coupon_count':2,'required_tests':['macroetch'],'proof_applicable':False})
        cls.wps=cls.fixture_revision('WPS','wps')
        cls.evidence=cls.fixture_revision('EVIDENCE','pqr')
        cls.op=Operation.objects.create(unit=cls.unit,joint_family='tts',operator=cls.person,machine=cls.machine,wps=cls.wps,plan=cls.plan,material_lot='LOT-A',filler_lot='FILLER-A',fixture_reference='FIXTURE-TEST',state='gate2')
    @classmethod
    def make_user(cls,name,org,owner=False,senior=False):
        u=get_user_model().objects.create_user(name,password='synthetic-test-password')
        Profile.objects.create(user=u,organization=org,is_owner=owner,is_senior=senior)
        return u
    @classmethod
    def grant(cls,user,action,org):
        return AuthorityGrant.objects.create(user=user,organization=org,action=action,evidence='Synthetic test designation, not actual authority.')
    @classmethod
    def fixture_revision(cls,number,kind='inspection',payload=None,unit=None,performer=None,resolved=True):
        record=ControlledRecord.objects.create(number=number,kind=kind,title='Synthetic software fixture',unit=unit)
        rev=Revision.objects.create(record=record,body='SYNTHETIC FIXTURE ONLY',payload=payload or {},requirements_resolved=resolved,basis='Synthetic software fixture; not engineering requirements.',state='approved' if resolved else 'draft',performed_by=performer,entered_by=cls.owner,frozen_at=timezone.now() if resolved else None)
        record.current_revision=rev;record.save()
        return rev
    def ready(self):
        for kind in ['operator','machine']:
            Qualification.objects.create(kind=kind,person=self.person if kind=='operator' else None,machine=self.machine if kind=='machine' else None,wps=self.wps,joint_family='tts',evidence=self.evidence,status='qualified',last_activity=timezone.localdate(),activity_source='Synthetic actual-activity evidence')
        cs=self.coupon(status='accepted');cs.coverage.add(self.unit)
        self.fixture_revision('FINAL',payload={'stage':'final','result':'pass'},unit=self.unit)
        return cs
    def coupon(self,status='pending',purpose='production',number='CV-TEST'):
        return CouponSet.objects.create(number=number,purpose=purpose,joint_family='tts',operation=self.op,plan=self.plan,operator=self.person,machine=self.machine,material_lot='LOT-A',status=status)
    def specimen(self,cs=None,number='SP-TEST',nde=True):
        cs=cs or self.coupon()
        assembly=CouponAssembly.objects.create(coupon_set=cs,identifier='ASSY-'+number,drawing_reference='SYNTHETIC',nde_complete=nde)
        weld=CouponWeld.objects.create(assembly=assembly,side='A')
        PassActual.objects.create(weld=weld,ordinal=1,raw_parameters='Synthetic software fixture actuals, not production settings.')
        specimen=Specimen.objects.create(identifier=number,assembly=assembly,layout_reference='SYNTHETIC',integrity='valid')
        specimen.welds.add(weld)
        return specimen
    def record_test(self,specimen,**overrides):
        data={'method':'macroetch','provider':'Synthetic lab','method_reference':'Synthetic fixture method','validity':'valid','result':'pass','observations':'Software fixture observations','report':self.evidence}
        data.update(overrides)
        return s.record_test(self.approver,specimen=specimen,**data)

    def test_membership_and_superuser_do_not_grant_approval(self):
        self.viewer.is_superuser=True;self.viewer.save()
        with self.assertRaises(PermissionDenied): s.authorize(self.viewer,'release')
    def test_wrong_organization_cannot_disposition(self):
        with self.assertRaises(PermissionDenied): s.authorize(self.approver,'disposition')
    def test_owner_capacity_must_be_explicit(self):
        with self.assertRaises(PermissionDenied): s.authorize(self.owner,'release')
        self.assertIsNone(s.authorize(self.owner,'release','owner'))
    def test_other_user_cannot_select_owner(self):
        with self.assertRaises(PermissionDenied): s.authorize(self.customer,'release','owner')
    def test_delegate_capacity_requires_recorded_customer_grant(self):
        with self.assertRaises(PermissionDenied): s.authorize(self.owner,'disposition','picogrid')
        g=self.grant(self.owner,'disposition',self.pg)
        self.assertEqual(s.authorize(self.owner,'disposition','picogrid'),g)
    def test_revoked_and_expired_grants_fail(self):
        g=AuthorityGrant.objects.get(user=self.approver,action='release')
        g.ends_at=timezone.now()-timedelta(seconds=1);g.save()
        with self.assertRaises(PermissionDenied): s.authorize(self.approver,'release')
        g.ends_at=None;g.revoked_at=timezone.now();g.save()
        with self.assertRaises(PermissionDenied): s.authorize(self.approver,'release')
    def test_self_approval_requires_authority(self):
        with self.assertRaises(PermissionDenied): s.authorize(self.worker,'coupon_accept',performer=self.person)
        self.grant(self.worker,'coupon_accept',self.cone)
        self.assertIsNotNone(s.authorize(self.worker,'coupon_accept',performer=self.person))
    def test_self_approval_restriction_compares_performer_not_entrant(self):
        self.grant(self.worker,'coupon_accept',self.cone)
        s.change_policy(self.approver,self.cone,False)
        with self.assertRaises(PermissionDenied): s.authorize(self.worker,'coupon_accept',performer=self.person)
        self.assertIsNotNone(s.authorize(self.approver,'coupon_accept',performer=self.person))
    def test_senior_cannot_change_other_organization_policy(self):
        with self.assertRaises(PermissionDenied): s.change_policy(self.approver,self.pg,False)
    def test_policy_change_preserves_old_approval_version(self):
        a=s.decision(self.approver,'coupon_accept',self.unit,'Synthetic decision')
        s.change_policy(self.approver,self.cone,False)
        a.refresh_from_db();self.assertEqual(a.policy_version,1)
        self.cone.refresh_from_db();self.assertEqual(self.cone.policy_version,2)
    def test_senior_cannot_grant_picogrid_actions(self):
        with self.assertRaises(PermissionDenied): s.grant_authority(self.approver,self.worker,self.cone,'disposition','LANDER','Not customer authority')
    def test_unresolved_evidence_cannot_be_approved_even_by_owner(self):
        rev=self.fixture_revision('TBD',resolved=False)
        with self.assertRaises(ValidationError): s.approve_revision(self.owner,rev,'Owner review','owner')
        self.assertFalse(Approval.objects.filter(target_id=rev.record_id).exists())
    def test_wps_requires_separate_approved_pqr(self):
        record=s.create_record(self.owner,number='NEW-WPS',kind='wps',title='Synthetic',body='Draft',requirements_resolved=True,basis='Synthetic fixture')
        with self.assertRaises(ValidationError): s.approve_revision(self.customer,record.current_revision,'Approve')
    def test_frozen_revision_cannot_be_overwritten(self):
        self.evidence.body='Rewritten'
        with self.assertRaises(ValidationError): self.evidence.save()
    def test_amendment_preserves_old_revision_and_blocks_dependents(self):
        oldbody=self.plan.body
        new=s.amend_record(self.owner,self.plan.record,body='Corrected synthetic plan',reason='Incorrect source',basis='New draft')
        self.plan.refresh_from_db()
        self.assertEqual(self.plan.body,oldbody)
        self.assertEqual(new.number,2)
        self.assertTrue(self.unit.impacts.filter(status='open').exists())
    def test_impact_walks_transitive_dependencies(self):
        linked=self.fixture_revision('LINKED',unit=self.other_unit)
        EvidenceDependency.objects.create(source=self.evidence,target=linked)
        case=s.flag_impact(self.approver,self.evidence,'Incorrect test source')
        self.assertIn(self.other_unit,list(case.units.all()))
    def test_machine_hold_applies_across_serials(self):
        s.open_hold(self.approver,unit=self.other_unit,number='H-SHARED',origin='gate1',issue='Machine concern',machine=self.machine)
        self.assertTrue(s.active_holds(self.unit).exists())
    def test_process_hold_does_not_automatically_create_ncr(self):
        s.open_hold(self.worker,unit=self.unit,number='H-PROCESS',origin='gate1',issue='Process issue')
        self.assertEqual(NCR.objects.count(),0)
    def test_hold_cannot_close_with_only_pass_or_unresolved_problem(self):
        h=s.open_hold(self.worker,unit=self.unit,number='H1',origin='gate2',issue='Issue')
        HoldCheck.objects.create(hold=h,operator=self.person,machine=self.machine,result='pass',performed_at=timezone.now(),corrective_action_reference='Action',entered_by=self.worker)
        with self.assertRaises(ValidationError): s.close_hold(self.approver,h,'Close')
    def test_hold_gate2_return_does_not_close_ncr(self):
        h=s.open_hold(self.worker,unit=self.unit,number='H2',origin='gate2',issue='Issue')
        h.corrective_action='Cause fixed';h.problem_resolved=True;h.verification=self.evidence;h.save()
        HoldCheck.objects.create(hold=h,operator=self.person,machine=self.machine,result='pass',performed_at=timezone.now(),corrective_action_reference='Action',entered_by=self.worker)
        n=NCR.objects.create(number='NCR-H2',unit=self.unit,hold=h,description='Hardware concern')
        s.close_hold(self.approver,h,'Required checks passed')
        self.op.refresh_from_db();n.refresh_from_db()
        self.assertEqual(self.op.state,'gate2');self.assertEqual(n.status,'open')
    def test_failed_coupon_hold_requires_bc(self):
        h=s.open_hold(self.worker,unit=self.unit,number='H3',origin='gate1',issue='Failure')
        h.requires_bc=True;h.corrective_action='Fixed';h.problem_resolved=True;h.verification=self.evidence;h.save()
        HoldCheck.objects.create(hold=h,operator=self.person,machine=self.machine,result='pass',performed_at=timezone.now(),corrective_action_reference='Action',entered_by=self.worker)
        with self.assertRaises(ValidationError): s.close_hold(self.approver,h,'Only A passed')
    def test_invalid_test_is_not_weld_rejection(self):
        specimen=self.specimen()
        self.record_test(specimen,validity='invalid',result='pending',reason='Specimen slipped')
        self.assertFalse(NCR.objects.exists());self.assertFalse(Hold.objects.exists())
    def test_valid_failed_test_creates_hold_and_ncr(self):
        specimen=self.specimen()
        self.record_test(specimen,result='fail')
        self.assertEqual(NCR.objects.count(),1);self.assertEqual(Hold.objects.count(),1)
        self.assertTrue(Hold.objects.first().requires_bc)
    def test_nde_required_before_destructive_test(self):
        specimen=self.specimen(nde=False)
        with self.assertRaises(ValidationError): self.record_test(specimen)
    def test_corner_pull_exemption_is_enforced(self):
        cs=self.coupon();cs.joint_family='corner';cs.save()
        specimen=self.specimen(cs)
        with self.assertRaises(ValidationError): self.record_test(specimen,method='pull')
    def test_unknown_criteria_only_accept_raw_pending_observations(self):
        cs=self.coupon();plan=self.fixture_revision('UNKNOWN',kind='plan',resolved=False);cs.plan=plan;cs.save()
        sp=self.specimen(cs)
        with self.assertRaises(ValidationError): self.record_test(sp)
        self.record_test(sp,validity='pending',result='pending',report=None)
        self.assertEqual(TestAttempt.objects.count(),1)
    def test_repeat_test_keeps_original_attempt(self):
        sp=self.specimen()
        first=self.record_test(sp,validity='invalid',result='pending',reason='Slippage')
        second=self.record_test(sp,prior_attempt=first)
        self.assertEqual(second.prior_attempt,first);self.assertEqual(TestAttempt.objects.count(),2)
    def test_two_sides_do_not_count_as_two_physical_coupons(self):
        cs=self.coupon();sp=self.specimen(cs)
        CouponWeld.objects.create(assembly=sp.assembly,side='B')
        with self.assertRaisesMessage(ValidationError,'physical coupon'):s.accept_coupon(self.approver,cs,'Accept')
    def test_complete_coupon_acceptance_requires_each_weld_test(self):
        cs=self.coupon()
        for i in [1,2]:
            sp=self.specimen(cs,number=f'SP-{i}')
            self.record_test(sp)
        s.accept_coupon(self.approver,cs,'Synthetic full coverage')
        cs.refresh_from_db();self.assertEqual(cs.status,'accepted')
    def test_failed_result_cannot_be_tested_away(self):
        cs=self.coupon();sp=self.specimen(cs)
        self.record_test(sp,result='fail')
        self.record_test(sp,result='pass')
        with self.assertRaises(ValidationError):s.accept_coupon(self.approver,cs,'Use later pass')
    def test_qualification_requires_section_c_and_accepted_b(self):
        q=Qualification.objects.create(kind='operator',person=self.person,wps=self.wps,joint_family='tts',evidence=self.evidence)
        with self.assertRaises(ValidationError): s.award_qualification(self.approver,q,'Approve')
    def test_model_identity_does_not_transfer_machine_qualification(self):
        self.ready();replacement=Machine.objects.create(identifier='M2',model='Test model',serial='MACHINE-2')
        self.op.machine=replacement
        self.assertFalse(s.qualification_current(self.op,'machine'))
    def test_accepted_coupon_from_wrong_context_cannot_start_production(self):
        cs=self.ready();cs.material_lot='OTHER-LOT';cs.save()
        self.op.state='triggers';self.op.save()
        with self.assertRaises(ValidationError):s.advance_operation(self.approver,self.op,'start_welding','Synthetic context mismatch',version=self.op.version)

    def test_more_than_six_months_inactivity_prevents_current_award(self):
        self.ready();Qualification.objects.filter(kind='operator').update(last_activity=timezone.localdate()-timedelta(days=200))
        self.assertFalse(s.qualification_current(self.op,'operator'))
    def test_unknown_activity_is_not_continuity_evidence(self):
        self.ready();Qualification.objects.filter(kind='operator').update(last_activity=None)
        self.assertFalse(s.qualification_current(self.op,'operator'))
    def test_normal_release_uses_only_complete_defined_evidence(self):
        self.ready();issues,pending,_=s.release_checklist(self.unit)
        self.assertEqual(issues,[]);self.assertEqual(pending,[])
        rel=s.release_unit(self.approver,self.unit,'Synthetic complete evidence')
        self.assertEqual(rel.route,'normal');self.assertEqual(self.unit.shipments.count(),0)
    def test_pending_coupon_not_normal_release(self):
        cs=self.ready();cs.status='pending';cs.save()
        with self.assertRaises(ValidationError):s.release_unit(self.approver,self.unit,'Normal')
    def test_pending_release_requires_explicit_picogrid_authorization(self):
        cs=self.ready();cs.status='pending';cs.save()
        with self.assertRaises(ValidationError):s.release_unit(self.approver,self.unit,'Pending',route='pending')
        a=s.authorize_pending(self.customer,self.unit,'Explicit synthetic pending coupon scope')
        rel=s.release_unit(self.approver,self.unit,'Execute authorization',route='pending')
        self.assertEqual(rel.pending_authorization,a)
    def test_known_failure_cannot_use_pending_exception(self):
        cs=self.ready();cs.status='rejected';cs.save()
        with self.assertRaises(ValidationError): s.authorize_pending(self.customer,self.unit,'Not eligible')
    def test_owner_action_preserves_outstanding_requirements_and_identity(self):
        rel=s.release_unit(self.owner,self.unit,'Explicit synthetic owner action','owner',route='owner')
        self.assertTrue(rel.outstanding);self.assertEqual(rel.approval.actor,self.owner)
        self.assertEqual(rel.approval.capacity,'owner');self.assertIsNone(rel.approval.grant)
        self.wps.refresh_from_db();self.assertEqual(self.wps.body,'SYNTHETIC FIXTURE ONLY')
    def test_one_serial_hold_does_not_block_other_serial_without_shared_scope(self):
        self.ready();s.open_hold(self.worker,unit=self.other_unit,number='OTHER-H',origin='gate1',issue='Other unit only')
        rel=s.release_unit(self.approver,self.unit,'Independent synthetic serial')
        self.assertEqual(rel.unit,self.unit)
    def test_new_impact_prevents_shipment_after_release_without_erasing_release(self):
        self.ready();rel=s.release_unit(self.approver,self.unit,'Synthetic release')
        s.flag_impact(self.approver,self.plan,'Report / criterion found incorrect')
        with self.assertRaises(ValidationError):s.record_shipment(self.approver,rel,'SHIP-1','Ship')
        self.assertTrue(Release.objects.filter(pk=rel.pk).exists());self.assertFalse(Shipment.objects.exists())
    def test_shipment_keeps_actual_history_after_late_impact(self):
        self.ready();rel=s.release_unit(self.approver,self.unit,'Synthetic release')
        shipment=s.record_shipment(self.approver,rel,'SHIP-1','Synthetic shipment')
        case=s.flag_impact(self.approver,self.plan,'Late corrected source')
        self.assertTrue(Shipment.objects.filter(pk=shipment.pk).exists());self.assertIn(self.unit,list(case.units.all()))
    def test_stale_workflow_version_is_rejected(self):
        with self.assertRaises(ValidationError):s.advance_operation(self.approver,self.op,'final_inspection','Reason',version=0)
    def test_workflow_qualification_returns_to_start_not_welding(self):
        self.ready();self.op.state='verification';self.op.save()
        op=s.advance_operation(self.approver,self.op,'return_c','Synthetic qualifying return',version=self.op.version)
        self.assertEqual(op.state,'start')
    def test_frozen_evidence_rejects_added_attachment(self):
        upload=SimpleUploadedFile('test.pdf',b'%PDF-1.4\nfixture')
        with self.assertRaises(ValidationError):s.add_attachment(self.approver,self.evidence,upload)
    def test_active_content_disguised_as_pdf_is_rejected(self):
        rev=self.fixture_revision('DRAFT-UPLOAD',resolved=False)
        upload=SimpleUploadedFile('test.pdf',b'<script>unsafe</script>')
        with self.assertRaises(ValidationError):s.add_attachment(self.approver,rev,upload)
    def test_private_download_requires_login(self):
        response=self.client.get('/evidence/00000000-0000-0000-0000-000000000001/')
        self.assertEqual(response.status_code,302)
    def test_all_workspace_pages_render_for_member(self):
        self.client.force_login(self.approver)
        cs=self.coupon();h=s.open_hold(self.worker,unit=self.unit,number='PAGE-HOLD',origin='gate1',issue='Synthetic')
        n=NCR.objects.create(number='PAGE-NCR',unit=self.unit,description='Synthetic')
        for url in ['/', '/jobs/',f'/jobs/{self.job.pk}/',f'/units/{self.unit.pk}/',f'/operations/{self.op.pk}/','/records/',f'/records/{self.plan.record_id}/','/coupons/',f'/coupons/{cs.pk}/','/issues/',f'/holds/{h.pk}/',f'/ncrs/{n.pk}/','/qualifications/','/resources/','/decisions/','/impacts/','/authority/','/sources/',f'/units/{self.unit.pk}/dossier/']:
            with self.subTest(url=url):self.assertEqual(self.client.get(url).status_code,200)
    def test_read_only_viewer_cannot_create_record_via_post(self):
        self.client.force_login(self.viewer)
        response=self.client.post('/jobs/new/',{'number':'HACK','title':'Unauthorized'})
        self.assertEqual(response.status_code,403);self.assertFalse(WorkOrder.objects.filter(number='HACK').exists())
    def test_csrf_is_required_for_authenticated_write(self):
        from django.test import Client
        client=Client(enforce_csrf_checks=True);client.force_login(self.approver)
        self.assertEqual(client.post('/jobs/new/',{'number':'FORGED','title':'No CSRF'}).status_code,403)
    def test_duplicate_physical_weld_identity_rejected(self):
        sp=self.specimen()
        with self.assertRaises(IntegrityError),transaction.atomic():CouponWeld.objects.create(assembly=sp.assembly,side='A')

    def test_failed_inspection_routes_to_hold_and_ncr_without_concealing_failure(self):
        record=s.create_record(self.approver,number='FAILED-INSP',kind='inspection',title='Synthetic failed final inspection',body='Raw indication',unit=self.unit,payload={'stage':'final','result':'fail'})
        self.assertTrue(Hold.objects.filter(unit=self.unit,origin='gate2').exists())
        self.assertTrue(NCR.objects.filter(unit=self.unit).exists())
        self.assertEqual(record.current_revision.payload['result'],'fail')
    def test_hardware_impact_cannot_be_cleared_with_only_cone_process_authority(self):
        case=s.flag_impact(self.approver,self.plan,'Incorrect supporting evidence')
        with self.assertRaises(PermissionDenied):s.clear_impact(self.approver,case,'Process review alone')
        s.clear_impact(self.customer,case,'Synthetic customer-scoped resolution')
        case.refresh_from_db();self.assertEqual(case.status,'resolved')
    def test_cannot_revoke_other_organization_grant(self):
        grant=AuthorityGrant.objects.filter(user=self.customer,action='disposition').first()
        with self.assertRaises(PermissionDenied):s.revoke_authority(self.approver,grant)
    def test_read_only_viewer_cannot_download_files_without_membership(self):
        self.viewer.profile.delete()
        self.client.force_login(self.viewer)
        self.assertEqual(self.client.get('/').status_code,403)

from django.test import TransactionTestCase, skipUnlessDBFeature
from django.db import close_old_connections, connections
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class ConcurrencyTests(TransactionTestCase):
    @skipUnlessDBFeature('has_select_for_update')
    def test_simultaneous_approvals_cannot_approve_one_revision_twice(self):
        org=Organization.objects.create(code='CONE',name='Cone')
        users=[]
        for name in ['reviewer_a','reviewer_b']:
            u=get_user_model().objects.create_user(name,password='synthetic-test-password')
            Profile.objects.create(user=u,organization=org)
            AuthorityGrant.objects.create(user=u,organization=org,action='coupon_accept',evidence='Synthetic concurrency fixture')
            users.append(u)
        record=ControlledRecord.objects.create(number='CONCURRENT',kind='inspection',title='Synthetic test evidence')
        revision=Revision.objects.create(record=record,body='Synthetic test fixture',requirements_resolved=True,basis='Not engineering evidence',entered_by=users[0])
        record.current_revision=revision;record.save()
        barrier=Barrier(2)
        def approve(uid):
            close_old_connections()
            try:
                actor=get_user_model().objects.get(pk=uid)
                target=Revision.objects.get(pk=revision.pk)
                barrier.wait(timeout=10)
                try:
                    s.approve_revision(actor,target,'Synthetic concurrent review')
                    return 'approved'
                except ValidationError:
                    return 'stale'
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(approve,[u.pk for u in users]))
        self.assertCountEqual(results,['approved','stale'])
        self.assertEqual(Approval.objects.filter(target_id=record.pk).count(),1)
