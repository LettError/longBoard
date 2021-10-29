from pprint import pprint
import os
import random
import time

from mojo.subscriber import Subscriber, WindowController
from mojo.subscriber import registerRoboFontSubscriber, unregisterRoboFontSubscriber, registerGlyphEditorSubscriber
from mojo.events import addObserver, postEvent, removeObserver

import vanilla
import merz

import ufoProcessor
import ufoProcessor.varModels
from ufoProcessor.emptyPen import checkGlyphIsEmpty


import ezui


def ip(a, b, f):
    return a+f*(b-a)
    
# subscriber
# https://robofont.com/documentation/reference/api/mojo/mojo-subscriber/?highlight=roboFontDidChangeScreen

# windowcontroller
# https://doc.robofont.com/documentation/topics/window-controller/?highlight=WindowController


class LongBoardDesignSpaceProcessor(ufoProcessor.DesignSpaceProcessor):
    # this is responsible for 1 designspace document. 
    # keep track of fonts opening and closing
    # build and cache mutators for all things
    # make presentation layers when a glypheditor asks for it
    # all the math will happen here
    
    def _test_randomLocation(self):
        # pick a random location somewhere in the defined space
        loc = {}
        for axis in self.axes:
            loc[axis.name] = ip(axis.minimum, axis.maximum, random.random())
        return loc
    
    def _test_LocationAtCenter(self):
        # make a test location at the center of the defined space
        loc = {}
        for axis in self.axes:
            loc[axis.name] = ip(axis.minimum, axis.maximum, .5)
        return loc
        
        
    def makePresentation(self, viewGlyph, merzView, location, bend=True, changed=False):
        print(f'{time.time()} makePresentation')
        print(self.toolLog)
        # draw something in the view of the glyph
        #print('drawing', time.time(), glyph)    #, merzView)
        fc1 = (0,0.4,1,0.05)
        #location = self._test_LocationAtCenter()
        #print('makePresentation', changed)
        glyphMutator = self.getGlyphMutator(viewGlyph.name, fromCache= False)
        glyphInstanceObject = glyphMutator.makeInstance(location, bend=bend)
        #print('glyphInstanceObject', glyphInstanceObject)
        merzView.clearSublayers()
        
        # draw interpolation
        pathLayer = merzView.appendPathSublayer(
            fillColor=None,
            strokeColor=(1,0.2,0.2,1),
            strokeWidth=1,
            #lineDash=(30, 30)
            )
            
        pen = pathLayer.getPen({})
        glyphInstanceObject.draw(pen)
        
        # draw the other outlines
        
        for srcDescriptor in self.sources:
            for key, f in self.fonts.items():
                if srcDescriptor.name == key:
                    pathLayer = merzView.appendPathSublayer(
                        fillColor=fc1,
                        )
                    pen = pathLayer.getPen(f)
                    thisGlyph = f[viewGlyph.name]        #.getLayer(srcDescriptor.layerName)
                    thisGlyph.draw(pen)
        
        # draw the viewglyph
        #pathLayer = merzView.appendPathSublayer(
        #    #fillColor=(1,0.4,0,0.2),
        #    #strokeColor=None,
        #    fillColor=fc1,)
        #pen = pathLayer.getPen(f)
        #viewGlyph.draw(pen)
        
    def isThisFontImportant(self, font):
        # called to check if the font with this path is relevant for this designspace
        for src in self.sources:
            if src.path == font.path:
                return True
        return False
        
        
        
        
