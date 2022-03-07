#!/usr/bin/env python3

# --------------- #
# MULTI LINE VIEW #
# --------------- #

# -- Modules -- #
import itertools
from collections import defaultdict
from collections.abc import MutableMapping
from difflib import Differ
from pathlib import Path

from merz import MerzView
from mojo.subscriber import Subscriber, WindowController, registerRoboFontSubscriber
from mojo.UI import splitText
from vanilla import Button, EditText, HorizontalStackView, VerticalStackView, Window

from customEvents import DEBUG_MODE
from designSpaceManager import DesignSpaceManager
from tools import windowed

# -- Constants -- #
BLACK = 0, 0, 0, 1
RED = 1, 0, 0, 1
WHITE = 1, 1, 1, 1
TRANSPARENT = 0, 0, 0, 0


# -- Objects -- #
def fromDictToTuple(location):
    """
    Sometimes we need to use locations as immutable keys of a dict
    """
    toBeFreezed = []
    for axisName, value in sorted(location.items(), key=lambda x: x[0]):
        toBeFreezed.append((axisName, value))
    return tuple(toBeFreezed)


def fromTupleToDict(frozenLocation):
    """
    Sometimes we need to go back from immutable keys to regular design space locations
    """
    location = {}
    for axisName, value in frozenLocation:
        location[axisName] = value
    return location


class Info:
    unitsPerEm = 1000


class LongBoardMathFont(MutableMapping):

    kerning = None
    charMap = defaultdict(set)

    def __init__(self, frozenLocation):
        self.store = dict()
        self.frozenLocation = frozenLocation

        # RA: this is definitely a hack, we cannot always assume a 1000upm grid
        #     I think this data should come from the design space manager, right?
        self.info = Info()

    def __getitem__(self, glyphName):
        return self.store[glyphName]

    def __setitem__(self, glyphName, glyphObj):
        if glyphObj.unicodes:
            for eachCode in glyphObj.unicodes:
                self.charMap[eachCode].add(glyphName)
        self.store[glyphName] = glyphObj

    def __delitem__(self, glyphName):
        for eachPair in self.kerning.keys():
            if glyphName in eachPair:
                del self.kerning[eachPair]
        self._removeFromCharMap(glyphName)
        del self.store[glyphName]

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)

    def injectKerningFrom(self, designSpace):
        possiblePairs = list(itertools.product(self.keys(), self.keys()))
        # check which lib is used to calculate this
        mutator = designSpace.getKerningMutator(pairs=possiblePairs)
        self.kerning = mutator.makeInstance(fromTupleToDict(self.frozenLocation))

    # the following methods make LongBoardMathFont compatible with RFont
    def getCharacterMapping(self):
        return self.charMap

    def getFlatKerning(self):
        return self.kerning

    # internals
    def _removeFromCharMap(self, glyphName):
        for uniCode, names in self.charMap.items():
            if glyphName in names:
                if len(names) == 1:
                    del self.charMap[uniCode]
                else:
                    self.charMap[uniCode].remove(glyphName)


class MockController:

    _displayedLocationsOnMultiLineView = []

    def __init__(self):
        self.designSpaceManager = DesignSpaceManager()
        self.loadTestDocument()

        for _ in range(5):
            loc = self.designSpaceManager._test_randomLocation()
            self._displayedLocationsOnMultiLineView.append(loc)
        self._displayedLocationsOnMultiLineView.append({"width": 0, "weight": 0})
        print(self._displayedLocationsOnMultiLineView)

    @property
    def displayedLocationsOnMultiLineView(self):
        return self._displayedLocationsOnMultiLineView

    def loadTestDocument(self):
        print("loadTestDocument")
        testDocPath = Path.cwd().parent / "resources" / "MutatorSans.designspace"
        self.designSpaceManager.useVarlib = True
        self.designSpaceManager.read(testDocPath)
        self.designSpaceManager.loadFonts(reload_=True)
        self.currentDesignSpaceLocation = self.designSpaceManager.newDefaultLocation(bend=True)
        self.currentDesignSpaceLocation = self.designSpaceManager._test_LocationAtCenter()
        print("self.currentDesignSpaceLocation", self.currentDesignSpaceLocation)


