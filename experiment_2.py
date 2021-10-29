from mojo.subscriber import Subscriber, WindowController
from mojo.subscriber import registerRoboFontSubscriber, unregisterRoboFontSubscriber, registerGlyphEditorSubscriber
from mojo.events import addObserver, postEvent, removeObserver
import vanilla
import os
import merz
import time

import ufoProcessor
#importlib.reload(ufoProcessor)
import ufoProcessor.varModels
#import ufoProcessor.sp3
from ufoProcessor.emptyPen import checkGlyphIsEmpty
import os

class LongBoardDesignSpaceProcessor(ufoProcessor.DesignSpaceProcessor):
    def __init__(self, readerClass=None, writerClass=None, fontClass=None, ufoVersion=3, useVarlib=False):
        self._fontsLoaded = False
        self.fonts = {}
        super(ufoProcessor.DesignSpaceProcessor, self).__init__(readerClass=readerClass, writerClass=writerClass)

    def update(self):
        # placeholder 
        pass
    
    def oneOfOurs(self, path):
        # check if this ufo is used as one of the sources in this document
        for sourceDescriptor in self.sources:
            if sourceDescriptor.path is not None:
                if sourceDescriptor.path == path:
                    return True
        return False

    def _instantiateFont(self, path):
        """ Return a instance of a font object with all the given subclasses"""
        for f in AllFonts():
            if f.path == path and f.path is not None:
                return f
        return RFont(path, showInterface=False)
    
    def loadFonts(self, reload=False):
        # Load the fonts and find the default candidate based on the info flag
        # pay attention:
        #     1. different sources can reference different layers in the same ufo
        #     2. also: the same source can appear in different places in the designspace
        # so maybe the sourcedescriptor.name is not a good identifier
        if self._fontsLoaded and not reload:
            return
        names = set()
        for sourceDescriptor in self.sources:
            if not sourceDescriptor.name in self.fonts:
                pathOK = True
                if sourceDescriptor.path is not None:
                    if os.path.exists(sourceDescriptor.path):
                        self.fonts[sourceDescriptor.name] = self._instantiateFont(sourceDescriptor.path)
                        # this is not a problem, why report it as one?
                        names = names | set(self.fonts[sourceDescriptor.name].keys())
                else:
                    pathOK = False
                if not pathOK:
                    self.fonts[sourceDescriptor.name] = None
                    self.problems.append("can't load master from %s"%(sourceDescriptor.path))
        self.glyphNames = list(names)
        self._fontsLoaded = True



# subscriber
# https://robofont.com/documentation/reference/api/mojo/mojo-subscriber/?highlight=roboFontDidChangeScreen

# windowcontroller
# https://doc.robofont.com/documentation/topics/window-controller/?highlight=WindowController

# how are these parts going to communicate? mojo.events?