class LongBoardUI(Subscriber, WindowController):
    # this is the window with the UI
    debug = True

    def build(self):
        self.vendor = None
        self.currentLocation = None
        # assuming we're only going to use the Processor and Presenter when we have the UI open
        # we should register them here, no?
        registerGlyphEditorSubscriber(LongBoardPresenter)    # this here?
        addObserver(self, 'listenForUpdateRequests', 'longboard.requestUpdate')

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
                    #dict(text = "Variable Font"),
                    #dict(text = "Text"),
                    #dict(text = "Space"),
                ]
            )
        )
        
        itemDescriptions = [
            segmentButtonItem,
        ]
        
        toolbarDescription = dict(
            identifier="longBoardToolbar",
            itemDescriptions=itemDescriptions,
            #displayMode="image"
        )
        
        sourcesListTestItems =[]
        for i in range(10):
            sourcesListTestItems.append(
                    dict(
                        status="ok",
                        isDefault=False,
                        ufoName=f"Aaaa_{i}.ufo",
                        layerName=None
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
                    width=300,
                ),
                dict(
                    identifier="layerName",
                    title="Layer",
                    width=300,
                ),
                ],
            items = sourcesListTestItems,
            width=800,    # should be flex
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
                #style='any',
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
            #size=(800, "auto"),
            size=(700, 500),
            maxSize=(1000, 1000),
            title="Longboard",
            toolbarDescription=toolbarDescription      ,      
            contentDescription=windowContent
        )
        self.w = ezui.makeItem(
            windowDescription
        )

    def started(self):
        self.w.open()
        postEvent('longboard.is.active')
        print(f'LongBoardUI {id(self)} opened')
        self.loadTestDocument()

    def stackCallback(self, sender):
        print(sender.get())


    def sourcesTableDoubleClickCallback(self, sender):
        # callback for double clicking on source list items
        # we expext to open these UFOs
        print('sourcesTableDoubleClickCallback', sender.getSelectedItems())
        openThese = []
        bringTheseToFront = []
        for selectedItem in sender.getSelectedItems():
            if selectedItem['status'] == "closed":
                if selectedItem['ufoPath'] not in openThese:
                    openThese.append(selectedItem['ufoPath'])
        # now find the paths
        [OpenFont(f) for f in openThese]
        
        
    def updateCurrentLocation(self):
        # update the UI presentation of the current location
        # 'axisName', 'designSpaceValue', 'userSpaceValue', 'normalisedValue', 'interactionDirection'
        locItems = []
        locTable = self.w.findItem('currentLocationTable')

        for name, value in self.currentLocation.items():
            locItems.append(dict(
                axisName = name,
                designSpaceValue = value,
                userSpaceValue = 'x',
                normalisedValue = 'x',
                interactionDirection = '111'
                )
            )
        locTable.set(locItems)
            
    def updateSources(self,closeTheseFonts=None):
        # update the sources and layers list whenever we have to. 
        if closeTheseFonts is None:
            closeTheseFonts = []
        self.vendor.loadFonts(reload=True)
        
        srcTable = self.w.findItem('sourcesTable')
        srcItems =[]
        openPaths = [f.path for f in AllFonts()]
        for srcDescriptor in self.vendor.sources:
            print('updateSources', srcDescriptor)
            if srcDescriptor.layerName is not None:
                layerName = srcDescriptor.layerName
            else:
                layerName = ""
            if srcDescriptor.path in openPaths and srcDescriptor.path not in closeTheseFonts:
                status = "open"
            else:
                if not os.path.exists(srcDescriptor.path):
                    status = "missing"
                else:
                    status = "closed"
            srcItems.append(
                    dict(
                        status=status,
                        isDefault=False,
                        ufoName=f"{os.path.basename(srcDescriptor.path)}",
                        layerName=f"{layerName}",
                        ufoPath=srcDescriptor.path,    # can we add arbitrary data?
                    )
                )
        srcTable.set(srcItems)
            
    def loadTestDocument(self):
        print('loadTestDocument')
        # temporary
        self.vendor = LongBoardDesignSpaceProcessor()
        path = os.getcwd()
        testDocPath = os.path.join(os.getcwd(), "test", "MutatorSans.designspace")
        print('testDocPath', testDocPath, os.path.exists(testDocPath))
        #pathField = self.w.findItem("documentPathText")
        #pathField.set("testDocPath")
        #self.w.set(dict(documentPathText="1234"))

        self.vendor.useVarlib = True
        self.vendor.read(testDocPath)
        self.vendor.loadFonts(reload=False)
        self.currentLocation = self.vendor.newDefaultLocation(bend=True)
        self.currentLocation = self.vendor._test_LocationAtCenter()
        print('self.currentLocation', self.currentLocation)
        self.updateCurrentLocation()
        self.updateSources()

    def listenForUpdateRequests(self, info):
        #print('LongBoardUI.listenForUpdateRequests ping')
        viewGlyph = info.get('viewGlyph')
        changed = info.get('changed', True)
        
        if viewGlyph is not None and self.vendor is not None:
            self.vendor.makePresentation(viewGlyph, info['layer'], self.currentLocation, changed=changed)
        
    def roboFontDidBecomeActive(self, info):
        # refresh documents?
        print(f'LongBoardUI {id(self)} roboFontDidBecomeActive')
        print('info', info)
        self.updateSources()
    
    def destroy(self):
        print(f'LongBoardUI {id(self)} closing')
        removeObserver(self, 'longboard.requestUpdate')

    def fontDocumentWillOpen(self, info):
        """
            LongBoardUI 4624339216 responds to fontDocumentWillOpen
            {'font': <RFont 'MutatorMathTest LightWide' path='/Users/erik/code/LongBoard/test/MutatorSansLightWide.ufo' at 5265509328>,
             'iterations': [{'font': <RFont 'MutatorMathTest LightWide' path='/Users/erik/code/LongBoard/test/MutatorSansLightWide.ufo' at 5265509328>}],
             'lowLevelEvents': [{'font': <RFont 'MutatorMathTest LightWide' path='/Users/erik/code/LongBoard/test/MutatorSansLightWide.ufo' at 5265509328>,
                                 'glyph': None,
                                 'notificationName': 'fontWillOpen',
                                 'tool': <lib.eventTools.editingTool.EditingTool object at 0x116418550>,
                                 'view': None}],
             'subscriberEventName': 'fontDocumentWillOpen'}
        """
        print(f"LongBoardUI {id(self)} responds to fontDocumentWillOpen")
        if self.vendor.isThisFontImportant(info['font']):
            self.updateSources()
            print("relevant font opening")
    
    def fontDocumentDidChangeExternally(self, info):
        print(f"LongBoardUI {id(self)} responds to fontDocumentDidChangeExternally")
        if self.vendor.isThisFontImportant(info['font']):
            self.updateSources()
            print("relevant font changed externally")
    
    def fontDocumentWillClose(self, info):
        print(f"LongBoardUI {id(self)} responds to fontDocumentWillClose")
        print('info', info)
        if self.vendor.isThisFontImportant(info['font']):
            self.updateSources(closeTheseFonts=info['font'].path)
        
        
        

