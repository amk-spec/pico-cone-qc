from functools import wraps
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import FileResponse, HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from . import forms, services as svc
from .models import *


def member(view):
    @login_required
    @wraps(view)
    def wrapped(request,*args,**kwargs):
        p=svc.profile(request.user)
        if p.organization.code not in ('CONE','PICOGRID','AMK'):
            raise PermissionDenied('No Lander-program membership.')
        return view(request,*args,**kwargs)
    return wrapped


def attempt(request, callback):
    try:
        result=callback()
    except ValidationError as e:
        for text in e.messages: messages.error(request,text)
        return None,False
    messages.success(request,'Prototype record saved. This is not production authorization.')
    return result,True


def entry_authority(request):
    svc.authorize(request.user,'enter','owner' if svc.profile(request.user).is_owner else 'organization')


def form_page(request, form, title, eyebrow='NEW RECORD', back='/', description='', save=None):
    if request.method=='POST' and form.is_valid():
        obj,ok=attempt(request,lambda:save(form))
        if ok: return redirect(back(obj) if callable(back) else back)
    return render(request,'qc/form.html',{'form':form,'title':title,'eyebrow':eyebrow,'back':back if isinstance(back,str) else '/','description':description,'multipart':True})

@member
def dashboard(request):
    units=HardwareUnit.objects.select_related('work_order').all()
    return render(request,'qc/dashboard.html',{'title':'Program overview','jobs':WorkOrder.objects.prefetch_related('units')[:4], 'unit_count':units.count(),'job_count':WorkOrder.objects.count(),'coupon_count':CouponSet.objects.count(),'pending_count':CouponSet.objects.filter(status='pending').count(),'approval_count':Revision.objects.filter(state__in=['draft','submitted']).exclude(record__kind='source').count(),'recent':AuditEvent.objects.select_related('actor')[:7], 'units':units[:6], 'todo_records':ControlledRecord.objects.filter(current_revision__state__in=['draft','submitted']).exclude(kind='source')[:4], 'holds':Hold.objects.exclude(status='closed').select_related('unit')[:3]})

@member
def jobs(request):
    query=request.GET.get('q','')
    qs=WorkOrder.objects.prefetch_related('units')
    if query: qs=qs.filter(Q(number__icontains=query)|Q(title__icontains=query)|Q(units__serial__icontains=query)).distinct()
    return render(request,'qc/jobs.html',{'title':'Work orders','jobs':qs,'q':query})

@member
def job_detail(request,pk):
    job=get_object_or_404(WorkOrder,pk=pk)
    return render(request,'qc/job.html',{'title':job.number,'job':job,'units':job.units.prefetch_related('operations','holds','ncrs','shipments')})

@member
def job_new(request):
    entry_authority(request)
    def save(form):
        obj=form.save();svc.audit(request.user,'work_order_created',obj);return obj
    return form_page(request,forms.WorkOrderForm(request.POST or None),'New work order',back=lambda x:f'/jobs/{x.pk}/',save=save)

@member
def unit_new(request):
    entry_authority(request)
    def save(form):
        obj=form.save();svc.audit(request.user,'serial_created',obj);return obj
    return form_page(request,forms.UnitForm(request.POST or None,initial={'work_order':request.GET.get('job')}),'Add Lander serial',back=lambda x:f'/units/{x.pk}/',save=save)

@member
def unit_detail(request,pk):
    unit=get_object_or_404(HardwareUnit.objects.select_related('work_order'),pk=pk)
    issues,pending,manifest=svc.release_checklist(unit)
    return render(request,'qc/unit.html',{'title':unit.serial,'unit':unit,'operations':unit.operations.select_related('operator','machine','wps__record','plan__record'),'issues':issues,'pending':pending,'manifest':manifest,'records':unit.records.select_related('current_revision'),'holds':svc.active_holds(unit),'ncrs':unit.ncrs.all(),'releases':unit.releases.select_related('approval__actor'),'impacts':unit.impacts.filter(status='open'),'decision_form':forms.DecisionForm(),'shipments':unit.shipments.all()})

