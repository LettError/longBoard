#!/usr/bin/env python3

# --------- #
# LONGBOARD #
# --------- #

# -- Modules -- #
from pathlib import Path
from os.path import basename
from random import random

from AppKit import NSImage
from mojo.subscriber import WindowController, Subscriber
from mojo.subscriber import registerRoboFontSubscriber, unregisterRoboFontSubscriber
from mojo.subscriber import registerGlyphEditorSubscriber, unregisterGlyphEditorSubscriber
from mojo.subscriber import registerCurrentGlyphSubscriber, unregisterCurrentGlyphSubscriber

from mojo.roboFont import OpenWindow, OpenFont
from mojo.events import BaseEventTool, uninstallTool, installTool, postEvent
from vanilla import FloatingWindow, Window, RadioGroup
from merz import MerzView

from designSpaceManager import DesignSpaceManager
from multiLineView import MultiLineView
from customEvents import TOOL_KEY, DEBUG_MODE

"""
Notes:
- the broken mutator preview only works with mutatorMath

"""


# -- Constants -- #
BLACK = 0, 0, 0, 1

# -- Objects -- #
def randomizeLayerColors(layer):
    with layer.propertyGroup():
        rgb = [random(), random(), 0]
        layer.setFillColor(tuple(rgb + [0.1]))
        layer.setStrokeColor(tuple(rgb + [0.5]))


class Controller(WindowController):

    """
    The controller own the main LongBoard UI window
    and every object of the tool own an attribute self.controller pointing
    to this object

    In this way every part of the tool can access to other objects, for example
    if the SpaceWindow needs a make a preview using a mutator, it can access the
    DesignSpaceManager in this way
    self.controller.designSpaceManager.makePresentation()

    """

    debug = DEBUG_MODE
    _currentDesignSpaceLocation = None

    def build(self):
        self.w = FloatingWindow((300, 80), "Controller")
        self.w.varModelRadio = RadioGroup((10, 10, -10, 40),
                                          ["varLib", "mutatorMath"],
                                          callback=self.varModelRadioCallback)
        # varLib is then selected in loadTestDocument()
        self.w.varModelRadio.set(0)
        self.w.open()

    def started(self):
        self.loadTestDocument()

        NavigatorTool.controller = self
        self.navigator = NavigatorTool()
        installTool(self.navigator)

        SpaceWindow.controller = self
        registerRoboFontSubscriber(SpaceWindow)

        MultiLineView.controller = self
        registerRoboFontSubscriber(MultiLineView)

        GlyphEditorSubscriber.controller = self
        registerGlyphEditorSubscriber(GlyphEditorSubscriber)

        CurrentGlyphSubscriber.controller = self
        registerCurrentGlyphSubscriber(CurrentGlyphSubscriber)

        FontManager.controller = self
        registerRoboFontSubscriber(FontManager)

    def destroy(self):
        postEvent(f"{TOOL_KEY}.controllerWillClose")

        NavigatorTool.controller = None
        uninstallTool(self.navigator)

        SpaceWindow.controller = None
        unregisterRoboFontSubscriber(SpaceWindow)

        MultiLineView.controller = None
        unregisterRoboFontSubscriber(MultiLineView)

        GlyphEditorSubscriber.controller = None
        unregisterGlyphEditorSubscriber(GlyphEditorSubscriber)

        CurrentGlyphSubscriber.controller = None
        unregisterCurrentGlyphSubscriber(CurrentGlyphSubscriber)

        FontManager.controller = None
        unregisterRoboFontSubscriber(FontManager)

    @property
    def currentDesignSpaceLocation(self):
        return self._currentDesignSpaceLocation

    @currentDesignSpaceLocation.setter
    def currentDesignSpaceLocation(self, value):
        self._currentDesignSpaceLocation = value
        postEvent(f"{TOOL_KEY}.currentDesignSpaceLocationDidChange")

    # controls callbacks
    def varModelRadioCallback(self, sender):
        self.designSpaceManager.useVarlib = True if sender.get() == 'varLib' else False
        self.designSpaceManager.clearCache()
        postEvent(f"{TOOL_KEY}.varModelDidChange")

    # temp
    def loadTestDocument(self):
        print('loadTestDocument')
        self.designSpaceManager = DesignSpaceManager()
        testDocPath = Path.cwd().parent / "resources" / "MutatorSans.designspace"
        self.designSpaceManager.useVarlib = True
        self.designSpaceManager.read(testDocPath)
        self.designSpaceManager.loadFonts(reload_=True)
        self._currentDesignSpaceLocation = self.designSpaceManager.newDefaultLocation(bend=True)
        self._currentDesignSpaceLocation = self.designSpaceManager._test_LocationAtCenter()
        print('self.currentDesignSpaceLocation', self.currentDesignSpaceLocation)


