#!/usr/bin/env python3

from mojo.subscriber import registerSubscriberEvent

TOOL_KEY = 'com.lettError.LongBoard'

if __name__ == '__main__':
    registerSubscriberEvent(
        subscriberEventName=f"{TOOL_KEY}.changed",
        methodName="paletteDidChange",
        lowLevelEventNames=[f"{TOOL_KEY}.changed"],
        dispatcher="roboFont",
        documentation="Send when the tool palette did change parameters.",
        delay=0,
        debug=True
    )