@member
@require_POST
def unit_action(request,pk):
    unit=get_object_or_404(HardwareUnit,pk=pk)
    f=forms.DecisionForm(request.POST)
    if f.is_valid():
        d=f.cleaned_data;action=request.POST.get('action')
        if action=='release':
            attempt(request,lambda:svc.release_unit(request.user,unit,d['reason'],d['capacity'],request.POST.get('route','normal')))
        elif action=='at_risk': attempt(request,lambda:svc.authorize_pending(request.user,unit,d['reason'],d['capacity']))
        elif action=='ship':
            rel=get_object_or_404(Release,pk=request.POST.get('release'),unit=unit)
            attempt(request,lambda:svc.record_shipment(request.user,rel,request.POST.get('reference',''),d['reason'],d['capacity']))
        else: raise Http404
    else: messages.error(request,'Select capacity and enter a decision basis.')
    return redirect('unit',pk=unit.pk)

@member
def operation_new(request):
    entry_authority(request)
    def save(form):
        obj=form.save();svc.audit(request.user,'operation_created',obj);return obj
    return form_page(request,forms.OperationForm(request.POST or None,initial={'unit':request.GET.get('unit')}),'Define a welding operation',back=lambda x:f'/operations/{x.pk}/',description='Link the actual operator, unique machine, lots, WPS and plan. Undefined requirements remain review-needed.',save=save)

@member
def operation_detail(request,pk):
    op=get_object_or_404(Operation.objects.select_related('unit','operator','machine','wps__record','plan__record'),pk=pk)
    if request.method=='POST':
        f=forms.DecisionForm(request.POST)
        if f.is_valid():
            attempt(request,lambda:svc.advance_operation(request.user,op,request.POST.get('action'),f.cleaned_data['reason'],f.cleaned_data['capacity'],int(request.POST.get('version',-1))))
        else: messages.error(request,'Enter a decision basis and acting capacity.')
        return redirect('operation',pk=pk)
    return render(request,'qc/operation.html',{'title':str(op),'operation':op,'issues':svc.readiness_issues(op),'decision_form':forms.DecisionForm(),'runs':op.runs.all(),'coupons':op.coupons.all()})

@member
def record_list(request):
    qs=ControlledRecord.objects.select_related('current_revision','unit')
    group=request.GET.get('group');kind=request.GET.get('kind','')
    if group=='procedures': qs=qs.filter(kind__in=['wps','pqr','plan'])
    elif group=='inspections': qs=qs.filter(kind__in=['inspection','proof'])
    elif kind: qs=qs.filter(kind=kind)
    else: qs=qs.exclude(kind='source')
    query=request.GET.get('q','')
    if query: qs=qs.filter(Q(number__icontains=query)|Q(title__icontains=query))
    return render(request,'qc/records.html',{'title':'WPS & PQR' if group=='procedures' else 'Inspections & proof' if group=='inspections' else dict(KINDS).get(kind,'Controlled records'),'records':qs,'q':query,'kind':kind,'group':group})

@member
def record_new(request):
    entry_authority(request)
    form=forms.RecordForm(request.POST or None,initial={'kind':request.GET.get('kind','inspection'),'unit':request.GET.get('unit')})
    def save(f):
        d=f.cleaned_data
        return svc.create_record(request.user,**{k:d[k] for k in ['number','kind','title','body','unit','machine','performed_by','performed_at','requirements_resolved','basis']},payload=f.payload())
    return form_page(request,form,'Create controlled record',back=lambda x:f'/records/{x.pk}/',description='Capture facts once. Paper source, performer, entry person and approval remain separately attributable. All content here is prototype-only.',save=save)

@member
def record_detail(request,pk):
    record=get_object_or_404(ControlledRecord.objects.select_related('current_revision','unit','machine'),pk=pk)
    return render(request,'qc/record.html',{'title':record.number,'record':record,'revision':record.current_revision,'revisions':record.revisions.select_related('entered_by','performed_by'),'decision_form':forms.DecisionForm(),'attachment_form':forms.AttachmentForm(),'approvals':Approval.objects.filter(target_id=record.pk).select_related('actor','grant__organization')})

