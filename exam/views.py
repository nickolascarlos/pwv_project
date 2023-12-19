from concurrent.futures import ThreadPoolExecutor
import threading
from typing import Any
from mimetypes import guess_type
from django import forms
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView, UpdateView, DeleteView
from django.db.models import Q
from django.contrib import messages
from exam.models import Exam
from patient.models import Patient
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from media_processing_scripts import video_processing

executor = ThreadPoolExecutor(max_workers=2)

# View para listar exames
class ExamListView(ListView):
    model = Exam

    def get_queryset(self):
        # Definindo o número de resultados por página
        results_per_page = 25

        # Obtendo os parâmetros da consulta e da página
        query = self.request.GET.get('q')
        page = self.request.GET.get('page', 1)

        # Construindo a consulta com base nos parâmetros
        if not query:
            queryset = self.model.objects.all().order_by('-id')
        else:
            query_filters = Q(
                id__icontains=query) | Q(date__icontains=query) | Q(
                patient__name__icontains=query) | Q(
                patient__partner__first_name__icontains=query) | Q(
                patient__partner__last_name__icontains=query) | Q(
                patient__partner__username__icontains=query)

            queryset = self.model.objects.filter(query_filters).order_by('-id')

        # Paginação dos resultados
        paginator = Paginator(queryset, results_per_page)

        try:
            return paginator.page(page).object_list
        except (PageNotAnInteger, EmptyPage, ValueError):
            # Tratamento de exceções ao recuperar a página
            return paginator.page(1).object_list

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)

        # Obtendo o número da página atual
        page = self.get_page_number()

        # Construindo a string de parâmetros da consulta
        request_params = [(param_name, self.request.GET[param_name]) for param_name in self.request.GET if param_name != 'page']
        params_string = '&'.join(['='.join([name, value]) for (name, value) in request_params])

        # Construindo a lista de números de páginas com respectivas strings de parâmetros
        pages_numbers = [n for n in range(page-7, page+8) if n > 0]
        relation_pages_number_to_params_str = [[n, params_string + f'&page={n}'] for n in pages_numbers]

        # Adicionando a lista de páginas ao contexto
        context['pages'] = relation_pages_number_to_params_str
        return context

    def get_page_number(self):
        return int(self.request.GET.get('page', 1))

# View para exibir detalhes de um exame
class ExamDetailView(DetailView):
    model = Exam

# View para atualizar um exame
class ExamUpdateView(UpdateView):
    # Formulário personalizado para a atualização do exame
    class ExamUpdateForm(forms.ModelForm):
        class Meta:
            model = Exam 
            fields = '__all__'
            exclude = [
                'patient',
                'partner',
                'rest_graph',
                'after_cuff_released_graph',
                'video_file',
                'processed_video_file',
                'processing_status'
            ]

        # Personalizando o campo de data e hora
        date = forms.DateTimeField(
            label='Data e Hora',
            input_formats=['%d/%m/%Y %H:%M:%S'],
            widget=forms.DateTimeInput(attrs={'placeholder': 'DD/MM/AAAA HH:MM:SS'})
        )

    model = Exam
    form_class = ExamUpdateForm

    def form_valid(self, form):
        # Mensagem de sucesso ao atualizar o exame
        messages.success(self.request, 'Atualização bem-sucedida!')
        return super().form_valid(form)

    def form_invalid(self, form):
        # Mensagem de erro ao atualizar o exame
        messages.error(self.request, 'Erro na atualização. Por favor, corrija os erros no formulário. ::: \n' + form.errors.as_text())
        return super().form_invalid(form)

    def get_success_url(self):
        # Redireciona para a página de detalhes do exame após a atualização
        return reverse_lazy('app_exam:exam_detail', kwargs={'pk': self.object.id})
    
    def dispatch(self, request, *args, **kwargs):
        # Verifica se o usuário logado é o responsável pelo exame
        obj = self.get_object()
        if obj.partner != request.user:
            return render(request, 'exam/exam_forbidden.html', context={'pk': kwargs['pk']}, status=401)
        else:
            return super().dispatch(request, *args, **kwargs)

