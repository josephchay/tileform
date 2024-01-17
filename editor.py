import pygame.draw
from pygame.locals import *
from pygame.math import Vector2 as Vector

from settings import *
from tilemap import Tilemap
from utils.helpers import *


class Editor:
    def __init__(self, main):
        self.main = main
        self.providers = self.main.providers

        self.display = self.main.display
        self.display_grid = pygame.Surface((self.display.get_width(), self.display.get_height()))
        self.display_grid.set_alpha(30)

        self.screen = self.main.screen
        self.clock = self.main.clock

        self.tile_assets = {
            'grass': self.providers['files'].readimgdir('tiles/grass'),
            'stone': self.providers['files'].readimgdir('tiles/stone'),
            'decor': self.providers['files'].readimgdir('tiles/decor'),
            'large_decor': self.providers['files'].readimgdir('tiles/large_decor'),
            'spawners': self.providers['files'].readimgdir('tiles/spawners'),
        }

        self.movements = {
            'left': False,
            'right': False,
            'up': False,
            'down': False
        }

        self.tilemap = Tilemap(self, tile_size=TILE_SIZE)

        # scroll
        self.scroll = Vector()
        self.scroll_offset = Vector()
        self.origin = Vector()

        # scroll reset
        self.scroll_reset = False
        self.scroll_target = self.scroll.copy()
        self.scroll_transition_duration = None
        self.scroll_transition_elapsed = None

        # assets tiles
        self.tile_list = list(self.tile_assets)
        self.tile_group_active = 0
        self.tile_variant_active = 0

        # events
        self.clicking = False
        self.right_clicking = False
        self.draggable = False
        self.dragging = False
        self.back = False
        self.ctrl = False
        self.shift = False
        self.panning = False
        self.panning_start_pos = None

        self.ongrid = True

        # menu
        self.menu = Menu(self, (0, 0), (EDITOR_MENU_WIDTH, self.display.get_height()))

    def run(self, mouse_pos, dt):
        self.display.fill(EDITOR_BACKGROUND_COLOR)

        if self.scroll_reset:
            self.update_scroll_reset(dt)

        key_scroll = Vector(
            (self.movements['right'] - self.movements['left']) * KEY_SCROLL_SPEED,
            (self.movements['down'] - self.movements['up']) * KEY_SCROLL_SPEED
        )

        self.scroll += key_scroll * dt

        if WINDOW_SMOOTH_SCROLL:
            self.scroll_offset = int(self.scroll.x * TILE_SIZE), int(self.scroll.y * TILE_SIZE)
        else:
            self.scroll_offset = (int(self.scroll.x) * TILE_SIZE, int(self.scroll.y) * TILE_SIZE)

        self.tilemap.render(self.display, offset=self.scroll_offset)

        self._update_grid(mouse_pos)

        self.menu.run(mouse_pos, dt)

        if self.menu.collide(mouse_pos):
            self.menu.hovered()
        else:
            self.menu.unhovered()

            if not self.draggable:
                current_tile_img = self.tile_assets[self.tile_list[self.tile_group_active]][self.tile_variant_active].copy()
                current_tile_img.set_alpha(100)

                tile_pos = (int((mouse_pos[0] + self.scroll_offset[0]) // TILE_SIZE), int((mouse_pos[1] + self.scroll_offset[1]) // TILE_SIZE))

                if self.ongrid:
                    # Blit the selected image to the tile the mouse is hovering over
                    self.display.blit(current_tile_img, (tile_pos[0] * TILE_SIZE - self.scroll_offset[0], tile_pos[1] * TILE_SIZE - self.scroll_offset[1]))
                else:
                    self.display.blit(current_tile_img, mouse_pos)

                self._update_tiling(mouse_pos, tile_pos)

    def _update_tiling(self, mouse_pos, tile_pos) -> None:
        """
        Update the tile placement and removal actions on the tilemap.

        :param mouse_pos: The mouse position.
        :param tile_pos: The tile position.
        :return: None
        """

        if not self.panning:
            if self.clicking and self.ongrid:
                tile_loc = f"{tile_pos[0]};{tile_pos[1]}"
                self.tilemap.map[tile_loc] = {
                    'type': self.tile_list[self.tile_group_active],
                    'variant': self.tile_variant_active,
                    'pos': tile_pos
                }

                if EDITOR_AUTOMATIC_AUTO_TILE:
                    self.tilemap.autotile()

            if self.right_clicking:
                tile_loc = f"{tile_pos[0]};{tile_pos[1]}"

                # Remove the tile if it exists
                if tile_loc in self.tilemap.map:
                    del self.tilemap.map[tile_loc]

                    if EDITOR_AUTOMATIC_AUTO_TILE:
                        self.tilemap.autotile()

                for tile in self.tilemap.freeform_tiles.copy():
                    tile_image = self.tile_assets[tile['type']][tile['variant']]
                    tile_rect = pygame.Rect(tile['pos'][0] - self.scroll_offset[0], tile['pos'][1] - self.scroll_offset[1], tile_image.get_width(), tile_image.get_height())

                    if tile_rect.collidepoint(mouse_pos):
                        self.tilemap.freeform_tiles.remove(tile)

    def _update_grid(self, mouse_pos):
        cols = self.display.get_width() // TILE_SIZE
        rows = self.display.get_height() // TILE_SIZE

        display_width, display_height = self.display.get_size()

        self.origin = Vector(-self.scroll_offset[0], -self.scroll_offset[1])

        self.display_grid.fill((0, 0, 0))

        for col in range(cols + 1):
            x = (-self.scroll_offset[0] % TILE_SIZE) + col * TILE_SIZE

            if x == 0 - self.scroll_offset[0]:
                self.origin.x = x

        for row in range(rows + 1):
            y = (-self.scroll_offset[1] % TILE_SIZE) + row * TILE_SIZE

            if y == 0 - self.scroll_offset[1]:
                self.origin.y = y

        line_spacing = 2
        self._update_origin_grid(self.origin, Vector(self.display.get_size()), line_spacing)
        self._update_origin_offset_grid(mouse_pos, self.origin + Vector(self.tilemap.size[0], self.tilemap.size[1]), self.origin - Vector(line_spacing, line_spacing), line_spacing)

        for col in range(cols + 1):
            x = (-self.scroll_offset[0] % TILE_SIZE) + col * TILE_SIZE
            pygame.draw.line(self.display_grid, EDITOR_GRID_COLOR, (x, 0), (x, display_height))

        for row in range(rows + 1):
            y = (-self.scroll_offset[1] % TILE_SIZE) + row * TILE_SIZE
            pygame.draw.line(self.display_grid, EDITOR_GRID_COLOR, (0, y), (display_width, y))

        self.display.blit(self.display_grid, (0, 0))

    def _update_origin_grid(self, pos, max_pos, spacing=2) -> None:
        """
        Update the grid for the origin point

        :param pos: The position of the origin point
        :param max_pos: The maximum position of the lines to be drawn
        :param spacing: The spacing between the lines
        :return: None
        """

        for i in range(2):
            if i == 1:
                spacing = -spacing

            pygame.draw.line(self.display, EDITOR_ORIGIN_POINT_COLOR, (pos.x + spacing, pos.y + spacing), (max_pos.x, pos.y + spacing))
            pygame.draw.line(self.display, EDITOR_ORIGIN_POINT_COLOR, (0, pos.y + spacing), (pos.x + spacing, pos.y + spacing))
            pygame.draw.line(self.display, EDITOR_ORIGIN_POINT_COLOR, (pos.x + spacing, pos.y + spacing), (pos.x + spacing, max_pos.y))
            pygame.draw.line(self.display, EDITOR_ORIGIN_POINT_COLOR, (pos.x + spacing, 0), (pos.x + spacing, pos.y + spacing))

    def _update_origin_offset_grid(self, mouse_pos, pos, max_pos, spacing=2) -> None:
        """
        Update the draggable grid offset from the origin point and handle its resizing
        Determines the fixed size of the tilemap

        :param mouse_pos: The mouse position
        :param pos: The dragged position from the origin point
        :param max_pos: The maximum position of the lines to be drawn
        :param spacing: The spacing between the lines
        :return: None
        """

        for i in range(2):
            if i == 1:
                spacing = -spacing

            pygame.draw.line(self.display, EDITOR_ORIGIN_POINT_OFFSET_COLOR, (max_pos.x, pos.y + spacing), (pos.x + spacing, pos.y + spacing))
            pygame.draw.line(self.display, EDITOR_ORIGIN_POINT_OFFSET_COLOR, (pos.x + spacing, max_pos.y), (pos.x + spacing, pos.y + spacing))

        # drag indicator
        drag_indicator_len = 4

        for j in range(2):
            drag_indicator_offset = (j + 1.8) * spacing

            pygame.draw.line(self.display, EDITOR_ORIGIN_POINT_OFFSET_DRAG_INDICATOR_COLOR,
                             (pos.x - drag_indicator_offset - drag_indicator_len, pos.y - spacing - drag_indicator_offset),
                             (pos.x - spacing - drag_indicator_offset, pos.y - spacing - drag_indicator_offset))
            pygame.draw.line(self.display, EDITOR_ORIGIN_POINT_OFFSET_DRAG_INDICATOR_COLOR,
                             (pos.x - spacing - drag_indicator_offset, pos.y - drag_indicator_offset - drag_indicator_len),
                             (pos.x - spacing - drag_indicator_offset, pos.y - spacing - drag_indicator_offset))

        spacing = -spacing

        # boundaries for the horizontal draggable line
        horizontal_line_y1 = self.origin.y + self.tilemap.size[1] - spacing
        horizontal_line_y2 = self.origin.y + self.tilemap.size[1] + spacing

        # boundaries for the vertical draggable line
        vertical_line_x1 = self.origin.x + self.tilemap.size[0] - spacing
        vertical_line_x2 = self.origin.x + self.tilemap.size[0] + spacing

        # common x boundary for the horizontal line
        common_x1 = self.origin.x
        common_x2 = self.origin.x + self.tilemap.size[0]

        # common y boundary for the vertical line
        common_y1 = self.origin.y
        common_y2 = self.origin.y + self.tilemap.size[1]

        corner_x1 = vertical_line_x1 - spacing
        corner_x2 = vertical_line_x2 + spacing - drag_indicator_offset + drag_indicator_len
        corner_y1 = horizontal_line_y1 - spacing
        corner_y2 = horizontal_line_y2 + spacing - drag_indicator_offset + drag_indicator_len

        on_horizontal_line = common_x1 <= mouse_pos[0] <= common_x2 and horizontal_line_y1 <= mouse_pos[1] <= horizontal_line_y2
        on_vertical_line = vertical_line_x1 <= mouse_pos[0] <= vertical_line_x2 and common_y1 <= mouse_pos[1] <= common_y2
        on_corner = corner_x1 <= mouse_pos[0] <= corner_x2 and corner_y1 <= mouse_pos[1] <= corner_y2

        # the additional invisible length given for dragging area detection for better smooth dragging when at higher speeds
        drag_allowance_len = 140

        on_allowed_horizontal_line = common_x1 - drag_allowance_len <= mouse_pos[0] <= common_x2 + drag_allowance_len and horizontal_line_y1 - drag_allowance_len <= mouse_pos[1] <= horizontal_line_y2 + drag_allowance_len
        on_allowed_vertical_line = vertical_line_x1 - drag_allowance_len <= mouse_pos[0] <= vertical_line_x2 + drag_allowance_len and common_y1 - drag_allowance_len <= mouse_pos[1] <= common_y2 + drag_allowance_len
        on_allowed_corner = corner_x1 - drag_allowance_len <= mouse_pos[0] <= corner_x2 + drag_allowance_len and corner_y1 - drag_allowance_len <= mouse_pos[1] <= corner_y2 + drag_allowance_len

        # if on_allowed_vertical_line:
        #     if on_vertical_line:
        #         self.draggable = True
        #         self.main.cursorize('handle', 90)
        #
        #     if self.clicking:
        #         self.tilemap.size[1] = (Vector(mouse_pos) - self.origin)[1] // TILE_SIZE * TILE_SIZE
        #     else:
        #         if not on_vertical_line and self.draggable:
        #             self.draggable = False
        #             self.main.cursorize()
        # elif on_allowed_horizontal_line:
        #     if on_horizontal_line:
        #         self.draggable = True
        #         self.main.cursorize('handle')
        #
        #     if self.clicking:
        #         self.tilemap.size[0] = (Vector(mouse_pos) - self.origin)[0] // TILE_SIZE * TILE_SIZE
        #     else:
        #         if not on_horizontal_line and self.draggable:
        #             self.draggable = False
        #             self.main.cursorize()
        if on_allowed_corner:
            if on_corner:
                self.draggable = True
                self.main.cursorize('handle', 45)

            if self.clicking and self.draggable:
                self.tilemap.size = (Vector(mouse_pos) - self.origin) // TILE_SIZE * TILE_SIZE
            else:
                if not on_corner and self.draggable:
                    self.draggable = False
                    self.main.cursorize()
        else:
            self.draggable = False
            self.main.cursorize()

    def handle_events(self, event, mouse_pos) -> None:
        """
        Handle events for mouse scrolling, presses and key presses.

        :param event: The event to handle
        :param mouse_pos: The mouse position
        :return: None
        """

        if event.type == MOUSEBUTTONDOWN:
            if event.button == 1:
                self.clicking = True

                if not self.panning:
                    if not self.ongrid:
                        self.tilemap.freeform_tiles.append({
                            'type': self.tile_list[self.tile_group_active],
                            'variant': self.tile_variant_active,
                            'pos': Vector(mouse_pos) + self.scroll_offset
                        })

                if self.menu.pos[0] <= mouse_pos[0] <= (self.menu.pos[0] + self.menu.size[0]):
                    self.handle_menu_assets_events(mouse_pos)

            elif event.button == 2:
                self.panning = True
                self.panning_start_pos = mouse_pos
            elif event.button == 3:
                self.right_clicking = True
            elif event.button == 6:
                self.back = not self.back

            if self.back:
                if self.clicking:
                    self.panning = True
                    self.panning_start_pos = mouse_pos

                if event.button == 4:
                    if mouse_pos[0] > self.menu.size[0]:
                        self.scroll[0] -= 1 * SCROLL_SPEED
                if event.button == 5:
                    if mouse_pos[0] > self.menu.size[0]:
                        self.scroll[0] += 1 * SCROLL_SPEED
            elif self.ctrl:
                if self.shift:
                    if event.button == 4:
                        self.scroll_tile_variant(-1)
                    if event.button == 5:
                        self.scroll_tile_variant(1)
                    self.swap_tile_variant(self.tile_list[self.tile_group_active], self.tile_variant_active)
                else:
                    if event.button == 4:
                        self.scroll_tile_group(-1)
                    if event.button == 5:
                        self.scroll_tile_group(1)
                    self.swap_tile_group(self.tile_list[self.tile_group_active])
            else:
                if event.button == 4:
                    if mouse_pos[0] > self.menu.size[0]:
                        self.scroll[1] -= 1 * SCROLL_SPEED
                    else:
                        if mouse_pos[1] < self.menu.top.size[1]:
                            if self.menu.top.scroll[1] != 0:
                                self.menu.top.scroll[1] -= min(1 * SCROLL_SPEED, self.menu.top.scroll[1])
                        else:
                            if self.menu.bottom.scroll[1] != 0:
                                self.menu.bottom.scroll[1] -= min(1 * SCROLL_SPEED, self.menu.bottom.scroll[1])
                if event.button == 5:
                    if self.menu.pos[0] <= mouse_pos[0] <= (self.menu.pos[0] + self.menu.size[0]):
                        if self.menu.top.pos[1] <= mouse_pos[1] <= (self.menu.top.pos[1] + self.menu.top.size[1]):
                            if self.menu.top.contentport[1] - self.menu.top.scroll_offset[1] >= self.menu.top.size[1]:
                                self.menu.top.scroll[1] += min(1 * SCROLL_SPEED, self.menu.top.contentport[1] - self.menu.top.scroll_offset[1] - self.menu.top.size[1])
                        else:
                            if self.menu.bottom.contentport[1] - self.menu.bottom.scroll_offset[1] >= self.menu.bottom.size[1]:
                                self.menu.bottom.scroll[1] += min(1 * SCROLL_SPEED, self.menu.bottom.contentport[1] - self.menu.bottom.scroll_offset[1] - self.menu.bottom.size[1])
                    else:
                        self.scroll[1] += 1 * SCROLL_SPEED

        if event.type == MOUSEMOTION:
            if self.panning:
                if mouse_pos[0] > self.menu.size[0]:
                    pan_offset = Vector(mouse_pos) - self.panning_start_pos

                    self.scroll -= pan_offset / TILE_SIZE * SCROLL_SPEED

                    self.panning_start_pos = mouse_pos

        if event.type == MOUSEBUTTONUP:
            if event.button == 1:
                self.clicking = False

                if self.panning:
                    self.panning_start_pos = None
                    self.panning = False
            elif event.button == 2:
                self.panning_start_pos = None
                self.panning = False
            elif event.button == 3:
                self.right_clicking = False

        if event.type == KEYDOWN:
            if event.key == K_LSHIFT or event.key == K_RSHIFT:
                self.shift = True
            if event.key == K_LCTRL or event.key == K_RCTRL:
                self.ctrl = True

            if event.key == K_r:
                self.start_reset_scroll((0, 0), 1.0)

            if self.ctrl:
                if event.key == K_s:
                    self.tilemap.save()
                elif event.key == K_o:
                    self.tilemap.load()

            if event.key == K_a:
                self.movements['left'] = True
            if event.key == K_d:
                self.movements['right'] = True
            if event.key == K_w:
                self.movements['up'] = True
            if event.key == K_s:
                self.movements['down'] = True

            if event.key == K_g:
                self.ongrid = not self.ongrid
            if event.key == K_t:
                if not EDITOR_AUTOMATIC_AUTO_TILE:
                    self.tilemap.autotile()

        if event.type == KEYUP:
            if event.key == K_LSHIFT:
                self.shift = False
            if event.key == K_LCTRL:
                self.ctrl = False

            if event.key == K_a:
                self.movements['left'] = False
            if event.key == K_d:
                self.movements['right'] = False
            if event.key == K_w:
                self.movements['up'] = False
            if event.key == K_s:
                self.movements['down'] = False

    def handle_menu_assets_events(self, mouse_pos) -> None:
        """
        Handle events for the menu assets.

        :param mouse_pos: The position of the mouse
        :return: None
        """

        # menu top
        if self.menu.top.pos[1] <= mouse_pos[1] <= (self.menu.top.pos[1] + self.menu.top.size[1]):
            for tile_group_name, tile_group in self.menu.top.tile_groups.items():
                if tile_group.collide(mouse_pos, self.menu.top.scroll_offset):
                    self.swap_tile_group(tile_group_name)

        # menu divider
        elif self.menu.divider.pos[1] <= mouse_pos[1] <= (self.menu.divider.pos[1] + self.menu.divider.size[1]):
            pass

        # menu bottom
        else:
            for tile_group_name, tile_group in self.menu.bottom.tile_groups.items():
                if tile_group.selected:
                    for i, tile_variant in enumerate(tile_group.variants):
                        if tile_variant.collide(mouse_pos, self.menu.bottom.scroll_offset):
                            self.swap_tile_variant(tile_group_name, i)

    def scroll_tile_group(self, direction: int) -> None:
        """
        Scroll the tile group in the given direction.

        :param direction: The direction to scroll the tile group in.
        :return: None
        """

        self.tile_group_active = (self.tile_group_active + direction) % len(self.tile_list)

    def swap_tile_group(self, group: str) -> None:
        """
        Swap the tile group in the given direction.

        :param group: The tile group to swap to
        :return: None
        """

        if self.tile_list[self.tile_group_active] != group:
            self.tile_group_active = self.tile_list.index(group)

        for other_tile_group_name, other_tile_group in self.menu.top.tile_groups.items():
            if other_tile_group_name != group:
                other_tile_group.selected = False
                other_tile_group.overlay = False
                self.menu.bottom.tile_groups[other_tile_group_name].selected = False

        self.menu.top.tile_groups[group].selected = True
        self.menu.top.tile_groups[group].overlay = True
        self.menu.bottom.tile_groups[group].selected = True

        self.tile_variant_active = 0

    def scroll_tile_variant(self, direction: int) -> None:
        """
        Scroll the tile variant in the given direction.

        :param direction: The direction to scroll the tile variant in.
        :return: None
        """

        self.tile_variant_active = (self.tile_variant_active + direction) % len(self.tile_assets[self.tile_list[self.tile_group_active]])

    def swap_tile_variant(self, group: str, variant: int) -> None:
        """
        Swap the tile variant in the given direction.

        :param group: The tile group the variant belongs to
        :param variant: The variant to swap to
        :return: None
        """

        if self.tile_list[self.tile_group_active] != group:
            self.tile_group_active = self.tile_list.index(group)

        if self.tile_variant_active != variant:
            self.tile_variant_active = variant

        for other_tile_variant in self.menu.bottom.tile_groups[group].variants:
            other_tile_variant.selected = False
            other_tile_variant.overlay = False
            self.menu.top.tile_groups[group].variants[variant].selected = False

        self.menu.bottom.tile_groups[group].variants[variant].selected = True
        self.menu.bottom.tile_groups[group].variants[variant].overlay = True
        self.menu.top.tile_groups[group].variants[variant].selected = True

    def start_reset_scroll(self, target_position, duration):
        """
        Initialize the scroll reset process with the target position and the duration.

        :param target_position: The target scroll position, a tuple (x, y).
        :param duration: The duration over which to reset the scroll.
        """

        self.scroll_target = Vector(target_position)
        self.scroll_transition_duration = duration
        self.scroll_transition_elapsed = 0
        self.scroll_reset = True

    def update_scroll_reset(self, dt):
        """
        Update the scroll position smoothly towards the target position.

        :param dt: The time elapsed since the last frame, in seconds.
        """

        if self.scroll_reset:
            self.scroll_transition_elapsed += dt
            t = min(self.scroll_transition_elapsed / self.scroll_transition_duration, 1)

            # Calculate the new scroll position using linear interpolation
            self.scroll = Vector.lerp(self.scroll, self.scroll_target, t)

            if t >= 1:
                self.scroll_reset = False


class Menu:
    def __init__(self, editor, pos, size):
        self.editor = editor
        self.display = self.editor.display
        self.pos = pos
        self.size = size

        # sections
        self.top = MenuTop(self, self.pos, [self.size[0], self.size[1] // 3])
        self.bottom = MenuBottom(self, [self.pos[0], self.pos[1] + self.top.size[1]], [self.size[0], self.size[1] - self.top.size[1]])
        self.divider = MenuDivider(self, (self.size[0], 1))

        # animation
        self.target_opacity = EDITOR_MENU_OPACITY

    def run(self, mouse_pos, dt):
        self.top.render(mouse_pos, dt)
        self.bottom.render(mouse_pos, dt)
        self.divider.render()

        self._update_opacity()

    def _update_opacity(self) -> None:
        """
        Updates the menu opacity.

        :return: None
        """

        current_opacity = self.top.display.get_alpha()
        if current_opacity < self.target_opacity:
            current_opacity += EDITOR_MENU_OPACITY_CHANGE_SPEED
        elif current_opacity > self.target_opacity:
            current_opacity -= EDITOR_MENU_OPACITY_CHANGE_SPEED

        self.top.display.set_alpha(current_opacity)
        self.bottom.display.set_alpha(current_opacity)

    def hovered(self) -> None:
        if self.target_opacity != EDITOR_MENU_HOVER_OPACITY:
            self.target_opacity = EDITOR_MENU_HOVER_OPACITY

    def unhovered(self) -> None:
        if self.target_opacity != EDITOR_MENU_OPACITY:
            self.target_opacity = EDITOR_MENU_OPACITY

    def collide(self, point: tuple | list) -> bool:
        """
        Check whether the given position collides with the menu.

        :param point: The position to check.
        :return: True if the mouse is in the menu, False otherwise.
        """

        return self.pos[0] <= point[0] < self.size[0] and self.pos[1] <= point[1] < self.size[1]


class MenuSection:
    def __init__(self, menu, pos, size, color):
        self.menu = menu
        self.pos = pos
        self.size = size

        self.display = pygame.Surface(self.size, SRCALPHA)
        self.color = color

        # scroll
        self.scroll = Vector()
        self.scroll_offset = Vector()

        self.tile_group_margin = TileGroup.margin

    def render(self, mouse_pos, dt) -> None:
        scroll_velocity = Vector()

        self.scroll += scroll_velocity * dt

        if WINDOW_SMOOTH_SCROLL:
            self.scroll_offset = [int(self.scroll.x * TILE_SIZE), int(self.scroll.y * TILE_SIZE)]
        else:
            self.scroll_offset = [int(self.scroll.x) * TILE_SIZE, int(self.scroll.y) * TILE_SIZE]

        self.display.fill(self.color)

        if EDITOR_MENU_TILE_TRANSPARENT:
            self.update(mouse_pos)
            self.menu.display.blit(self.display, self.pos)
        else:
            self.menu.display.blit(self.display, self.pos)
            self.update(mouse_pos)

    def update(self, mouse_pos) -> None:
        """
        Updates the respective menu section

        :param mouse_pos: The position of the mouse.
        :return: None
        """

        self._update_assets(mouse_pos)

    def _update_assets(self, mouse_pos) -> None:
        """
        [ABSTRACT METHOD]
        Updates the assets on the respective menu section

        :param mouse_pos: The mouse position.
        :return: None
        """

        pass


class MenuTop(MenuSection):
    def __init__(self, menu, pos, size):
        super().__init__(menu, pos, size, EDITOR_MENU_TOP_COLOR)

        self.contentport = pos

        # assets
        self.assets = self.menu.editor.tile_assets
        self.tile_groups = {}
        self.tile_groups_list = []

        self._load_assets()

    def _load_assets(self) -> None:
        """
        Loads the assets into the top section of the menu

        :return: None
        """

        self.contentport = [self.contentport[0] + self.tile_group_margin, self.contentport[1] + self.tile_group_margin]

        for i, tile_group_name in enumerate(self.assets):
            tile_variants = []

            for j, tile_var_img in enumerate(self.assets[tile_group_name].copy()):
                tile_height = tile_var_img.get_height()
                tile_variants.append(TileVariant(self, tile_var_img))

            current_pos = self.contentport.copy()

            self.tile_groups[tile_group_name] = TileGroup(self, tile_variants, current_pos)

            if i == 0:
                self.tile_groups[tile_group_name].default = True
                self.tile_groups[tile_group_name].selected = True
                self.tile_groups[tile_group_name].overlay = True

            # Move to the next line for the next asset
            self.contentport[1] += tile_height + self.tile_group_margin

        self.tile_groups_list = list(self.tile_groups)

    def _update_assets(self, mouse_pos) -> None:
        """
        Updates the assets on the top menu section

        :param mouse_pos: The mouse position
        :return: None
        """

        for tile_group_name, tile_group in self.tile_groups.items():
            if self.size[1] > tile_group.pos[1] - self.scroll_offset[1] > 0:
                if tile_group.collide(mouse_pos, self.scroll_offset):
                    tile_group.render(len(tile_group.variants), (self.scroll_offset[0], self.scroll_offset[1] + EDITOR_MENU_TILE_HOVERED_RAISE))
                else:
                    tile_group.render(len(tile_group.variants), self.scroll_offset)


class MenuBottom(MenuSection):
    def __init__(self, menu, pos, size):
        super().__init__(menu, pos, size, EDITOR_MENU_BOTTOM_COLOR)

        # assets
        self.assets = self.menu.editor.tile_assets

        self.contentports = {}
        for tile_group_name in self.assets:
            self.contentports[tile_group_name] = pos

        self.tile_groups = {}
        self.tile_groups_list = []

        self._load_assets()

    def _load_assets(self) -> None:
        """
        Loads the assets into the top section of the menu

        :return: None
        """

        for i, tile_group_name in enumerate(self.assets):
            self.contentport = self.contentports[tile_group_name]
            self.contentport = [self.contentport[0] + self.tile_group_margin, self.contentport[1] + self.tile_group_margin]

            tile_vars = []

            for j, tile_var_img in enumerate(self.assets[tile_group_name].copy()):
                tile_height = tile_var_img.get_height()
                tile_variant = TileVariant(self, tile_var_img)

                if j == 0:
                    tile_variant.selected = True
                    tile_variant.overlay = True

                tile_vars.append(tile_variant)

            current_pos = self.contentport.copy()

            self.tile_groups[tile_group_name] = TileGroup(self, tile_vars, current_pos)

            if i == 0:
                self.tile_groups[tile_group_name].default = True
                self.tile_groups[tile_group_name].selected = True

            self.contentport[1] += (tile_height + self.tile_group_margin) * (len(self.assets[tile_group_name]) / EDITOR_MENU_MAX_TILE_VARIANT_COUNT_PER_ROW)
            self.contentports[tile_group_name] = self.contentport

        self.tile_groups_list = list(self.tile_groups)

    def _update_assets(self, mouse_pos) -> None:
        """
        Updates the assets on the bottom menu section

        :param mouse_pos: The mouse position
        :return: None
        """

        for tile_group_name, tile_group in self.tile_groups.items():
            if self.size[1] > tile_group.pos[1] - self.scroll_offset[1] > 0:
                if tile_group.selected:
                    tile_group.render(EDITOR_MENU_MAX_TILE_VARIANT_COUNT_PER_ROW, self.scroll_offset)


class MenuDivider:
    def __init__(self, menu, size):
        self.menu = menu
        self.size = size

        self.pos = (0, self.menu.top.pos[1] + self.menu.top.size[1])

        self.display = pygame.Surface(self.size, SRCALPHA)
        pygame.draw.line(self.display, EDITOR_MENU_DIVIDER_COLOR, (0, 0), (self.size[0], 0))

    def render(self):
        self.menu.display.blit(self.display, self.pos)


class TileGroup:
    margin = EDITOR_MENU_TILE_GROUP_MARGIN

    def __init__(self, menu_section, variants: list, pos):
        """
        A group of its tiles variants in the menu.

        :param menu_section: The respective menu section
        :param variants: The tile variants
        :param pos: The position of the tile group
        """

        self.menu_section = menu_section
        self.display = self.menu_section.display if EDITOR_MENU_TILE_TRANSPARENT else self.menu_section.menu.display

        self.pos = pos

        # variants
        self.variants = variants

        self.default = False
        self.selected = False
        self.overlay = False

        # overlay
        self.display_overlay_inflation = 6

        max_height = 0
        for variant in self.variants:
            max_height = max(max_height, variant.img.get_height())

        self.size = self.menu_section.size[0] - (EDITOR_MENU_TILE_GROUP_MARGIN * 2), max_height

        self.display_overlay_original_size = self.size[0] + self.display_overlay_inflation, self.size[1] + self.display_overlay_inflation
        self.display_overlay = pygame.Surface(self.display_overlay_original_size, SRCALPHA)
        self.display_overlay.set_alpha(EDITOR_MENU_TILE_OVERLAY_OPACITY)

    def cal_row_spacing(self, max_count_per_row) -> int:
        """
        Calculates the spacing between each variant to evenly distribute them across the row.

        :param max_count_per_row: The maximum number of variants to display per row
        :return: The spacing between each variant
        """

        if max_count_per_row <= 1:
            return 0

        total_variants = len(self.variants)

        if total_variants >= max_count_per_row:
            # Calculate total width for the variants in the row
            total_images_width_per_row = sum(variant.img.get_width() for variant in self.variants[:max_count_per_row])

            available_space = self.menu_section.size[0] - (TileGroup.margin * 2) - total_images_width_per_row
            total_gaps = max(max_count_per_row - 1, 0)  # Gaps between variants in a row

            return available_space / total_gaps if total_gaps > 0 else 0
        else:
            # If total_variants is less than max_count_per_row, evenly distribute the space without gaps
            available_space = self.menu_section.size[0] - (TileGroup.margin * 2) - sum(variant.img.get_width() for variant in self.variants)

            return available_space / (total_variants - 1) if total_variants > 1 else 0

    def render(self, max_count_per_row, offset=(0, 0)) -> None:
        """
        Renders the tile groups on one per row with the variants separated by the given spacing

        :param max_count_per_row: The maximum number of items to display per row
        :param offset: The offset for the position
        :return: None
        """

        spacing = self.cal_row_spacing(max_count_per_row)
        offset_pos = [self.pos[0] - offset[0], self.pos[1] - offset[1]]

        for i, variant in enumerate(self.variants):
            if i > 0 and i % max_count_per_row == 0:
                offset_pos[0] = self.pos[0] - offset[0]
                offset_pos[1] += self.variants[i - 1].img.get_height() + TileGroup.margin

            if offset_pos[1] <= self.menu_section.size[1]:
                variant.pos = offset_pos.copy()
                variant.render()

            offset_pos[0] += self.variants[i].img.get_width() + spacing

        if self.selected and self.overlay:
            # render the overlay with only the size of the visible part of the tile group
            visible_overlay_height = min(self.display_overlay_original_size[1], self.menu_section.size[1] - offset_pos[1] - EDITOR_MENU_TILE_HOVERED_RAISE + TileGroup.margin / 2)
            self.display_overlay = pygame.transform.scale(self.display_overlay,(self.display_overlay_original_size[0], visible_overlay_height))
            self.display_overlay.fill(EDITOR_MENU_TILE_GROUP_SELECTED_COLOR)
            self.display.blit(self.display_overlay, ((self.pos[0] - self.display_overlay_inflation / 2) - offset[0], (self.pos[1] - self.display_overlay_inflation / 2) - offset[1]))

    def collide(self, point: tuple | list, offset=(0, 0)) -> bool:
        """
        Check whether the given position collides with the menu asset group.

        :param point: The position to check.
        :param offset: The offset of the menu top section
        :return: True if the mouse is in the menu asset group, False otherwise.
        """

        return self.pos[0] - offset[0] <= point[0] < self.pos[0] + self.size[0] - offset[0] and self.pos[1] - offset[1] <= point[1] < self.pos[1] + self.size[1] - offset[1]


class TileVariant:
    def __init__(self, menu_section, img: pygame.Surface, pos=None):
        """
        A variant of a tile group

        :param menu_section: The respective menu section
        :param img: The image of the variant
        """

        self.pos = pos

        self.menu_section = menu_section
        self.img = img
        self.margin = EDITOR_MENU_TILE_GROUP_MARGIN

        self.display = self.menu_section.display if EDITOR_MENU_TILE_TRANSPARENT else self.menu_section.menu.display

        self.default = False
        self.selected = False
        self.overlay = False

        # overlay
        self.display_overlay_inflation = 6
        self.size = self.img.get_width(), self.img.get_height()

        self.display_overlay_original_size = self.size[0] + self.display_overlay_inflation, self.size[1] + self.display_overlay_inflation
        self.display_overlay = pygame.Surface(self.display_overlay_original_size, SRCALPHA)
        self.display_overlay.set_alpha(EDITOR_MENU_TILE_OVERLAY_OPACITY)

    def render(self, offset=(0, 0)):
        # render the visible part of the image
        visible_height = min(self.img.get_height(), self.menu_section.pos[1] + self.menu_section.size[1] - self.pos[1] - offset[1])
        visible_subsurface = self.img.subsurface(pygame.Rect(0, 0, self.img.get_width(), visible_height))
        self.display.blit(visible_subsurface, (self.pos[0] - offset[0], self.pos[1] - offset[1]))

        if self.selected and self.overlay:
            # render the overlay with only the size of the visible part of the tile group
            visible_overlay_height = min(self.display_overlay_original_size[1], self.menu_section.pos[1] + self.menu_section.size[1] - self.pos[1] - EDITOR_MENU_TILE_HOVERED_RAISE + TileGroup.margin / 2)
            self.display_overlay = pygame.transform.scale(self.display_overlay,(self.display_overlay_original_size[0], visible_overlay_height))
            self.display_overlay.fill(EDITOR_MENU_TILE_GROUP_SELECTED_COLOR)
            self.display.blit(self.display_overlay, ((self.pos[0] - self.display_overlay_inflation / 2) - offset[0], (self.pos[1] - self.display_overlay_inflation / 2) - offset[1]))

    def collide(self, point: tuple | list, offset=(0, 0)) -> bool:
        """
        Check whether the given position collides with the menu asset group.

        :param point: The position to check.
        :param offset: The offset of the menu top section
        :return: True if the mouse is in the menu asset group, False otherwise.
        """

        return self.pos[0] - offset[0] <= point[0] < self.pos[0] + self.size[0] - offset[0] and self.pos[1] - offset[1] <= point[1] < self.pos[1] + self.size[1] - offset[1]