class LongBoardPresenter(Subscriber):
    # this is the thing that will run in the glypheditor.
    # respond to relevant change events in glyph geometry
    # request new presentations when we have changes
    # don't do any math here, just order
    debug = True
    glyphEditGlyphDidChangeOutlineDelay = 0
    
    def build(self):
        addObserver(self, 'listenForLongboardActive', 'longboard.is.not.active')
        self.glyph = CurrentGlyph()    
        
        glyphEditor = self.getGlyphEditor()
        container = glyphEditor.extensionContainer("com.letterror.longboard.test", location='background')

        # a layer for the glyph and the baseline
        self.longBoardPreviewLayer = container.appendBaseSublayer(
            size=(self.glyph.width, self.glyph.font.info.unitsPerEm),
            backgroundColor=(1, 1, 1, 1)
        )
        # do we need to request an update here as well?
        postEvent('longboard.requestUpdate', layer=self.longBoardPreviewLayer)
    
    def clearPresentation(self):
        glyphEditor = self.getGlyphEditor()
        container = glyphEditor.extensionContainer("com.letterror.longboard.test", location='background')
        container.clearSublayers()

    def listenForLongboardActive(self, info):
        # listen if we're active or not
        if info.get('notificationName', None) == 'longboard.is.not.active':
            self.clearPresentation()
        
    def glyphDidChangeMetrics(self, info):
        g = self.getGlyphEditor().getGlyph()
        postEvent('longboard.requestUpdate', layer=self.longBoardPreviewLayer, viewGlyph=g)
    
    def glyphDidChangeOutline(self, info):
        g = self.getGlyphEditor().getGlyph()
        postEvent('longboard.requestUpdate', layer=self.longBoardPreviewLayer, viewGlyph=g, changed=True)
    
    def glyphDidChangeComponents(self, info):
        # check all the component bits
        g = self.getGlyphEditor().getGlyph()
        postEvent('longboard.requestUpdate', layer=self.longBoardPreviewLayer, viewGlyph=g, changed=True)
        
    # glyphDidChangeComponents
    # https://robofont.com/documentation/reference/api/mojo/mojo-subscriber/
    
    def roboFontDidSwitchCurrentGlyph(self, info):
        g = self.getGlyphEditor().getGlyph()
        postEvent('longboard.requestUpdate', layer=self.longBoardPreviewLayer, viewGlyph=g, changed=False)
    
    def glyphEditorWillClose(self, info):
        print('glyphEditorWillClose')
        removeObserver(self, 'longboard.is.not.active')


if __name__ == '__main__':
    OpenWindow(LongBoardUI)