# Função para processar mídia de exame assincronamente
def process_exam_media_async(exam):
    def async_function():
        # Caminho absoluto para o arquivo de vídeo original
        original_video_file = str(exam.video_file)
        _exam = Exam.objects.get(id=exam.pk)

        # Processa o vídeo e lida com erros
        success, error = video_processing.process(original_video_file, _exam)
        if not success:
            print('ERRO NO PROCESSAMENTO DO VÍDEO - EXAME #%s :: %s' % (_exam.pk, error))

    executor.submit(async_function)  
    # thread = threading.Thread(target=async_function)
    # thread.start()

# View para criar um novo exame
def exam_create_view(request):
    # Formulário para criar um novo exame
    class ExamCreateForm(forms.ModelForm):
        class Meta:
            model = Exam
            fields = '__all__'
            exclude = [
                'partner',
                'rest_graph',
                'after_cuff_released_graph',
                'processed_video_file',
                'processing_status'
            ]

    if request.method == 'POST':
        form = ExamCreateForm(request.POST, request.FILES)
        if form.is_valid():
            # Salva o exame e associa ao usuário logado
            new_exam = form.save(commit=False)
            new_exam.partner = request.user
            new_exam.save()

            messages.success(request, 'Exame criado! Aguarde o processamento do vídeo')
            response = JsonResponse({ 'success': True, 'message': 'created', 'exam_id': new_exam.pk})

            # Inicia o processamento assíncrono do vídeo
            process_exam_media_async(new_exam)
            
            return response 
        else:
            # Mensagem de erro se o formulário for inválido
            messages.error(request, 'Não foi possível adicionar o exame! ::: \n' + form.errors.as_text())
            # Retorna uma resposta JSON com os detalhes do erro
            return JsonResponse({ 'success': False, 'message': 'not created: ' + form.errors.as_text()})

    createForm = ExamCreateForm()

    # Recupera o ID do paciente da consulta se disponível
    patient_id = request.GET.get('patient_id')
    patient = None
    if patient_id:
        patient = get_object_or_404(Patient, id=patient_id)
        createForm.fields['patient'].initial = patient.id

    return render(request, 'exam/exam_main_form.html', { 'form': createForm, 'patient': patient })

# View para listar pacientes e vincular a um exame
def exam_connect_list(request, *args, **kwargs):
    exam_id = kwargs['pk']
    exam = Exam.objects.get(id=exam_id)
    if exam.partner != request.user:
        return render(request, 'exam/exam_forbidden.html', context={'pk': kwargs['pk']}, status=401)

    query = request.GET.get('q')
    if not query:
        patients = Patient.objects.all()
    else:
        patients = Patient.objects.filter(
            Q(name__icontains=query) |
            Q(city__icontains=query) |
            Q(address__icontains=query) |
            Q(email__icontains=query) |
            Q(cellphone__icontains=query) |
            Q(phone__icontains=query) |
            Q(medical_record__icontains=query) |
            Q(birth_date__icontains=query)
        )

    return render(request, 'exam/exam_connect_list.html', {
        'object_list': patients
    })

# View para confirmar a conexão entre um exame e um paciente
def exam_connect_confirmation(request, *args, **kwargs):
    exam_id = kwargs['pk']
    exam = Exam.objects.get(id=exam_id)
    if exam.partner != request.user:
        return render(request, 'exam/exam_forbidden.html', context={'pk': kwargs['pk']}, status=401)

    if request.method == 'POST':
        # Associa o paciente ao exame
        patient = Patient.objects.get(id=kwargs['patient_pk'])
        exam = Exam.objects.get(id=kwargs['pk'])
        exam.patient = patient
        exam.save()

        messages.success(request, 'Exame e paciente vinculados com sucesso')
        return redirect('/exam/' + str(exam.pk))

    patient = Patient.objects.get(id=kwargs['patient_pk'])

    return render(request, 'exam/exam_connect_confirm.html', {
        'exam_id': kwargs['pk'],
        'patient_name': patient.name
    })