@member
@require_POST
def record_action(request,pk):
    record=get_object_or_404(ControlledRecord,pk=pk)
    action=request.POST.get('action')
    if action=='attach':
        f=forms.AttachmentForm(request.POST,request.FILES)
        if f.is_valid(): attempt(request,lambda:svc.add_attachment(request.user,record.current_revision,f.cleaned_data['file'],f.cleaned_data['signed_paper']))
        else: messages.error(request,'Choose valid evidence to attach.')
    elif action=='flag': attempt(request,lambda:svc.flag_impact(request.user,record.current_revision,request.POST.get('reason','')))
    elif action in ('approve','reject'):
        f=forms.DecisionForm(request.POST)
        if f.is_valid(): attempt(request,lambda:svc.approve_revision(request.user,record.current_revision,f.cleaned_data['reason'],f.cleaned_data['capacity'],reject=action=='reject'))
        else: messages.error(request,'Select capacity and enter a decision basis.')
    else: raise Http404
    return redirect('record',pk=pk)

@member
def record_amend(request,pk):
    entry_authority(request)
    record=get_object_or_404(ControlledRecord,pk=pk)
    rev=record.current_revision
    f=forms.AmendmentForm(request.POST or None,initial={'body':rev.body,'basis':rev.basis})
    return form_page(request,f,f'Amend {record.number}',back=f'/records/{pk}/',description='A new revision preserves the prior evidence. Amending approved evidence automatically creates an impact review for dependent hardware.',save=lambda f:svc.amend_record(request.user,record,**f.cleaned_data))

@member
def attachment_download(request,pk):
    attachment=get_object_or_404(Attachment,pk=pk)
    return FileResponse(attachment.file.open('rb'),as_attachment=True,filename=attachment.original_name,content_type='application/octet-stream')

@member
def coupons(request):
    qs=CouponSet.objects.select_related('operator','machine','plan__record').prefetch_related('coverage','assemblies')
    query=request.GET.get('q','')
    if query: qs=qs.filter(Q(number__icontains=query)|Q(operator__name__icontains=query)|Q(coverage__serial__icontains=query)).distinct()
    return render(request,'qc/coupons.html',{'title':'Coupon register','coupons':qs,'q':query})

@member
def coupon_new(request):
    entry_authority(request)
    def save(form):
        obj=form.save();svc.audit(request.user,'coupon_set_created',obj);return obj
    return form_page(request,forms.CouponForm(request.POST or None),'New coupon set',back=lambda x:f'/coupons/{x.pk}/',description='A set contains physical coupon assemblies. A and B are distinct welds on one assembly; they do not count as two physical coupons.',save=save)

@member
def coupon_detail(request,pk):
    cs=get_object_or_404(CouponSet.objects.select_related('operator','machine','plan__record','operation__unit'),pk=pk)
    if request.method=='POST':
        f=forms.DecisionForm(request.POST)
        if f.is_valid(): attempt(request,lambda:svc.accept_coupon(request.user,cs,f.cleaned_data['reason'],f.cleaned_data['capacity']))
        else: messages.error(request,'Enter acting capacity and acceptance basis.')
        return redirect('coupon',pk=pk)
    return render(request,'qc/coupon.html',{'title':cs.number,'coupon':cs,'assemblies':cs.assemblies.prefetch_related('welds__passes','specimens__tests'),'decision_form':forms.DecisionForm()})

@member
def assembly_new(request,pk):
    entry_authority(request);cs=get_object_or_404(CouponSet,pk=pk)
    def save(f):
        if cs.status=='accepted': raise ValidationError('Accepted coupon evidence requires a new controlled verification set.')
        obj=f.save(commit=False);obj.coupon_set=cs;obj.save();svc.audit(request.user,'assembly_created',obj);return obj
    return form_page(request,forms.AssemblyForm(request.POST or None),'Add physical coupon assembly',back=f'/coupons/{pk}/',save=save)

