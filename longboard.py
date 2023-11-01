import ezui
import math
from mojo.events import postEvent

from mojo.events import (
    installTool,
    EditingTool,
    BaseEventTool,
    setActiveEventTool,
    publishEvent
)

from mojo.subscriber import (
    Subscriber,
    registerGlyphEditorSubscriber,
    unregisterGlyphEditorSubscriber,
    registerSubscriberEvent
)

from pprint import pprint
from fontTools.pens.basePen import BasePen



eventID = "com.letterror.longboardNavigator"
navigatorLocationChangedEventKey = eventID + "navigatorLocationChanged.event"
navigatorUnitChangedEventKey = eventID + "navigatorUnitChanged.event"
navigatorActiveEventKey = eventID + "navigatorActive.event"
navigatorInactiveEventKey = eventID + "navigatorInctive.event"


toolID = "com.letterror.longboard"
containerKey = toolID + ".layer"
settingsChangedEventKey = toolID + "settingsChanged.event"
operatorChangedEventKey = toolID + "operatorChanged.event"
#print('eventKey', eventKey)

interactionSourcesLibKey = toolID + ".interactionSources"

defaultStrokeWidth = 1




class CollectorPen(BasePen):
    def __init__(self, glyphSet, path=None):
        self.offset = 0,0
        self.onCurves = []
        self.offCurves = []
        self.startPoints = []
        self._pointIndex = 0
        #self.tag = "untagged"
        BasePen.__init__(self, glyphSet)
    def setOffset(self, x=0,y=0):
        self.offset = x, y
    def _moveTo(self, pos):
        self.onCurves.append((pos[0]+self.offset[0], pos[1]+self.offset[1]))
        self.startPoints.append(self._pointIndex)
        self._pointIndex += 1
    def _lineTo(self, pos):
        self.onCurves.append((pos[0]+self.offset[0], pos[1]+self.offset[1]))
        self._pointIndex += 1
    def _curveToOne(self, a, b, c):
        self.offCurves.append((a[0]+self.offset[0], a[1]+self.offset[1]))
        self.offCurves.append((b[0]+self.offset[0], b[1]+self.offset[1]))
        self.onCurves.append((c[0]+self.offset[0], c[1]+self.offset[1]))
        self._pointIndex += 3
    def _closePath(self):
        pass
        
def getLocationsForFont(font, doc):
    # theoretically, a single UFO can be a source in different discrete locations
    discreteLocations = [] 
    continuousLocations = []
    for s in doc.sources:
        if s.path == font.path:
            cl, dl = doc.splitLocation(s.location)
            if dl is not None:
                discreteLocations.append(dl)
            if cl is not None:
                continuousLocations.append(cl)
    return continuousLocations, discreteLocations


items = [
    dict(
            textValue="Weight",
            popUpValue=0,
        ),
    dict(
            textValue="Width",
            popUpValue=1,
        ),
    dict(
            textValue="Whatever",
            popUpValue=2,
        ),
    ]