# View para confirmar a desconexão entre um exame e um paciente
def exam_disconnect_confirm(request, *args, **kwargs):
    exam_id = kwargs['pk']
    exam = Exam.objects.get(id=exam_id)
    if exam.partner != request.user:
        return render(request, 'exam/exam_forbidden.html', context={'pk': kwargs['pk']}, status=401)

    if not exam.patient:
        return HttpResponse('Nenhum paciente vinculado a esse exame', status=404)

    if request.method == 'POST':
        # Desassocia o paciente do exame
        exam.patient = None
        exam.save()
        messages.success(request, 'Exame e paciente desvinculados com sucesso')
        return redirect(f'/exam/{exam.pk}')

    return render(request, 'exam/exam_disconnect_confirm.html', {
        'exam_id': exam.pk,
        'patient_name': exam.patient.name
    })

# View para excluir um exame
class ExamDelete(DeleteView):
    model = Exam
    success_url = reverse_lazy('app_exam:exam_list')

    def form_valid(self, form):
        # Mensagem de sucesso ao excluir o exame
        messages.success(self.request, 'Exame excluído com sucesso')
        return super(ExamDelete, self).form_valid(form)
    
    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        # Verifica se o usuário logado é o responsável pelo exame
        exam_to_be_deleted = get_object_or_404(Exam, id=kwargs['pk'])
        if exam_to_be_deleted.partner != request.user:
            return render(request, 'exam/exam_forbidden.html', context={'pk': kwargs['pk']}, status=401)
        
        return super().dispatch(request, *args, **kwargs)

# Função para servir o arquivo de vídeo original do exame
def serve_exam_video_file(request, *args, **kwargs):
    exam_id = kwargs['pk']
    exam = Exam.objects.get(id=exam_id)

    try:
        with open(str(exam.video_file), 'rb') as file:
            file_data = file.read()
        
        mime_type, _ = guess_type(str(exam.video_file))
        response = HttpResponse(file_data, content_type=mime_type)

        return response
    except IOError:
        return HttpResponse('Vídeo não encontrado', status=404)

# View para servir o arquivo de vídeo processado do exame
def serve_exam_processed_video_file(request, *args, **kwargs):
    exam_id = kwargs['pk']
    screen_position = kwargs['screen_position']
    
    if screen_position not in ['left', 'central', 'right']:
        raise Http404 
    
    exam = Exam.objects.get(id=exam_id)
    full_video_filename = "exam_videos/" + str(exam.processed_video_file) + screen_position + '.mp4'
    try:
        with open(full_video_filename, 'rb') as file:
            file_data = file.read()
        
        mime_type, _ = guess_type(full_video_filename)
        response = HttpResponse(file_data, content_type=mime_type)

        return response
    except IOError:
        return HttpResponse('Vídeo não encontrado', status=404)

# View para servir o arquivo de vídeo de segmentação do exame
def serve_exam_segmentation_video_file(request, *args, **kwargs):
    exam_id = kwargs['pk']
    exam = Exam.objects.get(id=exam_id)
    full_video_file = 'segmentation_exam_videos/' + str(exam.segmentation_video_file)
    try:
        with open(full_video_file, 'rb') as file:
            file_data = file.read()
        
        mime_type, _ = guess_type(str(exam.video_file))
        response = HttpResponse(file_data, content_type=mime_type)

        return response
    except IOError:
        return HttpResponse('Vídeo não encontrado', status=404)

# View para servir o arquivo de imagem do exame
def serve_exam_image_file(request, *args, **kwargs):
    image_filename = str(kwargs['filename'])
    full_image_filename = 'exam_images/' + image_filename
    try:
        with open(full_image_filename, 'rb') as file:
            file_data = file.read()

        mime_type, _ = guess_type(full_image_filename)
        response = HttpResponse(file_data, content_type=mime_type)

        return response
    except IOError:
        return HttpResponse('Arquivo não encontrado', status=404)
