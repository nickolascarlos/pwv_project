import cv2 as cv
import numpy as np

def correct_perspective(image):
    gray_image = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    coords = get_coordinates(gray_image)
    if coords is None:
        return None
    
    # Transformed image properties
    width, height = 970, 515
    new_coords = [[0, 0], [width, 0], [0, height], [width, height]]

    perspective_transform = cv.getPerspectiveTransform(np.float32([coords[0], coords[1], coords[2], coords[3]]), np.float32(new_coords))
    warped_image = cv.warpPerspective(image, perspective_transform, (width, height))

    return warped_image

def get_coordinates(image):
    _, image_tbp = cv.threshold(image, 90, 255, cv.THRESH_BINARY)

    kernel = cv.getStructuringElement(cv.MORPH_RECT, (10, 10))
    image_tbp = cv.dilate(image_tbp, kernel)
    image_tbp = cv.erode(image_tbp, kernel)

    # Get external contours
    contours, _ = cv.findContours(image_tbp, cv.RETR_LIST, cv.CHAIN_APPROX_SIMPLE)

    def contour_key(c):
        _, _, w, h = cv.boundingRect(c)
        return w * h

    # Make a copy of the contour list and sort it
    contours_copy = list(contours)
    contours_copy.sort(key=contour_key, reverse=True)

    # Get the largest contour
    largest_contour = contours_copy[0]

    # Approximate the contour with a polygon
    epsilon = 0.04 * cv.arcLength(largest_contour, True)
    approx = cv.approxPolyDP(largest_contour, epsilon, True)

    corner_points_classification = classify_corner_points(approx)
    if corner_points_classification is None:
        return None
    
    return corner_points_classification

def classify_corner_points(approx, silent=True):
    # Convert the list of points into a list of lists
    points = [list(x) for x in list(np.squeeze(approx))]

    if len(points) > 4:
        if not silent:
            raise Exception('There must be only 4 points')
        else:
            return None
        
    # Sort the points by y-coordinate
    points.sort(key=lambda x: x[1])
    
    # Divide into upper and bottom points
    upper_points = points[:2]
    lower_points = points[2:]
    
    # Sort the upper points by x-coordinate
    upper_points.sort(key=lambda x: x[0])
    
    # Sort the bottom points by x-coordinate
    lower_points.sort(key=lambda x: x[0])
    
    return upper_points[0], upper_points[1], lower_points[0], lower_points[1]