class LongBoardUIController(Subscriber, ezui.WindowController):

    def build(self):
        content = """
        Interactions
        | ------- | @table
        | tf | pu |
        | ------- |

        Designspaces
        [X] Only show relevant @onlyShowRelevantDesignspace
        Discrete locations
        [X] Follow Current Font @useDiscreteLocationOfCurrentFont

        Appearance
        [X] Show Preview @showPreview
        [X] Show Sources @showSources
        [X] Show On Curves @showOnCurveVectors
        [X] Show Off Curves @showOffCurveVectors
        [X] Show Measurements @showMeasurements
        [X] Center Preview @centerPreview

        Transparency
        --X-- Haziness @hazeSlider
        """
        descriptionData = dict(
            table=dict(
                identifier="table",
                height=120,
                items = [],
                columnDescriptions = [
                    dict(
                        identifier="textValue",
                        title="Axis",
                        width=100,
                        editable=True
                    ),
                    dict(
                        identifier="popUpValue",
                        title="PopUp",
                        editable=True,
                        cellDescription=dict(
                            cellType="PopUpButton",
                            cellClassArguments=dict(
                                items=["Horizontal", "Vertical", "Ignore"]
                            )
                        )
                    ),
                ],
            ),
            hazeSlider=dict(
                minValue=0.08,
                maxValue=1,
                value=0.16
                ),
        )
        self.w = ezui.EZPanel(
            title="Longboard",
            content=content,
            descriptionData=descriptionData,
            controller=self,
            size=(300, "auto")
        )
        self.operator = None

    def tableEditCallback(self, sender):
        # callback for the interaction sources table
        # maybe it can have a less generic name than "tableEditCallback"
        # tableEditCallback [{'textValue': 'weight', 'popUpValue': 0}]
        # @@
        prefs = []
        for axis in self.w.getItem("table").get():
            axisName = axis['textValue']
            if axis['popUpValue'] == 0:     # horizontal
                prefs.append((axisName, "horizontal"))
            elif axis['popUpValue'] == 1:     # vertical
                prefs.append((axisName, "vertical"))
            elif axis['popUpValue'] == 2:     # vertical
                prefs.append((axisName, "ignore"))
        # where is the operatr coming from?
        if self.operator is not None:
            print("tableEditCallback pref set", prefs)
            self.operator.lib[interactionSourcesLibKey] = prefs
            self.operator.changed()
        else:
            print("tableEditCallback pref not set, no operator", pref)
        
    def started(self):
        self.w.open()
        registerGlyphEditorSubscriber(LongboardEditorView)

    def destroy(self):
        unregisterGlyphEditorSubscriber(LongboardEditorView)

    def navigatorLocationChanged(self, info):
        # @@ receive notifications about the navigator location changing.
        # scale mouse movement to "increment units"
        # send units + interaction sources to the previewer
        # preview can pass increment units to the designspace
        # designspace has axes 
        
        # [{'textValue': 'width', 'popUpValue': 1}, {'textValue': 'weight', 'popUpValue': 0}]
        view = info["lowLevelEvents"][0].get('view')
        popOptions = ['horizontal', 'vertical', None]
        data = info["lowLevelEvents"][0].get('data')
        nav = data['horizontal'], data['vertical']
        #pprint(info)
        offset = view.offset()
        viewScale = view.scale()
        #print('offset', offset)
        #print('scale', viewScale)

        unit = {}
        unitScale = 500
        for axis in self.w.getItem("table").get():
            name = axis['textValue']
            if axis['popUpValue'] == 0:     # horizontal
                unit[name] = (data['horizontal'] / viewScale)/unitScale
            elif axis['popUpValue'] == 1:     # vertical
                unit[name] = (data['vertical'] / viewScale)/unitScale
            # and for ignore we don't pass anything
        if unit:
            postEvent(navigatorUnitChangedEventKey, unit=unit)
            #print("posting navigatorUnitChangedEventKey", unit)
        
    def relevantOperatorChanged(self, info):
        # @@ from https://robofont.com/documentation/reference/api/mojo/mojo-subscriber/#mojo.subscriber.registerSubscriberEvent
        #print("\t\trelevantOperatorChanged", info["lowLevelEvents"][0].get('operator'))
        operator = info["lowLevelEvents"][0].get('operator')
        # @@ ask operator for the interaction sources stored in its lib
        if operator is not None:
            items = []
            prefs = []
            interactionSourcesPref = operator.lib.get(interactionSourcesLibKey)
            #interactionSourcesPref = None    # reset prefs
            #print("1 relevantOperatorChanged interactionSourcesPref", interactionSourcesPref)
            if interactionSourcesPref is not None:
                for axisName, interaction in interactionSourcesPref:
                    v = 2
                    if interaction == "horizontal":
                        v = 0
                    elif interaction == "vertical":
                        v = 1
                    items.append(dict(textValue=axisName, popUpValue=v))
            else:
                v = 0
                for axis in operator.getOrderedContinuousAxes():
                    items.append(dict(textValue=axis.name, popUpValue=v))
                    if v == 0:
                        prefs.append((axis.name, "horizontal"))
                    elif v == 1:
                        prefs.append((axis.name, "vertical"))
                    elif v == 2:
                        prefs.append((axis.name, "ignore"))
                    v += 1
                    v = max(v, 2)
                operator.lib[interactionSourcesLibKey] = prefs
                operator.changed()
            #print('2 relevantOperatorChanged', items)
            #print("3 prefs", operator.lib[interactionSourcesLibKey])
            self.w.getItem("table").set(items)
            self.operator = operator

    def fillInteractionSourcesList(self, ds=None):
        print("fillInteractionSourcesList")
        
    def showPreviewCallback(self, sender):
        value = sender.get()
        postEvent(settingsChangedEventKey, showPreview=value)

    def showSourcesCallback(self, sender):
        value = sender.get()
        postEvent(settingsChangedEventKey, showSources=value)

    def centerPreviewCallback(self, sender):
        value = sender.get()
        postEvent(settingsChangedEventKey, centerPreview=value)

    def showOnCurveVectorsCallback(self, sender):
        value = sender.get()
        postEvent(settingsChangedEventKey, showOnCurveVectors=value)

    def showOffCurveVectorsCallback(self, sender):
        value = sender.get()
        postEvent(settingsChangedEventKey, showOffCurveVectors=value)

    def showMeasurementsCallback(self, sender):
        value = sender.get()
        postEvent(settingsChangedEventKey, showMeasurements=value)
    
    def useDiscreteLocationOfCurrentFontCallback(self, sender):
        value = sender.get()
        postEvent(settingsChangedEventKey, useDiscreteLocationOfCurrentFont=value)

    def hazeSliderCallback(self, sender):
        value = sender.get()
        postEvent(settingsChangedEventKey, hazeValue=value)


