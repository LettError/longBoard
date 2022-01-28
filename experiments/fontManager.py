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
    fontSoonWithoutInterface = None

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
        self.fontSoonWithoutInterface = info['font']

    def fontDocumentDidClose(self, info):
        print('fontDocumentDidClose!')
        # substitute the font with interface (closing down) with the font without interface
        # collected from fontDocumentWillClose()
        self.fonts[self.fontSoonWithoutInterface.path] = self.fontSoonWithoutInterface
        self.fontSoonWithoutInterface = None
        self.printStatus()

    def loadFontsInBackground(self):
        sourcesFolder = Path.cwd().parent / "source" / "resources"
        for eachPath in [pp for pp in sourcesFolder.iterdir() if pp.suffix == '.ufo']:
            fontObj = OpenFont(eachPath, showInterface=False)
            self.fonts[fontObj.path] = fontObj


"""
snippet from Frederik

from mojo.subscriber import Subscriber, registerRoboFontSubscriber

class Test(Subscriber):

    debug = True

    font = None
    def fontDocumentWillClose(self, info):
        self.font = info["font"]

    def fontDocumentDidClose(self, info):
        if self.font is not None:
            print(self.font.document())

            # self.font.openInterface()

registerRoboFontSubscriber(Test)

"""


# -- Instructions -- #
if __name__ == '__main__':
    registerRoboFontSubscriber(FontManager)