@member
def weld_new(request,pk):
    entry_authority(request);assembly=get_object_or_404(CouponAssembly,pk=pk)
    def save(f):
        if assembly.coupon_set.status=='accepted': raise ValidationError('Accepted evidence cannot be changed in place.')
        obj=f.save(commit=False);obj.assembly=assembly;obj.save();svc.audit(request.user,'weld_created',obj);return obj
    return form_page(request,forms.WeldForm(request.POST or None),'Add weld / side',back=f'/coupons/{assembly.coupon_set_id}/',save=save)

@member
def pass_new(request,pk):
    entry_authority(request);weld=get_object_or_404(CouponWeld,pk=pk)
    def save(f):
        if weld.assembly.coupon_set.status=='accepted': raise ValidationError('Accepted evidence cannot be changed in place.')
        obj=f.save(commit=False);obj.weld=weld;obj.save();svc.audit(request.user,'pass_actual_recorded',weld,pass_number=obj.ordinal);return obj
    return form_page(request,forms.PassForm(request.POST or None),'Record actual pass',back=f'/coupons/{weld.assembly.coupon_set_id}/',description='Actual readouts and raw notes only. A successful trial does not establish approved production ranges.',save=save)

@member
def specimen_new(request,pk):
    entry_authority(request);assembly=get_object_or_404(CouponAssembly,pk=pk)
    f=forms.SpecimenForm(request.POST or None,assembly=assembly)
    def save(f):
        if assembly.coupon_set.status == 'accepted': raise ValidationError('Accepted coupon evidence cannot be changed in place.')
        if not assembly.nde_complete: raise ValidationError('Document the applicable pre-cut NDE before specimen extraction.')
        obj=f.save(commit=False);obj.assembly=assembly;obj.save();f.save_m2m();svc.audit(request.user,'specimen_created',obj);return obj
    return form_page(request,f,'Identify extracted specimen',back=f'/coupons/{assembly.coupon_set_id}/',save=save)

@member
def test_new(request,pk):
    entry_authority(request);specimen=get_object_or_404(Specimen,pk=pk)
    f=forms.TestForm(request.POST or None,specimen=specimen)
    return form_page(request,f,'Record test evidence',back=f'/coupons/{specimen.assembly.coupon_set_id}/',description='Validity describes the evidence. A valid failed weld is different from an invalid test. Unresolved criteria allow raw observations only.',save=lambda f:svc.record_test(request.user,specimen=specimen,**f.cleaned_data))

@member
def issues(request):
    return render(request,'qc/issues.html',{'title':'Holds & nonconformances','holds':Hold.objects.select_related('unit','machine','raised_by'),'ncrs':NCR.objects.select_related('unit','hold')})

@member
def hold_new(request):
    entry_authority(request)
    f=forms.HoldForm(request.POST or None,initial={'unit':request.GET.get('unit')})
    return form_page(request,f,'Open Engineering Hold',back=lambda h:f'/holds/{h.pk}/',description='Stop the affected machine / job, identify the origin and assess hardware impact. A process hold does not automatically create an NCR.',save=lambda f:svc.open_hold(request.user,**f.cleaned_data))

@member
def hold_detail(request,pk):
    hold=get_object_or_404(Hold.objects.select_related('unit','machine','raised_by','verification__record'),pk=pk)
    if request.method=='POST':
        f=forms.DecisionForm(request.POST)
        if f.is_valid(): attempt(request,lambda:svc.close_hold(request.user,hold,f.cleaned_data['reason'],f.cleaned_data['capacity']))
        else: messages.error(request,'Record closure basis and acting capacity.')
        return redirect('hold',pk=pk)
    return render(request,'qc/hold.html',{'title':hold.number,'hold':hold,'decision_form':forms.DecisionForm(),'checks':hold.checks.select_related('operator','machine','entered_by'),'ncrs':hold.ncrs.all()})

@member
def hold_update(request,pk):
    entry_authority(request);hold=get_object_or_404(Hold,pk=pk)
    def save(f):
        if hold.status=='closed': raise ValidationError('Closed hold history cannot be overwritten.')
        obj=f.save();svc.audit(request.user,'hold_corrective_action',obj);return obj
    return form_page(request,forms.HoldResolutionForm(request.POST or None,instance=hold),'Record corrective action',back=f'/holds/{pk}/',save=save)

