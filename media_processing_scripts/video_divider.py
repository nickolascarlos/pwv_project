import cv2 as cv
from . import info_extractor_2 as iex

class VideoDivider:

    # TODO: Change video_path back to video_cap. Careful: get_part_{1,2}_as_iterator
    def __init__(self, video_path):
        self.video_path = video_path
        self.video_cap = cv.VideoCapture(video_path)

    # TODO: Maybe iter(self.video_cap.read) solves it properly
    def get_whole_video_as_iterator(self):
        local_video_cap = cv.VideoCapture(self.video_path)
        while True:
            success, frame = local_video_cap.read()
            if not success:
                break
            yield frame
    
    def find_division_in_frame_indexing(self):
        # Parameters for frame processing
        skip_frames = 10  # Number of frames to skip during iteration
        debounce_limit = 6  # Number of consecutive frames without patient information before division
        debounce = 0

        for frame_number, frame in enumerate(self.get_whole_video_as_iterator()):
            if frame_number % skip_frames == 0:
                # Create an InfoExtractor instance to check if frame contains patient information
                extractor = iex.InfoExtractor(frame, None)

                if not extractor.is_image_extractable():
                    return frame_number
                # TODO: Reimplement debouncing
                #     debounce += 1

                #     if debounce == debounce_limit:
                #         # Return the frame closest to the detection that is not a patient information screen.
                #         # Adjust the frame number because in this state (debounce=2), we are already a few frames
                #         # ahead of the frame from which the detection was made.
                #         return frame_number - (debounce_limit-1) * skip_frames
                # else:
                #     debounce = 0
        
        # If no suitable frame is found, return -1
        return -1
    
    def get_division_in_seconds(self):
        frame_rate = self.video_cap.get(cv.CAP_PROP_FPS)
        division_frame_number = self.find_division_in_frame_indexing()

        return division_frame_number/frame_rate
    
    def get_part_1_as_iterator(self):
        frame_division = self.find_division_in_frame_indexing()
        video_capture = cv.VideoCapture(self.video_path)

        frame_count = 0
        while frame_count < frame_division:
            success, frame = video_capture.read()
            if not success:
                break
            yield frame
            frame_count += 1

    def get_part_2_as_iterator(self):
        division_frame_number = self.find_division_in_frame_indexing()
        
        video_capture = cv.VideoCapture(self.video_path)
        video_capture.set(cv.CAP_PROP_POS_FRAMES, division_frame_number)

        frame_count = division_frame_number
        while True:
            success, frame = video_capture.read()
            if not success:
                break
            yield frame
            frame_count += 1

    def get_divided_video_as_iterators(self):
        return self.get_part_1_as_iterator(), self.get_part_2_as_iterator()


    def show_transition(self):
        video = cv.VideoCapture(self.video_path)
        division_frame = self.find_division_in_frame_indexing()
        frame_count = 0
        while True:
            success, frame = video.read()
            if not success:
                break
            if division_frame-1 <= frame_count <= division_frame+1:
                cv.imshow('', frame)
                cv.waitKey(0)
            elif frame_count >= division_frame+1:
                break
            frame_count += 1
        cv.destroyAllWindows()



