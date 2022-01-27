#!/usr/bin/env python3

# ------------ #
# Script title #
# ------------ #

# -- Modules -- #
from mojo.subscriber import registerCurrentFontSubscriber
from followComponentSubscriber import FollowComponentSubscriber

# -- Instructions -- #
if __name__ == '__main__':
    registerCurrentFontSubscriber(FollowComponentSubscriber)
