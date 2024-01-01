import os
import pygame

from settings import *
from utils.helpers import isf_img


class GFX:
    def __init__(self, base_path: str, pixel_per_tile=False):
        """
        Handles basic graphic elements / images of the game

        :param base_path: The base path to the images folder
        :param pixel_per_tile: Whether to scale every pixel of the images to a tile size
        """

        self.base_path = base_path
        self.pixel_per_tile = pixel_per_tile

        self._imgs = {}
        self._img_groups = {}  # store the group of images loaded from a given directory

    def load(self, path: str, scale: tuple = None, colorkey: tuple | str = 'black', prefix: str = None, key: str = None) -> dict:
        """
        Loads the given image path and adds it to the dict.

        :param path: The path to the image.
        :param scale: An optional tuple (width, height) representing the new size of the image.
        :param colorkey: An optional tuple representing the color that should be treated as transparent in the loaded image.
                         Defaults to black.
        :param prefix: The prefix to add to the image name to reference the image by. If None, the file name will be used as the key.
        :param key: The direct to reference the image by. If None, the file name will be used as the key.
        :return: Dictionary of the loaded image keyed by its name.
        :rtype: dict
        """

        full_path = os.path.join(self.base_path, path)

        if not os.path.isfile(full_path):
            raise FileNotFoundError(f"No file found at {full_path}")
        if not isf_img(full_path):
            raise ValueError(f"The file at {full_path} is not a recognized image type.")

        img = pygame.image.load(full_path).convert()
        img.set_colorkey(colorkey)

        if scale is not None:
            if len(scale) != 2:
                raise ValueError("Scale must be a tuple of two integers (width, height)")

            width, height = img.get_size()
            if self.pixel_per_tile:
                scaled_width = int(width * scale[0])
                scaled_height = int(height * scale[1])
            else:
                aspect_ratio = width / height

                if aspect_ratio > 1:  # Width is the limiting factor
                    scaled_width = scale[0]
                    scaled_height = int(scale[1] / aspect_ratio)
                else:  # Height is the limiting factor
                    scaled_height = scale[0]
                    scaled_width = int(scale[1] * aspect_ratio)

            img = pygame.transform.scale(img, (scaled_width, scaled_height))

        img_name, _ = os.path.splitext(os.path.basename(path))
        if key is not None:
            img_name = key
        if prefix is not None:
            img_name = prefix + '_' + img_name

        self._imgs[img_name] = img

        return {img_name: img}

    def __setitem__(self, key, value):
        """
        Directly set the image with its name

        :param key: The image name
        :param value: The loaded image
        :return: None
        """

        self._imgs[key] = value

    def loadmul(self, paths: list, scale: tuple = None, colorkey: tuple | str = 'black', prefix: str = None, key: str = None) -> dict:
        imgs = {}
        for path in paths:
            imgs.update(self.load(path, scale, colorkey, prefix, key))

        return imgs

    def loaddir(self, path: str, scale: tuple = None, colorkey: tuple | str = 'black', prefix: str = None, key: str = None) -> dict:
        """
        Loads all the images in the given directory and adds them to the dict.

        :param path: The path to the directory.
        :param scale: An optional tuple (width, height) representing the new size of the image.
        :param colorkey: An optional tuple representing the color that should be treated as transparent in the loaded image.
                        Defaults to black.
        :param prefix: The prefix to add to the image name to reference the image by. If None, the file name will be used as the key.
        :param key: The direct to reference the image by. If None, the file name will be used as the key.
        :return: A dictionary of the loaded images keyed by their names.
        :rtype: dict
        """

        dir_path = os.path.join(self.base_path, path)

        if not os.path.isdir(dir_path):
            raise NotADirectoryError(f"No directory found at {dir_path}")

        img_paths = [os.path.join(path, img_name) for img_name in sorted(os.listdir(dir_path))]
        prefix = prefix or os.path.basename(path)

        imgs = self.loadmul(img_paths, scale, colorkey, prefix, key)

        self._img_groups[path] = imgs

        return imgs

    def loaddirs(self, paths: list, scale: tuple = None, colorkey: tuple | str = 'black', category: str = None) -> dict:
        imgs = {}
        for path in paths:
            category_for_path = category or os.path.basename(path)
            loaded_images = self.loaddir(path, scale, colorkey, category_for_path)
            imgs.update(loaded_images)

        return imgs

    def get(self, *keys) -> dict:
        """
        Get the file paths of specific images.

        :param keys: Variable number of keys to reference the images.
        :return: A dictionary where keys are the provided keys, and values are images.
        :rtype: dict
        """

        imgs = {}
        for key in keys:
            img = self._imgs.get(key)
            if img is not None:
                imgs[key] = img

        return imgs

    def get_only(self, key: str) -> pygame.Surface:
        """
        Get the image with the given key

        :param key: The key to reference the image
        :return: The image surface
        :rtype: pygame.Surface
        """

        return self._imgs[key]

    def get_as_list(self, *keys) -> list:
        imgs = []
        for key in keys:
            img = self._imgs.get(key)
            if img is not None:
                imgs.append(img)

        return imgs

    def get_group(self, *keys) -> dict:
        """
        Get the images loaded from the specified directory.

        :param keys: Variable number of keys to reference the image group.
        :return: A dictionary of keys matching the respective previously loaded image group
        :rtype: dict
        """

        img_groups = {}
        for key in keys:
            img = self._img_groups.get(key)
            if img is not None:
                img_groups[key] = img

        return img_groups

    def get_group_as_list(self, *keys) -> list:
        """
        Get the images loaded from the specified directory.

        :param keys: Variable number of keys to reference the image group.
        :return: A list of images matching the respective previously loaded image group
        :rtype: list
        """

        imgs = []
        for key in keys:
            img = self._img_groups.get(key)
            if img is not None:
                imgs.extend(img.values())

        return imgs

    def __getitem__(self, key):
        return self._imgs[key]

    def remove(self, *keys) -> dict:
        """
        Remove specific images from the dictionary.

        :param keys: Variable number of keys to reference the images for removal.
        :return: A dictionary where keys are the removed keys, and values are the file paths of the removed images.
        :rtype: dict

        :raises KeyError: If any of the specified keys are not found.
        """

        imgs = {}
        for key in keys:
            img = self._imgs.pop(key, None)
            if img is None:
                raise KeyError(f"No image found for key: {key}")

            for img_group_key, img_group in self._img_groups.items():
                if img in img_group:
                    img_group.remove(img)

                    if not img_group:
                        del self._img_groups[img_group_key]
                    break

            imgs[key] = img

        return imgs

    def keys(self):
        return self._imgs.keys()

    def group_keys(self):
        return self._img_groups.keys()

    def __contains__(self, key):
        return key in self._imgs
