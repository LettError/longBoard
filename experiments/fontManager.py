#!/usr/bin/env python3

# ---------------------------- #
# Font Manager Subscriber Demo #
# ---------------------------- #

# -- Modules -- #
from pathlib import Path
from os.path import basename

from mojo.roboFont import OpenFont
from mojo.subscriber import Subscriber, registerRoboFontSubscriber


# -- Objects, Functions, Procedures -- #
class FontManager(Subscriber):

    debug = True
    fonts = {}
    soonToBeCloseFontPath = None

    def build(self):
        print('build!')
        self.loadFontsInBackground()

    def started(self):
        print('started!')

    def destroy(self):
        print('closing down!')
        for path, eachFont in self.fonts.items():
            if not eachFont.hasInterface():
                eachFont.close()

    def printStatus(self):
        print('----'*4)
        for path, eachFont in self.fonts.items():
            print(f'{basename(eachFont.path)}; glyphs amount: {len(eachFont)}; has interface? {eachFont.hasInterface()}')
        print('----'*4)

    def fontDocumentDidOpen(self, info):
        print('fontDocumentDidOpen!')
        # substitute the font without interface with the font with interface
        fontObj = info['font']
        self.fonts[fontObj.path] = fontObj
        self.printStatus()

    def fontDocumentWillClose(self, info):
        self.soonToBeCloseFontPath = info['font'].path

    def fontDocumentDidClose(self, info):
        print('fontDocumentDidClose!')
        # substitute the font with interface (closing down) with the font without interface
        self.fonts[self.soonToBeCloseFontPath] = OpenFont(self.soonToBeCloseFontPath, showInterface=False)
        self.soonToBeCloseFontPath = None
        self.printStatus()

    def loadFontsInBackground(self):
        sourcesFolder = Path.cwd().parent / "resources"
        for eachPath in [pp for pp in sourcesFolder.iterdir() if pp.suffix == '.ufo']:
            fontObj = OpenFont(eachPath, showInterface=False)
            self.fonts[fontObj.path] = fontObj


# -- Instructions -- #
if __name__ == '__main__':
    registerRoboFontSubscriber(FontManager)