class LongboardEditorView(Subscriber):

    debug = True
    hazeValue = 0.16
    
    def setPreferences(self):
        self.sourceStrokeColor = (0,0,1, self.hazeValue)
        self.previewStrokeColor = (0,0,0, self.hazeValue)
        self.previewFillColor = (.8,.8,.8, self.hazeValue)
        self.vectorStrokeColor = (0,0,1, self.hazeValue)
        self.measurementStrokeColor = (.5,0,1, self.hazeValue)
        self.measurementMarkerSize = 6
        self.measurementStrokeWidth = 5
        self.measurementFillColor = (.5,0,1, self.hazeValue)
        self.vectorStrokeDash = (5, 5)
        self.markerSize = 5
        self.previewMarkerSize = 6
        self.measureLineCurveOffset = 70
    
    def build(self):
        self.setPreferences()
        self.currentOperator = None
        self.showPreview = True
        self.showSources = True
        self.centerAllGlyphs = True
        self.showOnCurveVectors = True
        self.showOffCurveVectors = True
        self.showMarkers = True
        self.showMeasurements = True
        self.useDiscreteLocationOfCurrentFont = True

        self.previewLocation = None

        glyphEditor = self.getGlyphEditor()
        self.container = glyphEditor.extensionContainer(containerKey)
        self.previewPathLayer = self.container.appendPathSublayer(
            strokeColor=self.previewStrokeColor,
            strokeWidth=1,
            fillColor = self.previewFillColor
        )
        self.sourcesPathLayer = self.container.appendPathSublayer(
            strokeColor=self.sourceStrokeColor,
            strokeWidth=1,
            fillColor = None
        )
        self.sourcesVectorsLayer = self.container.appendLineSublayer(
            strokeColor=self.vectorStrokeColor,
            strokeWidth=1,
            fillColor = None,
            strokeDash=self.vectorStrokeDash,
        )
        self.markersLayer = self.container.appendSymbolSublayer(
            fillColor = self.sourceStrokeColor,
        )
        self.markersLayer.setImageSettings(
            dict(
                name="rectangle",
                size=(self.markerSize, self.markerSize),
                fillColor=self.sourceStrokeColor
            )
        )
        self.measurementsIntersectionsLayer = self.container.appendLineSublayer(
            strokeColor=self.measurementStrokeColor,
            strokeWidth=self.measurementStrokeWidth,
            fillColor = None,
            #strokeDash=self.vectorStrokeDash,
        )
        self.measurementMarkerLayer = self.container.appendSymbolSublayer(
        )
        self.measurementMarkerLayer.setImageSettings(
            dict(
                name="rectangle",
                size=(self.markerSize, self.markerSize),
                fillColor=self.measurementStrokeColor
            )
        )
        self.measurementTextLayer = self.container.appendBaseSublayer()

    def relevantForThisEditor(self, info=None):
        # check if the current font belongs to the current designspace.
        #    glyphEditorDidSetGlyph {'subscriberEventName': 'glyphEditorDidSetGlyph', 'lowLevelEvents': [{'view': <DoodleGlyphView: 0x7fa11b4f8c20>, 'glyph': <RGlyph 'O' ('foreground') at 140332211638384>, 'notificationName': 'viewDidChangeGlyph', 'tool': <lib.eventTools.editingTool.EditingTool object at 0x7fa1a0940fd0>}], 'iterations': [{'glyph': <RGlyph 'O' ('foreground') at 140332211638384>, 'glyphEditor': <lib.doodleGlyphWindow.DoodleGlyphWindow object at 0x7fa1a1f7a3d0>, 'locationInGlyph': None, 'deviceState': None, 'NSEvent': None}], 'glyph': <RGlyph 'O' ('foreground') at 140332211638384>, 'glyphEditor': <lib.doodleGlyphWindow.DoodleGlyphWindow object at 0x7fa1a1f7a3d0>, 'locationInGlyph': None, 'deviceState': None, 'NSEvent': None}
        font = None
        ds = None
        # try to find the current space from the glyph
        if info is not None:
            #pprint(info)
            glyphFromNotification = info.get('glyph')
            if glyphFromNotification is not None:
                font = glyphFromNotification.font
                allSpaces = AllDesignspaces(usingFont=font)
                if len(allSpaces)>=1:
                    self.operator = allSpaces[0]
                    postEvent(operatorChangedEventKey, operator=self.operator)
                    #print("relevantForThisEditor -> found space from info")
                    return True, font, allSpaces[0]
        # try to find it from the currentfont
        font = CurrentFont()
        allSpaces = AllDesignspaces(usingFont=font)
        #print("relevantForThisEditor -> trying to find space from font")
        if len(allSpaces)>=1:
            self.operator = allSpaces[0]
            return True, font, allSpaces[0]
        return False, font, None
    
    def getAxisIncrementUnit(self, axisName):
        # calculate our preferred smallest step along this axis
        axisSteps = 500     # emprically established constant, from skateboard
        minimum, default, maximum = self.operator.getAxisExtremes(self.operator.getAxis(axisName))
        return (maximum - minimum)/axisSteps

    def navigatorUnitChanged(self, info):
        #print("navigatorUnitChanged", info)
        unit = info['lowLevelEvents'][0]['unit']
        glyphEditor = self.getGlyphEditor()
        previewLocation = self.operator.getPreviewLocation()
        #print('before unit change', previewLocation )
        for axisName, change in unit.items():
            unit = self.getAxisIncrementUnit(axisName)
            if change < 0:
                previewLocation[axisName] = previewLocation[axisName] - unit
            elif change > 0:
                previewLocation[axisName] = previewLocation[axisName] + unit
        #print('after unit change', previewLocation )
        self.operator.setPreviewLocation(previewLocation)
        
    def updatePreviewLocation(self, newLocation):
        self.previewLocation = newLocation
        self.updateOutline()
        
    def destroy(self):
        self.currentOperator = None
        glyphEditor = self.getGlyphEditor()
        container = glyphEditor.extensionContainer(containerKey)
        container.clearSublayers()
        
    def glyphEditorDidSetGlyph(self, info):
        relevant, font, ds = self.relevantForThisEditor(info)
        if not relevant:
            return
        #ds = CurrentDesignspace()
        ds = self.operator
        previewLocation = ds.getPreviewLocation()
        if previewLocation is None:
            previewLocation = ds.newDefaultLocation()
            ds.setPreviewLocation(previewLocation)
        previewContinuous, previewDiscrete = ds.splitLocation(previewLocation)
        glyphEditor = self.getGlyphEditor()
        editorGlyph = self.getGlyphEditor().getGlyph()
        editorContinuous, editorDiscrete = getLocationsForFont(editorGlyph.font, ds)
        if editorDiscrete not in [[], [None], [None,None], None]:
            if self.useDiscreteLocationOfCurrentFont:
                    if editorDiscrete != previewDiscrete:
                        #print('editorDiscrete', editorDiscrete)
                        #print('previewDiscrete', previewDiscrete)
                        if editorDiscrete:
                            previewContinuous.update(editorDiscrete[0])
                            ds.setPreviewLocation(previewContinuous)
                            self.updateOutline()
        else:
            ds.setPreviewLocation(previewContinuous)
            self.updateOutline()

    def designspaceEditorSourceGlyphDidChange(self, info):
        relevant, font, ds = self.relevantForThisEditor(info)
        if not relevant:
            return
        self.updateOutline()

    def designspaceEditorPreviewLocationDidChange(self, info):
        relevant, font, ds = self.relevantForThisEditor(info)
        if not relevant:
            return
        self.previewLocation = info['location']
        self.updateOutline()
    
    def glyphDidChangeMeasurements(self, info):
        relevant, font, ds = self.relevantForThisEditor(info)
        if not relevant:
            return
        self.updateOutline()
    
    def drawMeasurements(self, editorGlyph, previewShift, previewGlyph):
        # draw intersections for the current measuring beam and the current preview
        for m in editorGlyph.measurements:
            if m.startPoint is None or m.endPoint is None:
                continue
            x1, y1 = m.startPoint
            x2, y2 = m.endPoint
            beamData = ((x1,y1),(x2,y2))
            r = previewGlyph.getRepresentation("doodle.Beam", 
                beam=beamData, 
                canHaveComponent=False, 
                italicAngle=editorGlyph.font.info.italicAngle)
            r.intersects.sort()
            for i, mp in enumerate(r.intersects):
                if i == len(r.intersects)-1:
                    break
                mp1 = r.intersects[i]
                mp2 = r.intersects[(i+1)]
                measureLineAngle = math.atan2(mp1[1]-mp2[1], mp1[0]-mp2[0]) - .5*math.pi
                # draw the jumper curve
                bcp1 = mp1[0]
                jumperLayer = self.measurementsIntersectionsLayer.appendPathSublayer(
                    strokeWidth=self.measurementStrokeWidth,
                    strokeColor=self.measurementStrokeColor,
                    fillColor=None,
                )
                needlex = math.cos(measureLineAngle) * self.measureLineCurveOffset
                needley = math.sin(measureLineAngle) * self.measureLineCurveOffset
                jumperPen = jumperLayer.getPen(clear=True)
                jumperPen.moveTo(mp1)
                jumperPen.curveTo((mp1[0]+needlex, mp1[1]+needley), (mp2[0]+needlex, mp2[1]+needley), (mp2[0], mp2[1]))
                jumperPen.endPath()
                # draw the end markers
                symbolLayer = self.measurementMarkerLayer.appendSymbolSublayer(position=mp1)
                symbolLayer.setImageSettings(
                    dict(
                        name="oval",
                        size=(self.measurementMarkerSize, self.measurementMarkerSize),
                        fillColor=self.measurementFillColor
                        )
                    )
                symbolLayer = self.measurementMarkerLayer.appendSymbolSublayer(position=mp2)
                symbolLayer.setImageSettings(
                    dict(
                        name="oval",
                        size=(self.measurementMarkerSize, self.measurementMarkerSize),
                        fillColor=self.measurementFillColor
                        )
                    )
                # draw the measurement distance text
                textPos = .5*(mp1[0]+mp2[0])+needlex, .5*(mp1[1]+mp2[1])+needley
                dist = math.hypot(mp1[0]-mp2[0], mp1[1]-mp2[1])
                textLayer= self.measurementTextLayer.appendTextLineSublayer(
                    position=textPos,
                    pointSize=10,
                    fillColor=(1,1,1,1),
                    backgroundColor=self.measurementFillColor,
                    horizontalAlignment="center",
                    cornerRadius=6,
                    padding=(3, 1)
                    )
                textLayer.setText(f"{dist:3.2f}")
        
    def updateOutline(self):
        self.previewPathLayer.clearSublayers()
        self.sourcesPathLayer.clearSublayers()
        self.sourcesVectorsLayer.clearSublayers()
        self.markersLayer.clearSublayers()
        self.measurementMarkerLayer.clearSublayers()
        self.measurementsIntersectionsLayer.clearSublayers()
        self.measurementTextLayer.clearSublayers()
        
        if self.operator is None:
            return
        ds = self.operator
        editorGlyph = self.getGlyphEditor().getGlyph()
        #if glyph.width != self.centeredWidth:
        #    self.centeredWidth = glyph.width
        #    ds.glyphChanged(glyph.name)
        cpCurrent = CollectorPen(glyphSet=editorGlyph.font)
        sourcePens = []
        editorGlyph.draw(cpCurrent)
        if self.previewLocation is None:
            return
            
        # # boldly assume a font is only in a single discrete location
        cl, dl = getLocationsForFont(editorGlyph.font, ds)
        continuousLocationForCurrentSource = {}
        discreteLocationForCurrentSource = {}
        if cl:
            if cl[0] is not None:
                continuousLocationForCurrentSource = cl[0]
        if dl:
            if dl[0] is not None:
                discreteLocationForCurrentSource = dl[0]

        if self.previewLocation is not None:
            mathGlyph = ds.makeOneGlyph(editorGlyph.name, location=self.previewLocation)
            if editorGlyph is None or mathGlyph is None:
                path = None
            else:
                previewGlyph = RGlyph()
                mathGlyph.extractGlyph(previewGlyph.asDefcon())
                shift = 0
                if self.centerAllGlyphs:
                    xMin, yMin, xMax, yMax = previewGlyph.bounds
                    shift = .5*editorGlyph.width-.5*previewGlyph.width
                    previewGlyph.moveBy((shift, 0))
                cpPreview = CollectorPen(glyphSet={})
                previewGlyph.draw(cpPreview)
                if self.showMeasurements:
                    self.drawMeasurements(editorGlyph,  shift, previewGlyph)
                if self.showPreview==1:
                    path = previewGlyph.getRepresentation("merz.CGPath")
                    layer = self.previewPathLayer.appendPathSublayer(
                        fillColor = self.previewFillColor,
                        strokeColor=self.previewStrokeColor,
                        strokeWidth=1)
                    layer.setPath(path)
                    # draw the preview markers
                    for m in cpPreview.onCurves:
                        symbolLayer = self.markersLayer.appendSymbolSublayer(position=m)
                        symbolLayer.setImageSettings(
                            dict(
                                name="oval",
                                size=(self.previewMarkerSize, self.previewMarkerSize),
                                fillColor=self.previewStrokeColor
                                )
                            )

        if self.showSources or self.showOnCurveVectors:
            items, unicodes = ds.collectSourcesForGlyph(glyphName=editorGlyph.name, decomposeComponents=True, discreteLocation=discreteLocationForCurrentSource)
            for item in items:
                loc, srcMath, thing = item
                sourcePen = CollectorPen(glyphSet={})
                # do not draw the master we're drawing in
                # 
                if loc==continuousLocationForCurrentSource: continue
                srcGlyph = RGlyph()
                srcMath.extractGlyph(srcGlyph.asDefcon())
                if self.centerAllGlyphs:
                    xMin, yMin, xMax, yMax = srcGlyph.bounds
                    shift = .5*editorGlyph.width-.5*srcGlyph.width
                    srcGlyph.moveBy((shift, 0))
                srcGlyph.draw(sourcePen)
                sourcePens.append(sourcePen)
                if self.showSources:
                    path = srcGlyph.getRepresentation("merz.CGPath")
                    layer = self.sourcesPathLayer.appendPathSublayer(
                        fillColor=None,
                        strokeColor=self.sourceStrokeColor,
                        strokeWidth=1)
                    layer.setPath(path)
            if self.showOnCurveVectors:
                for s in sourcePens:
                    for a, b in zip(cpCurrent.onCurves, s.onCurves):
                        lineLayer = self.sourcesVectorsLayer.appendLineSublayer(
                            startPoint=a,
                            endPoint=b,
                            strokeWidth=1,
                            strokeColor=self.vectorStrokeColor,
                            strokeDash=self.vectorStrokeDash,
                        )
                        if self.showMarkers:
                            symbolLayer = self.markersLayer.appendSymbolSublayer(position=b)
                            symbolLayer.setImageSettings(
                                dict(
                                    name="oval",
                                    size=(self.markerSize, self.markerSize),
                                    fillColor=self.sourceStrokeColor
                                    )
                                )
            if self.showOffCurveVectors:
                for s in sourcePens:
                    for a, b in zip(cpCurrent.offCurves, s.offCurves):
                        lineLayer = self.sourcesVectorsLayer.appendLineSublayer(
                            startPoint=a,
                            endPoint=b,
                            strokeWidth=1,
                            strokeColor=self.vectorStrokeColor,
                            strokeDash=self.vectorStrokeDash,
                        )
                        if self.showMarkers:
                            symbolLayer = self.markersLayer.appendSymbolSublayer(position=b)
                            symbolLayer.setImageSettings(
                                dict(
                                    name="oval",
                                    size=(self.markerSize, self.markerSize),
                                    fillColor=self.sourceStrokeColor
                                    )
                                )
                
    def showSettingsChanged(self, info):
        if info["showPreview"] is not None:
            self.showPreview = info["showPreview"]
        if info["showSources"] is not None:
            self.showSources = info["showSources"]
        if info["centerPreview"] is not None:
            self.centerAllGlyphs = info["centerPreview"]
        if info["showOnCurveVectors"] is not None:
            self.showOnCurveVectors = info["showOnCurveVectors"]
        if info["showOffCurveVectors"] is not None:
            self.showOffCurveVectors = info["showOffCurveVectors"]
        if info["showMeasurements"] is not None:
            self.showMeasurements = info["showMeasurements"]
        if info["useDiscreteLocationOfCurrentFont"] is not None:
            self.useDiscreteLocationOfCurrentFont = info["useDiscreteLocationOfCurrentFont"]
        if info["hazeValue"] is not None:
            self.hazeValue = info["hazeValue"]
            self.setPreferences()
        self.updateOutline()


