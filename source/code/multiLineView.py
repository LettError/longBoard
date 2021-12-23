#!/usr/bin/env python3

# --------------- #
# MULTI LINE VIEW #
# --------------- #

# -- Modules -- #
from collections import defaultdict
from pathlib import Path
from difflib import Differ

from mojo.subscriber import Subscriber, WindowController
from mojo.subscriber import registerRoboFontSubscriber
from mojo.UI import splitText
from vanilla import Window, EditText, VerticalStackView
from merz import MerzView

from tools import windowed
from designSpaceManager import DesignSpaceManager
from customEvents import DEBUG_MODE


# -- Constants -- #
BLACK = 0, 0, 0, 1
RED = 1, 0, 0, 1
WHITE = 1, 1, 1, 1
TRANSPARENT = 0, 0, 0, 0


# -- Objects -- #
class MockController():

    def __init__(self):
        self.loadTestDocument()

    def loadTestDocument(self):
        print('loadTestDocument')
        self.designSpaceManager = DesignSpaceManager()
        testDocPath = Path.cwd().parent / "resources" / "MutatorSans.designspace"
        self.designSpaceManager.useVarlib = True
        self.designSpaceManager.read(testDocPath)
        self.designSpaceManager.loadFonts(reload_=True)
        self.currentDesignSpaceLocation = self.designSpaceManager.newDefaultLocation(bend=True)
        self.currentDesignSpaceLocation = self.designSpaceManager._test_LocationAtCenter()
        print('self.currentDesignSpaceLocation', self.currentDesignSpaceLocation)


class MultiLineView(Subscriber, WindowController):

    debug = DEBUG_MODE
    txt = 'AVATAR'
    controller = None
    fonts_2_boxes = defaultdict(list)

    def build(self):
        self.w = Window((600, 400), "MultiLineView", minSize=(200, 40))
        self.editText = EditText((10, 10, -10, 22), text=self.txt,
                                 callback=self.editTextCallback)
        self.view = MerzView(
            "auto",
            backgroundColor=(1, 1, 1, 1),
            delegate=self
        )
        self.w.stack = VerticalStackView(
            (0, 0, 0, 0),
            views=[
                dict(view=self.editText),
                dict(view=self.view)
            ],
            spacing=10,
            edgeInsets=(10, 10, 10, 10)
        )
        self.container = self.view.getMerzContainer()
        self.w.open()

    def editTextCallback(self, sender):
        self.updateView(prevTxt=self.txt, currentTxt=sender.get())
        self.txt = sender.get()

    def started(self):
        self.createFontLayers()
        self.updateView(prevTxt='', currentTxt=self.txt)

    def sizeChanged(self, sender):
        fonts = self.controller.designSpaceManager.fonts
        fontLayerHgt = self.view.height()/len(fonts)
        if len(self.container.getSublayers()) > 0:
            with self.container.propertyGroup():
                for index, (fontName, fontObj) in enumerate(fonts.items()):
                    fontLayer = self.container.getSublayer(name=fontName)
                    fontLayer.setPosition((0, index*fontLayerHgt))
                    fontLayer.setSize((self.view.width(), fontLayerHgt))
                    scalingFactor = fontLayerHgt/fontObj.info.unitsPerEm
                    for eachGlyphBox in fontLayer.getSublayers():
                        eachGlyphBox.removeTransformation(name="scale")
                        eachGlyphBox.addScaleTransformation(scalingFactor)

    def createFontLayers(self):
        fonts = self.controller.designSpaceManager.fonts
        fontLayerHgt = self.view.height()/len(fonts)
        for index, (fontName, fontObj) in enumerate(fonts.items()):
            self.container.appendRectangleSublayer(
                name=fontName,
                position=(0, index*fontLayerHgt),
                size=(self.view.width(), fontLayerHgt),
                strokeColor=RED,
                fillColor=WHITE,
                strokeWidth=1
            )

    def destroy(self):
        pass

    def updateView(self, prevTxt, currentTxt):
        """this should work through a diff, to avoid refreshing the entire stack of layers, what might change:
            - chars in edit text (one less, one more, copy paste of an entire different string)
            - fonts?
            - currentLocation
        --> check the diffStrings.py example in the experiments folder
        """
        differ = Differ()
        fonts = self.controller.designSpaceManager.fonts
        fontLayerHgt = self.view.height()/len(fonts)

        with self.container.propertyGroup():
            for index, (fontName, fontObj) in enumerate(fonts.items()):
                fontLayer = self.container.getSublayer(name=fontName)
                scalingFactor = fontLayerHgt/fontObj.info.unitsPerEm

                prevGlyphNames = splitText(prevTxt, fontObj.getCharacterMapping())
                glyphNames = splitText(currentTxt, fontObj.getCharacterMapping())

                xx = 0
                layerIndex = 0
                prevRemoved = False
                for difference in differ.compare(prevGlyphNames, glyphNames):
                    sign, name = difference[0], difference[2:]
                    glyphObj = fontObj[name]

                    # remove
                    if sign == '-':
                        glyphBoxLayer = self.fonts_2_boxes[fontName][layerIndex]
                        fontLayer.removeSublayer(glyphBoxLayer)
                        del self.fonts_2_boxes[fontName][layerIndex]
                        prevRemoved = True

                    # insert
                    elif sign == '+':
                        glyphBoxLayer = fontLayer.appendRectangleSublayer(
                            position=(xx, 0),
                            size=(glyphObj.width, fontObj.info.unitsPerEm),
                            strokeColor=BLACK,
                            fillColor=TRANSPARENT,
                            strokeWidth=1
                        )
                        glyphBoxLayer.addScaleTransformation(scalingFactor, name="scale")
                        self.fonts_2_boxes[fontName].insert(layerIndex, glyphBoxLayer)

                        glyphPathLayer = glyphBoxLayer.appendPathSublayer(
                            fillColor=BLACK
                        )
                        glyphPathLayer.setPath(glyphObj.getRepresentation("merz.CGPath"))
                        xx += glyphObj.width
                        layerIndex += 1 if not prevRemoved else 0
                        prevRemoved = False

                    # common, we only adjust xx position if necessary
                    elif sign == ' ':
                        glyphBoxLayer = self.fonts_2_boxes[fontName][layerIndex]
                        glyphBoxLayer.setPosition((xx, 0))
                        xx += glyphObj.width
                        layerIndex += 1 if not prevRemoved else 0
                        prevRemoved = False

                    else:
                        raise NotImplementedError(f"difflib issue! {name}")

                # applying kerning after the diffing
                if len(glyphNames) > 2:
                    flatKerning = fontObj.getFlatKerning()
                    correction = 0
                    for lftIndex, rgtIndex in windowed(range(len(glyphNames)), 2):
                        pair = glyphNames[lftIndex], glyphNames[rgtIndex]
                        if pair in flatKerning:
                            correction += flatKerning[pair]
                        boxLayer = self.fonts_2_boxes[fontName][rgtIndex]
                        prevX, prevY = boxLayer.getPosition()
                        boxLayer.setPosition((prevX+correction, prevY))

    def currentDesignSpaceLocationDidChange(self, info):
        pass


if __name__ == '__main__':
    mc = MockController()
    MultiLineView.controller = mc
    registerRoboFontSubscriber(MultiLineView)
