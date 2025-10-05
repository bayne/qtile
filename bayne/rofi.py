from libqtile import log_utils
from typing import List

from libqtile.lazy import lazy
import os

env = os.environ.copy()
env.update({'PATH': env['PATH'] + ':/home/bpayne/.bin'})

logger = log_utils.logger

class RofiScript:
    def __init__(self, name, path):
        self.name = name
        self.path = path

class Rofi:
    def __init__(self, rofi_scripts: List[RofiScript]):
        combi_modi = [
            'window',
            *map(lambda rofi_script: f"{rofi_script.name}:{rofi_script.path}", rofi_scripts),
            'drun',
            'run'
        ]
        self.cmd = [
            'rofi', '-show', 'combi',
            '-modi', '"combi"',
            '-combi-modi', f'\'{",".join(combi_modi)}\'',
            '-show-icons',
        ]
        logger.info(f"Rofi cmd: {' '.join(self.cmd)}")

    def show(self):
        return lazy.spawn(self.cmd, env=env, shell=True)