def previewSettingsExtractor(subscriber, info):
    # crikey there as to be a more efficient way to do this.
    info["showPreview"] = None
    info["showSources"] = None
    info["centerPreview"] = None
    info["showOnCurveVectors"] = None
    info["showOffCurveVectors"] = None
    info["showMeasurements"] = None
    info["useDiscreteLocationOfCurrentFont"] = None
    info["hazeValue"] = None
    for lowLevelEvent in info["lowLevelEvents"]:
        info["showPreview"] = lowLevelEvent.get("showPreview")
        info["showSources"] = lowLevelEvent.get("showSources")
        info["centerPreview"] = lowLevelEvent.get("centerPreview")
        info["showOnCurveVectors"] = lowLevelEvent.get("showOnCurveVectors")
        info["showOffCurveVectors"] = lowLevelEvent.get("showOffCurveVectors")
        info["showMeasurements"] = lowLevelEvent.get("showMeasurements")
        info["useDiscreteLocationOfCurrentFont"] = lowLevelEvent.get("useDiscreteLocationOfCurrentFont")
        info["hazeValue"] = lowLevelEvent.get("hazeValue")


# 
registerSubscriberEvent(
    subscriberEventName=settingsChangedEventKey,
    methodName="showSettingsChanged",
    lowLevelEventNames=[settingsChangedEventKey],
    eventInfoExtractionFunction=previewSettingsExtractor,
    dispatcher="roboFont",
    delay=0,
    debug=True
)

