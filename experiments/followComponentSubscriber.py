#!/usr/bin/env python3

# ---------------------------------------------------------- #
# Get a notification when a component inside a glyph changes #
# ---------------------------------------------------------- #

"""
This snippet should work, but there is an issue in Subscriber
It's safer to use a .reversedComponentMapping() method inside a
glyph changed callback, we'll use that in Longboard
"""

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
