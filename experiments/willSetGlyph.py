from mojo.subscriber import Subscriber, registerGlyphEditorSubscriber

class Example(Subscriber):

    debug = True

    def build(self):
        print("hello!")

    def glyphEditorWillSetGlyph(self, info):
        print(info)
        print(info['glyph'])
        print('*'*20)

if __name__ == '__main__':
    registerGlyphEditorSubscriber(Example)
