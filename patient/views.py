from typing import Any
from django import forms
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, UpdateView, DeleteView
from django.contrib import messages
from django.db.models import Q

from patient.models import Patient

# Define a ListView for displaying a list of patients
class PatientListView(ListView):
    model = Patient

    # Customize the queryset based on search query parameters
    def get_queryset(self):
        query = self.request.GET.get('q')
        
        if not query:
            return self.model.objects.all()
        
        return self.model.objects.filter(
            Q(name__icontains=query) |
            Q(city__icontains=query) |
            Q(address__icontains=query) |
            Q(email__icontains=query) |
            Q(cellphone__icontains=query) |
            Q(phone__icontains=query) |
            Q(medical_record__icontains=query) |
            Q(birth_date__icontains=query)
        )

# Define a DetailView for displaying detailed information about a patient
class PatientDetailView(DetailView):
    model = Patient
    context_object_name = 'patient'

# Define an UpdateView for updating patient information
class PatientUpdateView(UpdateView):
    # Define a custom form for updating patient information
    class PatientUpdateForm(forms.ModelForm):
        class Meta:
            model = Patient
            exclude = ['partner']
            
    model = Patient
    form_class = PatientUpdateForm

    # Override form_valid to add a success message upon successful form submission
    def form_valid(self, form):
        messages.success(self.request, 'Atualização bem sucedida!')
        return super().form_valid(form)

    # Override form_invalid to add an error message upon unsuccessful form submission
    def form_invalid(self, form):
        messages.error(self.request, 'Erro ao atualizar. Corrija os erros no formulário!')
        return super().form_invalid(form)

    # Define the success URL after updating a patient
    def get_success_url(self):
        return reverse_lazy('app_patient:patient_detail', kwargs={'pk': self.object.pk})

# Define a function-based view for creating a new patient
def PatientCreateView(request):
    # Define a form for creating a new patient
    class PatientCreateForm(forms.ModelForm):
        class Meta:
            model = Patient
            fields = '__all__'
            exclude = ['partner']

    if request.method == 'POST':
        form = PatientCreateForm(request.POST)
        if form.is_valid():
            # Save the new patient and associate it with the currently logged-in user
            new_patient = form.save(commit=False)
            new_patient.partner = request.user
            new_patient.save()
            messages.success(request, 'Paciente criado!')
            return HttpResponseRedirect(f'/patient/{new_patient.id}')
        else:
            messages.error(request, 'Unable to add the patient!')
            # Pass the invalidated form to maintain the previously entered information
            return render(request, 'patient/patient_form.html', { 'form': form})

    return render(request, 'patient/patient_form.html', { 'form': PatientCreateForm()})

# Define a DeleteView for deleting a patient
class PatientDelete(DeleteView):
    model = Patient
    success_url = reverse_lazy('app_patient:patient_list')

    # Override form_valid to add a success message upon successful deletion
    def form_valid(self, form):
        messages.success(self.request, 'Paciente excluído com sucesso!')
        return super(PatientDelete, self).form_valid(form)
    
    # Override dispatch to check if the user has permission to delete the patient
    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        # Retrieve the patient to be deleted
        patient_to_be_deleted = get_object_or_404(Patient, id=kwargs['pk'])
        
        # Check if the logged-in user has permission to delete the patient
        if patient_to_be_deleted.partner != request.user:
            return render(request, 'patient/patient_forbidden.html', context={'pk': kwargs['pk']}, status=401)
        
        return super().dispatch(request, *args, **kwargs)
