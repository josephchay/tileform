import os
import pygame


class SFX:
    def __init__(self):
        """
        Handles all the sound effects
        """

        pygame.mixer.init()
        self.sounds = {}  # {key: {'sound': sound_file_path, 'vol': volume_value}}

    def set(self, key, file_path, volume=1.0) -> None:
        """
        Add a sound to the dictionary

        :param key: The key to reference the sound
        :param file_path: The path to the sound file
        :param volume: The initial volume of the sound
        :return: None
        """

        try:
            sound = pygame.mixer.Sound(file_path)
            sound.set_volume(volume)
            self.sounds[key] = {'sound': sound, 'vol': volume}
        except pygame.error as e:
            raise Exception(f"Error loading sound: {e}")

    def get(self, key) -> dict:
        """
        Get the sound object

        :param key: The key to reference the sound
        :return: Dictionary with the following keys:
                - sound: The sound object
                - vol: The volume of the sound
        :rtype: dict
        """

        if key not in self.sounds:
            raise Exception(f"Sound '{key}' not found.")

        return self.sounds[key]

    def remove(self, key) -> None:
        """
        Remove a sound from the dictionary

        :param key: The key to reference the sound
        :return: None
        """

        if key in self.sounds:
            del self.sounds[key]

    def play(self, key, loops: int = 0) -> None:
        """
        Play a sound with the specified amounts of loop

        :param key: The key to reference the sound
        :param loops: The amount of loops to play the sound
        :return: None
        """

        if key not in self.sounds:
            raise Exception(f"Sound '{key}' not found.")

        sound = self.sounds[key]['sound']
        sound.play(loops)

    def vol(self, key, volume) -> None:
        """
        Set the volume of the specific sound

        :param key: The key to reference the sound
        :param volume: The volume to set the sound to
        :return: None
        """

        if key not in self.sounds:
            raise Exception(f"Sound '{key}' not found.")

        if volume > 1.0 or volume < 0.0:
            raise ValueError(f"Volume must be between 0.0 and 1.0")

        self.sounds[key]['vol'] = volume