@member
def hold_check(request,pk):
    entry_authority(request);hold=get_object_or_404(Hold,pk=pk)
    def save(f):
        if hold.status=='closed': raise ValidationError('The hold is closed.')
        obj=f.save(commit=False);obj.hold=hold;obj.entered_by=request.user;obj.save();svc.audit(request.user,'hold_strike_plate',hold,result=obj.result);return obj
    return form_page(request,forms.HoldCheckForm(request.POST or None),'H-required strike-plate verification',back=f'/holds/{pk}/',description='Unlike routine passing A checks, Section H requires this check and its result to be recorded.',save=save)

@member
def ncr_new(request):
    entry_authority(request)
    def save(f):
        obj=f.save();svc.audit(request.user,'ncr_opened',obj);return obj
    return form_page(request,forms.NCRForm(request.POST or None),'Open hardware NCR',back=lambda n:f'/ncrs/{n.pk}/',save=save)

@member
def ncr_detail(request,pk):
    ncr=get_object_or_404(NCR.objects.select_related('unit','hold','verification__record'),pk=pk)
    if request.method=='POST':
        f=forms.DecisionForm(request.POST)
        if f.is_valid():
            d=f.cleaned_data
            if request.POST.get('action')=='disposition': attempt(request,lambda:svc.approve_disposition(request.user,ncr,request.POST.get('disposition',''),d['reason'],d['capacity']))
            elif request.POST.get('action')=='close': attempt(request,lambda:svc.close_ncr(request.user,ncr,d['reason'],d['capacity']))
            else: raise Http404
        else: messages.error(request,'Enter capacity and decision basis.')
        return redirect('ncr',pk=pk)
    return render(request,'qc/ncr.html',{'title':ncr.number,'ncr':ncr,'decision_form':forms.DecisionForm(),'approvals':Approval.objects.filter(target_id=ncr.pk).select_related('actor')})

@member
def ncr_execution(request,pk):
    entry_authority(request);ncr=get_object_or_404(NCR,pk=pk)
    def save(f):
        if ncr.status!='action_required': raise ValidationError('Record authorized Picogrid disposition before executing actions.')
        obj=f.save();svc.audit(request.user,'disposition_execution',obj);return obj
    return form_page(request,forms.NCRExecutionForm(request.POST or None,instance=ncr),'Disposition execution / reinspection',back=f'/ncrs/{pk}/',save=save)

@member
def qualifications(request):
    return render(request,'qc/qualifications.html',{'title':'Qualification register','qualifications':Qualification.objects.select_related('person','machine','wps__record','evidence__record')})

@member
def qualification_new(request):
    entry_authority(request)
    def save(f):
        obj=f.save();svc.audit(request.user,'qualification_case_created',obj);return obj
    return form_page(request,forms.QualificationForm(request.POST or None),'Prepare qualification case',back='/qualifications/',description='A pending record is not a qualification. Section C requires accepted B evidence, defined scope and the appropriate approval.',save=save)

@member
@require_POST
def qualification_approve(request,pk):
    award=get_object_or_404(Qualification,pk=pk);f=forms.DecisionForm(request.POST)
    if f.is_valid(): attempt(request,lambda:svc.award_qualification(request.user,award,f.cleaned_data['reason'],f.cleaned_data['capacity']))
    else: messages.error(request,'Record capacity and decision basis.')
    return redirect('qualifications')

@member
def resources(request):
    return render(request,'qc/resources.html',{'title':'Equipment & people','machines':Machine.objects.all(),'people':Person.objects.select_related('organization','user')})

@member
def resource_new(request,kind):
    entry_authority(request)
    if kind not in ('person','machine'): raise Http404
    form_class=forms.PersonForm if kind=='person' else forms.MachineForm
    def save(f):
        obj=f.save();svc.audit(request.user,f'{kind}_created',obj);return obj
    return form_page(request,form_class(request.POST or None),f'Add {kind}',back='/resources/',save=save)

