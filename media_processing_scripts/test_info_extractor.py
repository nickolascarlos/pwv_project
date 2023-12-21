import info_extractor_2 as iex
import cv2 as cv
# import easyocr
from pprint import pprint

#reader = easyocr.Reader(['en', 'pt'])

ie = iex.InfoExtractor(cv.imread(r"H:\Archive-3\Captura de tela 2023-11-20 073040.png"), None)

u = ie.extract_graphs()
for graph in u:
    image = u[graph]
    cv.imshow('', cv.resize(image, (1042, 695)))
    cv.waitKey(0)

cv.destroyAllWindows()