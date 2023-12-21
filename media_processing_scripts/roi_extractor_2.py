"""
 This script extracts the ROI (artery images) from the recorded screen.
"""

import cv2 as cv
import numpy as np
import sys, math

import perspective_correction as pc

def extract(videofile, dst_dir, prefix):
    print("REX2: Processing %s file" % videofile)
    vidcap = cv.VideoCapture(videofile)
    total_frames = int(vidcap.get(cv.CAP_PROP_FRAME_COUNT))

    count = 0
    frames_count = 0
    success, image = vidcap.read()
    while success:
        if frames_count % 100 == 0:
            print('REX2: frame %d/%d | %.2f' % (frames_count, total_frames, ((frames_count/total_frames)*100)))

        # Loading the image
        img = image

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

        # Creating a copy of the original image to draw the contours
        image_with_contours = img.copy()

        # Drawing the contours on the image
        for contour in contours:
            # Getting the bounding rectangle
            x, y, w, h = cv.boundingRect(contour)

            if 1.5 <= w/h <= 2.8 and w*h > 300000:
                # Drawing the bounding rectangle on the image
                cv.rectangle(image_with_contours, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
                # Crop, correct perspective, and save
                cropped_image = img[y:y+h, x:x+w]
                warped_image = pc.correct_perspective(cropped_image)

                warped_width = 970
                warped_height = 515

                # Crop left, center, and right screens
                left_screen = warped_image[0:512, 0:384]
                central_screen = warped_image[0:512, 384:385+200]
                right_screen = warped_image[0:512, 384+200:384+200+384]

                cv.imwrite(dst_dir + "/%s_frame_%s_left.jpg" % (prefix, count), left_screen)
                cv.imwrite(dst_dir + "/%s_frame_%s_central.jpg" % (prefix, count), central_screen)
                cv.imwrite(dst_dir + "/%s_frame_%s_right.jpg" % (prefix, count), right_screen)
                count += 1

        success, image = vidcap.read()
        frames_count += 1