@member
def decisions(request):
    return render(request,'qc/decisions.html',{'title':'Decisions & history','approvals':Approval.objects.select_related('actor','grant__organization')[:100],'events':AuditEvent.objects.select_related('actor')[:100]})

@member
def impacts(request):
    return render(request,'qc/impacts.html',{'title':'Evidence-impact review','impacts':ImpactCase.objects.select_related('revision__record','raised_by').prefetch_related('units'),'decision_form':forms.DecisionForm()})

@member
@require_POST
def impact_resolve(request,pk):
    case=get_object_or_404(ImpactCase,pk=pk);f=forms.DecisionForm(request.POST)
    if f.is_valid(): attempt(request,lambda:svc.clear_impact(request.user,case,f.cleaned_data['reason'],f.cleaned_data['capacity']))
    else: messages.error(request,'Enter resolution and acting capacity.')
    return redirect('impacts')

@member
def authority(request):
    if request.method=='POST':
        organization=get_object_or_404(Organization,pk=request.POST.get('organization'))
        if request.POST.get('action')=='policy': attempt(request,lambda:svc.change_policy(request.user,organization,request.POST.get('allow')=='yes'))
        elif request.POST.get('action')=='revoke':
            grant=get_object_or_404(AuthorityGrant,pk=request.POST.get('grant'),organization=organization)
            svc.revoke_authority(request.user,grant);messages.success(request,'Grant revoked for future use. Historical decisions remain intact.')
        else: raise Http404
        return redirect('authority')
    return render(request,'qc/authority.html',{'title':'Authority & access','organizations':Organization.objects.all(),'grants':AuthorityGrant.objects.select_related('user','organization').order_by('organization__name','user__username','action'),'profiles':Profile.objects.select_related('user','organization')})

@member
def grant_new(request):
    p=svc.profile(request.user)
    if not p.is_owner and not p.is_senior: raise PermissionDenied('Senior organizational authority is required.')
    return form_page(request,forms.GrantForm(request.POST or None),'Record authority designation',back='/authority/',description='Granting software authority does not create a technical qualification. Picogrid delegation must have recorded designation evidence.',save=lambda f:svc.grant_authority(request.user,target_user=f.cleaned_data['user'],**{k:v for k,v in f.cleaned_data.items() if k!='user'}))

@member
def sources(request):
    return render(request,'qc/sources.html',{'title':'Source baseline & open controls','sources':ControlledRecord.objects.filter(kind='source').select_related('current_revision'),'plans':ControlledRecord.objects.filter(kind='plan').select_related('current_revision')})

@member
def dossier(request,pk):
    unit=get_object_or_404(HardwareUnit,pk=pk)
    issues,pending,manifest=svc.release_checklist(unit)
    return render(request,'qc/dossier.html',{'unit':unit,'issues':issues,'pending':pending,'manifest':manifest,'records':unit.records.select_related('current_revision'),'releases':unit.releases.select_related('approval__actor'),'shipments':unit.shipments.all(),'operations':unit.operations.select_related('operator','machine','wps__record','plan__record'),'holds':svc.active_holds(unit),'ncrs':unit.ncrs.all()})


@member
def assembly_update(request,pk):
    entry_authority(request)
    assembly=get_object_or_404(CouponAssembly,pk=pk)
    def save(form):
        if assembly.coupon_set.status=='accepted': raise ValidationError('Accepted evidence cannot be changed in place.')
        if assembly.specimens.exists(): raise ValidationError('Pre-cut inspection and drawing history cannot be changed after extraction. Record a controlled amendment/impact review instead.')
        obj=form.save();svc.audit(request.user,'precut_evidence_recorded',obj,nde_complete=obj.nde_complete);return obj
    return form_page(request,forms.AssemblyForm(request.POST or None,instance=assembly),'Document pre-cut inspection',back=f'/coupons/{assembly.coupon_set_id}/',save=save)


def health(request):
    from django.db import connection
    from django.http import JsonResponse
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
    except Exception:
        return JsonResponse({'status':'unavailable'},status=503)
    return JsonResponse({'status':'ok','mode':'prototype'})
