#!/usr/bin/env python3

# -------------------- #
# DESIGN SPACE MANAGER #
# -------------------- #

# -- Modules -- #
import os
import random
from pprint import pprint

import ufoProcessor
from fontMath import MathGlyph
from merz import MerzPen
from mojo.pens import DecomposePointPen
from mojo.roboFont import AllFonts, RFont

from tools import sharedCharacterMapping


# -- Helpers -- #
def lerp(a, b, f):
    return a + (b - a) * f


# -- Objects -- #
class LongBoardMathGlyph(MathGlyph):

    _cgPath = None

    def getRepresentation(self, name, **kwargs):
        if name == "merz.CGPath":
            if self._cgPath is None:
                pen = MerzPen(None)
                self.draw(pen)
                self._cgPath = pen.path
            return self._cgPath


class DesignSpaceManager(ufoProcessor.DesignSpaceProcessor):
    # this is responsible for 1 designspace document.
    # keep track of fonts opening and closing
    # build and cache mutators for all things
    # make glyphMath objects when the main controller asks for it
    # all the math will happen here

    def _instantiateFont(self, path):
        """Return an instance of a font object with all the given subclasses"""
        for f in AllFonts():
            if f.path == path and f.path is not None:
                return f
        return RFont(path, showInterface=False)

    def isSource(self, location):
        for eachSourceDescriptor in self.sources:
            if location == eachSourceDescriptor.location:
                return True, eachSourceDescriptor.font
        return False, None

    def loadFonts(self, reload_=False):
        print("loadFonts")
        # Load the fonts and find the default candidate based on the info flag
        # pay attention:
        #     1. different sources can reference different layers in the same ufo
        #     2. also: the same source can appear in different places in the designspace
        # so maybe the sourcedescriptor.name is not a good identifier

        # font are already loaded, if not asked explicitly, we keep serving
        # what we already have
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
                            print(f"loadFonts font is open {sourceDescriptor.path}")
                            _fonts[sourceDescriptor.name] = currentPaths[sourceDescriptor.path]
                        else:
                            print(f"loadFonts font is not open {sourceDescriptor.path}")
                            _fonts[sourceDescriptor.name] = RFont(sourceDescriptor.path, showInterface=False)
                        names = names | set(_fonts[sourceDescriptor.name].keys())
                else:
                    pathOK = False
                if not pathOK:
                    _fonts[sourceDescriptor.name] = None
                    self.problems.append(f"can't load master from {sourceDescriptor.path}")

        self.characterMapping, discarded = sharedCharacterMapping(_fonts.values())
        self.toolLog.append(
            f"The following code points cannot be accessed because they are not shared among the sources: {discarded}"
        )
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
            loc[axis.name] = lerp(axis.minimum, axis.maximum, 0.5)
        return loc

    def clearCache(self):
        self._glyphMutators.clear()

    def invalidateGlyphCache(self, glyphName):
        print(f"invalidateCache: {glyphName}")
        cacheKey = (glyphName, True)  # the boolean value refers to `decomposeComponents`
        if cacheKey in self._glyphMutators:
            del self._glyphMutators[cacheKey]

    def updateGlyphMutator(self, glyphName, decomposeComponents=False):

        """
        Here we should take care of decomposing the glyph for display
        """
        cacheKey = (glyphName, decomposeComponents)
        print(glyphName)
        items = self.collectMastersForGlyph(glyphName, decomposeComponents=decomposeComponents)

        # RA: it seems that the second item of each tuple coming from the collectMastersForGlyph method
        #     might be some kind of glyph object, which kinds?
        #     also, could be a nice idea to change collectMastersForGlyph in something like collectSourcesForGlyph?
        new = []
        for location, glyphObj, sourceAttributes in items:
            print(glyphObj.components)
            if hasattr(glyphObj, "toMathGlyph"):
                # note: calling toMathGlyph ignores the mathGlyphClass preference
                # maybe the self.mathGlyphClass is not necessary?
                new.append((location, glyphObj.toMathGlyph()))
            else:
                new.append((location, self.mathGlyphClass(glyphObj)))

        # RA: this is named optional because it might be None (if incompatible sources)
        optionalMutator = None
        try:
            bias, optionalMutator = self.getVariationModel(
                new, axes=self.serializedAxes, bias=self.newDefaultLocation(bend=True)
            )

        # RA: I tried to make some source incompatible (by adding a point to a contour)
        #     but they throw an IndexError, not a TypeError. Also, the Exception seem to come for somewhere deeper
        #     when using varLib and I could not manage to catch it. How should we catch these mistakes?
        # except (TypeError, IndexError):
        except TypeError:
            self.toolLog.append(f"getGlyphMutator {glyphName} items: {items} new: {new}")
            self.problems.append(f"\tCan't make processor for glyph {glyphName}")

            # RA: I think it is a good idea to invalidate the cache here.
            #     Even if the old mutator works, it does not
            #     represent the current state correctly
            self.invalidateCache(glyphName)

        # RA: conditional removed, we either insert a working mutator or False, check above!
        self._glyphMutators[cacheKey] = optionalMutator

    def getGlyphMutator(self, glyphName, decomposeComponents=False):
        # make a mutator / varlib object for glyphName.
        cacheKey = (glyphName, decomposeComponents)
        if cacheKey not in self._glyphMutators:
            self.updateGlyphMutator(glyphName, decomposeComponents=decomposeComponents)
        return self._glyphMutators[cacheKey]

    def makePresentation(self, glyphName, location, bend=True, changed=False):
        # draw something in the view of the glyph
        # fc1 = (0, 0.4, 1, 0.05)
        # fc2 = (0.3, 0.4, 0, 0.1)
        # _drawAllMasters = False

        # not properly working
        status, font = self.isSource(location=location)
        if status:
            return font[glyphName]
        else:
            glyphMutator = self.getGlyphMutator(glyphName, decomposeComponents=True)
            print(f"glyphMutator: {glyphName}\n\tid: {id(glyphMutator)}\n\trepr: {glyphMutator}")
            if glyphMutator is None:
                # huh nothing works
                return
            instance = glyphMutator.makeInstance(location, bend=bend)
            return LongBoardMathGlyph(instance)

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
