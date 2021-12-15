import random
import Quartz
import AppKit
import vanilla
import merz
from merz.collectionView import MerzCollectionViewContainer
from merz.tools.caLayerClasses import MerzCALayer
from merz.tools.drawingTools import NSImageDrawingTools



import objc
objc.setVerbose(True)

class TestWindow(object):

    def __init__(self):
        self.w = vanilla.Window(
            (700, 500),
            "MerzCollectionView",
            minSize=(500, 500)
        )

        # Controls
        # --------

        stackGroup = self.w.controlGroup = vanilla.VerticalStackGroup(
            "auto",
            spacing=metrics["spacing"]
        )

        self.insetGroup = OneField("Inset:", "20")
        stackGroup.addView(
            self.insetGroup,
            gravity="top"
        )
        self.lineHeightGroup = OneField("Line Height:", "50")
        stackGroup.addView(
            self.lineHeightGroup,
            gravity="top"
        )
        self.sizeGroup = OneField("Size:", "50, 50")
        stackGroup.addView(
            self.sizeGroup,
            gravity="top"
        )
        self.widthsGroup = OnePopUp("Widths:", ["vary", "mono"])
        stackGroup.addView(
            self.widthsGroup,
            gravity="top"
        )
        self.alignmentGroup = OnePopUp("Alignment:", ["left", "center", "right"])
        stackGroup.addView(
            self.alignmentGroup,
            gravity="top"
        )
        self.spacingGroup = OneField("Spacing:", "0")
        stackGroup.addView(
            self.spacingGroup,
            gravity="top"
        )

        self.flushItemsGroup = OneField("Flush Items:", "50")
        stackGroup.addView(
            self.flushItemsGroup,
            gravity="top"
        )
        self.overshootItemsGroup = OneField("Overshoot Items:", "50")
        stackGroup.addView(
            self.overshootItemsGroup,
            gravity="top"
        )
        self.advanceItemsGroup = OneField("Advance Items:", "25, 25")
        stackGroup.addView(
            self.advanceItemsGroup,
            gravity="top"
        )
        self.placementItemsGroup = OneField("Placement Items:", "25, 25")
        stackGroup.addView(
            self.placementItemsGroup,
            gravity="top"
        )

        self.itemTypeGroup = OnePopUp("Item Type:", ["Merz", "CALayer", "Image"])
        stackGroup.addView(
            self.itemTypeGroup,
            gravity="top"
        )
        self.detailsGroup = OneCheckBox("Show Merz Details:", False)
        stackGroup.addView(
            self.detailsGroup,
            gravity="top"
        )

        self.shuffleGroup = OneCheckBox("Shuffle:", False)
        stackGroup.addView(
            self.shuffleGroup,
            gravity="top"
        )

        self.w.applyButton = vanilla.Button(
            "auto",
            "Apply",
            callback=self.applyButtonCallback
        )

        # View
        # ----

        self.w.collectionView = merz.MerzCollectionView(
            "auto"
        )

        # Window Rules
        # ------------

        rules = [
            # Horizontal
            "H:|-margin-[controlGroup(==230)]-[collectionView]|",
            "H:|-margin-[applyButton(==230)]",
            # Vertical
            "V:|"
                "-margin-"
                "[controlGroup]"
                "[applyButton]"
                "-margin-"
                "|",
            "V:|"
                "[collectionView]"
                "|"
        ]
        self.w.addAutoPosSizeRules(rules, metrics)
        self.applyButtonCallback(None)

        self.w.open()

    def applyButtonCallback(self, sender):
        inset = int(self.insetGroup.get())
        lineHeight = int(self.lineHeightGroup.get())
        size = self.sizeGroup.get()
        if "," in size:
            size = [int(i.strip()) for i in size.split(",")]
        else:
            size = int(size)
            size = (size, size)
        varyWidths = self.widthsGroup.get() == "vary"
        alignment = self.alignmentGroup.get()
        spacing = int(self.spacingGroup.get())
        flushItems = int(self.flushItemsGroup.get())
        overshootItems = int(self.overshootItemsGroup.get())
        advanceItems = self.advanceItemsGroup.get()
        if "," in advanceItems:
            negativeAdvanceItems, positiveAdvanceItems = (int(i.strip()) for i in advanceItems.split(","))
        else:
            advanceItems = int(advanceItems)
            negativeAdvanceItems = positiveAdvanceItems = advanceItems // 2
        placementItems = self.placementItemsGroup.get()
        if "," in placementItems:
            negativePlacementItems, positivePlacementItems = (int(i.strip()) for i in placementItems.split(","))
        else:
            placementItems = int(placementItems)
            negativePlacementItems = positivePlacementItems = placementItems // 2
        itemType = self.itemTypeGroup.get().lower()
        details = self.detailsGroup.get()
        shuffle = self.shuffleGroup.get()

        if itemType == "calayer":
            testMaker = makeTestCALayerItem
        elif itemType == "image":
            testMaker = makeTestImageItem
        else:
            testMaker = makeTestItem
        items = []
        itemCounter = 0

        if flushItems:
            items += [
                testMaker(
                    size,
                    name=str(itemCounter + i),
                    varyWidth=varyWidths,
                    details=details
                )
                for i in range(flushItems)
            ]
            itemCounter = len(items)
        if overshootItems:
            items += [
                testMaker(
                    size,
                    name=str(itemCounter + i),
                    overshoot=(20, 20),
                    varyWidth=varyWidths,
                    fillColor=(1, 1, 0, 0.75),
                    details=details
                )
                for i in range(overshootItems)
            ]
            itemCounter = len(items)
        if negativeAdvanceItems:
            items += [
                testMaker(
                    size,
                    name=str(itemCounter + i),
                    advance=(-20, -20),
                    varyWidth=varyWidths,
                    fillColor=(1, 0, 0, 0.75),
                    details=details
                )
                for i in range(negativeAdvanceItems)
            ]
            itemCounter = len(items)
        if positiveAdvanceItems:
            items += [
                testMaker(
                    size,
                    name=str(itemCounter + i),
                    advance=(20, 20),
                    varyWidth=varyWidths,
                    fillColor=(0, 1, 0, 0.75),
                    details=details
                )
                for i in range(positiveAdvanceItems)
            ]
            itemCounter = len(items)
        if negativePlacementItems:
            items += [
                testMaker(
                    size,
                    name=str(itemCounter + i),
                    placement=(-10, -10),
                    varyWidth=varyWidths,
                    fillColor=(1, 0, 0, 0.75),
                    details=details
                )
                for i in range(negativePlacementItems)
            ]
            itemCounter = len(items)
        if positivePlacementItems:
            items += [
                testMaker(
                    size,
                    name=str(itemCounter + i),
                    placement=(10, 10),
                    varyWidth=varyWidths,
                    fillColor=(0, 1, 0, 0.75),
                    details=details
                )
                for i in range(positivePlacementItems)
            ]
            itemCounter = len(items)

        if shuffle:
            random.shuffle(items)

        self.w.collectionView.setInset(inset)
        self.w.collectionView.setLineHeight(lineHeight)
        self.w.collectionView.setSpacing(spacing)
        self.w.collectionView.setAlignment(alignment)
        self.w.collectionView.set(items)
        # self.w.collectionView.setReflowDuringResize(len(items) < 500)


