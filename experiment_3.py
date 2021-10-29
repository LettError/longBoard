from mojo.subscriber import Subscriber, WindowController
from mojo.subscriber import registerRoboFontSubscriber, unregisterRoboFontSubscriber, registerGlyphEditorSubscriber
from mojo.events import addObserver, postEvent, removeObserver
import vanilla
import os
import merz
import time

import ufoProcessor
import ufoProcessor.varModels
from ufoProcessor.emptyPen import checkGlyphIsEmpty



import ezui



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
    
    def makePresentation(self, viewGlyph, merzView):
        # draw something in the view of the glyph
        #print('drawing', time.time(), glyph)    #, merzView)
        merzView.clearSublayers()
        
        for f in AllFonts():
            pathLayer = merzView.appendPathSublayer(
                #fillColor=(1,0.4,0,0.2),
                #strokeColor=None,
                strokeColor=(1,0.4,0,0.7),
                fillColor=None,
                strokeWidth=1)
            pen = pathLayer.getPen(f)
            thisGlyph = f[viewGlyph.name]
            thisGlyph.draw(pen)
        
        
        
        
        
class LongBoardUI(Subscriber, WindowController):
    # this is the window with the UI
    debug = True

    def build(self):
        self.vendor = None
        # assuming we're only going to use the Processor and Presenter when we have the UI open
        # we should register them here, no?
        registerGlyphEditorSubscriber(LongBoardPresenter)    # this here?
        addObserver(self, 'listenForUpdateRequests', 'longboard.requestUpdate')


        stackContent = [
            dict(
                type="Label",
                text="This is some text.",
                identifier="documentPathText",
            ),
            dict(
                type="Checkbox",
                identifier="checkbox",
                text="A Checkbox",
                value=1
            ),
            dict(
                type="Slider",
                identifier="slider"
            ),
            dict(
                type="TextEditor",
                identifier="textEditor",
                text="This is long text.",
                height=100
            )
        ]
        windowContent = dict(
            type="VerticalStack",
            contentDescriptions=stackContent,
            callback=self.stackCallback
        )
        windowDescription = dict(
            type="Window",
            size=(300, "auto"),
            title="LongBoard",
            contentDescription=windowContent
        )
        self.w = ezui.makeItem(
            windowDescription
        )
        self.w.open()

        self.loadTestDocument()
        postEvent('longboard.is.active')

    def stackCallback(self, sender):
        print(sender.get())

    def loadTestDocument(self):
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

    def listenForUpdateRequests(self, info):
        print('LongBoardUI.listenForUpdateRequests ping')
        viewGlyph = info.get('viewGlyph')
        if viewGlyph is not None:
            self.vendor.makePresentation(viewGlyph, info['layer'])
        
    def roboFontDidBecomeActive(self, info):
        # refresh documents
        print(f'LongBoardUI {id(self)} roboFontDidBecomeActive')
    
    def destroy(self):
        print(f'LongBoardUI {id(self)} closing')
        removeObserver(self, 'longboard.requestUpdate')

        # windowwillclose

    def roboFontDidBecomeActive(self, info):
        print(f"LongBoardUI {id(self)} responds to roboFontDidBecomeActive")
        print(info)
    
    def fontDocumentWillOpen(self, info):
        print(f"LongBoardUI {id(self)} responds to fontDocumentWillOpen")
        print(info)
    
    def fontDocumentDidChangeExternally(self, info):
        print(f"LongBoardUI {id(self)} responds to fontDocumentDidChangeExternally")
        print(info)
    
    def fontDocumentWillClose(self, info):
        print(f"LongBoardUI {id(self)} responds to fontDocumentWillClose")
        print(info)
        
        
        

class LongBoardPresenter(Subscriber):
    # this is the thing that will run in the glypheditor.
    # respond to relevant change events in glyph geometry
    # request new presentations when we have changes
    # don't do any math here, just order
    debug = True
    
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
        postEvent('longboard.requestUpdate', layer=self.longBoardPreviewLayer, viewGlyph=g)
    
    def glyphDidChangeComponents(self, info):
        # check all the component bits
        g = self.getGlyphEditor().getGlyph()
        postEvent('longboard.requestUpdate', layer=self.longBoardPreviewLayer, viewGlyph=g)
        
    # glyphDidChangeComponents
    # https://robofont.com/documentation/reference/api/mojo/mojo-subscriber/
    
    def roboFontDidSwitchCurrentGlyph(self, info):
        g = self.getGlyphEditor().getGlyph()
        postEvent('longboard.requestUpdate', layer=self.longBoardPreviewLayer, viewGlyph=g)
    
    def glyphEditorWillClose(self, info):
        print('glyphEditorWillClose')
        removeObserver(self, 'longboard.is.not.active')


if __name__ == '__main__':
    OpenWindow(LongBoardUI)
