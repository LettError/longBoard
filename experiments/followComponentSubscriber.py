#!/usr/bin/env python3

# ---------------------------------------------------------- #
# Get a notification when a component inside a glyph changes #
# ---------------------------------------------------------- #

# -- Modules -- #
from mojo.subscriber import Subscriber, registerCurrentFontSubscriber

# -- Constants -- #

# -- Objects, Functions, Procedures -- #
class FollowComponentSubscriber(Subscriber):

    debug = True

    def build(self):
        print("build")

    def started(self):
        print("started")

    def destroy(self):
        print("destroy")

    def currentFontGlyphDidChangeComponents(self, info):
        print(info['glyph'].name)


# -- Instructions -- #
if __name__ == '__main__':
    registerCurrentFontSubscriber(FollowComponentSubscriber)
