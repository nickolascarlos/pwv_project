import os, cv2
import numpy as np
from glob import glob
import tensorflow as tf
from tensorflow.keras.layers import Conv2D, BatchNormalization, Activation, MaxPool2D, Conv2DTranspose, Concatenate, Input
from tensorflow.keras.models import Model
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau, CSVLogger

from segmentation_scripts.model.predictor import get_predicted_segmentation


# def segment(image, min_area=5000, color=(0, 0, 255), thickness=3):
#     _, thresholded = get_predicted_segmentation(image)
#     contours, _ = cv2.findContours(thresholded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

#     contour_image = cv2.imread(image)
#     for contour in contours:
#         _, _, w, h = cv2.boundingRect(contour)
#         if w * h >= min_area:
#             contour_image = cv2.drawContours(contour_image, [contour], -1, color, thickness)

#     return contour_image

def segment(image, min_area=5000, color=(0, 0, 255), thickness=3):
    _, __, colormapped = get_predicted_segmentation(image)
    # contours, _ = cv2.findContours(thresholded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # contour_image = cv2.imread(image)
    # for contour in contours:
    #     _, _, w, h = cv2.boundingRect(contour)
    #     if w * h >= min_area:
    #         contour_image = cv2.drawContours(contour_image, [contour], -1, color, thickness)

    return colormapped



