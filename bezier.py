""" Bézier curve creation (as used in CSS animation)

Written by Cyprien N, 2018
Feel free to do what you like with it.

This script uses tuples for coordinates, as we
need to create lots of small ones often,
and tuples are more efficient at this task
http://zwmiller.com/blogs/python_data_structure_speed.html
"""
# pylint: disable=no-name-in-module, no-member

import pygame
from pygame.constants import (
    QUIT, MOUSEMOTION, MOUSEBUTTONDOWN,
    MOUSEBUTTONUP
)

WIDTH = 800
HEIGHT = 800
GRAPH_WIDTH = 7 / 8 * WIDTH
GRAPH_MARGIN = (WIDTH - GRAPH_WIDTH) / 2
GRAPH_SIZE = GRAPH_MARGIN + GRAPH_WIDTH
DISPLAY = pygame.display.set_mode((WIDTH, HEIGHT))


def vectormult(multiplier: int, vector: list):
    """ Multiply vector by multiplier """
    return [multiplier * vector[0], multiplier * vector[1]]


def vectoradd(*vectors: list):
    return [
        sum([vector[0] for vector in vectors]),
        sum([vector[1] for vector in vectors])
    ]


class Bezier():
    """ Object that'll take care of Bézier creation,
    blitting, updating.
    Enter coordinates of control points 1 and 2 of
    a cubic Bézier, each having the form [x, y].
    granularity is the number of points of the curve,
    its precision.
    """
    def __init__(self, p1: tuple, p2: tuple, granularity=60):
        self.granularity = 1 / granularity
        self.p1 = Control_Point(p1, 15)
        self.p2 = Control_Point(p2, 15)
        self.display_rect = pygame.Rect(
            GRAPH_MARGIN, 0, 75, 75
        )
        self.display_rect.centery = HEIGHT - (HEIGHT - GRAPH_SIZE) / 2

        self.generate_bezier()


    def generate_bezier(self):
        """ Calculate and scale points for Bézier curve. """
        self.points = []
        self._calculate_bezier()
        self._scale()


    def _calculate_bezier(self):
        """ Do the actual curve calculation work. """
        p1 = self.p1.normalize()
        p2 = self.p2.normalize()
        p0, p3 = (0, 1), (1, 0)
        t = 0.0

        # Don't forget that last segment
        while t <= 1 + self.granularity:
            self.points.append(
                vectoradd(
                    vectormult((1 - t) ** 3, p0),
                    vectormult(3 * (1 - t) ** 2 * t, p1),
                    vectormult(3 * (1 - t) * t ** 2, p2),
                    vectormult(t ** 3, p3)
                )
            )
            t += self.granularity


    def _scale(self):
        """ Scale raw Bézier curve points into
        ones that are visible when drawn.
        """
        offset = [GRAPH_MARGIN, GRAPH_MARGIN]

        for i in range(len(self.points)):
            # Use index values rather than iterating so that
            # we don't need to create a copy of points.
            # Less readable, but this operation will be done
            # a lot and needs to be efficient
            self.points[i] = vectoradd(
                vectormult(GRAPH_WIDTH, self.points[i]),
                offset
            )


    def get_control_points(self):
        """ Return normalized coordinates of controls points. """
        points = [
            *self.p1.normalize(),
            *self.p2.normalize()
        ]
        for i in (1, 3):
            points[i] = round(1 - points[i], 2)

        for i in (0, 2):
            points[i] = round(points[i], 2)

        return points


    def draw(self, target: pygame.Surface, color: tuple):
        """ Draw all curve elements to target. """
        DISPLAY.fill((0, 0, 0))
        pygame.draw.aaline(
            target, (100, 100, 100),
            (GRAPH_MARGIN, GRAPH_SIZE),
            self.p1.rect.center
        )
        pygame.draw.aaline(
            target, (100, 100, 100),
            (GRAPH_SIZE, GRAPH_MARGIN),
            self.p2.rect.center
        )
        self.p1.draw(target, (255, 255, 255))
        self.p2.draw(target, (255, 255, 255))
        pygame.draw.aalines(target, color, False, self.points)


    def update(self, mouse_rel: tuple):
        """ Update curve upon control point modification.
        Returns positive if a change was noted.
        """
        # Avoid useless recalculations
        if self.p1.update(mouse_rel) or self.p2.update(mouse_rel):
            self.generate_bezier()
            return True
        return False


    def check_click(self, mouse_pos: tuple):
        """ Check if user clicks on a control point, or
        clicks on rect to animate it.
        """
        self.p1.check_click(mouse_pos)
        self.p2.check_click(mouse_pos)


    def deselect(self):
        """ User has unpressed mouse, deselect points. """
        self.p1.selected = False
        self.p2.selected = False


class Control_Point():
    """ Object that represents a draggable item
    that can be used to customize Bézier.
    """
    def __init__(self, position: tuple, diameter: int):
        # Transform Bézier point coordinates into
        # pixel coordinates.
        coords = (
            position[0] * GRAPH_WIDTH + GRAPH_MARGIN,
            # Pixel y coordinates grow downwards, whereas
            # in the Cartesian system they grow in the opposite
            # direction. We need to invert the point's
            # y value to get the pixel value.
            (1 - position[1]) * GRAPH_WIDTH + GRAPH_MARGIN
        )
        self.rect = pygame.Rect(
           *coords, diameter, diameter
        )
        self.rect.center = coords
        self.selected = False


    def normalize(self):
        """ Return coordinates formatted to be usable
        as a control point in a Bézier curve.
        """
        return (
            (self.rect.centerx - GRAPH_MARGIN) / GRAPH_WIDTH,
            (self.rect.centery - GRAPH_MARGIN) / GRAPH_WIDTH
        )


    def check_click(self, mouse_pos: tuple):
        """ Check if user clicks on handle. """
        if self.rect.collidepoint(mouse_pos):
            self.selected = True


    def update(self, mouse_rel: tuple):
        """ Move point along with mouse. Returns
        True if selected, False otherwise.
        """
        if not self.selected:
            return False
        self.rect.centerx += mouse_rel[0]
        self.rect.centerx = max(
            GRAPH_MARGIN, min(self.rect.centerx, GRAPH_SIZE)
        )
        self.rect.centery += mouse_rel[1]
        return True


    def draw(self, target: pygame.Surface, color: tuple):
        """ Blit control plot handle to target. """
        pygame.draw.ellipse(target, color, self.rect)


bezier_manager = Bezier((1, 0), (0, 1))
pygame.display.set_caption(
    "Cubic Bézier curve: {}, {}, {}, {}".format(
        *bezier_manager.get_control_points()
    )
)
clock = pygame.time.Clock()

DISPLAY.fill((0, 0, 0))
bezier_manager.draw(DISPLAY, (255, 255, 255))
pygame.display.update()

while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            exit(0)

        if event.type == MOUSEBUTTONDOWN:
            if event.button == 1:
                bezier_manager.check_click(pygame.mouse.get_pos())
                # This is necessary because we don't
                # want the object to jump around.
                # This happends because movement
                # between subsequent calls is returned
                pygame.mouse.get_rel()

        if event.type == MOUSEBUTTONUP:
            bezier_manager.deselect()

        if event.type == MOUSEMOTION:
            # Avoid useless redraws
            if bezier_manager.update(pygame.mouse.get_rel()):
                pygame.display.set_caption(
                    "Cubic Bézier Curve: ({}, {}, {}, {})".format(
                        *bezier_manager.get_control_points()
                    )
                )
                bezier_manager.draw(DISPLAY, (255, 255, 255))
                pygame.display.update()

    clock.tick(60)
