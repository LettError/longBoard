#!/usr/bin/env python3

# -- #
# 🛹 #
# -- #

# -- Modules -- #
from pathlib import Path

from AppKit import NSImage
from mojo.subscriber import WindowController, Subscriber
from mojo.subscriber import registerRoboFontSubscriber, unregisterRoboFontSubscriber
from mojo.subscriber import registerGlyphEditorSubscriber, unregisterGlyphEditorSubscriber

from mojo.roboFont import OpenWindow
from mojo.events import BaseEventTool, uninstallTool, installTool, postEvent
from vanilla import FloatingWindow, Window
from merz import MerzView

from designSpaceManager import DesignSpaceManager
from multiLineView import MultiLineView
from customEvents import TOOL_KEY, DEBUG_MODE


# -- Constants -- #
BLACK = 0, 0, 0, 1

# -- Objects -- #
class Controller(WindowController):

    debug = DEBUG_MODE
    _currentDesignSpaceLocation = None

    def build(self):
        self.w = FloatingWindow((200, 40), "Controller")
        self.w.open()

    def started(self):
        self.loadTestDocument()

        NavigatorTool.controller = self
        self.navigator = NavigatorTool()
        installTool(self.navigator)

        SpaceWindow.controller = self
        registerRoboFontSubscriber(SpaceWindow)

        MultiLineView.controller = self
        self.multiLineWindow = MultiLineView()

        GlyphEditorSubscriber.controller = self
        registerGlyphEditorSubscriber(GlyphEditorSubscriber)

    def destroy(self):
        GlyphEditorSubscriber.controller = None
        unregisterGlyphEditorSubscriber(GlyphEditorSubscriber)

        NavigatorTool.controller = None
        uninstallTool(self.navigator)

        SpaceWindow.controller = None
        unregisterRoboFontSubscriber(SpaceWindow)

        MultiLineView.controller = None
        self.multiLineWindow.destroy()

    @property
    def currentDesignSpaceLocation(self):
        return self._currentDesignSpaceLocation

    @currentDesignSpaceLocation.setter
    def currentDesignSpaceLocation(self, value):
        self._currentDesignSpaceLocation = value
        postEvent(f"{TOOL_KEY}.currentDesignSpaceLocationDidChange")

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


class GlyphEditorSubscriber(Subscriber):

    debug = DEBUG_MODE
    controller = None

    def build(self):
        glyphEditor = self.getGlyphEditor()

        container = glyphEditor.extensionContainer(
            identifier=TOOL_KEY,
            location='background',
            clear=True
        )

        self.drawingLayer = container.appendPathSublayer(
            fillColor=(1, 0, 0, 0.1),
            strokeColor=(1, 0, 0, 0.5),
            strokeWidth=0.5,
        )

    def started(self):
        self.updatePreview()

    def destroy(self):
        self.drawingLayer.clearSublayers()

    def updatePreview(self):
        glyphName = self.getGlyphEditor().getGlyph().name
        location = self.controller.currentDesignSpaceLocation
        glyphObj = self.controller.designSpaceManager.makePresentation(glyphName, location)
        pen = self.drawingLayer.getPen()
        glyphObj.draw(pen)

    def currentDesignSpaceLocationDidChange(self, info):
        self.updatePreview()


class NavigatorTool(BaseEventTool):

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

    debug = DEBUG_MODE
    controller = None

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

    def mouseDragged(self, view, event):
        pass

    def mouseDown(self, view, event):
        print(f"space window mouseDown: {event}")
        location = self.controller.designSpaceManager._test_randomLocation()
        self.controller.currentDesignSpaceLocation = location

    def updateCurrentLocationLayer(self):
        glyphObj = self.controller.designSpaceManager.makePresentation('A', self.controller.currentDesignSpaceLocation)
        pen = self.currentDesignSpaceLocationLayer.getPen()
        glyphObj.draw(pen)

    def currentDesignSpaceLocationDidChange(self, info):
        self.updateCurrentLocationLayer()


# -- Instructions -- #
if __name__ == '__main__':
    OpenWindow(Controller)
