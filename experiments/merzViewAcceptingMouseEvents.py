from mojo.roboFont import OpenWindow
from mojo.subscriber import Subscriber, WindowController
from merz import MerzView
from vanilla import Window, VerticalStackView

class SpaceWindow(Subscriber, WindowController):

    debug = True

    def build(self):
        self.w = Window((400, 80), "Merz Window", minSize=(200, 40))
        self.view = MerzView(
            "auto",
            backgroundColor=(1, 1, 1, 1),
            delegate=self
        )
        self.w.stack = VerticalStackView(
            (0, 0, 0, 0),
            views=[dict(view=self.view)],
            edgeInsets=(10, 10, 10, 10)
        )
        self.w.open()

    def acceptsFirstResponder(self, sender):
        return True

    def started(self):
        print('started!')

    def destroy(self):
        print('destroy')

    def mouseDragged(self, view, event):
        print(f'mouse dragged: {event}')

    def mouseDown(self, view, event):
        print(f'mouse down: {event}')


if __name__ == '__main__':
    OpenWindow(SpaceWindow)