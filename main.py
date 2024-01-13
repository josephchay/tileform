import sys
from dotenv import load_dotenv

from pygame.math import Vector2 as Vector

from settings import *
from core.filesystem import *
from utils.helpers import *
from editor import Editor


class Main:
    def __init__(self):
        """ The main constructor """

        load_dotenv()

        pygame.init()
        pygame.display.set_caption(os.getenv('APP_NAME'))

        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.display = pygame.Surface((WINDOW_WIDTH / RENDER_SCALE, WINDOW_HEIGHT / RENDER_SCALE))
        self.clock = pygame.time.Clock()

        self.editor_active = True

        self.providers = {
            'files': Filesystem(ASSETS_PATH),
        }

        self.editor = Editor(self)

        # cursors
        self.cursor_assets = {
            'default': self.providers['files'].readimg('cursors/default.png', colorkey=COLORKEY_WHITE),
            'handle': self.providers['files'].readimg('cursors/handle.png', colorkey=COLORKEY_WHITE),
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

                if self.editor_active:
                    self.editor.handle_press_events(event, mouse_pos)

            if self.editor_active:
                self.editor.run(mouse_pos, dt)

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


if __name__ == '__main__':
    Main().run()
