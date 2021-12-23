from mojo.subscriber import registerRoboFontSubscriber, Subscriber, WindowController
from vanilla import FloatingWindow
from mojo.roboFont import CurrentFont

class Tool(Subscriber, WindowController):

    def build(self):
        self.w = FloatingWindow((200, 40), "Controller")

    def started(self):
        fontObj = CurrentFont()
        for glyphName in 'ABC':
            self.addAdjunctObjectToObserve(fontObj[glyphName])

    def destroy(self):
        fontObj = CurrentFont()
        for glyphName in 'ABC':
            self.addAdjunctObjectToObserve(fontObj[glyphName])

    def adjunctGlyphDidChangeContours(self, info):
        print(f'contours changed {info["glyph"]}')


if __name__ == '__main__':
    registerRoboFontSubscriber(Tool)
