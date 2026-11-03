from django.urls import path
from django.contrib.auth import views as auth
from qc import views as v
urlpatterns = [
    path('health/',v.health,name='health'),
    path('login/',auth.LoginView.as_view(template_name='registration/login.html'),name='login'),
    path('logout/',auth.LogoutView.as_view(),name='logout'),
    path('',v.dashboard,name='dashboard'),path('jobs/',v.jobs,name='jobs'),path('jobs/new/',v.job_new,name='job_new'),path('jobs/<uuid:pk>/',v.job_detail,name='job'),
    path('units/new/',v.unit_new,name='unit_new'),path('units/<uuid:pk>/',v.unit_detail,name='unit'),path('units/<uuid:pk>/decision/',v.unit_action,name='unit_action'),path('units/<uuid:pk>/dossier/',v.dossier,name='dossier'),
    path('operations/new/',v.operation_new,name='operation_new'),path('operations/<uuid:pk>/',v.operation_detail,name='operation'),
    path('records/',v.record_list,name='records'),path('records/new/',v.record_new,name='record_new'),path('records/<uuid:pk>/',v.record_detail,name='record'),path('records/<uuid:pk>/action/',v.record_action,name='record_action'),path('records/<uuid:pk>/amend/',v.record_amend,name='record_amend'),path('evidence/<uuid:pk>/',v.attachment_download,name='evidence'),
    path('coupons/',v.coupons,name='coupons'),path('coupons/new/',v.coupon_new,name='coupon_new'),path('coupons/<uuid:pk>/',v.coupon_detail,name='coupon'),path('coupons/<uuid:pk>/assemblies/new/',v.assembly_new,name='assembly_new'),path('assemblies/<uuid:pk>/inspection/',v.assembly_update,name='assembly_update'),path('assemblies/<uuid:pk>/welds/new/',v.weld_new,name='weld_new'),path('assemblies/<uuid:pk>/specimens/new/',v.specimen_new,name='specimen_new'),path('welds/<uuid:pk>/passes/new/',v.pass_new,name='pass_new'),path('specimens/<uuid:pk>/tests/new/',v.test_new,name='test_new'),
    path('issues/',v.issues,name='issues'),path('holds/new/',v.hold_new,name='hold_new'),path('holds/<uuid:pk>/',v.hold_detail,name='hold'),path('holds/<uuid:pk>/update/',v.hold_update,name='hold_update'),path('holds/<uuid:pk>/checks/new/',v.hold_check,name='hold_check'),path('ncrs/new/',v.ncr_new,name='ncr_new'),path('ncrs/<uuid:pk>/',v.ncr_detail,name='ncr'),path('ncrs/<uuid:pk>/execution/',v.ncr_execution,name='ncr_execution'),
    path('qualifications/',v.qualifications,name='qualifications'),path('qualifications/new/',v.qualification_new,name='qualification_new'),path('qualifications/<uuid:pk>/approve/',v.qualification_approve,name='qualification_approve'),path('resources/',v.resources,name='resources'),path('resources/new/<str:kind>/',v.resource_new,name='resource_new'),path('decisions/',v.decisions,name='decisions'),path('impacts/',v.impacts,name='impacts'),path('impacts/<uuid:pk>/resolve/',v.impact_resolve,name='impact_resolve'),path('authority/',v.authority,name='authority'),path('authority/new/',v.grant_new,name='grant_new'),path('sources/',v.sources,name='sources'),
]
