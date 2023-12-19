import cv2
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt

from .model import modelx

height = 512
width = 384

def predict(image):
    # image_path = "/content/drive/MyDrive/N011-3_frame_944_right.jpg"
    image_ = tf.keras.preprocessing.image.load_img(image, target_size=(height, width))
    
    # Resize the image to the target size
    # image_resized = cv2.resize(image, (width, height))
    image_tensor = tf.keras.preprocessing.image.img_to_array(image_)

    # Add batch dimension
    image_tensor = tf.expand_dims(image_tensor, axis=0)

    # Normaliza
    image_tensor /= 255.0

    return modelx.predict(image_tensor)

def get_predicted_segmentation(image, alpha=0.5):
    y = predict(image)
    
    segmentation = np.where(y[0] > alpha, 1, 0)
    alpha_normalized_image = cv2.normalize(segmentation, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
    rgb_image = cv2.cvtColor(alpha_normalized_image, cv2.COLOR_GRAY2RGB)

    probability_normalized_image = cv2.normalize(y[0], None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
    colormapped_image = cv2.applyColorMap(probability_normalized_image, cv2.COLORMAP_PLASMA)

    return rgb_image, alpha_normalized_image, colormapped_image
