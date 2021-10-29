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


class LongBoardDesignSpaceProcessorTester(object):
    # hardwired test data for now
    def __init__(self):
        path = os.getcwd()
        testDocPath = os.path.join(os.getcwd(), "test", "MutatorSans.designspace")
        print('testDocPath', testDocPath, os.path.exists(testDocPath))

        self.ds = LongBoardDesignSpaceProcessor()
        self.ds.useVarlib = True
        # XX Wrap in try / except
        self.ds.read(testDocPath)
        
        self.ds.findDefault()
        #self.data_updateDocumentVerticalMetrics()
        self.ds.loadFonts()    # reload
        print(self.ds.fonts)


LongBoardDesignSpaceProcessorTester()