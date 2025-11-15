# hospital/urls.py

from django.urls import path
from . import views
from django.contrib.auth.views import LoginView, LogoutView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    
    # HOME & STATIC PAGES
    path('', views.home_view, name='home'),
    path('aboutus', views.aboutus_view, name='aboutus'),
    path('contactus', views.contactus_view, name='contactus'),

    # CLICKS
    path('adminclick', views.adminclick_view, name='adminclick'),
    path('doctorclick', views.doctorclick_view, name='doctorclick'),
    path('patientclick', views.patientclick_view, name='patientclick'),

    # SIGNUP
    path('adminsignup', views.admin_signup_view, name='adminsignup'),
    path('doctorsignup', views.doctor_signup_view, name='doctorsignup'),
    path('patientsignup', views.patient_signup_view, name='patientsignup'),

    # LOGIN / LOGOUT
    path('adminlogin', LoginView.as_view(template_name='hospital/adminlogin.html'), name='adminlogin'),
    path('doctorlogin', views.doctor_login_view, name='doctorlogin'),
    path('patientlogin', views.patient_login_view, name='patientlogin'),
    path('afterlogin', views.afterlogin_view, name='afterlogin'),
    path('logout', LogoutView.as_view(template_name='hospital/index.html'), name='logout'),

    # ==============================
    # ADMIN SECTION
    # ==============================
    path('admin-dashboard', views.admin_dashboard_view, name='admin-dashboard'),
    path('admin-doctor', views.admin_doctor_view, name='admin-doctor'),
    path('admin-view-doctor', views.admin_view_doctor_view, name='admin-view-doctor'),
    path('delete-doctor-from-hospital/<int:pk>', views.delete_doctor_from_hospital_view, name='delete-doctor-from-hospital'),
    path('update-doctor/<int:pk>', views.update_doctor_view, name='update-doctor'),
    path('admin-add-doctor', views.admin_add_doctor_view, name='admin-add-doctor'),
    path('admin-view-doctor-specialisation', views.admin_view_doctor_specialisation_view, name='admin-view-doctor-specialisation'),
    path('admin-view-doctor-json/', views.admin_view_doctor_json, name='admin-view-doctor-json'),
    
    path('admin/api/doctor/<int:doctor_id>/view/', views.admin_view_doctor_detail_api, name='admin-view-doctor-detail'),
    path('admin/api/doctor/<int:doctor_id>/update/', views.admin_update_doctor_api, name='admin-update-doctor-api'),
    path('admin/api/doctor/<int:doctor_id>/delete/', views.admin_delete_doctor_api, name='admin-delete-doctor-api'),
    path('admin/api/doctor/<int:doctor_id>/appointments/', views.admin_doctor_appointments_api, name='admin-doctor-appointments-api'),
    
    path('admin/api/patient/<int:patient_id>/', views.admin_view_patient_detail_api, name='admin-view-patient-detail'),
    path('admin/api/patient/<int:patient_id>/delete/', views.admin_delete_patient_api, name='admin-delete-patient-api'),
    
    path('admin/api/appointment/<int:appointment_id>/cancel/', views.admin_cancel_appointment_api, name='admin-cancel-appointment-api'),
    
    # API Endpoints for Real-Time Data
    path('admin/api/stats/', views.get_stats_data, name='get-stats-data'),
    path('admin/api/doctors/', views.get_doctors_data, name='get-doctors-data'),
    path('admin/api/patients/', views.get_patients_data, name='get-patients-data'),
    path('admin/api/appointments/', views.get_appointments_data, name='get-appointments-data'),
    # Patient Management APIs
    path('admin/api/patient/<int:patient_id>/delete/', views.delete_patient_from_hospital_view, name='delete-patient-api'),
    path('admin/api/patient/<int:patient_id>/', views.get_patient_info_api, name='get-patient-info-api'),
    
    # Appointment Management APIs
    path('admin/api/appointment/<int:appointment_id>/cancel/', views.cancel_appointment_api, name='cancel-appointment-api'),

    path('admin-patient', views.admin_patient_view, name='admin-patient'),
    path('admin-view-patient', views.admin_view_patient_view, name='admin-view-patient'),
    path('delete-patient-from-hospital/<int:pk>', views.delete_patient_from_hospital_view, name='delete-patient-from-hospital'),
    path('update-patient/<int:pk>', views.update_patient_view, name='update-patient'),
    path('admin-add-patient', views.admin_add_patient_view, name='admin-add-patient'),
    path('admin-approve-patient', views.admin_approve_patient_view, name='admin-approve-patient'),
    path('approve-patient/<int:pk>', views.approve_patient_view, name='approve-patient'),
    path('reject-patient/<int:pk>', views.reject_patient_view, name='reject-patient'),
    path('admin-discharge-patient', views.admin_discharge_patient_view, name='admin-discharge-patient'),
    path('discharge-patient/<int:pk>', views.discharge_patient_view, name='discharge-patient'),
    path('download-pdf/<int:pk>', views.download_pdf_view, name='download-pdf'),

    path('admin-appointment', views.admin_appointment_view, name='admin-appointment'),
    path('admin-view-appointment', views.admin_view_appointment_view, name='admin-view-appointment'),
    path('admin-add-appointment', views.admin_add_appointment_view, name='admin-add-appointment'),
    path('admin-approve-appointment', views.admin_approve_appointment_view, name='admin-approve-appointment'),
    path('approve-appointment/<int:pk>', views.approve_appointment_view, name='approve-appointment'),
    path('reject-appointment/<int:pk>', views.reject_appointment_view, name='reject-appointment'),

    # ==============================
    # DOCTOR SECTION
    # ==============================
    path('doctor-dashboard', views.doctor_dashboard_view, name='doctor-dashboard'),
    path('doctor-appointments', views.doctor_appointment_view, name='doctor-appointments'),
    path('doctor-view-appointment', views.doctor_view_appointment_view, name='doctor-view-appointment'),
    path('doctor-delete-appointment', views.doctor_delete_appointment_view, name='doctor-delete-appointment'),
    path('delete-appointment/<int:pk>', views.delete_appointment_view, name='delete-appointment'),
    path('doctor-appointment-cancel/<int:appointment_id>/', views.cancel_appointment_api, name='cancel-appointment'),
    path('doctor-appointment-complete/<int:appointment_id>/', views.complete_appointment, name='complete-appointment'),
    path('doctor-patient', views.doctor_patient_view, name='doctor-patient'),
    path('doctor-view-patient', views.doctor_view_patient_view, name='doctor-view-patient'),
    path('doctor-view-discharge-patient', views.doctor_view_discharge_patient_view, name='doctor-view-discharge-patient'),
    path('upload-report/', views.upload_report, name='upload-report'),
    path('search', views.search_view, name='search'),
    path('doctor/appointment/<int:appointment_id>/<str:action>/',views.doctor_update_appointment_status,name='doctor-appointment-action'),  # In DOCTOR SECTION - add these:
    path('doctor/api/profile/', views.get_doctor_profile_api, name='doctor-api-profile'),
    path('doctor/api/appointments/realtime/', views.get_doctor_appointments_realtime, name='doctor-api-appointments-realtime'),

    path('doctor-appointments', views.doctor_appointment_view, name='doctor-appointments'),
    path('doctor-patients', views.doctor_patient_view, name='doctor-patients'),
    path('doctor-profile', views.doctor_dashboard_view, name='doctor-profile'),

    # ==============================
    # PATIENT SECTION
    # ==============================
    path('patient-dashboard', views.patient_dashboard_view, name='patient-dashboard'),
    path('patient-appointment', views.patient_appointment_view, name='patient-appointment'),
    path('patient-book-appointment/<int:doctor_id>/', views.patient_book_appointment_view, name='patient-book-appointment'),
    path('patient-view-appointment', views.patient_view_appointment_view, name='patient-view-appointment'),
    path('patient-view-doctor', views.patient_view_doctor_view, name='patient-view-doctor'),
    path('feedback/<int:appointment_id>/', views.submit_feedback, name='submit-feedback'),
    path('searchdoctor', views.search_doctor_view, name='searchdoctor'),
    path('patient-discharge', views.patient_discharge_view, name='patient-discharge'),
    path('patient/api/profile/', views.get_patient_profile_api, name='patient-api-profile'),
    path('patient/api/appointments/realtime/', views.get_patient_appointments_realtime, name='patient-api-appointments-realtime'),

]