class LongBoardVendor(Subscriber):

    # 1 per designspace doczou het handig zijn om meerdereument
    
    # maintain mutators for glyphs
    # construct paths for the Presenters
    # receive requests for making specific paths for CALayers
    #    * draw this glyph at the current location in this specific visual style
    # close font (font goes from active to file)
    # open font (font goes from file to active)
    # maintain mutators for kerning - mutator per pair? ooh!
    # analyse dependencies in a UFO
    # switch math model
    # keep track of the current location
    #        * keep track of dependencies (changes to components?)
    #        * build, maintain, execute kernlets
    # also needs to:
    #        * somehow this needs to be aware of changes to glyphs that are important for this
    #            * not all glyphs will be part of this designspace
    #            * glyphs we're showing
    #            * glyphs that are needed for the glyphs we're showing
    

    # Tal wrote:
    # The object that vends the path can post a custom notification through mojo.events announcing that the path needs to be updated and the info in the notification can carry the CGPath and whatever else you need to send along. Your subscriber class can have a method that is called whenever that notification is posted. The method would be called and you’d just update the path in the existing layer.
    
    def build(self):
        self.doc = None
        pass
        
    def destroy(self):
        pass
    
    def host(self, designSpacePath):
        # the Vendor hosts the designspace.
        self.doc = LongBoardDesignSpaceProcessor()
        self.doc.read(designSpacePath)
        self.doc.loadFonts()
        
    def roboFontDidBecomeActive(self, info):
        print("LongBoardVendor responds to roboFontDidBecomeActive")
        print(info)
    
    def fontDocumentWillOpen(self, info):
        print("LongBoardVendor responds to fontDocumentWillOpen")
        print(info)
    
    def fontDocumentDidChangeExternally(self, info):
        print("LongBoardVendor responds to fontDocumentDidChangeExternally")
        print(info)
    
    def fontDocumentWillClose(self, info):
        print("LongBoardVendor responds to fontDocumentWillClose")
        print(info)
        
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
    # part 1
    # the window with UI, document info, sources, etc
    # show sources
    # show instances
    # show interesting locations
    # show current location
    # couple of convenience buttons at the top
    # keep track of which sources are enabled, update processor
    
    # only need 1 for the whole of RF
    # 1 longboard UI could have several designspaces ("activate italic")
    debug = True

    def build(self):
        self.vendor = None
        addObserver(self, 'listenForUpdateRequests', 'longboard.requestUpdate')
        self.w = vanilla.Window((400, 600), "Experimental LongBoard")
        self.w.open()
        self.loadTestDocument()
        postEvent('longboard.is.active')

    def loadTestDocument(self):
        # temporary
        print('registerRoboFontSubscriber(LongBoardVendor)')
        registerRoboFontSubscriber(LongBoardVendor)
        self.vendor = LongBoardVendor()
        path = os.getcwd()
        testDocPath = os.path.join(os.getcwd(), "test", "MutatorSans.designspace")
        print('testDocPath', testDocPath, os.path.exists(testDocPath))
        self.vendor.useVarlib = True
        # XX Wrap in try / except
        self.vendor.host(testDocPath)

    def listenForUpdateRequests(self, info):
        viewGlyph = info.get('viewGlyph')
        if viewGlyph is not None:
            self.vendor.makePresentation(viewGlyph, info['layer'])
        
    def roboFontDidBecomeActive(self, info):
        # refresh documents
        print('LongBoardUI roboFontDidBecomeActive')
    
    def destroy(self):
        print('LongBoardUI closing')
        removeObserver(self, 'longboard.requestUpdate')
        if self.vendor is not None:
            self.vendor.destroy()
            print('unregisterRoboFontSubscriber(self.vendor)')
            unregisterRoboFontSubscriber(self.vendor)
        postEvent('longboard.is.not.active')
        
        

class LongBoardPresenter(Subscriber):
    # part 2
    # this will draw the preview in any glyphwindow that's open
    # need to determine if a preview is needed 
    # there might be glyphwindows that are not part of the current designspace
    # one in every glyph editor

    debug = True
    
    def build(self):
        
        addObserver(self, 'listenForLongboardActive', 'longboard.is.not.active')
        print('LongBoardPresenter build')
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
        
    def glyphDidChangeContours(self, info):
        g = self.getGlyphEditor().getGlyph()
        postEvent('longboard.requestUpdate', layer=self.longBoardPreviewLayer, viewGlyph=g)
    
    def roboFontDidSwitchCurrentGlyph(self, info):
        g = self.getGlyphEditor().getGlyph()
        postEvent('longboard.requestUpdate', layer=self.longBoardPreviewLayer, viewGlyph=g)
    
    def glyphEditorWillClose(self, info):
        print('glyphEditorWillClose')
        removeObserver(self, 'longboard.is.not.active')

    
    # receive updates from the Processor about changes that happened in other parts of the tool
    # both glyphDidChangeMetrics and glyphDidChangeOutline happen when there are changes to
    # these things in **this** window. So these should alert the processor that there are
    # changes that need looking at. 

# part 3: navigator tool in the glyphwindow?
# one in every glyph editor
# this would just be to take input from mouse and convert that into current location changes
# maybe also construct the contextual menu? or can that go directly to the UI

# part 4: text window
# justs one in RF
# should take a cue from the superpolator preview. Different instances above each other
# also take mouse event input to change current location

# part 5: designspace overview
# justs one in RF
# like the Space Window, map out a 2D projection of the design space
# export to pdf
# maybe also draw glyphs? 
# also take mouse event input to change current location

if __name__ == '__main__':
    registerGlyphEditorSubscriber(LongBoardPresenter)
    OpenWindow(LongBoardUI)
