#!/usr/bin/env python3

# ------------- #
# CUSTOM EVENTS #
# ------------- #

# -- Modules -- #
from mojo.subscriber import registerSubscriberEvent, getRegisteredSubscriberEvents


# -- Constants -- #
TOOL_KEY = 'com.lettError.LongBoard'
DEBUG_MODE = True


# -- Events -- #
if __name__ == '__main__':
    subscriberEvents = getRegisteredSubscriberEvents()

    # current design space location
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

    # glyph mutator
    def glyphMutatorDidChangeInfoExtractor(subscriber, info):
        info["glyphName"] = []
        for lowLevelEvent in info["lowLevelEvents"]:
            info["glyphName"] = lowLevelEvent["glyphName"]

    eventName = f"{TOOL_KEY}.glyphMutatorDidChange"
    if eventName not in subscriberEvents:
        registerSubscriberEvent(
            subscriberEventName=eventName,
            methodName="glyphMutatorDidChange",
            lowLevelEventNames=[eventName],
            documentation="a glyph mutator did change",
            dispatcher="roboFont",
            eventInfoExtractionFunction=glyphMutatorDidChangeInfoExtractor,
            delay=0.2,
            debug=DEBUG_MODE
        )

    # var model
    eventName = f"{TOOL_KEY}.varModelDidChange"
    if eventName not in subscriberEvents:
        registerSubscriberEvent(
            subscriberEventName=eventName,
            methodName="varModelDidChange",
            lowLevelEventNames=[eventName],
            documentation="the var model did change",
            dispatcher="roboFont",
            delay=0.2,
            debug=DEBUG_MODE
        )

    # var model
    eventName = f"{TOOL_KEY}.controllerWillClose"
    if eventName not in subscriberEvents:
        registerSubscriberEvent(
            subscriberEventName=eventName,
            methodName="controllerWillClose",
            lowLevelEventNames=[eventName],
            documentation="main controller window will close",
            dispatcher="roboFont",
            delay=0,
            debug=DEBUG_MODE
        )
