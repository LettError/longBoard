import ezui
import AppKit

# https://typesupply.github.io/ezui/windows.html?highlight=toolbar

class Demo(ezui.WindowController):

    def build(self):


        sourcesListDescription = dict(
            identifier="complexTable",
            type="Table",
            columnDescriptions=[
                dict(
                    identifier="status",
                    title="",
                    width=35,
                ),
            ],

            items=[
                dict(
                    letter="A",
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
        windowContent = dict(
            type="VerticalStack",
            contentDescriptions=[
                pane1Description,
            ]
        )
        windowDescription = dict(
            type="Window",
            size=(500, "auto"),
            title="Longboard",
            contentDescription=windowContent
        )
        self.w = ezui.makeItem(
            windowDescription
        )

    def started(self):
        self.w.open()

Demo()