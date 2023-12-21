import uuid
import cv2 as cv
import numpy as np
from pathlib import Path

from .perspective_correction import correct_perspective
from .video_divider import VideoDivider

WARPED_WIDTH = 970
WARPED_HEIGHT = 515


def get_roi_area(vidcap, i = 0):
    # Get i-th frame
    vidcap.set(cv.CAP_PROP_POS_FRAMES, i)
    success, img = vidcap.read()
    if not success:
        return None

    # Rewind to i-th frame
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


def extract_to_videos(video_file, exam_instance, callback, callback_period=100):

    video_capture = cv.VideoCapture(video_file) # Just for FPS and get_roi_area
    fps = video_capture.get(cv.CAP_PROP_FPS)

    video_divider = VideoDivider(video_file)
    divisor_frame_index = video_divider.find_division_in_frame_indexing() # For get_roi_area seeking

    if divisor_frame_index == -1:
        print("error:division_frame == -1")
        return False, 'division_frame == -1'
    else:
        divisor_frame_index += 10 # NEEDED: Just to assure stability (maybe could be smaller)
    
    _, exam_screen_video_iterator = video_divider.get_divided_video_as_iterators()

    # TODO: Change from absolute to relative path, somehow
    uuidx = uuid.uuid4()
    result_video_filename_root = Path(video_file).stem[:15] + '_' + str(uuidx) + '_processed_'

    videos_dir_path = "exam_videos/"
    videos_extension = '.mp4' # Don't change that!!!
    absolute_result_video_filename_root = videos_dir_path + result_video_filename_root 
    absolute_result_video_filename_left = absolute_result_video_filename_root + 'left' + videos_extension
    absolute_result_video_filename_right =  absolute_result_video_filename_root + 'right' + videos_extension
    absolute_result_video_filename_central =  absolute_result_video_filename_root + 'central' + videos_extension

    result_video_left = cv.VideoWriter(absolute_result_video_filename_left, cv.VideoWriter_fourcc(*'MPJG'), fps, (384, 512))
    result_video_right = cv.VideoWriter(absolute_result_video_filename_right, cv.VideoWriter_fourcc(*'MPJG'), fps, (384, 512))
    result_video_central = cv.VideoWriter(absolute_result_video_filename_central, cv.VideoWriter_fourcc(*'MPJG'), fps, (200, 512))

    # Initialize variables
    x, y, w, h = None, None, None, None
    # Check the first 100 frames
    # If none contains the 'roi', stop the script
    for i in range (divisor_frame_index+1, divisor_frame_index+101):
        roi_area = get_roi_area(video_capture, i)
        if roi_area:
            x, y, w, h = roi_area
            break
    else:
        print("error:no roi to extract")
        return False, "Video doesn't contain a ROI"

    for count, frame in enumerate(exam_screen_video_iterator):
        cropped_image = frame[y:y + h, x:x + w]
        warped_image = correct_perspective(cropped_image)
        if warped_image is None:
            continue # Just ignore this frame
        gray = cv.cvtColor(warped_image, cv.COLOR_BGR2GRAY)
        equalized_image = cv.equalizeHist(gray)
        bgr_equalized_image = cv.cvtColor(equalized_image, cv.COLOR_GRAY2BGR)

        left_screen = bgr_equalized_image[0:512, 0:384]
        central_screen = bgr_equalized_image[0:512, 384:384+200]
        right_screen = bgr_equalized_image[0:512, 384+200:384+200+384]

        result_video_left.write(left_screen)
        result_video_right.write(right_screen)
        result_video_central.write(central_screen)

        if count % callback_period == 0:
            processed_frames = count
            total_frames = int(video_capture.get(cv.CAP_PROP_FRAME_COUNT))
            callback(exam_instance, processed_frames, total_frames)

    result_video_left.release()
    result_video_right.release()
    result_video_central.release()
    video_capture.release()

    print("success:Video ROI and patient information extracted")
    return True, result_video_filename_root