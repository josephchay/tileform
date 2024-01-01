import json
import pygame
import tkinter as tk
from tkinter import filedialog

from settings import *


class Tilemap:
    def __init__(self, game, tile_size):
        self.game = game
        self.tile_size = tile_size
        self.map = {}
        self.freeform_tiles = []

        self.size = [TILE_SIZE * 26, TILE_SIZE * 16]

    def extract(self, id_pairs, keep=False):
        """
        Extracts the tiles with the given id_pairs from the tilemap.

        :param id_pairs: the list of id_pairs
        :param keep: whether to keep the extracted tiles in the tilemap
        """

        matches = []

        for tile in self.freeform_tiles.copy():
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())

                if not keep:
                    self.freeform_tiles.remove(tile)

        for location in self.map:
            tile = self.map[location]
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())
                matches[-1]['pos'] = matches[-1]['pos'].copy()
                matches[-1]['pos'][0] *= self.tile_size
                matches[-1]['pos'][1] *= self.tile_size

                if not keep:
                    del self.map[location]

        return matches

    def tiles_around(self, pos):
        tiles = []
        tile_location = (int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))

        for offset in TILE_NEIGHBOR_OFFSETS:
            check_location = f"{tile_location[0] + offset[0]};{tile_location[1] + offset[1]}"
            if check_location in self.map:
                tiles.append(self.map[check_location])

        return tiles

    def check_solid(self, pos):
        """
        Checks if the tile at the given position is solid where physics are concerned.

        :param pos: the position to check
        :return: the tile at the given position if it is solid, otherwise None
        """

        tile_loc = f"{int(pos[0] // self.tile_size)};{int(pos[1] // self.tile_size)}"
        if tile_loc in self.map:
            if self.map[tile_loc]['type'] in PHYSICS_TILES:
                return self.map[tile_loc]

    def physics_rects_around(self, pos):
        rects = []

        for tile in self.tiles_around(pos):
            if tile['type'] in PHYSICS_TILES:
                rects.append(pygame.Rect(tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size, self.tile_size, self.tile_size))

        return rects

    def autotile(self) -> None:
        """
        Applies autotiling to the tiles in the tilemap.

        :return: None
        """

        for location in self.map:
            tile = self.map[location]
            neighbors = set()

            for shift in [(1, 0), (-1, 0), (0, -1), (0, 1)]:
                check_location = f"{tile['pos'][0] + shift[0]};{tile['pos'][1] + shift[1]}"
                if check_location in self.map:

                    # ensure that the neighbor tile is of the same type as the current tile
                    if self.map[check_location]['type'] == tile['type']:
                        neighbors.add(shift)

            neighbors = tuple(sorted(neighbors))

            if (tile['type'] in AUTO_TILES) and (neighbors in AUTOTILE_MAP):
                tile['variant'] = AUTOTILE_MAP[neighbors]

    def save(self, path: str = None) -> None:
        """
        Saves the tilemap to the selected JSON file.

        :param path: The path to save the JSON tilemap to. If None, a filedialog will be opened for the user to select the location.
        :return: None
        """

        if path is None:
            root = tk.Tk()
            root.withdraw()  # Hide the main window

            path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Save Tilemap"
            )

        if path:
            try:
                with open(path, 'w') as f:
                    json.dump({'tilemap': self.map, 'tile_size': self.tile_size, 'offgrid': self.freeform_tiles}, f)
            except FileNotFoundError:
                raise FileNotFoundError(f"Error saving tilemap: File not found - {path}")
            except PermissionError:
                raise PermissionError(f"Error saving tilemap: Permission denied - {path}")
            except Exception as e:
                raise Exception(f"Error saving tilemap to {path}: {e}")

    def load(self, path: str = None) -> None:
        """
        Loads the tilemap from the selected JSON file.

        :param path: The path to the JSON file to load. If None, a filedialog will be opened for the user to select the file.
        :return:
        """

        if path is None:
            root = tk.Tk()
            root.withdraw()  # Hide the main window

            path = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Load Tilemap"
            )

        if not path:
            print("Load operation canceled.")
            return

        try:
            with open(path, 'r') as f:
                map_data = json.load(f)
            print(f"Tilemap loaded successfully from {path}")
        except FileNotFoundError:
            raise FileNotFoundError(f"Error loading tilemap: File not found - {path}")
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Error loading tilemap from {path}: Invalid JSON format - {e}")
        except Exception as e:
            raise Exception(f"Error loading tilemap from {path}: {e}")

        self.map = map_data.get('tilemap', {})
        self.tile_size = map_data.get('tile_size', None)
        self.freeform_tiles = map_data.get('offgrid', [])

    def render(self, surf, offset=(0, 0)):
        for tile in self.freeform_tiles:
            surf.blit(self.game.tile_assets[tile['type']][tile['variant']], (tile['pos'][0] - offset[0], tile['pos'][1] - offset[1]))

        for x in range(offset[0] // self.tile_size, (offset[0] + surf.get_width()) // self.tile_size + 1):
            for y in range(offset[1] // self.tile_size, (offset[1] + surf.get_height()) // self.tile_size + 1):
                loc = f"{x};{y}"

                if loc in self.map:
                    tile = self.map[loc]
                    surf.blit(self.game.tile_assets[tile['type']][tile['variant']], (x * self.tile_size - offset[0], y * self.tile_size - offset[1]))

    def resize(self, size) -> None:
        """
        Resizes the map to the given size.

        :param size: The new size of the map.
        :return: None
        """

        self.size = size
