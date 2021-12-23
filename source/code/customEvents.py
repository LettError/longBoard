#!/usr/bin/env python3

# ------------- #
# CUSTOM EVENTS #
# ------------- #

# -- Modules -- #
from mojo.subscriber import registerSubscriberEvent, getRegisteredSubscriberEvents


# -- Constants -- #
TOOL_KEY = 'com.lettError.LongBoard'
DEBUG_MODE = True

if __name__ == '__main__':

# -- Events -- #
    subscriberEvents = getRegisteredSubscriberEvents()

    eventName = f"{TOOL_KEY}.currentDesignSpaceLocationDidChange"
    if eventName not in subscriberEvents:
        registerSubscriberEvent(
            subscriberEventName=eventName,
            methodName="currentDesignSpaceLocationDidChange",
            lowLevelEventNames=[eventName],
            documentation="from controller to subscribers",
            dispatcher="roboFont",
            delay=0.2,
            debug=DEBUG_MODE
        )
