#!/usr/bin/env python3

# ---------------------- #
# Experiment 7 – Roberto #
# ---------------------- #

# -- Modules -- #
from pprint import pprint
from pathlib import Path
import random
import os

from mojo.subscriber import Subscriber, WindowController
from mojo.subscriber import registerGlyphEditorSubscriber, unregisterGlyphEditorSubscriber
from mojo.roboFont import OpenWindow, AllFonts, OpenFont, RFont
import ezui
import ufoProcessor

from events import TOOL_KEY


# -- Objects, Functions, Procedures -- #
def lerp(a, b, f):
    return a + (b-a)*f

class LongBoardDesignSpaceProcessor(ufoProcessor.DesignSpaceProcessor):
    # this is responsible for 1 designspace document.
    # keep track of fonts opening and closing
    # build and cache mutators for all things
    # make presentation layers when a glypheditor asks for it
    # all the math will happen here

    def _instantiateFont(self, path):
        """ Return an instance of a font object with all the given subclasses"""
        for f in AllFonts():
            if f.path == path and f.path is not None:
                return f
        return RFont(path, showInterface=False)

    def loadFonts(self, reload_=False):
        print('loadFonts')
        # Load the fonts and find the default candidate based on the info flag
        # pay attention:
        #     1. different sources can reference different layers in the same ufo
        #     2. also: the same source can appear in different places in the designspace
        # so maybe the sourcedescriptor.name is not a good identifier
        if self._fontsLoaded and not reload_:
            return
        names = set()
        currentPaths = {f.path: f for f in AllFonts()}
        _fonts = {}
        for sourceDescriptor in self.sources:
            if sourceDescriptor.name not in self.fonts:
                pathOK = True
                if sourceDescriptor.path is not None:
                    if os.path.exists(sourceDescriptor.path):
                        if sourceDescriptor.path in currentPaths:
                            print(f'loadFonts font is open {sourceDescriptor.path}')
                            _fonts[sourceDescriptor.name] = currentPaths[sourceDescriptor.path]
                        else:
                            print(f'loadFonts font is not open {sourceDescriptor.path}')
                            _fonts[sourceDescriptor.name] = RFont(sourceDescriptor.path, showInterface=False)
                        names = names | set(_fonts[sourceDescriptor.name].keys())
                else:
                    pathOK = False
                if not pathOK:
                    _fonts[sourceDescriptor.name] = None
                    self.problems.append(f"can't load master from {sourceDescriptor.path}")
        self.glyphNames = list(names)
        self._fontsLoaded = True
        self.fonts = _fonts
        pprint(self.fonts)

    def _test_randomLocation(self):
        # pick a random location somewhere in the defined space
        loc = {}
        for axis in self.axes:
            loc[axis.name] = lerp(axis.minimum, axis.maximum, random.random())
        return loc

    def _test_LocationAtCenter(self):
        # make a test location at the center of the defined space
        loc = {}
        for axis in self.axes:
            loc[axis.name] = lerp(axis.minimum, axis.maximum, .5)
        return loc

    def makePresentation(self, viewGlyph, merzView, location, bend=True, changed=False):
        # draw something in the view of the glyph
        fc1 = (0, 0.4, 1, 0.05)
        fc2 = (0.3, 0.4, 0, 0.1)
        _drawAllMasters = False

        glyphMutator = self.getGlyphMutator(viewGlyph.name, fromCache=False)
        print('glyphMutator', id(glyphMutator), glyphMutator)
        if glyphMutator is None:
            # huh nothing works
            return
        glyphInstanceObject = glyphMutator.makeInstance(location, bend=bend)
        merzView.clearSublayers()

        # draw interpolation
        pathLayer = merzView.appendPathSublayer(
            fillColor=fc2,
            strokeColor=(1, 0.2, 0.2, 1),
            strokeWidth=.5,
        )

        pen = pathLayer.getPen({})
        glyphInstanceObject.draw(pen)

        if _drawAllMasters:
            # draw the other outlines
            for srcDescriptor in self.sources:
                for key, f in self.fonts.items():
                    if srcDescriptor.name == key:
                        print('srcDescriptor.layerName', srcDescriptor.layerName)
                        if srcDescriptor.layerName is not None:
                            continue
                        pathLayer = merzView.appendPathSublayer(
                            fillColor=fc1,
                            strokeColor=(fc1[0], fc1[1], fc1[2], 1),
                            strokeWidth=.5,
                        )
                        pen = pathLayer.getPen(f)
                        thisGlyph = f[viewGlyph.name]        # .getLayer(srcDescriptor.layerName)
                        thisGlyph.draw(pen)

    def isThisFontImportant(self, font):
        # called to check if the font with this path is relevant for this designspace
        for src in self.sources:
            if src.path == font.path:
                return True
        return False

    def getFont(self, path):
        for key, font in self.fonts.items():
            if font.path == path:
                return font
        return None


