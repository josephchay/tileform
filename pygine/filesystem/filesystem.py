import datetime
import json
import os
import shutil
import pygame


class Filesystem:
    def __init__(self, base_path='.') -> None:
        """
        Handles all file system operations

        :param base_path: The base path to use for all files
        """

        self.base_path = base_path
        self.imager = None

    def exists(self, path) -> bool:
        """
        Checks if a file or directory exists

        :param path: The path to the file or directory
        :return: bool
        """

        return os.path.exists(os.path.join(self.base_path, path))

    def isfile(self, path) -> bool:
        return os.path.isfile(os.path.join(self.base_path, path))

    def isimg(self, path) -> bool:
        return os.path.isfile(os.path.join(self.base_path, path)) and path.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', 'tiff'))

    def isdir(self, path) -> bool:
        return os.path.isdir(os.path.join(self.base_path, path))

    def read(self, file_path) -> str:
        with open(os.path.join(self.base_path, file_path), 'r') as file:
            return file.read()

    def readlines(self, file_path) -> list:
        with open(os.path.join(self.base_path, file_path), 'r') as file:
            return file.readlines()

    def readconfig(self, file_path) -> dict:
        with open(os.path.join(self.base_path, file_path), 'r') as file:
            return json.load(file)

    def readimg(self, file_path: str, colorkey: tuple | str = 'black', scale: tuple = None, pixel_per_tile=False) -> pygame.Surface:
        if self.imager is None:
            self.imager = Imager(self.base_path)

        if not self.isimg(file_path):
            raise ValueError(f"The file at {os.path.join(self.base_path, file_path)} is not a recognized image type.")

        img = self.imager.load(file_path, colorkey=colorkey)

        if scale is not None:
            img = self.imager.scale(img, scale, pixel_per_tile=pixel_per_tile)

        return img

    def readimgdir(self, dir_path: str, colorkey: tuple | str = 'black', scale: tuple = None, pixel_per_tile=False) -> list:
        full_dir_path = os.path.join(self.base_path, dir_path)

        imgs = []
        for img_name in sorted(os.listdir(full_dir_path)):
            img_path = os.path.join(dir_path, img_name)
            imgs.append(self.readimg(img_path, colorkey=colorkey, scale=scale, pixel_per_tile=pixel_per_tile))

        return imgs

    def write(self, file_path, content, mode='w') -> 'Filesystem':
        with open(os.path.join(self.base_path, file_path), mode) as file:
            file.write(content)

        return self

    def delete(self, file_path) -> 'Filesystem':
        os.remove(os.path.join(self.base_path, file_path))

        return self

    def rename(self, old_path, new_path) -> 'Filesystem':
        os.rename(os.path.join(self.base_path, old_path), os.path.join(self.base_path, new_path))

        return self

    def mkdir(self, dir_path) -> 'Filesystem':
        os.makedirs(os.path.join(self.base_path, dir_path), exist_ok=True)

        return self

    def rmdir(self, dir_path) -> 'Filesystem':
        shutil.rmtree(os.path.join(self.base_path, dir_path))

        return self

    def list_dir(self, dir_path='.') -> list:
        return os.listdir(os.path.join(self.base_path, dir_path))

    def copy(self, source_path, destination_path) -> 'Filesystem':
        shutil.copyfile(os.path.join(self.base_path, source_path), os.path.join(self.base_path, destination_path))

        return self

    def mv(self, source_path, destination_path) -> 'Filesystem':
        shutil.move(os.path.join(self.base_path, source_path), os.path.join(self.base_path, destination_path))

        return self

    def fdetails(self, path) -> dict | None:
        """
        Get the details of a file

        :param path: The path to the file
        :return: dict
        """

        path = os.path.join(self.base_path, path)
        if not os.path.isfile(path):
            return None

        stats = os.stat(path)
        return {
            "size": stats.st_size,
            "last_modified": datetime.datetime.fromtimestamp(stats.st_mtime),
            "last_accessed": datetime.datetime.fromtimestamp(stats.st_atime)
        }


class Imager:
    def __init__(self, base_path='.') -> None:
        """
        Handles all image operations

        :param base_path: The base path to use for all images
        """

        self.base_path = base_path

    def load(self, path: str, colorkey: tuple | str = 'black') -> pygame.Surface:
        """
        Loads the given image path and adds it to the dict.

        :param path: The path to the image.
        :param colorkey: An optional tuple representing the color that should be treated as transparent in the loaded image.
                         Defaults to black.
        :return: The loaded image
        :rtype: pygame.Surface
        """

        full_path = os.path.join(self.base_path, path)

        img = pygame.image.load(full_path).convert()
        img.set_colorkey(colorkey)

        return img

    def scale(self, img, scale: tuple, pixel_per_tile=False) -> pygame.Surface:
        """
        Scale the give image

        :param img:
        :param scale: A tuple (width, height) representing the new size of the image.
        :param pixel_per_tile:
        :return:
        """

        if len(scale) != 2:
            raise ValueError("Scale must be a tuple of two integers (width, height)")

        width, height = img.get_size()
        if pixel_per_tile:
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

        return pygame.transform.scale(img, (scaled_width, scaled_height))