class CurrentGlyphSubscriber(Subscriber):

    """
    Tracks edits to glyphs, even if not opened in the glyph editor:
    - space center
    - kerning
    - scripting window

    It is used to invalidate the cache of mutator with edited sources
    """

    debug = DEBUG_MODE
    controller = None

    currentGlyphDidChangeMetricsDelay = 0.2
    def currentGlyphDidChangeMetrics(self, info):
        print('currentGlyphDidChangeMetrics')
        glyphName = info['glyph'].name
        self.controller.designSpaceManager.invalidateGlyphCache(glyphName)
        self.invalidateCacheWhereGlyphIsUsedAsComponent(glyphName)
        postEvent(f"{TOOL_KEY}.glyphMutatorDidChange", glyphName=glyphName)

    currentGlyphDidChangeContoursDelay = 0.2
    def currentGlyphDidChangeContours(self, info):
        print('currentGlyphDidChangeContours')
        glyphObj = info['glyph']
        self.controller.designSpaceManager.invalidateGlyphCache(glyphObj.name)
        self.invalidateCacheWhereGlyphIsUsedAsComponent(glyphObj)
        postEvent(f"{TOOL_KEY}.glyphMutatorDidChange", glyphName=glyphObj.name)

    def invalidateCacheWhereGlyphIsUsedAsComponent(self, glyph):
        mapping = glyph.font.getReverseComponentMapping()
        if glyph.name in mapping:
            for componentName in mapping[glyph.name]:
                self.controller.designSpaceManager.invalidateGlyphCache(componentName)


class GlyphEditorSubscriber(Subscriber):

    """
    This subscriber takes care of the preview in the glyph editor

    """

    debug = DEBUG_MODE
    controller = None

    def build(self):
        glyphEditor = self.getGlyphEditor()

        self.container = glyphEditor.extensionContainer(
            identifier=TOOL_KEY,
            location='background',
            clear=True
        )

        self.previewLayer = self.container.appendPathSublayer(
            strokeWidth=0.5,
        )
        randomizeLayerColors(layer=self.previewLayer)

        self.sourcesLayer = self.container.appendBaseSublayer()

    def started(self):
        self.updatePreview()

    def destroy(self):
        self.container.clearSublayers()

    def updatePreview(self):
        glyphName = self.getGlyphEditor().getGlyph().name
        location = self.controller.currentDesignSpaceLocation
        glyphObj = self.controller.designSpaceManager.makePresentation(glyphName, location)
        print(f"glyphObj: {glyphObj}")

        # working mutator
        if glyphObj is not None:
            print("working mutator!")
            self.sourcesLayer.clearSublayers()
            randomizeLayerColors(layer=self.previewLayer)
            pen = self.previewLayer.getPen()
            glyphObj.draw(pen)

        # broken mutator
        else:
            print("broken mutator!")
            self.sourcesLayer.clearSublayers()
            self.previewLayer.clearSublayers()

            sources = self.controller.designSpaceManager.collectMastersForGlyph(glyphName, decomposeComponents=True)

            xx = 0
            for location, mathGlyph, sourceAttributes in sources:
                glyphLayer = self.sourcesLayer.appendPathSublayer(
                    strokeWidth=1
                )

                randomizeLayerColors(layer=glyphLayer)
                glyphLayer.addTranslationTransformation(value=(0, -250), name="moveToBottom")
                glyphLayer.addScaleTransformation(value=(0.25, 0.25), name="scaleDownToThumbnails")
                glyphLayer.addTranslationTransformation(value=(xx, 0), name="advanceWidth")

                pen = glyphLayer.getPen()
                mathGlyph.draw(pen)
                xx += mathGlyph.width

    def varModelDidChange(self, info):
        print('updating preview because varModel did change')
        self.updatePreview()

    def glyphMutatorDidChange(self, info):
        print(f'listening to this: {info["glyphName"]}')
        if info['glyphName'] == self.getGlyphEditor().getGlyph().name:
            self.updatePreview()

    def currentDesignSpaceLocationDidChange(self, info):
        self.updatePreview()


