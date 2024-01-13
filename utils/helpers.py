import os
import math
import numpy
import pygame


def isf_img(path: str) -> bool:
    """
    Checks if the file is an image

    :param path: The path to the image file
    :return: bool
    """

    return os.path.isfile(path) and path.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', 'tiff'))


def draw_dashed_line(surf, color, start_pos, end_pos, width=1, dash_length=10, skip_initial=0):
    x1, y1 = start_pos
    x2, y2 = end_pos
    dl = dash_length

    if x1 == x2:
        ycoords = [y for y in range(y1, y2, dl if y1 < y2 else -dl)]
        xcoords = [x1] * len(ycoords)
    elif y1 == y2:
        xcoords = [x for x in range(x1, x2, dl if x1 < x2 else -dl)]
        ycoords = [y1] * len(xcoords)
    else:
        a = abs(x2 - x1)
        b = abs(y2 - y1)
        c = round(math.sqrt(a**2 + b**2))
        dx = dl * a / c
        dy = dl * b / c

        xcoords = [x for x in numpy.arange(x1, x2, dx if x1 < x2 else -dx)]
        ycoords = [y for y in numpy.arange(y1, y2, dy if y1 < y2 else -dy)]

    next_coords = list(zip(xcoords[1::2], ycoords[1::2]))
    last_coords = list(zip(xcoords[0::2], ycoords[0::2]))

    for (x1, y1), (x2, y2) in zip(next_coords[skip_initial:], last_coords[skip_initial:]):
        start = (round(x1), round(y1))
        end = (round(x2), round(y2))
        pygame.draw.line(surf, color, start, end, width)


def swap_color(img, old, new, colorkey=None):
    img.set_colorkey(old)
    surf = img.copy()
    surf.fill(new)
    surf.blit(img, (0, 0))
    if colorkey is not None:
        surf.set_colorkey(colorkey)

    return surf


def tone_color(color, tone, opac_tone=0) -> tuple:
    """
    Tone a color (including transparency) darker or lighter based on the given tone.

    :param color: The original color. It can be either in the format (R, G, B) or (R, G, B, A) or a hex string.
    :param tone: A value indicating the tone adjustment. Use positive values for lighter and negative values for darker.
    :param opac_tone: Positive value for more opaque and negative value for more transparent.
    :return: The toned color in the format (R, G, B) or (R, G, B, A).
    """

    if isinstance(color, str):
        color = hex2rgb(color)
    elif not isinstance(color, tuple) or len(color) not in (3, 4):
        raise ValueError("Invalid color format")

    r, g, b = tuple(min(255, max(0, c + tone)) for c in color[0:3])
    a = max(0, min(255, int(color[3] + opac_tone))) if len(color) == 4 else max(0, min(255, int(255 + opac_tone)))

    return r, g, b, a


def hex2rgb(clr):
    """
    Convert a hex color string to RGBA format.

    :param clr: The hex color string (e.g., "#RRGGBB" or "#RRGGBBAA").
    :return: The corresponding RGBA tuple.
    """

    clr = clr.lstrip('#')
    if len(clr) in (6, 8):
        r = int(clr[0:2], 16)
        g = int(clr[2:4], 16)
        b = int(clr[4:6], 16)
        if len(clr) == 8:
            a = int(clr[6:8], 16)
            return r, g, b, a
        else:
            return r, g, b
    else:
        raise ValueError("Invalid hex color format")


def rgb2hex(clr):
    """
    Convert an RGBA color tuple to hex format.

    :param clr: The RGBA color tuple.
    :return: The corresponding hex color string.
    """
    if len(clr) in (3, 4):
        r, g, b = clr[0:3]
        a = clr[3] if len(clr) == 4 else 255
        return "#{:02X}{:02X}{:02X}{:02X}".format(r, g, b, a)
    else:
        raise ValueError("Invalid RGBA color format")
