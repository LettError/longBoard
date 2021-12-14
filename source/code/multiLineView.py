#!/usr/bin/env python3

# --------------- #
# Multi Line View #
# --------------- #

# -- Modules -- #
from pathlib import Path

from mojo.subscriber import Subscriber, WindowController
from mojo.subscriber import registerRoboFontSubscriber
from mojo.UI import splitText
from vanilla import Window, EditText, VerticalStackView
from merz import MerzView

from designSpaceManager import DesignSpaceManager
from customEvents import DEBUG_MODE


# -- Constants -- #
BLACK = 0, 0, 0, 1
RED = 1, 0, 0, 1
WHITE = 1, 1, 1, 1


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
        self.txt = sender.get()
        self.updateView()

    def started(self):
        self.populateLayers()

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

    def populateLayers(self):
        fonts = self.controller.designSpaceManager.fonts
        fontLayerHgt = self.view.height()/len(fonts)

        for index, (fontName, fontObj) in enumerate(fonts.items()):
            flatKerning = fontObj.getFlatKerning()
            fontLayer = self.container.appendRectangleSublayer(
                name=fontName,
                position=(0, index*fontLayerHgt),
                size=(self.view.width(), fontLayerHgt),
                strokeColor=RED,
                fillColor=WHITE,
                strokeWidth=1
            )

            scalingFactor = fontLayerHgt/fontObj.info.unitsPerEm
            xx = 0
            glyphNames = splitText(self.txt, fontObj.getCharacterMapping())
            for index, glyphName in enumerate(glyphNames):

                # adjust adv according to kerning
                if index == 0:
                    prevName = glyphName
                else:
                    pair = (prevName, glyphName)
                    if pair in flatKerning:
                        xx -= fontObj.getFlatKerning()[pair]

                glyphObj = fontObj[glyphName]
                glyphBoxLayer = fontLayer.appendRectangleSublayer(
                    name=f'{index}',
                    position=(xx, 0),
                    size=(glyphObj.width, fontObj.info.unitsPerEm),
                    strokeColor=BLACK,
                    fillColor=WHITE,
                    strokeWidth=1
                )
                glyphBoxLayer.addScaleTransformation(scalingFactor, name="scale")
                glyphPathLayer = glyphBoxLayer.appendPathSublayer(
                    fillColor=BLACK
                )
                glyphPathLayer.setPath(glyphObj.getRepresentation("merz.CGPath"))
                xx += glyphObj.width

    def destroy(self):
        pass

    def updateView(self):
        """this should work through a diff, to avoid refreshing the entire stack of layers, what might change:
            - chars in edit text (one less, one more, copy paste of an entire different string)
            - fonts?
            - currentLocation
        --> check the diffStrings.py example in the experiments folder

        meanwhile, just a hard refresh
        """
        self.container.clearSublayers()
        self.populateLayers()
        print(f"update multi line view: {self.txt}")

    def currentDesignSpaceLocationDidChange(self, info):
        pass


if __name__ == '__main__':
    mc = MockController()
    MultiLineView.controller = mc
    registerRoboFontSubscriber(MultiLineView)