class MultiLineView(Subscriber, WindowController):

    debug = DEBUG_MODE

    txt = "LONGBOARD"
    controller = None

    # this dict stores references to singleLine rectangle merz layer to the locations (frozen ones) displayed
    # in the multi line view, something like:
    # ((width, 100), (weight, 300)): merzLayer (second line from the top)
    frozenLocToFontMerzLayer = defaultdict(list)

    # this work as a container pseudo longboard fonts, dictionaries of custom MathGlyphs
    # these "font" objects must respect:
    # - a dict like structure {name: glyphObj}
    # - the glyph object must be able to execute a getRepresentation("merz.CGPath") method
    longBoardFonts = dict()

    def build(self):
        self.w = Window((600, 400), "MultiLineView", minSize=(200, 40))

        self.editText = EditText("auto", text=self.txt, callback=self.editTextCallback)
        self.refreshButton = Button("auto", chr(8634), callback=self.refreshButtonCallback)

        self.ctrlsView = HorizontalStackView(
            (0, 0, 0, 0),
            views=[dict(view=self.editText), dict(view=self.refreshButton)],
            spacing=10,
            alignment="center",
            distribution="fillProportionally",
            edgeInsets=(0, 0, 0, 0),
        )

        self.textView = MerzView("auto", backgroundColor=(1, 1, 1, 1), delegate=self)
        self.w.stack = VerticalStackView(
            (0, 0, 0, 0),
            views=[dict(view=self.ctrlsView, height=22), dict(view=self.textView)],
            spacing=10,
            edgeInsets=(10, 10, 10, 10),
        )
        self.container = self.textView.getMerzContainer()
        self.w.open()

    def started(self):
        self.populateFontsLayers()
        self.invalidCache = False
        self.updateView(prevTxt="", currentTxt=self.txt)

    def refreshButtonCallback(self, sender):
        """
        DRAWING
            This is a hard refresh, clears everything!
        """
        self.longBoardFonts.clear()
        self.frozenLocToFontMerzLayer.clear()
        self.container.clearSublayers()
        self.populateFontsLayers()
        self.invalidCache = False
        self.updateView(prevTxt="", currentTxt=self.txt)

    def editTextCallback(self, sender):
        self.updateView(prevTxt=self.txt, currentTxt=sender.get())
        self.txt = sender.get()

    @property
    def invalidCache(self):
        return self._invalidCache

    @invalidCache.setter
    def invalidCache(self, value):
        """
        DRAWING
            when the invalidCache value is set to False or True
            the gaussian filter applied on the merz container is applied or removed
            also, the edit text is enable/disabled
        """
        self._invalidCache = value
        if value:
            if not self.container.getFilter(name="gaussianBlur"):
                self.container.appendFilter(dict(name="gaussianBlur", filterType="gaussianBlur", radius=10))
        else:
            if self.container.getFilter(name="gaussianBlur"):
                self.container.removeFilter(name="gaussianBlur")
        self.editText.enable(not value)

    def sizeChanged(self, sender):
        """
        DRAWING
            when the size of the window is changed, and therefore the merz view too
            the view is not entirely re-drawn, only the size and position properties
            are updated
        """
        if not self.longBoardFonts:
            return
        fontLayerHgt = self.textView.height() / len(self.controller.displayedLocationsOnMultiLineView)
        if len(self.container.getSublayers()) > 0:
            with self.container.propertyGroup():
                for index, (frozenLocation, fontObj) in enumerate(self.longBoardFonts.items()):
                    fontLayer = self.container.getSublayer(name=str(frozenLocation))
                    fontLayer.setPosition((0, index * fontLayerHgt))
                    fontLayer.setSize((self.textView.width(), fontLayerHgt))
                    scalingFactor = fontLayerHgt / fontObj.info.unitsPerEm
                    for eachGlyphBox in fontLayer.getSublayers():
                        eachGlyphBox.removeTransformation(name="scale")
                        eachGlyphBox.addScaleTransformation(scalingFactor)

    def populateFontsLayers(self):
        """
        DRAWING
            This method create the font merz layers inside the container
            These are rectangles running from left to right in the container
            The height of each rectangle is the height of the container divided
            by the number of displayed locations
        """
        if len(self.controller.displayedLocationsOnMultiLineView) == 0:
            return

        fontLayerHgt = self.textView.height() / len(self.controller.displayedLocationsOnMultiLineView)
        for index, eachLocation in enumerate(self.controller.displayedLocationsOnMultiLineView):
            self.container.appendRectangleSublayer(
                name=str(fromDictToTuple(eachLocation)),
                position=(0, index * fontLayerHgt),
                size=(self.textView.width(), fontLayerHgt),
                strokeColor=RED,
                fillColor=WHITE,
                strokeWidth=1,
            )

    def controllerWillClose(self, info):
        """
        considering that the controller object does not have direct access to the subordinate
        object window, we need to use a custom event to close the MultiLineView vanilla window
        otherwise it will stay open after longboard has been closed by the user
        """
        self.w.close()

    def addGlyphs(self, glyphNames):
        """
        Add glyphs to the longboard fonts as needed for displaying on the multi line view

        """
        for eachLoc in self.controller.displayedLocationsOnMultiLineView:
            frozenLocation = fromDictToTuple(eachLoc)
            eachFont = (
                self.longBoardFonts[frozenLocation]
                if frozenLocation in self.longBoardFonts
                else LongBoardMathFont(frozenLocation=frozenLocation)
            )
            for eachGlyphName in glyphNames:
                eachFont[eachGlyphName] = self.controller.designSpaceManager.makePresentation(eachGlyphName, eachLoc)
            eachFont.injectKerningFrom(self.controller.designSpaceManager)
            self.longBoardFonts[frozenLocation] = eachFont

    def updateView(self, prevTxt, currentTxt):
        """
        DRAWING
            the updateView() works through a diff algorithm, to avoid refreshing the entire stack of layers
            if the user types one char at the time, we add only the newest one instead of re-drawing the entire view
            the same happens when a char is deleted, instead of cleaning everything, we only adjust the x position of the layers

            Hierarchy:
                - fontLayer
                    - glyphbox
                        - glyphpath

        """

        # if no location is displayed, we bail out
        if len(self.controller.displayedLocationsOnMultiLineView) == 0:
            return

        differ = Differ()
        charMap = self.controller.designSpaceManager.getNeutralFont().asFontParts().getCharacterMapping()
        prevGlyphNames = splitText(prevTxt, charMap)
        glyphNames = splitText(currentTxt, charMap)

        self.addGlyphs(glyphNames)

        fontLayerHgt = self.textView.height() / len(self.controller.displayedLocationsOnMultiLineView)
        with self.container.propertyGroup():
            for index, (frozenLocation, fontObj) in enumerate(self.longBoardFonts.items()):
                fontLayer = self.container.getSublayer(name=str(frozenLocation))
                scalingFactor = fontLayerHgt / fontObj.info.unitsPerEm

                xx = 0
                layerIndex = 0
                prevRemoved = False
                for difference in differ.compare(prevGlyphNames, glyphNames):
                    sign, name = difference[0], difference[2:]
                    glyphObj = fontObj[name]

                    # remove char
                    if sign == "-":
                        glyphBoxLayer = self.frozenLocToFontMerzLayer[frozenLocation][layerIndex]
                        fontLayer.removeSublayer(glyphBoxLayer)
                        del self.frozenLocToFontMerzLayer[frozenLocation][layerIndex]
                        prevRemoved = True

                    # insert char
                    elif sign == "+":
                        glyphBoxLayer = fontLayer.appendRectangleSublayer(
                            position=(xx, 0),
                            name=f"glyph box layer {name}",
                            size=(glyphObj.width, fontObj.info.unitsPerEm),
                            strokeColor=BLACK,
                            fillColor=TRANSPARENT,
                            strokeWidth=1,
                        )
                        glyphBoxLayer.addScaleTransformation(scalingFactor, name="scale")
                        self.frozenLocToFontMerzLayer[frozenLocation].insert(layerIndex, glyphBoxLayer)

                        glyphPathLayer = glyphBoxLayer.appendPathSublayer(name=f"glyph path {name}", fillColor=BLACK)
                        glyphPathLayer.setPath(glyphObj.getRepresentation("merz.CGPath"))
                        xx += glyphObj.width
                        layerIndex += 1 if not prevRemoved else 0
                        prevRemoved = False

                    # common char, we only adjust xx position if necessary
                    elif sign == " ":
                        glyphBoxLayer = self.frozenLocToFontMerzLayer[frozenLocation][layerIndex]
                        glyphBoxLayer.setPosition((xx, 0))
                        xx += glyphObj.width
                        layerIndex += 1
                        prevRemoved = False

                    else:
                        raise NotImplementedError(f"difflib issue! {name}")

                # applying kerning after the diffing
                if len(glyphNames) >= 2:
                    flatKerning = fontObj.getFlatKerning()
                    correction = 0
                    for lftIndex, rgtIndex in windowed(range(len(glyphNames)), 2):
                        pair = glyphNames[lftIndex], glyphNames[rgtIndex]
                        if pair in flatKerning:
                            correction += flatKerning[pair]
                        boxLayer = self.frozenLocToFontMerzLayer[frozenLocation][rgtIndex]
                        prevX, prevY = boxLayer.getPosition()
                        boxLayer.setPosition((prevX + correction, prevY))

    def displayedLocationsOnMultiLineViewDidChange(self, info):
        """
        A change on the displayed locations triggers a hard refresh
        """
        self.refreshButtonCallback(sender=None)

    def varModelDidChange(self, info):
        """
        A change on variation model triggers a hard refresh
        """
        self.refreshButtonCallback(sender=None)

    def glyphMutatorDidChange(self, info):
        """
        A change a glyph mutator invalidates the multi line view
        """
        self.invalidCache = True


if __name__ == "__main__":
    mc = MockController()
    MultiLineView.controller = mc
    registerRoboFontSubscriber(MultiLineView)
