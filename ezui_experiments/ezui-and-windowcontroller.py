from mojo.subscriber import Subscriber, WindowController
import ezui


import ezui

class Demo(Subscriber, WindowController):

    def build(self):
        stackContent = [
            dict(
                type="Label",
                text="This is some text."
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
            title="VerticalStack",
            contentDescription=windowContent
        )
        self.w = ezui.makeItem(
            windowDescription
        )

    def started(self):
        self.w.open()

    def stackCallback(self, sender):
        print(sender.get())

Demo()