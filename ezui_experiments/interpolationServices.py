# interpolator services


"""

    * list of open designspaces
    * list of available sources / open / on disk
    * construct interpolation object, either varlib or mutatormath
    * update interpolation object when there are changes
        - listen to changes somehow?
    * "I need to show glyph A, glyph B"
        - figure out dependencies
        - check if these are already available
        - make new interpolation objects (what were they called in skateboard)
    * report on errors
    * generate different kinds of interpolations
        * different locations
        * different types of data that can fit into CA layers
        * maybe have some sort of pen interface
    
    # which layers are we going to need
        - interpolated outline
        - points on the outline
        - something in the measurement object -> eventually check with Frederik
        
    request could be:
        <designspace><glyphname><layername><visualisationtype><designspacelocation><interpolationtype>
        ('MyDesign.designspace', ['adieresis', 'f_f_i'], 'foreground', ['outline', 'markers'], (('wght', 1000), ('opsz',39), 'mutatormath'))
        # that's already quite complicated, isn't it
        
    textviews
        multiple lines above each other, each with its own location
        also from different designspaces?        
        mixing different styles? 
        
    Can we prepare
        
"""

