#!/usr/bin/env python3

# -------------------- #
# DESIGN SPACE MANAGER #
# -------------------- #

# -- Modules -- #
from pprint import pprint
import random
import os

from mojo.roboFont import AllFonts, RFont
import ufoProcessor

def lerp(a, b, f):
    return a + (b-a) * f


# -- Object -- #
class DesignSpaceManager(ufoProcessor.DesignSpaceProcessor):
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

    def updateGlyphMutator(self, glyphName, decomposeComponents=False):
        cacheKey = (glyphName, decomposeComponents)
        items = self.collectMastersForGlyph(glyphName, decomposeComponents=decomposeComponents)
        new = []
        for a, b, c in items:
            if hasattr(b, "toMathGlyph"):
                # note: calling toMathGlyph ignores the mathGlyphClass preference
                # maybe the self.mathGlyphClass is not necessary?
                new.append((a, b.toMathGlyph()))
            else:
                new.append((a, self.mathGlyphClass(b)))
        newMutator = None
        try:
            bias, newMutator = self.getVariationModel(new, axes=self.serializedAxes, bias=self.newDefaultLocation(bend=True)) #xx
        except TypeError:
            self.toolLog.append("getGlyphMutator %s items: %s new: %s" % (glyphName, items, new))
            self.problems.append("\tCan't make processor for glyph %s" % (glyphName))
        if newMutator is not None:
            self._glyphMutators[cacheKey] = newMutator

    def getGlyphMutator(self, glyphName, decomposeComponents=False, fromCache=False):
        # make a mutator / varlib object for glyphName.
        cacheKey = (glyphName, decomposeComponents)
        if not (cacheKey in self._glyphMutators and fromCache):
            self.updateGlyphMutator(glyphName, decomposeComponents=decomposeComponents)
        return self._glyphMutators[cacheKey]

    def makePresentation(self, glyphName, location, bend=True, changed=False):
        # draw something in the view of the glyph
        # fc1 = (0, 0.4, 1, 0.05)
        # fc2 = (0.3, 0.4, 0, 0.1)
        # _drawAllMasters = False

        glyphMutator = self.getGlyphMutator(glyphName, fromCache=False)
        print('glyphMutator', id(glyphMutator), glyphMutator)
        if glyphMutator is None:
            # huh nothing works
            return
        return glyphMutator.makeInstance(location, bend=bend)

        # if _drawAllMasters:
        #     # draw the other outlines
        #     for srcDescriptor in self.sources:
        #         for key, f in self.fonts.items():
        #             if srcDescriptor.name == key:
        #                 print('srcDescriptor.layerName', srcDescriptor.layerName)
        #                 if srcDescriptor.layerName is not None:
        #                     continue
        #                 pathLayer = merzView.appendPathSublayer(
        #                     fillColor=fc1,
        #                     strokeColor=(fc1[0], fc1[1], fc1[2], 1),
        #                     strokeWidth=.5,
        #                 )
        #                 pen = pathLayer.getPen(f)
        #                 thisGlyph = f[viewGlyph.name]        # .getLayer(srcDescriptor.layerName)
        #                 thisGlyph.draw(pen)

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