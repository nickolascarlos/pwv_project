import cv2 as cv
import numpy as np
import easyocr

reader = easyocr.Reader(['en', 'pt'])

IMAGE_PATH = r"C:\Users\nicko\projetos\pfc\4-2.jpg"
image = cv.imread(IMAGE_PATH)

cv.imshow("main", image)
cv.waitKey(0)

image = cv.cvtColor(image, cv.COLOR_BGR2GRAY)

_, binary_image = cv.threshold(image, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)
kernel = np.ones((3, 20), np.uint8)  # Você pode ajustar o tamanho do kernel conforme necessário
dilated_image = cv.dilate(binary_image, kernel, iterations=1)

def get_left_tower(dilated_image):
    contours, _ = cv.findContours(dilated_image, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    towers = [] # left and right
    for contour in contours:
        x, y, w, h = cv.boundingRect(contour)
        if w*h > 5000 and  2.2 < h/w < 3.5:
            towers.append((x, y, w, h))
    towers.sort(key=lambda coords: coords[0])

    return towers[0]


contours, _ = cv.findContours(dilated_image, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

contour_image = cv.cvtColor(image.copy(), cv.COLOR_GRAY2BGR)

x, y, w, h = get_left_tower(dilated_image)
bottom_left_left_tower_corner = (x, y+h)
cv.rectangle(contour_image, (x, y), (x+w, y+h), (0, 0, 255), 2)

info_contours = []
for contour in contours:
    x, y, w, h = cv.boundingRect(contour)
    is_eligible = all([
        w/h > 1.75,
        w*h > 100,
        w > 10,
        h > 10,
        x < bottom_left_left_tower_corner[0],
        y < bottom_left_left_tower_corner[1]
    ])

    if is_eligible:
        # cv.rectangle(contour_image, (x, y), (x+w, y+h), (0, 255, 0), 1)
        info_contours.append((x, y, w, h))
        
def get_left_sorted_info_boxes(info_boxes):
    info_boxes = [i for i in info_boxes]
    info_boxes.sort(key=lambda coords: coords[0])
    return info_boxes

leftee_info_boxes = get_left_sorted_info_boxes(info_contours)
for ib in leftee_info_boxes[:6]:
    x, y, w, h = ib
    cv.rectangle(contour_image, (x, y), (x+w, y+h), (0, 255, 255), 1)

rightee_info_boxes = leftee_info_boxes[6:]
rightee_info_boxes.sort(key=lambda coords: coords[0])
ratihoo = rightee_info_boxes[:9]
ratihoo.sort(key=lambda coords: coords[1])
for ee, ib in enumerate(ratihoo):
    x, y, w, h = ib
    cv.rectangle(contour_image, (x, y), (x+w, y+h), (0, 255, 0), 1)
    cropped_image = image[y:y+h, x:x+w]
    # _, binary_image_cropped = cv.threshold(image, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)
    # cropped_image = cv.cvtColor(cv.erode(binary_image_cropped, np.ones((1,1), np.uint8)), cv.COLOR_GRAY2BGR)
    # if ee == 3:
    #     cv.imshow("c", cropped_image)
    text = reader.readtext(cropped_image, detail=0, decoder='beamsearch', allowlist=(list('0123456789/: ') if ee == 3 else None))
    cv.putText(contour_image, str(''.join(text)), (x, y), 1, 0.9, (0, 0, 255), 1)



cv.imshow("main", contour_image)
cv.waitKey(0)