class NavigatorTool(BaseEventTool):

    """
    This tool can update the design space location displayed in preview by LongBoard
    """

    def setup(self):
        print('navigator tool setup')

    def getToolbarIcon(self):
        return NSImage.imageWithSystemSymbolName_accessibilityDescription_("safari.fill", None)

    def getToolbarTip(self):
        return "LongBoard"

    def mouseDown(self, point, click):
        location = self.controller.designSpaceManager._test_randomLocation()
        self.controller.currentDesignSpaceLocation = location


class SpaceWindow(Subscriber, WindowController):

    """
    This window controller own a separate window where the geometry of the design space is displayed
    and receives a notification when
        - the main controller closes, so it can close its own window
        - when the displyed design space location changes
    """

    debug = DEBUG_MODE
    controller = None
    glyphName = 'C'

    def build(self):
        self.w = Window((500, 500), "Space Window")
        self.w.view = MerzView(
            (0, 0, 0, 0),
            backgroundColor=(1, 1, 1, 1),
            delegate=self
        )
        self.container = self.w.view.getMerzContainer()
        self.designSpaceLayer = self.container.appendBaseSublayer()
        self.currentDesignSpaceLocationLayer = self.container.appendPathSublayer()
        self.w.open()

    def acceptsFirstResponder(self, sender):
        return True

    def started(self):
        self.designSpaceLayer.appendRectangleSublayer(
            position=(50, 50),
            size=(400, 100),
            fillColor=(1, 0, 0, 0.1),
            strokeColor=(1, 0, 0, 1),
            strokeWidth=2,
        )
        self.updateCurrentLocationLayer()

    def destroy(self):
        self.container.clearSublayers()

    def controllerWillClose(self, info):
        # considering that the controller object does not have direct access to the subordinate
        # object window, we need to use a custom event to close the SpaceWindow vanilla window
        # otherwise it will stay open after longboard has been closed by the user
        self.w.close()

    def mouseDragged(self, view, event):
        pass

    def mouseDown(self, view, event):
        print(f"space window mouseDown: {event}")
        location = self.controller.designSpaceManager._test_randomLocation()
        self.controller.currentDesignSpaceLocation = location

    def updateCurrentLocationLayer(self):
        print('updateCurrentLocationLayer')
        glyphObj = self.controller.designSpaceManager.makePresentation(self.glyphName, self.controller.currentDesignSpaceLocation)
        pen = self.currentDesignSpaceLocationLayer.getPen()
        glyphObj.draw(pen)

    def currentDesignSpaceLocationDidChange(self, info):
        self.updateCurrentLocationLayer()


class FontManager(Subscriber):

    """
    This subscriber keeps track of opened/closed fonts
    and takes care to update the self.fonts dictionary of the design space manager
    with the right references

    NOT WORKING PROPERLY YET!
    """

    debug = DEBUG_MODE
    soonClosingFontPath = None

    def printStatus(self):
        print('----'*4)
        for path, eachFont in self.controller.designSpaceManager.fonts.items():
            print(f'{basename(eachFont.path)}; glyphs amount: {len(eachFont)}; has interface? {eachFont.hasInterface()}')
        print('----'*4)

    def fontDocumentDidOpen(self, info):
        print('fontDocumentDidOpen!')
        # substitute the font without interface with the font with interface
        fontObj = info['font']
        self.controller.designSpaceManager.fonts[fontObj.path] = fontObj
        self.printStatus()

    def fontDocumentWillClose(self, info):
        # catching this here, because once it's closed we will not be able to access it
        # from the info notification dictionary
        self.soonClosingFontPath = info['font'].path

    def fontDocumentDidClose(self, info):
        print('fontDocumentDidClose!')
        # substitute the font with interface (closing down) with a freshly opened font without interface
        # this will make sure that if the user did not save the last edits, the font we're using
        # will reflect the actual state of the file saved on disk
        self.controller.designSpaceManager.fonts[self.soonClosingFontPath] = OpenFont(self.soonClosingFontPath, showInterface=False)
        self.soonClosingFontPath = None
        self.printStatus()


# -- Instructions -- #
if __name__ == '__main__':
    OpenWindow(Controller)
