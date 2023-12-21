import cv2 as cv
import numpy as np
from pprint import pprint
from collections import defaultdict

class InfoExtractor:
    FACTOR = 5#.251439539347409

    def __init__(self, image, text_reader):
        #self.image = cv.resize(image, (1042, 695))
        self.image = cv.resize(image, (5472, 3648))
        self.text_reader = text_reader

        # For caching
        self.dilated_image = None
        self.dilated_image_contours = None
        self.named_content_info_boxes = None

    def get_dilated_image(self):
        if self.dilated_image is not None:
            return self.dilated_image
        
        image = cv.cvtColor(self.image, cv.COLOR_BGR2GRAY)
        _, binary_image = cv.threshold(image, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)
        kernel = np.ones((3*InfoExtractor.FACTOR, 15*InfoExtractor.FACTOR), np.uint8)
        dilated_image = cv.dilate(binary_image, kernel, iterations=1)
        self.dilated_image = dilated_image # caching

        return dilated_image

    def get_dilated_image_contours(self):
        if self.dilated_image_contours is not None:
            return self.dilated_image_contours
        
        dilated_image = self.get_dilated_image()
        contours, _ = cv.findContours(dilated_image, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
        self.dilated_image_contours = contours # caching

        return contours

    def is_image_extractable(self):
        # Check whether image is a "patient info screen".
        # It is identified by the presence or absense of two
        # special rectangles, here called "towers" due to
        # its shape ratio
        towers_count = len(self.get_towers())

        return towers_count == 2

    def get_towers(self):
        contours = self.get_dilated_image_contours()

        towers = []
        for contour in contours:
            x, y, w, h = cv.boundingRect(contour)
            if w*h > 5000*InfoExtractor.FACTOR and  2.2 < h/w < 3.5:
                towers.append((x, y, w, h))

        return towers
    
    def get_towers_sorted_by_x(self):
        towers = self.get_towers()
        towers.sort(key=lambda coords: coords[0])

        return towers
    
    def get_towers_sorted_by_y(self):
        towers = self.get_towers()
        towers.sort(key=lambda coords: coords[1])

        return towers
    
    def get_left_tower(self):
        sorted_towers = self.get_towers_sorted_by_x()
        
        return sorted_towers[0]
    
    def get_generic_info_boxes(self):
        contours = self.get_dilated_image_contours()
        info_contours = [contour for contour in contours if self.is_generic_info_box(contour)]
        
        return info_contours

    def is_generic_info_box(self, contour):
        x, y, w, h = cv.boundingRect(contour)

        tower_x, tower_y, tower_w, tower_h = self.get_left_tower()
        bottom_left_left_tower_corner = (tower_x, tower_y + tower_h)

        return all([
                w/h > 1.75,
                w/h < 20, # To filter out the divider
                w*h > 100*InfoExtractor.FACTOR,
                w > 5*InfoExtractor.FACTOR,
                h > 5*InfoExtractor.FACTOR,
                x < bottom_left_left_tower_corner[0],
                y < bottom_left_left_tower_corner[1]
            ])
    
    def get_left_sorted_generic_info_boxes(self):
        info_boxes = self.get_generic_info_boxes()
        info_boxes = InfoExtractor.sort_contours_from_left_to_right(info_boxes)
        return info_boxes
    
    def get_divider(self):
        contours = self.get_dilated_image_contours()

        tower_x, tower_y, tower_w, tower_h = self.get_left_tower()
        bottom_left_left_tower_corner = (tower_x, tower_y + tower_h)

        for contour in contours:
            x, y, w, h = cv.boundingRect(contour)
            if all([w/h > 10, w > 100*InfoExtractor.FACTOR, x < bottom_left_left_tower_corner[0], y < bottom_left_left_tower_corner[1]]):
                return (x, y, w, h)
    
    def get_divided_generic_info_boxes(self):
        info_boxes = self.get_generic_info_boxes()
        divider = self.get_divider()

        upper_info_boxes = []
        lower_info_boxes = []
        for box in info_boxes:
            if cv.boundingRect(box)[1] < divider[1]:
                upper_info_boxes.append(box)
            else:
                lower_info_boxes.append(box)

        return {
            "upper": upper_info_boxes,
            "lower": lower_info_boxes
        }
    
    # TODO: Decompose this function into smaller functions
    def get_content_regions(self):
        divided_info_boxes = self.get_divided_generic_info_boxes()
        upper_boxes = divided_info_boxes["upper"]
        lower_boxes = divided_info_boxes["lower"]

        # UPPER

        sorted_upper_boxes = InfoExtractor.sort_contours_from_left_to_right(upper_boxes)
        first_column_upper_boxes = InfoExtractor.sort_contours_from_top_to_bottom(sorted_upper_boxes[0:4])

        id_label_info_box = first_column_upper_boxes[0]
        idl_x, idl_y, idl_w, idl_h = cv.boundingRect(id_label_info_box)
        # The age_sex label is the biggest horizontal info box, so it'll
        # be used to delimite the right x coordinate of the region
        age_sex_label_info_box = first_column_upper_boxes[2]
        asl_x, asl_y, asl_w, asl_h = cv.boundingRect(age_sex_label_info_box)
        div_x, div_y, div_w, div_h = self.get_divider()
        upper_content_region = (asl_x+asl_w, idl_y, div_x+div_w-asl_x-asl_w, div_y-idl_y)

        # LOWER

        sorted_lower_boxes = InfoExtractor.sort_contours_from_left_to_right(lower_boxes)
        lower_semi_entire_region = InfoExtractor.bounding_rect_for_contours(sorted_lower_boxes[2:])
        x, y, w, h = lower_semi_entire_region
        image_lower_semi_entire_region = cv.cvtColor(self.image[y:y+h, x:x+w], cv.COLOR_BGR2GRAY)
        _, binary_image = cv.threshold(image_lower_semi_entire_region, 127, 255, cv.THRESH_BINARY)

        vertical_kernel = np.ones((80*InfoExtractor.FACTOR, 5*InfoExtractor.FACTOR), np.uint8)
        closed_image = cv.morphologyEx(binary_image, cv.MORPH_CLOSE, vertical_kernel)
        
        bordered_closed_image = cv.copyMakeBorder(closed_image, 10*InfoExtractor.FACTOR, 10*InfoExtractor.FACTOR, 10*InfoExtractor.FACTOR, 10*InfoExtractor.FACTOR, cv.BORDER_CONSTANT, value=[0, 0, 0])
        
        contours, _ = cv.findContours(bordered_closed_image, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
        sorted_contours = InfoExtractor.sort_contours_from_left_to_right(contours)
        translated_contours = [contour + (-10*InfoExtractor.FACTOR, -10*InfoExtractor.FACTOR) for contour in sorted_contours]

        content_contours = translated_contours[1] # All contours, except for the leftmost
        # |-> To hide the "metrics" region, basically change above line for "content_contours = sorted_contours[1]""

        lower_content_region = InfoExtractor.bounding_rect_for_contours(content_contours)
        translated_lower_content_region = (lower_content_region[0] + x, lower_content_region[1] + y, lower_content_region[2], lower_content_region[3])

        return upper_content_region, translated_lower_content_region
    
    def get_content_regions_cropped_images(self, bordered=True):
        upper_content_region, lower_content_region = self.get_content_regions()
        
        upper_x, upper_y, upper_w, upper_h = upper_content_region
        cropped_upper_region = self.image[upper_y:upper_y+upper_h, upper_x:upper_x+upper_w]

        lower_x, lower_y, lower_w, lower_h = lower_content_region
        cropped_lower_region = self.image[lower_y:lower_y+lower_h, lower_x:lower_x+lower_w]

        if bordered:
            image_float = cropped_upper_region.astype(np.float32)

            # Calculate the mean color
            mean_color = np.mean(image_float, axis=(0, 1))
            mean_color = mean_color.astype(np.uint8)
            mean_color_tuple = (int(mean_color[0]), int(mean_color[1]), int(mean_color[2]))

            cropped_upper_region = cv.copyMakeBorder(cropped_upper_region, 50*InfoExtractor.FACTOR, 50*InfoExtractor.FACTOR, 50*InfoExtractor.FACTOR, 50*InfoExtractor.FACTOR, cv.BORDER_CONSTANT, value=mean_color_tuple)
            cropped_lower_region = cv.copyMakeBorder(cropped_lower_region, 50*InfoExtractor.FACTOR, 50*InfoExtractor.FACTOR, 50*InfoExtractor.FACTOR, 50*InfoExtractor.FACTOR, cv.BORDER_CONSTANT, value=mean_color_tuple)
        
        return cropped_upper_region, cropped_lower_region
        
    @staticmethod
    def bounding_rect_for_contours(contours):
        # Combine all contours into one array
        combined_contours = np.vstack(contours)
        
        # Find the bounding rectangle that encloses all the contours
        x, y, w, h = cv.boundingRect(combined_contours)
        
        return (x, y, w, h)

    @staticmethod
    def sort_contours_from_left_to_right(contours):
        contours = [contour for contour in contours] # Make a copy
        contours.sort(key=lambda coords: cv.boundingRect(coords)[0])
        return contours
    
    @staticmethod
    def sort_contours_from_top_to_bottom(contours):
        contours = [contour for contour in contours] # Make a copy
        contours.sort(key=lambda coords: cv.boundingRect(coords)[1])
        return contours
    
    def get_content_info_boxes_contours(self):
        upper_content_image, lower_content_image = self.get_content_regions_cropped_images()

        upper_content_image = cv.cvtColor(upper_content_image, cv.COLOR_BGR2GRAY)
        lower_content_image = cv.cvtColor(lower_content_image, cv.COLOR_BGR2GRAY)
        
        _, upper_content_image_threshold = cv.threshold(upper_content_image, 127, 255, cv.THRESH_BINARY)
        _, lower_content_image_threshold = cv.threshold(lower_content_image, 127, 255, cv.THRESH_BINARY)

        horizonal_kernel = np.ones((1*InfoExtractor.FACTOR, 20*InfoExtractor.FACTOR), dtype=np.uint8)
        closed_upper_content_image = cv.morphologyEx(upper_content_image_threshold, cv.MORPH_CLOSE, horizonal_kernel)
        closed_lower_content_image = cv.morphologyEx(lower_content_image_threshold, cv.MORPH_CLOSE, horizonal_kernel)

        lower_content_contours, _ = cv.findContours(closed_lower_content_image, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        upper_content_contours, _ = cv.findContours(closed_upper_content_image, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

        # The contours, here obtained from the cropped images, need to be translated
        # to align their points with the coordinates of the original image
        (upper_x, upper_y, _, _), (lower_x, lower_y, _, _) = self.get_content_regions()

        # These "-50" are due to the border added to the region cropped images
        translated_upper_content_contours = [contour + (upper_x-50*InfoExtractor.FACTOR, upper_y-50*InfoExtractor.FACTOR) for contour in upper_content_contours]
        translated_lower_content_contours = [contour + (lower_x-50*InfoExtractor.FACTOR, lower_y-50*InfoExtractor.FACTOR) for contour in lower_content_contours]

        return translated_upper_content_contours, translated_lower_content_contours

    
    def get_named_content_info_boxes(self):
        if self.named_content_info_boxes is not None:
            return self.named_content_info_boxes
        
        upper_content_info_boxes, lower_content_info_boxes = self.get_content_info_boxes_contours()

        sorted_upper_content_info_boxes = InfoExtractor.sort_contours_from_top_to_bottom(upper_content_info_boxes)
        sorted_lower_content_info_boxes = InfoExtractor.sort_contours_from_top_to_bottom(lower_content_info_boxes)

        named_info_boxes = {
            "id": sorted_upper_content_info_boxes[0],
            "name": sorted_upper_content_info_boxes[1],
            "age_sex": sorted_upper_content_info_boxes[2],
            "date": sorted_upper_content_info_boxes[3],
            "vasodilatation_rate": sorted_lower_content_info_boxes[0],
            "rest_diameter": sorted_lower_content_info_boxes[1],
            "max_diameter": sorted_lower_content_info_boxes[2],
            "max_blood_flow_rate": sorted_lower_content_info_boxes[3],
            "vessel_wall_thickness": sorted_lower_content_info_boxes[4]
        }

        self.named_content_info_boxes = named_info_boxes

        return named_info_boxes
    
    def extract(self):
        if not self.is_image_extractable():
            raise 'Non extractable image. Missing towers.'

        # Just for the info names
        named_info_boxes = self.get_named_content_info_boxes()

        extracted_infos = {}
        for name in named_info_boxes:
            extracted_infos[name] = self.read_info_box(name)
        
        return extracted_infos

    def read_info_box(self, info):
        named_info_boxes = self.get_named_content_info_boxes()
        info_box = named_info_boxes[info]

        x, y, w, h = cv.boundingRect(info_box)
        cropped_image = self.image[y:y+h, x:x+w]

        _, cropped_image_thresh = cv.threshold(cropped_image, 127, 255, cv.THRESH_BINARY)

        horizontal_kernel = np.ones((5,1))
        cropped_image = cv.erode(cropped_image_thresh, horizontal_kernel)

        allow_lists = defaultdict(lambda: list('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz /-.0123456789'))
        allow_lists['date'] = list("/ 0123456789.")
        allow_lists['name'] = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ ")
        allow_lists['max_blood_flow_rate'] = list("0123456789.")
        allow_lists['max_diameter'] = list("0123456789.")
        allow_lists['rest_diameter'] = list("0123456789.")
        allow_lists['vasodilatation_rate'] = list("0123456789.")
        allow_lists['vessel_wall_thickness'] = list("0123456789.")

        return self.text_reader.readtext(cropped_image, detail=0, decoder='beamsearch', allowlist=allow_lists[info])
    
    def get_highlighted_info_boxes_image(self):
        contour_image = self.image.copy()
        contours = self.get_divided_generic_info_boxes()

        for contour in contours["upper"]:
            x, y, w, h = cv.boundingRect(contour)
            cv.rectangle(contour_image, (x, y), (x+w, y+h), (0, 255, 0), 2)

        for contour in contours["lower"]:
            x, y, w, h = cv.boundingRect(contour)
            cv.rectangle(contour_image, (x, y), (x+w, y+h), (0, 255, 255), 2)

        divider = self.get_divider()
        cv.rectangle(contour_image, (divider[0], divider[1]), (divider[0]+divider[2], divider[1]+divider[3]), (0, 0, 255), 2)
        x, y, w, h = self.get_left_tower()
        cv.rectangle(contour_image, (x, y), (x+w, y+h), (0, 0, 255), 2)

        return contour_image
    
    def show_highlighted_info_boxes(self):
        contour_image = self.get_highlighted_info_boxes_image()
        cv.imshow('', contour_image)
        cv.waitKey(0)

    def extract_graphs(self):
        grayscale = cv.cvtColor(self.image, cv.COLOR_BGR2GRAY)
        _, thresholded = cv.threshold(grayscale, 128, 255, cv.THRESH_BINARY)
        
        kernel = np.ones((20*InfoExtractor.FACTOR, 10*InfoExtractor.FACTOR), np.uint8)
        closed_image = cv.morphologyEx(thresholded, cv.MORPH_CLOSE, kernel)
        contours, _ = cv.findContours(closed_image, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

        tower = self.get_left_tower()
        x_tower, y_tower, w_tower, h_tower = tower
        bottom_left_corner_y = y_tower + h_tower
        graphs = []
        for contour in contours:
            x, y, w, h = cv.boundingRect(contour)
            if y > bottom_left_corner_y and w*h > 5000*InfoExtractor.FACTOR:
                graphs.append(contour)
        
        left_sorted_graphs = InfoExtractor.sort_contours_from_left_to_right(graphs)

        assert len(left_sorted_graphs) == 3, 'Graphs: expecting exactly 3, found ' + str(len(left_sorted_graphs))

        cropped_graphs = []
        for contour in left_sorted_graphs:
            x, y, w, h = cv.boundingRect(contour)
            cropped_graphs.append(self.image[y:y+h, x:x+w])

        return {
            "rest": cropped_graphs[0],
            "after_cuff_released": cropped_graphs[1],
            "history": cropped_graphs[2]
        }

    def show_content_regions(self):
        upper, lower = self.get_content_regions_cropped_images(bordered=False)
        x = self.get_divided_generic_info_boxes()

        # cv.imshow('upper', upper)
        # cv.imshow('lower', lower)

        image = self.image.copy()
        # contours, contours2 = self.get_content_info_boxes_contours()

        for contour in [*x["upper"], *x["lower"]]:
            x, y, w, h = cv.boundingRect(contour)
            cv.rectangle(image, (x, y), (x+w, y+h), (0,255,0), 4)

        image = cv.resize(image, (1042, 695))

        cv.imshow('', image)
        cv.waitKey(0)
        cv.destroyAllWindows()


    
    
    
    
    
    
    