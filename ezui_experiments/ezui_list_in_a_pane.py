import ezui
import AppKit

# https://typesupply.github.io/ezui/windows.html?highlight=toolbar

class Demo(ezui.WindowController):

    def build(self):


        myListDescription = dict(
            identifier="complexTable",
            type="Table",
            columnDescriptions=[
                dict(
                    identifier="letter",
                    title="Letter",
                    width=35,
                    editable=True
                ),
                dict(
                    identifier="numbers",
                    title="Numbers",
                    width=50,
                    cellDescription=dict(
                        valueType="integerList"
                    ),
                    editable=True
                ),
                dict(
                    identifier="value",
                    title="Value",
                    cellDescription=dict(
                        cellType="Slider",
                        minValue=0,
                        maxValue=1
                    ),
                    editable=True
                )
            ],
            items=[
                dict(
                    letter="A",
                    numbers=[1],
                    value=0
                ),
                dict(
                    letter="B",
                    numbers=[2, 2],
                    value=0.5
                ),
                dict(
                    letter="C",
                    numbers=[3, 3, 3],
                    value=1
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
                   myListDescription
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
            title="EZUI_Frankenstein",
            contentDescription=windowContent
        )
        self.w = ezui.makeItem(
            windowDescription
        )

    def started(self):
        self.w.open()

Demo()