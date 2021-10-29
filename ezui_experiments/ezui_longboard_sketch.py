import ezui
import AppKit

# https://typesupply.github.io/ezui/windows.html?highlight=toolbar

class Demo(ezui.WindowController):

    def build(self):

        segmentButtonItem = dict(
            identifier="segmentButtonToolbarItem",
            text="Button",
            itemDescription=dict(
                type="SegmentButton",
                identifier="segmentButton",
                segmentDescriptions=[
                    dict(text = "Close"),
                    dict(text = "Save"),
                    dict(text = "Edit"),
                    dict(text = "Variable Font"),
                    dict(text = "Text"),
                    dict(text = "Space"),
                ]
            )
        )
        
        itemDescriptions = [
            segmentButtonItem,
        ]
        
        toolbarDescription = dict(
            identifier="longBoardToolbar",
            itemDescriptions=itemDescriptions,
            displayMode="image"
        )

        sourcesListDescription = dict(
            identifier="sourcesTable",
            type="Table",
            columnDescriptions=[
                dict(
                    identifier="status",
                    title="",
                    width=35,
                ),
                dict(
                    identifier="isDefault",
                    title="",
                    width=35,
                ),
                dict(
                    identifier="ufoName",
                    title="UFO",
                    width=100,
                ),
                dict(
                    identifier="layerName",
                    title="Layer",
                    width=100,
                ),
            ],
            items=[
                dict(
                    status="ok",
                    isDefault=False,
                    ufoName="Aaaa.ufo",
                    layerName=None
                ),
                dict(
                    status="ok",
                    isDefault=False,
                    ufoName="Bbbb.ufo",
                    layerName=None
                ),
                dict(
                    status="ok",
                    isDefault=False,
                    ufoName="Cccc.ufo",
                    layerName=None
                ),
            ],
            width=400,
            height=400
        )
                
        pane1Description = dict(
            type="Pane",
            identifier="pane1",
            text="Sources and Layers",
            contentDescription=dict(
                type="VerticalStack",
                contentDescriptions=[
                   sourcesListDescription
                  ]
            )
        )
        pane2Description = dict(
            type="Pane",
            identifier="pane1",
            text="Current Location",
            closed=True,
            contentDescription=dict(
                type="VerticalStack",
                contentDescriptions=[
                    dict(
                        type="PushButton",
                        text="Button 3"
                    ),
                    dict(
                        type="PushButton",
                        text="Button 4"
                    )
                ]
            )
        )
        pane3Description = dict(
            type="Pane",
            identifier="pane1",
            text="All Locations",
            closed=True,
            contentDescription=dict(
                type="VerticalStack",
                contentDescriptions=[
                    dict(
                        type="PushButton",
                        text="Button 4"
                    ),
                    dict(
                        type="PushButton",
                        text="Button 5"
                    )
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
            size=(500, "auto"),
            title="Longboard",
            toolbarDescription=toolbarDescription      ,      
            contentDescription=windowContent
        )
        self.w = ezui.makeItem(
            windowDescription
        )

    def started(self):
        self.w.open()

Demo()