# The concept of "relevant" operator:
# it is the operator that belongs to the font that belongs to the glyph that is in the editor.
registerSubscriberEvent(
    subscriberEventName=operatorChangedEventKey,
    methodName="relevantOperatorChanged",
    lowLevelEventNames=[operatorChangedEventKey],
    dispatcher="roboFont",
    delay=0.01,
    documentation="This is sent when the glyph editor subscriber finds there is a new relevant designspace.",
    debug=True
)

registerSubscriberEvent(
    subscriberEventName=navigatorLocationChangedEventKey,
    methodName="navigatorLocationChanged",
    lowLevelEventNames=[navigatorLocationChangedEventKey],
    dispatcher="roboFont",
    delay=0,
    documentation="Posted by the Longboard Navigator Tool to the LongBoardUIController",
    debug=True
)

registerSubscriberEvent(
    subscriberEventName=navigatorUnitChangedEventKey,
    methodName="navigatorUnitChanged",
    lowLevelEventNames=[navigatorUnitChangedEventKey],
    dispatcher="roboFont",
    delay=0,
    documentation="Posted by the LongBoardUIController to the previewer",
    debug=True
)




class LongboardNavigatorTool(BaseEventTool):
    def setup(self):
        self.start = None

    #def becomeActive(self):
    #    publishEvent(navigatorActiveEventKey)

    #def becomeInactive(self):
    #    publishEvent(navigatorInactiveEventKey)

    def mouseDown(self, point, event):
        if self.start is None:
            self.start = point.x, point.y

    def mouseUp(self, event):
        self.start = None

    def mouseDragged(self, point=None, delta=None):
        self.didDrag = True
        currentPt = point.x, point.y
        verticalDelta = currentPt[1]-self.start[1]
        horizontalDelta = currentPt[0]-self.start[0]
        data = dict(vertical = verticalDelta, horizontal=horizontalDelta)
        publishEvent(navigatorLocationChangedEventKey, data=data)
        
    def getToolbarTip(self):
        return "Longboard Navigator"

if __name__ == "__main__":
    import time
    nt = LongboardNavigatorTool()
    installTool(nt)
    print(time.time(),"refreshed navigator")




    OpenWindow(LongBoardUIController)