# -----------------
# Control Shortcuts
# -----------------

metrics = dict(
    margin=15,
    spacing=10,
    title=120,
    field=90
)

class OneField(vanilla.Group):

    def __init__(self, title, value):
        super().__init__("auto")
        self.titleTextBox = vanilla.TextBox(
            "auto",
            title,
            alignment="right"
        )
        self.valueEditText = vanilla.EditText(
            "auto",
            value
        )
        rules = [
            "H:|[titleTextBox(==title)]-spacing-[valueEditText(==field)]|",
            "V:|[titleTextBox]|",
            "V:|[valueEditText]|"
        ]
        self.addAutoPosSizeRules(rules, metrics)

    def get(self):
        return self.valueEditText.get()


class OnePopUp(vanilla.Group):

    def __init__(self, title, options):
        super().__init__("auto")
        self.titleTextBox = vanilla.TextBox(
            "auto",
            title,
            alignment="right"
        )
        self.valuePopUp = vanilla.PopUpButton(
            "auto",
            options
        )
        rules = [
            "H:|[titleTextBox(==title)]-spacing-[valuePopUp(==field)]|",
            "V:|[titleTextBox]|",
            "V:|[valuePopUp]|"
        ]
        self.addAutoPosSizeRules(rules, metrics)

    def get(self):
        value = self.valuePopUp.get()
        value = self.valuePopUp.getItems()[value]
        return value


class OneCheckBox(vanilla.Group):

    def __init__(self, title, value):
        super().__init__("auto")
        self.titleTextBox = vanilla.TextBox(
            "auto",
            title,
            alignment="right"
        )
        self.valueCheckBox = vanilla.CheckBox(
            "auto",
            "",
            value=value
        )
        rules = [
            "H:|[titleTextBox(==title)]-spacing-[valueCheckBox(==field)]|",
            "V:|[titleTextBox]|",
            "V:|[valueCheckBox]|"
        ]
        self.addAutoPosSizeRules(rules, metrics)

    def get(self):
        return self.valueCheckBox.get()


