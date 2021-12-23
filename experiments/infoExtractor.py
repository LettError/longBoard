from mojo.subscriber import Subscriber, registerRoboFontSubscriber, registerSubscriberEvent

class SimpleSubscriberDemo(Subscriber):

    def myCustomSubscriberMethod(self, info):
        print("myCustomSubscriberMethod", info)

def simpleSubscriberEventInfoExtractor(subscriber, info):
    info["information"] = []
    for lowLevelEvent in info["lowLevelEvents"]:
        info["information"] = lowLevelEvent["information"]

registerSubscriberEvent(
    subscriberEventName="com.robofont.demo.subscriberEvent",
    methodName="myCustomSubscriberMethod",
    lowLevelEventNames=["com.robofont.demo.mojoEvent"],
    dispatcher="roboFont",
    delay=1,
    eventInfoExtractionFunction=simpleSubscriberEventInfoExtractor,
    documentation="This is my custom subscriber method."
)

registerRoboFontSubscriber(SimpleSubscriberDemo)


# ------------------
# SOME TIME LATER...
# ------------------

import random
from mojo.events import postEvent

postEvent("com.robofont.demo.mojoEvent", information="data", number=random.choice((-1, 1)))