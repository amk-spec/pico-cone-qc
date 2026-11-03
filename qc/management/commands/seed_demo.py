"""Synthetic examples only. Never imports historical observations as qualifications."""
import secrets
from pathlib import Path
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import os
from django.core.files import File
from django.db import transaction
from qc.models import *
from qc.services import create_record, audit

class Command(BaseCommand):
    help='Create idempotent synthetic demo accounts/data; credentials written to ignored .local/demo-accounts.txt'
    def hosted_passwords(self):
        if not settings.HOSTED_PREVIEW: return {}
        passwords={}
        for name in ['owner','cone','picogrid','operator','delegate','viewer']:
            value=os.environ.get(f'LANDER_PREVIEW_{name.upper()}_PASSWORD','')
            if name=='owner' and not value:
                raise CommandError('Set LANDER_PREVIEW_OWNER_PASSWORD securely in hosting settings before starting the preview.')
            if value:
                if len(value)<16: raise CommandError('Hosted preview account passwords must contain at least 16 characters.')
                try: validate_password(value)
                except ValidationError: raise CommandError('A configured preview password does not meet the password policy. Choose a long, unique password.')
                passwords[name]=value
        return passwords

    @transaction.atomic
    def handle(self,*args,**options):
        hosted_passwords=self.hosted_passwords()
        if WorkOrder.objects.filter(number='DEMO-WO-104').exists():
            for name,password in hosted_passwords.items():
                u=get_user_model().objects.get(username=name)
                if not u.check_password(password):
                    u.set_password(password);u.save(update_fields=['password'])
            self.stdout.write('Demo already exists; records preserved. Hosted account settings synchronized when configured.')
            return
        orgs={code:Organization.objects.get_or_create(code=code,defaults={'name':name})[0] for code,name in [('CONE','Cone Engineering'),('PICOGRID','Picogrid'),('AMK','AM Kreations')]}
        definitions=[('owner','Prototype Owner','AMK',True,True),('cone','Demo Cone Approver','CONE',False,True),('picogrid','Demo Picogrid Approver','PICOGRID',False,True),('operator','Demo Welding Operator','CONE',False,False),('delegate','Demo Picogrid Delegate','AMK',False,False),('viewer','Demo Program Viewer','PICOGRID',False,False)]
        users={};credentials=[]
        for username,name,org,owner,senior in definitions:
            u,created=get_user_model().objects.get_or_create(username=username,defaults={'first_name':name,'is_staff':False})
            if created:
                password=hosted_passwords.get(username) or secrets.token_urlsafe(18);u.set_password(password);u.save();credentials.append(f'{username}\t{password}\t{name}')
            Profile.objects.get_or_create(user=u,defaults={'organization':orgs[org],'is_owner':owner,'is_senior':senior})
            users[username]=u
        for name in ['owner','cone','picogrid','operator','delegate']:
            AuthorityGrant.objects.create(user=users[name],organization=users[name].profile.organization,action='enter',evidence='Synthetic prototype designation; no real engineering delegation.')
        for action in ['coupon_accept','qualification_approve','readiness','hold_close','ncr_close','release','ship','impact_clear']:
            AuthorityGrant.objects.create(user=users['cone'],organization=orgs['CONE'],action=action,evidence='Synthetic Cone role for prototype review only.')
        for name in ['picogrid','delegate']:
            for action in ['procedure_approve','disposition','at_risk','impact_clear']:
                AuthorityGrant.objects.create(user=users[name],organization=orgs['PICOGRID'],action=action,evidence='Synthetic Picogrid delegation example; not an actual customer appointment.')
        operator=Person.objects.create(name='Demo welding operator',organization=orgs['CONE'],user=users['operator'])
        assisted=Person.objects.create(name='Demo manual-record performer',organization=orgs['CONE'])
        machine=Machine.objects.create(identifier='DEMO-OPT-X01',model='Miller OptX 2 kW',serial='DEMO-MACHINE-001')
        Machine.objects.create(identifier='DEMO-OPT-X02',model='Miller OptX 2 kW',serial='DEMO-MACHINE-002')
        owner=users['owner']
        wps=create_record(owner,number='DEMO-WPS-001',kind='wps',title='Lander welding procedure — working draft',body='Synthetic prototype record. WPS parameter ranges and joint-specific criteria remain TBD pending the controlled engineering process. No settings are qualified by this template.',performed_by=assisted,basis='Rev A / Section C; approval and technical limits remain unresolved.')
        plan=create_record(owner,number='DEMO-PLAN-001',kind='plan',title='Joint-specific verification plan',body='Define approved coupon frequency, due point, physical coupon count, specimen layout, validity and joint-specific acceptance. Do not assume ten pieces/batches, 20 minutes idle or preliminary drawing limits.',basis='Rev C B; Rev A 1.8 / B.5 / 3.9. Unresolved; not production-approved.',payload={'proof_applicable':'TBD','required_tests':[]})
        job=WorkOrder.objects.create(number='DEMO-WO-104',title='Lander enclosure · pilot build',customer_reference='Synthetic program example',traveler_reference='Application traveler / demonstration',notes='Synthetic review data only. Each serial may have independent operations, holds and release decisions. No real production orders or weld qualifications are represented.')
        units=[]
        for n in range(14,18):
            u=HardwareUnit.objects.create(serial=f'DEMO-LN-{n:03}',work_order=job,part_number='LANDER-DEMO',drawing_revision='Drawing release TBD')
            Operation.objects.create(unit=u,joint_family='corner' if n%2 else 'tts',operator=operator,machine=machine,wps=wps.current_revision,plan=plan.current_revision,material_lot='DEMO-MATERIAL-A',filler_lot='DEMO-FILLER-A',fixture_reference='Fixture / controlled revision TBD',state='verification' if n!=16 else 'gate2')
            units.append(u)
        job2=WorkOrder.objects.create(number='DEMO-WO-105',title='Tube-to-sheet · process development',customer_reference='Synthetic development example',notes='Development hardware is never production hardware.')
        for n in [18,19]:
            HardwareUnit.objects.create(serial=f'DEMO-LN-{n:03}',work_order=job2,part_number='LANDER-DEMO',drawing_revision='Reference drawing only')
        cs=CouponSet.objects.create(number='DEMO-CV-014',purpose='production',joint_family='tts',operation=units[0].operations.first(),plan=plan.current_revision,operator=operator,machine=machine,material_lot='DEMO-MATERIAL-A',notes='Synthetic pending set. Specimens, actual source reports, approved limits and test methods are not yet available.')
        cs.coverage.add(units[0])
        assembly=CouponAssembly.objects.create(coupon_set=cs,identifier='DEMO-TTS-01',drawing_reference='AMK-TTS preliminary; released revision TBD')
        for side in ['A','B']:
            w=CouponWeld.objects.create(assembly=assembly,side=side,observations='Synthetic side identity; actual observations not yet recorded.')
            PassActual.objects.create(weld=w,ordinal=1,raw_parameters='Not entered. No qualified values inferred.',observations='Root-pass source evidence pending.')
        CouponSet.objects.create(number='DEMO-DEV-002',purpose='development',joint_family='corner',plan=plan.current_revision,operator=assisted,machine=machine,material_lot='DEMO-SCRAP',notes='Development-only finishing-method review. No production hardware and no inferred qualification.')
        hold=Hold.objects.create(number='DEMO-H-003',unit=units[2],origin='gate2',issue='Synthetic final-inspection issue requiring review before finishing / release.',hardware_affected=True,containment='Demo serial segregated; affected extent to be confirmed.',notification='Prototype notification reference only; no message has been sent.',raised_by=users['cone'])
        NCR.objects.create(number='DEMO-NCR-001',unit=units[2],hold=hold,description='Synthetic suspected hardware nonconformance for customer disposition review.',proposed_disposition='Proposed investigation only; no authorized rework or acceptance.')
        create_record(owner,number='DEMO-INSP-016',kind='inspection',title='Outside-corner final inspection',unit=units[2],body='Raw observations pending a defined inspection basis. Signed paper can be attached and reviewed without requiring the performer to log in.',performed_by=assisted,payload={'stage':'final','result':'pending'})
        create_record(owner,number='DEMO-DEV-RECORD-002',kind='development',title='Outside-corner finishing trial',body='Synthetic development record: compare finishing observations on scrap/development coupons. Store actual settings and notes without turning them into qualified WPS ranges.',performed_by=assisted)
        create_record(owner,number='DEMO-MAINT-001',kind='maintenance',title='Equipment change / impact assessment',machine=machine,body='Synthetic pending maintenance assessment. Routine setup/minor changes route A; applicable major maintenance routes C including B. Classification boundaries remain controlled engineering requirements.')
        Qualification.objects.create(kind='operator',person=operator,wps=wps.current_revision,joint_family='tts',evidence=wps.current_revision,activity_source='No source-backed continuity evidence yet; not qualified.')
        Qualification.objects.create(kind='machine',machine=machine,wps=wps.current_revision,joint_family='tts',evidence=plan.current_revision)
        source_specs=[('FLOW-REV-C','Rev C · governing workflow','Rev C · October 30, 2026. Locked for software development. Discussion Draft — Not Approved for Production Use.','*Flowchart*.pdf'),('PROC-REV-A','Rev A · written procedure','Rev A · November 2, 2026. Working Master Discussion Draft. H.2.7 preserves Gate 2-origin return; 1.6 requires requalification after more than six months of operator inactivity.','*Procedure*.pdf'),('WORKBOOK-20261102','QC master · 11 reference worksheets','Working draft workbook dated November 2, 2026. Reference forms and historical raw development data are not production approval. Source 9-1 and M1 Pass Data are referenced but absent.','*.xlsx')]
        import hashlib
        for number,title,body,pattern in source_specs:
            source=create_record(owner,number=number,kind='source',title=title,body=body)
            matches=[] if settings.HOSTED_PREVIEW else list(Path('/workspace/attachments').rglob(pattern))
            if len(matches)==1:
                path=matches[0]
                with path.open('rb') as stream:
                    Attachment.objects.create(revision=source.current_revision,file=File(stream,name=path.name),original_name=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),uploaded_by=owner)
        audit(owner,'demo_initialized',job,notice='Synthetic data; no historical observations interpreted as qualification or actual shipment.')
        if settings.HOSTED_PREVIEW:
            self.stdout.write('Synthetic hosted preview initialized. Sign in using securely configured preview account settings; credentials are not written to files or logs.')
            return
        out=settings.LOCAL_DIR/'demo-accounts.txt'
        out.write_text('Prototype-only local accounts. Do not use outside this development instance.\n'+'\n'.join(credentials)+'\n')
        out.chmod(0o600)
        self.stdout.write(f'Synthetic prototype data created. Local credentials: {out.relative_to(settings.BASE_DIR)} (not tracked).')
