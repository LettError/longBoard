#!/usr/bin/env python3

# ----------------------- #
# Coalescing + User Input #
# ----------------------- #

# -- Modules -- #
from datetime import datetime
from mojo.subscriber import registerCurrentFontSubscriber, Subscriber, WindowController
from mojo.subscriber import registerSubscriberEvent, getRegisteredSubscriberEvents
from mojo.events import postEvent
from vanilla import Window, Button, VerticalStackView
from merz import MerzView
from mojo.roboFont import CurrentGlyph


# -- Constants -- #
TOOL_KEY = 'com.coalescer.myTool'
DEBUG_MODE = True

# -- Objects, Functions, Procedures -- #
class Coalescer(Subscriber, WindowController):

    debug = DEBUG_MODE

    def build(self):
        self.w = Window((600, 1000), "Window Demo", minSize=(200, 200))
        self.merzView = MerzView(posSize="auto")
        self.refreshButton = Button((10, 10, -10, 20), "Refresh", callback=self.refreshButtonCallback)

        self.w.stack = VerticalStackView(
            (0, 0, 0, 0),
            views=[
                dict(view=self.merzView),
                dict(view=self.refreshButton)
            ],
            spacing=10,
            edgeInsets=(10, 10, 10, 10)
        )

        self.w.open()

    def started(self):
        self.container = self.merzView.getMerzContainer()
        self.glyphLayer = self.container.appendPathSublayer()
        self.updateView()

    def updateView(self):
        if self.glyphLayer.getFilter(name="glyphLayerBlur"):
            self.glyphLayer.removeFilter(name="glyphLayerBlur")
        self.glyphLayer.setPath(CurrentGlyph().getRepresentation("merz.CGPath"))

    def refreshButtonCallback(self, sender):
        print("manualRefresh", datetime.now())
        self.updateView()

    currentFontGlyphDidChangeDelay = 0.2
    def currentFontGlyphDidChange(self, info):
        if not self.glyphLayer.getFilter(name="glyphLayerBlur"):
            self.glyphLayer.appendFilter(
                dict(name="glyphLayerBlur",
                     filterType="gaussianBlur",
                     radius=20)
            )
        print('triggering an automatic refresh...', datetime.now())
        postEvent(f"{TOOL_KEY}.automaticRefresh")

    def automaticRefresh(self, info):
        print("automaticRefresh", datetime.now())
        self.updateView()


# -- Instructions -- #
if __name__ == '__main__':
    eventName = f"{TOOL_KEY}.automaticRefresh"
    if eventName not in getRegisteredSubscriberEvents():
        registerSubscriberEvent(
            subscriberEventName=eventName,
            methodName="automaticRefresh",
            lowLevelEventNames=[eventName],
            dispatcher="roboFont",
            delay=5,
            debug=DEBUG_MODE
        )

    registerCurrentFontSubscriber(Coalescer)
