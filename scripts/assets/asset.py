from scripts.assets.gfxs.gfx import GFX
from scripts.assets.vfxs.vfx import VFX
from scripts.assets.sfxs.sfx import SFX


class AssetHandler:
    def __init__(self, main, base_path):
        """
        Centralized point to manage all the assets of the game

        :param main: The main instance
        :param base_path: The base path to the images folder
        """

        self.main = main
        self.base_path = base_path

        self.managers = {
            'gfx': GFX(self.base_path),
            'vfx': VFX(),
            'sfx': SFX()
        }

    def __getitem__(self, item) -> GFX | VFX | SFX:
        """
        Get the asset manager of the specified type

        :param item: The type of asset manager to get
        :return: The asset manager
        :rtype: GFX | VFX | SFX
        """

        return self.managers[item]
