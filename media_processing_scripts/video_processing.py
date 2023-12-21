import media_processing_scripts.video_patient_info_and_graphs_extractor as info_and_graphs_extractor
import media_processing_scripts.video_exam_images_extractor as exam_images_extractor
from media_processing_scripts.video_segmentation import create_segmentation_video

def process(video_filename, exam_instance):
    def exam_images_extractor_callback(exam, processed_frames, total_frames):
        exam.processing_status = ('R:%.2f' % (processed_frames/total_frames*100)) + '%'
        exam.save()

    success, processed_video_filename_or_error = exam_images_extractor.extract_to_videos(video_filename, exam_instance, exam_images_extractor_callback)
    if not success:
        exam_instance.processing_status = 'failed'
        exam_instance.save()
        error = processed_video_filename_or_error
        return False, error
    
    def info_and_graphs_extractor_callback(step):
        exam_instance.processing_status = 'IaG:%d/4' % (step)
        exam_instance.save()

    success, info_and_graphs_or_error = info_and_graphs_extractor.extract(video_filename, info_and_graphs_extractor_callback)
    if not success:
        exam_instance.processing_status = 'failed'
        exam_instance.save()
        error = info_and_graphs_or_error
        return False, error
    
    def create_segmentation_video_callback(exam, processed_frames, total_frames):
        exam.processing_status = ('S:%.2f' % (processed_frames/total_frames*100)) + '%'
        exam.save()

    success, segmentation_video_filename_or_error = create_segmentation_video(video_filename, exam_instance, create_segmentation_video_callback, callback_period=20)
    if not success:
        exam_instance.processing_status = 'failed'
        exam_instance.save()
        error = segmentation_video_filename_or_error
        return False, error

    processed_video_filename = processed_video_filename_or_error
    segmentation_video_filename = segmentation_video_filename_or_error
    extracted_info, extracted_graphs = info_and_graphs_or_error

    exam_instance.processed_video_file.name = processed_video_filename
    exam_instance.segmentation_video_file.name = segmentation_video_filename

    # [!] extracted_graphs e extracted_info são iguais a None se
    # não existir a tela de informações do paciente no vídeo 
    if extracted_graphs is not None:
        exam_instance.rest_graph = extracted_graphs['rest_graph']
        exam_instance.after_cuff_released_graph = extracted_graphs['after_cuff_released_graph']

    if extracted_info is not None:
        extractable_attributes = ['vasodilatation_rate', 'rest_diameter', 'max_diameter', 'max_blood_flow_rate', 'vessel_wall_thickness']
        
        for attribute in extractable_attributes:
            try:
                if not getattr(exam_instance, attribute):
                    setattr(exam_instance, attribute, float(' '.join(extracted_info[attribute])))
            except Exception as e:
                print('ERRO! ' + str(e))
    
    exam_instance.processing_status = 'complete'
    exam_instance.save()

    return True, ''



