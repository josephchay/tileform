import os
import json
import shutil
import datetime


class Filesystem:
    def __init__(self, base_path='.'):
        """
        Handles all file system operations

        :param base_path: The base path to use for all files
        """

        self.base_path = base_path

    def exists(self, path) -> bool:
        """
        Checks if a file or directory exists

        :param path: The path to the file or directory
        :return: bool
        """

        return os.path.exists(os.path.join(self.base_path, path))

    def isfile(self, path):
        return os.path.isfile(os.path.join(self.base_path, path))

    def isdir(self, path):
        return os.path.isdir(os.path.join(self.base_path, path))

    def read(self, file_path):
        with open(os.path.join(self.base_path, file_path), 'r') as file:
            return file.read()

    def readlines(self, file_path):
        with open(os.path.join(self.base_path, file_path), 'r') as file:
            return file.readlines()

    def readconfig(self, file_path):
        with open(os.path.join(self.base_path, file_path), 'r') as file:
            return json.load(file)

    def write(self, file_path, content, mode='w'):
        with open(os.path.join(self.base_path, file_path), mode) as file:
            file.write(content)

    def delete(self, file_path):
        os.remove(os.path.join(self.base_path, file_path))

    def rename(self, old_path, new_path):
        os.rename(os.path.join(self.base_path, old_path), os.path.join(self.base_path, new_path))

    def mkdir(self, dir_path):
        os.makedirs(os.path.join(self.base_path, dir_path), exist_ok=True)

    def rmdir(self, dir_path):
        shutil.rmtree(os.path.join(self.base_path, dir_path))

    def list_dir(self, dir_path='.'):
        return os.listdir(os.path.join(self.base_path, dir_path))

    def copy(self, source_path, destination_path):
        shutil.copyfile(os.path.join(self.base_path, source_path), os.path.join(self.base_path, destination_path))

    def move(self, source_path, destination_path):
        shutil.move(os.path.join(self.base_path, source_path), os.path.join(self.base_path, destination_path))

    def file_details(self, path) -> dict | None:
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