class LongBoardUI(WindowController):

    debug = True
    thickness = 5

    def build(self):

        segmentButtonItem = dict(
            identifier="segmentButtonToolbarItem",
            itemDescription=dict(
                type="SegmentButton",
                identifier="segmentButton",
                style="push",
                segmentDescriptions=[
                    dict(text = "Close"),
                    dict(text = "Save"),
                    dict(text = "Edit"),
                    # dict(text = "Variable Font"),
                    # dict(text = "Text"),
                    # dict(text = "Space"),
                ]
            )
        )

        itemDescriptions = [
            segmentButtonItem,
        ]

        toolbarDescription = dict(
            identifier="longBoardToolbar",
            itemDescriptions=itemDescriptions,
            # displayMode="image"
        )

        sourcesListTestItems = []
        for i in range(10):
            sourcesListTestItems.append(
                dict(
                    status="ok",
                    isDefault=False,
                    ufoName=f"Aaaa_{i}.ufo",
                    layerName=None,
                    debug='-',
                )
            )

        sourcesListDescription = dict(
            identifier="sourcesTable",
            type="Table",
            doubleClickCallback=self.sourcesTableDoubleClickCallback,
            columnDescriptions=[
                dict(
                    identifier="status",
                    title="",
                    width=50,
                ),
                dict(
                    identifier="isDefault",
                    title="",
                    width=50,
                ),
                dict(
                    identifier="ufoName",
                    title="UFO",
                    width=250,
                ),
                dict(
                    identifier="layerName",
                    title="Layer",
                    width=250,
                ),
                dict(
                    identifier="debug",
                    title="Debug",
                    width=400,
                ),
            ],
            items = sourcesListTestItems,
            width=1400,    # should be flex
            height=200
        )

        pane1Description = dict(
            type="Pane",
            identifier="sources_pane",
            text="Sources and Layers",
            contentDescription=dict(
                type="VerticalStack",
                contentDescriptions=[
                    sourcesListDescription
                ]
            )
        )

        mathTypeSegmentButton = dict(
            type="SegmentButton",
            identifier="mathTypeSegmentButton",
            segmentDescriptions=[
                dict(text = "MutatorMath"),
                dict(text = "VariableFont"),
            ]
        )

        currentLocationDescription = dict(
            identifier="currentLocationTable",
            type="Table",
            # 'axisName', 'designSpaceValue', 'userSpaceValue', 'normalisedValue', 'interactionDirection'
            columnDescriptions=[
                dict(
                    identifier="axisName",
                    title="Name",
                    width=100,
                ),
                dict(
                    identifier="designSpaceValue",
                    title="DesignSpace",
                    width=100,
                ),
                dict(
                    identifier="userSpaceValue",
                    title="UserSpace",
                    width=100,
                ),
                dict(
                    identifier="normalisedValue",
                    title="Normalised",
                    width=100,
                ),
                dict(
                    identifier="interactionDirection",
                    title="Interaction",
                    width=100,
                ),
            ],
            items = [],
            width=800,    # should be flex
            height=150
        )

        pane2Description = dict(
            type="Pane",
            identifier="preview_pane",
            text="Current Location",
            closed=True,
            contentDescription=dict(
                type="VerticalStack",
                contentDescriptions=[
                    currentLocationDescription,
                    mathTypeSegmentButton,
                ]
            )
        )

        allLocationsDescription = dict(
            identifier="allLocationsTable",
            type="Table",
            # 'locationName', 'locationFlavor'
            columnDescriptions=[
                dict(
                    identifier="locationname",
                    title="Name",
                    width=200,
                ),
                dict(
                    identifier="locationFlavor",
                    title="Flavor",
                    width=200,
                ),
            ],

            items = [],
            width=800,    # should be flex
            height=150
        )

        locationFlavorSegmentButton = dict(
            type="SegmentButton",
            identifier="locationFlavorSegmentButton",
            # style='any',
            style='one',
            segmentDescriptions=[
                dict(text = "Sources"),
                dict(text = "Supports"),
                dict(text = "Instances"),
                dict(text = "Interesting"),
                dict(text = "Open"),
            ]
        )

        pane3Description = dict(
            type="Pane",
            identifier="locations_pane",
            text="All Locations",
            closed=True,
            contentDescription=dict(
                type="VerticalStack",
                contentDescriptions=[
                    allLocationsDescription,
                    locationFlavorSegmentButton,
                ]
            )
        )
        windowContent = dict(
            type="VerticalStack",
            contentDescriptions=[
                pane1Description,
                pane2Description,
                pane3Description
            ]
        )
        windowDescription = dict(
            type="Window",
            # size=(800, "auto"),
            size=(1000, 500),
            maxSize=(1500, 1500),
            title="Longboard",
            toolbarDescription=toolbarDescription,
            contentDescription=windowContent
        )
        self.w = ezui.makeItem(
            windowDescription
        )
        self.w.open()

    def started(self):
        self.loadTestDocument()
        LongBoardPresenter.controller = self
        registerGlyphEditorSubscriber(LongBoardPresenter)

    def destroy(self):
        unregisterGlyphEditorSubscriber(LongBoardPresenter)
        LongBoardPresenter.controller = None

    def sourcesTableDoubleClickCallback(self, sender):
        # callback for double clicking on source list items
        # we expext to open these UFOs
        print('sourcesTableDoubleClickCallback', sender.getSelectedItems())
        openThese = []
        alreadyOpen = [f.path for f in AllFonts()]
        for selectedItem in sender.getSelectedItems():
            if selectedItem['status'] == "closed":
                candidate = selectedItem['ufoPath']
                if candidate not in openThese and candidate not in alreadyOpen:
                    openThese.append(selectedItem['ufoPath'])
        # now find the paths
        for eachPath in openThese:
            OpenFont(eachPath)
        #self.updateSources()

    def loadTestDocument(self):
        print('loadTestDocument')
        # temporary
        self.vendor = LongBoardDesignSpaceProcessor()
        testDocPath = Path.cwd() / "test" / "MutatorSans.designspace"
        print('testDocPath', testDocPath, os.path.exists(testDocPath))
        # pathField = self.w.findItem("documentPathText")
        # pathField.set("testDocPath")
        # self.w.set(dict(documentPathText="1234"))

        self.vendor.useVarlib = True
        self.vendor.read(testDocPath)
        self.vendor.loadFonts(reload_=True)
        self.currentLocation = self.vendor.newDefaultLocation(bend=True)
        self.currentLocation = self.vendor._test_LocationAtCenter()
        print('self.currentLocation', self.currentLocation)
        self.updateCurrentLocation()
        self.updateSources()

    def updateCurrentLocation(self):
        # update the UI presentation of the current location
        # 'axisName', 'designSpaceValue', 'userSpaceValue', 'normalisedValue', 'interactionDirection'
        locItems = []
        locTable = self.w.findItem('currentLocationTable')

        for name, value in self.currentLocation.items():
            locItems.append(
                dict(
                    axisName = name,
                    designSpaceValue = value,
                    userSpaceValue = 'x',
                    normalisedValue = 'x',
                    interactionDirection = '111'
                )
            )
        locTable.set(locItems)

    def updateSources(self, theseFontsAreClosing=None, theseFontsAreOpening=None):
        # update the sources and layers list whenever we have to.
        # look at skateboard.py for reference // document_checkFonts()
        if theseFontsAreClosing is None:
            theseFontsAreClosing = []
        if theseFontsAreOpening is None:
            theseFontsAreOpening = []
        # let's make sure this needs to happen here.
        self.vendor.loadFonts(reload_=True)

        srcTable = self.w.findItem('sourcesTable')
        srcItems = []
        openPaths = [f.path for f in AllFonts()]
        for srcDescriptor in self.vendor.sources:
            if srcDescriptor.layerName is not None:
                layerName = srcDescriptor.layerName
            else:
                layerName = ""
            if srcDescriptor.path in openPaths and srcDescriptor.path not in theseFontsAreClosing:
                status = "open"
            else:
                if not os.path.exists(srcDescriptor.path):
                    status = "missing"
                else:
                    status = "closed"
            font = self.vendor.getFont(srcDescriptor.path)
            if font is None:
                debugNotice = "None"
            else:
                debugNotice = f"{id(font)} {font.__class__.__name__}"
            srcItems.append(
                dict(
                    status=status,
                    isDefault=False,
                    ufoName=f"{os.path.basename(srcDescriptor.path)}",
                    layerName=f"{layerName}",
                    ufoPath=srcDescriptor.path,    # can we add arbitrary data?
                    debug=debugNotice
                )
            )
        srcTable.set(srcItems)

