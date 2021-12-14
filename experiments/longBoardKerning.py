# longboard kerning
# kerning dict based on a set of mutators 
# assuming kerning does not need to be live
# and even when it is live, it does not need to be superfast

# object with a mutator for each pair
# reading can be quick
# less overhead in maintaining kernlets

# import from kerning objects
# pre-make all the things? just do it on demand?
# groups? or flat?
# or: handle invidual requests, update those

from mutatorMath import Mutator

class LongBoardKerning(object):
    pass

    