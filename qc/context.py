from .models import ImpactCase, Hold

def navigation(request):
    if not request.user.is_authenticated: return {}
    return {'nav_sections':[
        ('WORKSPACE', [('Overview','/','01'),('Work orders','/jobs/','02'),('Coupon register','/coupons/','03'),('Holds & NCRs','/issues/','04')]),
        ('QUALITY RECORDS', [('WPS & PQR','/records/?group=procedures','05'),('Inspections & proof','/records/?group=inspections','06'),('Qualifications','/qualifications/','07'),('Development','/records/?kind=development','08'),('Equipment & people','/resources/','09')]),
        ('CONTROL', [('Decisions & history','/decisions/','10'),('Evidence impact','/impacts/','11'),('Authority & access','/authority/','12'),('Source documents','/sources/','13')])],
        'open_hold_count':Hold.objects.exclude(status='closed').count(),
        'open_impact_count':ImpactCase.objects.filter(status='open').count()}
