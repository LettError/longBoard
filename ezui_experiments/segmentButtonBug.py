import ezui
from mojo.subscriber import Subscriber, WindowController

class SegmentButtonTest(Subscriber, WindowController):
    
    def build(self):
        print('starting')
        mySegmentButton = dict(
                type="SegmentButton",
                identifier="mySegmentButton",
                style='any',     # when commented out, this works
                segmentDescriptions=[
                    dict(text = "A"),
                    dict(text = "B"),
                    dict(text = "C"),
                ]
            )                    

        windowDescription = dict(
            type="Window",
            size=("auto", "auto"),
            title="HeyHeyHey",
            contentDescription=mySegmentButton,
        )

        self.w = ezui.makeItem(
            windowDescription
        )

    def started(self):
        self.w.open()
        print("hi")


if __name__ == '__main__':
    print('boo')
    OpenWindow(SegmentButtonTest)
