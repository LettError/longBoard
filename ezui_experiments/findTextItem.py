import ezui
from mojo.subscriber import Subscriber, WindowController

class SetSomething(Subscriber, WindowController):

    debug = True

    def build(self):

        stackContent = [
            dict(
                type="Label",
                text="This is some text.",
                identifier="documentPathText",
            ),
        ]

        windowContent = dict(
            type="VerticalStack",
            contentDescriptions=stackContent,
            callback=self.stackCallback
        )
        windowDescription = dict(
            type="Window",
            size=(300, "auto"),
            title="Lalala",
            contentDescription=windowContent
        )
        self.w = ezui.makeItem(
            windowDescription
        )

    def started(self):
        self.w.open()
        
        # can I set the text?
        # it's not finding it..
        print("haha", self.w.findItem('documentPathText'))
        
    def stackCallback(self, sender):
        print(sender.get())
    
SetSomething()