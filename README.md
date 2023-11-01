# LongBoard

A new edition of the tool formerly known as Skateboard, smoothly rolling on subscriber, ezui and merz, and free. It is also rough, unfinished, likely misinformed about major concepts and as such a research project rather than a neatly packed finished extension.

The goal is to provide quick and easy to navigate previews of the sources and interpolation of the glyph in the glyph editor. It should also calculate and draw measurements.

DSE2 and UFOOperator now take care of all the heavy lifting that Skateboard had to do. No building of mutators or managing fonts. This is great.

## Interaction sources
I like the idea of **interaction sources** from Skateboard. This is a table that maps each continuous axis in a designspace to a preferred dragging direction of the mouse. If **weight** maps to **horizontal**, the horizontal component of the drag relates to some sort of meaningful change to the axis values of the interpolation on preview. This table is part of the `LongBoardUIController`

## Relevant designspace and current discrete location
The glyph editor shows a glyph that belongs to a font. In turn, this font belongs to a designspace. So, the *relevant* designspace is not necessarily the *current* designspace. Also we only want to show the sources and interpolation that are related to the discrete location this font belongs to. So, we can infer the *current discrete location* from the designlocation the font of the glyph in the glypheditor.

## Action: glypheditor gets a new glyph
So when the glyph in the glypheditor is changed (for instance through EditNext), the following steps need to happen:
* `LongboardEditorView.relevantForThisEditor()` is called to find a designspace that this glyph can belong to. There may be multiple designspaces open. There may be fonts open that are not part of a designspace.
* If it finds a designspace, it will post a notification `operatorChangedEventKey` which `LongBoardUIController.relevantOperatorChanged` subcribes to. This allows the controller to update the axes in the interaction sources table. Changes to the interaction sources are written to the operator's lib.
* `LongboardEditorView.updateOutline` then rebuilds all the merz layers. 

 For the navigation part, I subclassed `BaseEventTool`

## Action: DSE2 makes changes in the designspace
`LongboardEditorView` subscribes to a couple of notifications from DSE2. These trigger some checks and a `updateOutline`.

## Action: LongboardNavigator makes a change
The `LongboardNavigatorTool` does not know about changes to the relevant operator. Ah, but it can. More research.


## Requirements

* RF 4.4+
* Open a designspace in DSE2
* Open a glyph window
* It may be necessary to install UFOProcessor.UFOOperator from its repository rather than rely on the one in RF. 

## Moving parts



### LongBoardUIController

### LongboardEditorView

### LongboardNavigatorTool

## Thanks

Based on many experiments and iterations and not anywhere done. Thanks for Frederik Berlaen, Tal Leming, Roberto Arista. 


