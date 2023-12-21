from itertools import islice
import uuid
import cv2 as cv
from easyocr import Reader
from subapps_pwv.media_processing_scripts.info_extractor_2 import InfoExtractor
from subapps_pwv.media_processing_scripts.video_divider import VideoDivider

ocr_reader = Reader(['en', 'pt'])

def extract(video_file, callback):
    video_divider = VideoDivider(video_file)
    divisor_frame_index = video_divider.find_division_in_frame_indexing()

    patient_screen_video_iterator, _ = video_divider.get_divided_video_as_iterators()

    info_extracted, graphs_extracted = None, None
    # Verifica se o vídeo tem a parte da tela do paciente 
    if divisor_frame_index > 2: # TODO: Melhorar essa verificação (talvez divisor_frame == 0 ou 1 sirva)
        print('STARTED INFO AND GRAPHS EXTRACTION')
        callback(1)
        # Pula os 10 primeiros frames (com islice) e pega o 11º (espera-se que este seja mais "estável" que os primeiros)
        patient_screen_frame = next(islice(patient_screen_video_iterator, 10, 11))
        info_extractor = InfoExtractor(patient_screen_frame, ocr_reader)
        
        try:
            info_extracted = info_extractor.extract()
            callback(2)
        except Exception as e:
            return False, 'Failed to extract info ::' + str(e)
        
        try:
            graphs_extracted = info_extractor.extract_graphs()
            callback(3)
            uuidx = uuid.uuid4()
            # TODO: Change from absolute to relative path
            rest_graph_filename = "subapps_pwv/exam_images/" + str(uuidx) + "_rest_graph.jpg"         
            after_cuff_filename = "subapps_pwv/exam_images/" + str(uuidx) + "_after_cuff.jpg"

            rest_graph = graphs_extracted['rest']
            after_cuff_released_graph = graphs_extracted['after_cuff_released']
            rest_graph_height, rest_graph_width, _ =  rest_graph.shape
            after_cuff_released_graph_height, after_cuff_released_graph_width, _ = after_cuff_released_graph.shape
            
            resize_factor = 5 # Quanto vai DIMINUIR
            rest_graph = cv.resize(rest_graph, (rest_graph_width//resize_factor, rest_graph_height//resize_factor))
            after_cuff_released_graph = cv.resize(after_cuff_released_graph, (after_cuff_released_graph_width//resize_factor, after_cuff_released_graph_height//resize_factor))

            cv.imwrite(rest_graph_filename, rest_graph)
            cv.imwrite(after_cuff_filename, after_cuff_released_graph)

            graphs_extracted = {
                'rest_graph': str(uuidx) + "_rest_graph.jpg",
                'after_cuff_released_graph': str(uuidx) + "_after_cuff.jpg"
            }
            callback(4)
        except Exception as e:
            return False, 'Failed to extract graphs ::' + str(e)
        
        print('FINISHED INFO AND GRAPHS EXTRACTION')

    return True, (info_extracted, graphs_extracted)