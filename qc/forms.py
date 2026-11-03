from django import forms
from django.contrib.auth import get_user_model
from .models import *

class StyledForm(forms.Form):
    pass

class DecisionForm(forms.Form):
    capacity = forms.ChoiceField(choices=Approval._meta.get_field('capacity').choices)
    reason = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), label='Decision basis / conditions')

class RecordForm(forms.ModelForm):
    body = forms.CharField(widget=forms.Textarea(attrs={'rows': 5}), label='Observations / controlled content')
    performed_by = forms.ModelChoiceField(Person.objects.all(), required=False, label='Performed by (may differ from entry person)')
    performed_at = forms.DateTimeField(required=False, widget=forms.DateTimeInput(attrs={'type':'datetime-local'}), label='Actual activity / signed-paper date and time')
    requirements_resolved = forms.BooleanField(required=False, label='Applicable requirements are defined for this prototype record')
    basis = forms.CharField(required=False, label='Acceptance / authorization basis and revision')
    stage = forms.ChoiceField(required=False, choices=[('', 'Not applicable'), ('pre_finish','Before finishing'),('post_finish','After finishing'),('final','Final inspection'),('proof','Assembly proof test')])
    result = forms.ChoiceField(choices=[('pending','Pending / raw observations only'),('pass','Meets the defined basis'),('fail','Does not meet the defined basis')])
    coupon_count = forms.IntegerField(required=False, min_value=1, label='Plan: required physical coupon count')
    required_tests = forms.MultipleChoiceField(required=False, choices=[('macroetch','Macroetch'),('pull','Pull test')], widget=forms.CheckboxSelectMultiple)
    proof_applicable = forms.ChoiceField(required=False, choices=[('','TBD'),('yes','Required by stated plan'),('no','Not applicable under stated plan')], label='Plan: proof-test applicability')
    supporting_pqr = forms.ModelChoiceField(Revision.objects.filter(record__kind='pqr'),required=False,label='WPS: supporting PQR revision')
    qualification_coupon = forms.ModelChoiceField(CouponSet.objects.filter(purpose='qualification'),required=False,label='C / PQR: qualification coupon set')
    section_c_complete = forms.BooleanField(required=False,label='Section C: required evidence/scope has been reviewed for this prototype case')
    class Meta:
        model = ControlledRecord
        fields = ['number','kind','title','unit','machine']
    def clean(self):
        data = super().clean()
        if data.get('requirements_resolved') and not data.get('basis','').strip(): self.add_error('basis','Identify the defined requirement/acceptance basis; TBD is not a passing criterion.')
        return data
    def payload(self):
        d=self.cleaned_data
        payload={'stage':d.get('stage',''),'result':d['result']}
        if d.get('coupon_count'): payload['coupon_count']=d['coupon_count']
        if d.get('required_tests'): payload['required_tests']=d['required_tests']
        if d.get('proof_applicable'): payload['proof_applicable']=d['proof_applicable']=='yes'
        if d.get('supporting_pqr'): payload['pqr_id']=str(d['supporting_pqr'].pk)
        if d.get('qualification_coupon'): payload['coupon_set_id']=str(d['qualification_coupon'].pk)
        payload['section_c_complete']=d.get('section_c_complete',False)
        return payload

class AmendmentForm(forms.Form):
    body = forms.CharField(widget=forms.Textarea(attrs={'rows': 7}))
    reason = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), label='Amendment reason / impact')
    basis = forms.CharField(required=False)
    requirements_resolved = forms.BooleanField(required=False)

class AttachmentForm(forms.Form):
    file = forms.FileField(label='PDF / PNG / JPEG (up to 10 MB)')
    signed_paper = forms.BooleanField(required=False, label='Signed paper source / assisted entry')

class WorkOrderForm(forms.ModelForm):
    class Meta:
        model=WorkOrder
        fields=['number','title','customer_reference','traveler_reference','notes']

class UnitForm(forms.ModelForm):
    class Meta:
        model=HardwareUnit
        fields=['serial','work_order','part_number','drawing_revision']

class OperationForm(forms.ModelForm):
    class Meta:
        model=Operation
        fields=['unit','joint_family','operator','machine','wps','plan','material_lot','filler_lot','fixture_reference']
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['wps'].queryset=Revision.objects.filter(record__kind='wps')
        self.fields['plan'].queryset=Revision.objects.filter(record__kind='plan')

class CouponForm(forms.ModelForm):
    class Meta:
        model=CouponSet
        fields=['number','purpose','joint_family','operation','plan','operator','machine','material_lot','coverage','notes']
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['plan'].queryset=Revision.objects.filter(record__kind='plan')
        self.fields['coverage'].help_text='Explicit serial population. Hold Ctrl / Command to select several.'

class AssemblyForm(forms.ModelForm):
    class Meta:
        model=CouponAssembly
        fields=['identifier','drawing_reference','nde_complete']
        labels={'nde_complete':'Applicable pre-cut VT/dimensional evidence is documented in set notes / references'}

class WeldForm(forms.ModelForm):
    class Meta:
        model=CouponWeld
        fields=['side','observations']

class PassForm(forms.ModelForm):
    class Meta:
        model=PassActual
        fields=['ordinal','preset','raw_parameters','observations']

class SpecimenForm(forms.ModelForm):
    class Meta:
        model=Specimen
        fields=['identifier','welds','layout_reference','integrity']
    def __init__(self,*args,assembly=None,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['welds'].queryset=assembly.welds.all() if assembly else CouponWeld.objects.none()
        self.fields['welds'].required=True

class TestForm(forms.ModelForm):
    class Meta:
        model=TestAttempt
        fields=['method','provider','method_reference','validity','result','observations','reason','report','prior_attempt']
    def __init__(self,*args,specimen=None,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['prior_attempt'].queryset=specimen.tests.all() if specimen else TestAttempt.objects.none()

class HoldForm(forms.ModelForm):
    class Meta:
        model=Hold
        fields=['number','unit','machine','origin','issue','hardware_affected','containment','notification']

class HoldResolutionForm(forms.ModelForm):
    class Meta:
        model=Hold
        fields=['corrective_action','problem_resolved','verification','coupon_evidence','qualification_evidence','notification','containment']

class HoldCheckForm(forms.ModelForm):
    class Meta:
        model=HoldCheck
        fields=['operator','machine','performed_at','result','corrective_action_reference']
        widgets={'performed_at':forms.DateTimeInput(attrs={'type':'datetime-local'})}

class NCRForm(forms.ModelForm):
    class Meta:
        model=NCR
        fields=['number','unit','hold','description','proposed_disposition']

class NCRExecutionForm(forms.ModelForm):
    class Meta:
        model=NCR
        fields=['execution','verification']

class QualificationForm(forms.ModelForm):
    class Meta:
        model=Qualification
        fields=['kind','person','machine','wps','joint_family','evidence','last_activity','activity_source']
        widgets={'last_activity':forms.DateInput(attrs={'type':'date'})}

class PersonForm(forms.ModelForm):
    class Meta:
        model=Person
        fields=['name','organization','user']

class MachineForm(forms.ModelForm):
    class Meta:
        model=Machine
        fields=['identifier','model','serial']

class GrantForm(forms.Form):
    user=forms.ModelChoiceField(get_user_model().objects.filter(is_active=True))
    organization=forms.ModelChoiceField(Organization.objects.all())
    action=forms.ChoiceField(choices=ACTIONS)
    scope=forms.CharField(initial='LANDER')
    evidence=forms.CharField(widget=forms.Textarea(attrs={'rows':3}),label='Designation / delegation source (prototype)')