# ---------------
# Item Generators
# ---------------

def makeContainerSize(
        size,
        overshoot,
        varyWidth
    ):
    bodyWidth, bodyHeight = size
    if varyWidth:
        bodyWidth = random.randint(int(bodyWidth * 0.75), int(bodyWidth * 1.5))
    overshootX, overshootY = overshoot
    fullWidth = bodyWidth + (overshootX * 2)
    fullHeight = bodyHeight + (overshootY * 2)
    return (bodyWidth, bodyHeight), (fullWidth, fullHeight)

def setContainerPositioning(
        container,
        size,
        advance,
        placement
    ):
    container.setWidth(size[0])
    container.setHeight(size[1])
    container.setXAdvance(advance[0])
    container.setYAdvance(advance[1])
    container.setXPlacement(placement[0])
    container.setYPlacement(placement[1])

# Merz

def makeTestItem(
        size,
        name="",
        overshoot=(0, 0),
        advance=(0, 0),
        placement=(0, 0),
        varyWidth=False,
        fillColor=(0, 0, 1, 0.75),
        details=False
    ):
    borderColor = (0, 0, 0, 0.25)
    (bodyWidth, bodyHeight), (fullWidth, fullHeight) = makeContainerSize(size, overshoot, varyWidth)
    container = MerzCollectionViewContainer(
        size=(fullWidth, fullHeight),
        imageOrigin=overshoot,
        backgroundColor=fillColor,
        borderColor=borderColor,
        borderWidth=1
    )
    setContainerPositioning(
        container,
        size=(bodyWidth, bodyHeight),
        advance=advance,
        placement=placement
    )
    if details:
        text = "S {size}\nO {overshoot}\nA {advance}\nP {placement}\nn={name}"
        text = text.format(
            size=repr(size),
            overshoot=repr(overshoot),
            advance=repr(advance),
            placement=repr(placement),
            name=name
        )
        t = container.appendTextBoxSublayer(
            size=(bodyWidth, bodyHeight),
            position=overshoot,
            backgroundColor=None,
            borderColor=borderColor,
            borderWidth=1,
            fillColor=(0, 0, 0, 1),
            pointSize=6,
            padding=(5, 5),
            text=text
        )
    return container


# Unwrapped CALayer

class TestCALayer(MerzCALayer, merz.MerzCollectionViewItemMixin):

    def getImageSize(self):
        return self.frame().size

def makeTestCALayerItem(
        size,
        name="",
        overshoot=(0, 0),
        advance=(0, 0),
        placement=(0, 0),
        varyWidth=False,
        fillColor=(0, 0, 1, 0.75),
        details=False
    ):
    borderColor = (0, 0, 0, 0.25)
    (bodyWidth, bodyHeight), (fullWidth, fullHeight) = makeContainerSize(size, overshoot, varyWidth)
    container = TestCALayer.alloc().init()
    container.setFrame_(((0, 0), (fullWidth, fullHeight)))
    container.setBackgroundColor_(Quartz.CGColorCreateGenericRGB(*fillColor))
    container.setBorderColor_(Quartz.CGColorCreateGenericRGB(*borderColor))
    container.setBorderWidth_(1.0)
    container.setImageOrigin(overshoot)
    setContainerPositioning(
        container,
        size=(bodyWidth, bodyHeight),
        advance=advance,
        placement=placement
    )
    return container


# NSImage

_imageCache = {}

def makeTestImageItem(
        size,
        name="",
        overshoot=(0, 0),
        advance=(0, 0),
        placement=(0, 0),
        varyWidth=False,
        fillColor=(0, 0, 1, 0.75),
        details=False
    ):
    borderColor = (0, 0, 0, 0.25)
    (bodyWidth, bodyHeight), (fullWidth, fullHeight) = makeContainerSize(size, overshoot, varyWidth)
    key = (
        ("size", (fullWidth, fullHeight)),
        ("fillColor", fillColor)
    )
    if key not in _imageCache:
        bot = NSImageDrawingTools((fullWidth, fullHeight))
        bot.fill(*fillColor)
        bot.stroke(*borderColor)
        bot.strokeWidth(1)
        bot.rect(0, 0, fullWidth, fullHeight)
        image = bot.getImage()
        _imageCache[key] = image
    image = _imageCache[key]
    container = TestCALayer.alloc().init()
    container.setFrame_(((0, 0), (fullWidth, fullHeight)))
    container.setContents_(
        image.layerContentsForContentsScale_(container.contentsScale())
    )
    container.setImageOrigin(overshoot)
    setContainerPositioning(
        container,
        size=(bodyWidth, bodyHeight),
        advance=advance,
        placement=placement
    )
    return container


if __name__ == "__main__":
    TestWindow()