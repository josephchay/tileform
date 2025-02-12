import time
import pygame

from pygine.foundation.container import Container
from pygine.foundation.window import Window


class Application(Container):
    def __init__(self, dimensions=(1280, 720), caption='pygine', flags=0, fps_cap=60, dt_cap=1, opengl=False, frag_path=None):
        super().__init__()

        self.window = Window(dimensions=dimensions, caption=caption, flags=flags, fps_cap=fps_cap, dt_cap=dt_cap, opengl=opengl, frag_path=frag_path)
