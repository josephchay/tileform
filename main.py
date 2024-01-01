import random
import sys

from pygame.math import Vector2 as Vector

from scripts.assets import *
from settings import *
from utils.helpers import *
from editor import Editor


class Main:
    def __init__(self):
        """ The main constructor """

        pygame.init()
        pygame.display.set_caption('Tileform')

        self.is_fullscreen = False
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.display = pygame.Surface((WINDOW_WIDTH / RENDER_SCALE, WINDOW_HEIGHT / RENDER_SCALE))
        self.clock = pygame.time.Clock()

        # self.fullscreen_transition = FullScreenTransition(self.screen, (WINDOW_WIDTH + 140, WINDOW_HEIGHT + 140))

        self.editor_active = True

        self.providers = {
            'assets': AssetHandler(self, ASSETS_PATH),
        }

        self.editor = Editor(self)

        # cursors
        self.providers['assets']['gfx'].loaddir('cursors', colorkey=IMG_COLORKEY_WHITE, prefix='cursor')
        self.cursor_assets = {
            'default': self.providers['assets']['gfx'].get_only('cursor_default'),
            'handle': self.providers['assets']['gfx'].get_only('cursor_handle'),
        }

        self.cursorize()

    def run(self) -> None:
        """
        Handles the main loop

        :return: None
        """

        while True:
            mouse_pos = Vector(pygame.mouse.get_pos()) / RENDER_SCALE

            dt = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_f:
                        pass
                        # self.fullscreen_transition.toggle_screen_size()

                if self.editor_active:
                    self.editor.handle_press_events(event, mouse_pos)

            if self.editor_active:
                self.editor.run(mouse_pos, dt)

            # self.fullscreen_transition.update()
            # self.fullscreen_transition.draw()

            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
            pygame.display.update()

    def cursorize(self, category: str = 'default', rotation: float = 0.0) -> None:
        """
        Sets the cursor to the given type with optional rotation.

        :param category: The type of cursor.
        :param rotation: The rotation angle in degrees (default is 0.0).
        :return: None
        """

        cursor_surface = self.cursor_assets[category]

        if rotation != 0.0:
            cursor_surface = pygame.transform.rotate(cursor_surface, rotation)

        pygame.mouse.set_cursor(pygame.cursors.Cursor((0, 0), cursor_surface))


# prototype phase
class FullScreenTransition:
    def __init__(self, screen, target_screen_size: tuple | list):
        self.screen = screen
        self.original_screen_size = screen.get_size()
        self.target_screen_size = target_screen_size

        self.is_enlarged = False
        self.transitioning = False
        self.rects = []  # List to hold rectangles
        self.create_transition_rects()

    def create_transition_rects(self):
        self.rects.clear()
        rect_width = self.screen.get_width() // 10
        for i in range(11):
            rect = pygame.Rect(i * rect_width, 0, rect_width, self.screen.get_height())
            self.rects.append(rect)

    def toggle_screen_size(self):
        self.is_enlarged = not self.is_enlarged
        self.screen = pygame.display.set_mode(self.target_screen_size) if self.is_enlarged else pygame.display.set_mode(self.original_screen_size)

        self.create_transition_rects()
        self.transitioning = True

    def update(self):
        if self.transitioning:
            for rect in self.rects:
                rect.x -= 20
                if rect.right < 0:
                    self.rects.remove(rect)
            if not self.rects:
                self.transitioning = False

    def draw(self):
        for rect in self.rects:
            pygame.draw.rect(self.screen, (0, 0, 0), rect)


if __name__ == '__main__':
    Main().run()
