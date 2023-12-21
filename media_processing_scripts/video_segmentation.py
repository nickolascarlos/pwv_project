import os
import uuid
import cv2 as cv
from pathlib import Path

import numpy as np
from media_processing_scripts.perspective_correction import correct_perspective

from media_processing_scripts.video_divider import VideoDivider
from segmentation_scripts.segmenter import segment

def get_roi_area(vidcap, i = 0):
    # Get first frame
    vidcap.set(cv.CAP_PROP_POS_FRAMES, i)
    success, img = vidcap.read()
    if not success:
        return None

    # Rewind to first frame
    vidcap.set(cv.CAP_PROP_POS_FRAMES, i)

     # Converting to grayscale
    gray_image = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

    # Applying threshold (binarizing the image)
    _, binary_image = cv.threshold(gray_image, 127, 255, cv.THRESH_BINARY)

    # Creating a kernel for the dilation operation
    kernel = np.ones((15, 15), np.uint8)

    # Applying dilation
    dilated_image = cv.dilate(binary_image, kernel, iterations=1)

    # Finding contours in the dilated image
    contours, _ = cv.findContours(dilated_image, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        x, y, w, h = cv.boundingRect(contour)
        if 1.5 <= w / h <= 2.8 and w * h > 300000:
            return x, y, w, h

    return None


def create_segmentation_video(video_file, exam_instance, callback, alpha=0.333, callback_period=100):
    
    video_capture = cv.VideoCapture(video_file) # Just for FPS and get_roi_area
    fps = video_capture.get(cv.CAP_PROP_FPS)

    video_divider = VideoDivider(video_file)
    divisor_frame = video_divider.find_division_in_frame_indexing() # For get_roi_area seeking
    
    divisor_frame += 10 # NEEDED: Just to assure stability (maybe could be smaller)
    
    _, exam_screen_video_iterator = video_divider.get_divided_video_as_iterators()

    # TODO: Change from absolute to relative path, somehow
    uuidx = uuid.uuid4()
    videos_dir_path = "C:/Users/nicko/projetos/pwv_project/segmentation_exam_videos/"
    result_video_filename_root = Path(video_file).stem[:15] + '_' + str(uuidx) + '_segmented.mp4'
    absolute_result_video_filename = videos_dir_path + result_video_filename_root

    result_video = cv.VideoWriter(absolute_result_video_filename, cv.VideoWriter_fourcc(*'MPJG'), fps/30, (384*2+200, 512))

    # Initialize variables
    x, y, w, h = None, None, None, None
    # Check the first 100 frames
    # If none contains the 'roi', stop the script
    for i in range (divisor_frame+1, divisor_frame+101):
        roi_area = get_roi_area(video_capture, i)
        if roi_area:
            x, y, w, h = roi_area
            break
    else:
        print("error:no roi to extract")
        return False, "Video doesn't contain a ROI"

    for count, frame in enumerate(exam_screen_video_iterator):
        # Trazido para cima por causa da linha do bloco que sucede esse. "if count % 10 != 10: continue"
        if count % callback_period == 0:
            processed_frames = count
            total_frames = int(video_capture.get(cv.CAP_PROP_FRAME_COUNT))
            callback(exam_instance, processed_frames, total_frames)

        if count % 30 != 0:
            continue

        cropped_image = frame[y:y + h, x:x + w]
        warped_image = correct_perspective(cropped_image)
        if warped_image is None:
            continue # Just ignore this frame

        left_screen = warped_image[0:512, 0:384]
        central_screen = warped_image[0:512, 384:384+200]
        right_screen = warped_image[0:512, 384+200:384+200+384]

        # TODO: Remover criação de arquivos temporários
        left_uuid = str(uuid.uuid4())
        right_uuid = str(uuid.uuid4())
        temp_path = r"C:\Users\nicko\projetos\pwv_project\temp\\"
        left_filename = temp_path + left_uuid + '.jpg'
        right_filename = temp_path + right_uuid + '.jpg'
        cv.imwrite(left_filename, left_screen)
        cv.imwrite(right_filename, right_screen)

        segmented_left_screen = segment(temp_path + left_uuid + '.jpg', min_area=3000)
        segmented_right_screen = segment(temp_path + right_uuid + '.jpg', min_area=3000)
        # central_black_image = np.zeros((512, 200, 3), dtype=np.uint8)
        concat_image = cv.hconcat([segmented_left_screen, central_screen, segmented_right_screen])

        os.remove(left_filename)
        os.remove(right_filename)

        result_video.write(concat_image)

    result_video.release()
    video_capture.release()

    print("success:Segmentation video created")
    return True, result_video_filename_root
