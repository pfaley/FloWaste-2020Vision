import math
import cv2
import numpy as np

import timeit
from typing import List, Dict, Set, Tuple

from core.config import \
    CIRCLE_DETECT_MIN_DISTANCE_BETWEEN_CENTERS, \
    CIRCLE_DETECT_MIN_RADIUS, \
    CIRCLE_DETECT_PADDING_BOXES, \
    IMAGE_SEGMENT_SIZE_PX

from .circle import Circle
from .segmented_circle import SegmentedCircle, Segment


def is_contained_within_circle(cx, cy, cr, rx, ry, rw, rh):
    points = [
        (rx, ry),
        (rx + rw, ry),
        (rx, ry + rh),
        (rx + rw, ry + rh)
    ]

    for i, point in enumerate(points):
        if not is_point_on_circle(*point, cx, cy, cr):
            return False

    return True


def is_point_on_circle(px, py, cx, cy, cr):
    distance = math.sqrt(((cx - px) ** 2) + ((cy - py) ** 2))
    return distance <= cr


class CircleDetector:
    def __init__(self,
                 grid_size=IMAGE_SEGMENT_SIZE_PX,
                 min_radius=CIRCLE_DETECT_MIN_RADIUS,
                 min_distance_between_centers=CIRCLE_DETECT_MIN_DISTANCE_BETWEEN_CENTERS):
        self.grid_size: int = grid_size
        self.min_radius: int = min_radius
        self.min_distance_between_centers: int = min_distance_between_centers

    def get_segmented_circles(self, image: np.ndarray) -> List[SegmentedCircle]:
        start = timeit.default_timer()
        resized = cv2.resize(image, (640, 360))
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        min_dist_centers = 640
        min_radius = 100
        max_radius = 200
        circles = cv2.HoughCircles(gray,
                                   cv2.HOUGH_GRADIENT,
                                   1.2,
                                   min_dist_centers,
                                   minRadius=min_radius,
                                   maxRadius=max_radius)
        stop = timeit.default_timer()
        # print("detecting circle took %d" % (stop - start))

        if circles is None or circles is []:
            min_radius = 50
            max_radius = 100
            circles = cv2.HoughCircles(gray,
                                       cv2.HOUGH_GRADIENT,
                                       1.2,
                                       min_dist_centers,
                                       minRadius=min_radius,
                                       maxRadius=max_radius)

        if circles is None:
            return []
        # print(circles[0])
        circles = [Circle(c * 2) for c in circles]

        segmented_circles: List[SegmentedCircle] = []
        start = timeit.default_timer()
        for circle in circles:
            segmented_circles.append(self.get_segmented_circle(circle))

        stop = timeit.default_timer()
        # print("Segmenting circles took %d" % (stop - start))
        return segmented_circles

    # TODO: Multithread
    def get_segmented_circle(self, circle: Circle) -> SegmentedCircle:
        cx, cy, cr = circle.get_as_tuple()
        start_x = cx - cr
        start_y = cy - cr
        num_boxes = int(2 * cr / IMAGE_SEGMENT_SIZE_PX)
        segmented_circle: SegmentedCircle = SegmentedCircle(circle)

        for i in range(0, num_boxes):
            x1 = start_x + i * self.grid_size
            x2 = x1 + self.grid_size
            for j in range(0, num_boxes):
                y1 = start_y + j * self.grid_size
                y2 = y1 + self.grid_size
                if is_contained_within_circle(cx, cy, cr, x1, y1, self.grid_size, self.grid_size):
                    segmented_circle.add_segment(Segment(x1, y1, x2, y2))

        return segmented_circle

    def draw_segmented_circle(self, image):
        segmented_circles: List[SegmentedCircle] = self.get_segmented_circles(image)
        # print("Found %d circles" % len(segmented_circles))
        for segmented_circle in segmented_circles:
            segmented_circle.draw(image)
