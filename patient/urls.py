from django.urls import path
from django.contrib.auth.decorators import login_required
from patient.views import PatientCreateView, PatientDelete, PatientDetailView, PatientListView, PatientUpdateView

app_name = "app_patient"

urlpatterns = [
    path('', login_required(PatientListView.as_view()), name="patient_list"),
    path('<int:pk>', login_required(PatientDetailView.as_view()), name="patient_detail"),
    path('<int:pk>/edit', login_required(PatientUpdateView.as_view()), name="patient_update"),
    path('<int:pk>/delete', login_required(PatientDelete.as_view()), name="patient_delete"),
    path('create', login_required(PatientCreateView), name="patient_create")
]