class LongBoardPresenter(Subscriber):

    debug = True
    controller = None

    def build(self):
        # addObserver(self, 'listenForLongboardActive', 'longboard.is.not.active')
        glyphEditor = self.getGlyphEditor()
        self.glyph = glyphEditor.getGlyph()
        container = glyphEditor.extensionContainer(f"{TOOL_KEY}.test", location='background')

        # a layer for the glyph and the baseline
        self.longBoardPreviewLayer = container.appendBaseSublayer(
            size=(self.glyph.width, self.glyph.font.info.unitsPerEm),
            backgroundColor=(1, 1, 1, 1)
        )
        # do we need to request an update here as well?
        # postEvent('longboard.requestUpdate', layer=self.longBoardPreviewLayer)

    def clearPresentation(self):
        glyphEditor = self.getGlyphEditor()
        container = glyphEditor.extensionContainer(f"{TOOL_KEY}.test", location='background')
        container.clearSublayers()

    def listenForLongboardActive(self, info):
        # listen if we're active or not
        if info.get('notificationName', None) == 'longboard.is.not.active':
            self.clearPresentation()

    def glyphDidChangeMetrics(self, info):
        glyph = info['glyph']
        # postEvent('longboard.requestUpdate', layer=self.longBoardPreviewLayer, viewGlyph=g)

    def glyphDidChangeOutline(self, info):
        glyph = info['glyph']
        # postEvent('longboard.requestUpdate', layer=self.longBoardPreviewLayer, viewGlyph=g, changed=True)

    def glyphDidChangeComponents(self, info):
        # check all the component bits
        glyph = info['glyph']
        # postEvent('longboard.requestUpdate', layer=self.longBoardPreviewLayer, viewGlyph=g, changed=True)

    # glyphDidChangeComponents
    # https://robofont.com/documentation/reference/api/mojo/mojo-subscriber/

    def roboFontDidSwitchCurrentGlyph(self, info):
        glyph = info['glyph']
        # postEvent('longboard.requestUpdate', layer=self.longBoardPreviewLayer, viewGlyph=g, changed=False)

    def glyphEditorWillClose(self, info):
        print('glyphEditorWillClose')
        # removeObserver(self, 'longboard.is.not.active')


# -- Instructions -- #
if __name__ == '__main__':
    OpenWindow(LongBoardUI)
