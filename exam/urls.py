
from django.urls import path
from django.contrib.auth.decorators import login_required
from exam.views import ExamDelete, exam_connect_list, exam_disconnect_confirm, exam_connect_confirmation, exam_create_view, ExamDetailView, ExamListView, ExamUpdateView, serve_exam_image_file, serve_exam_processed_video_file, serve_exam_segmentation_video_file, serve_exam_video_file

app_name = 'app_exam'

urlpatterns = [
    path('', login_required(ExamListView.as_view()), name='exam_list'),
    path('<int:pk>', login_required(ExamDetailView.as_view()), name='exam_detail'),
    path('<int:pk>/edit', login_required(ExamUpdateView.as_view()), name='exam_update'),
    path('create', login_required(exam_create_view), name='exam_create'),
    path('<int:pk>/delete', login_required(ExamDelete.as_view()), name='exam_delete'),
    
    path('<int:pk>/connect', login_required(exam_connect_list), name='exam_connect'),
    path('<int:pk>/connect/<int:patient_pk>', login_required(exam_connect_confirmation), name='exam_connect_confirm'),
    path('<int:pk>/disconnect', login_required(exam_disconnect_confirm), name='exam_disconnect_confirm'),

    path('<int:pk>/video_file', login_required(serve_exam_video_file), name='exam_video_serve'),
    path('<int:pk>/processed_video_file/<str:screen_position>', login_required(serve_exam_processed_video_file), name='exam_processed_video_serve'),
    path('<int:pk>/segmentation_video_file', login_required(serve_exam_segmentation_video_file), name='exam_segmentation_video_serve'),
    
    path('image/<str:filename>', login_required(serve_exam_image_file), name='exam_image_serve'),


]