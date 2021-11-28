# Noteplan Theming


## JSON Attributes
Hint: The Settings are discovered and used by my theme, maybe on some attributes there are more settings possible!

### editor

#### textColor
- Foldername on the top left
- Settings: on the top right
- Calendar Dates
- Calendar Times
- File Icons in the folder tree

#### tintColor
- Cursor
- Hashtags
- Mentions
- Links

#### tintColor2
- Overlay for the selected date in the calendar

#### toolbarBackgroundColor
- Background of new event/reminder popup
- Line separator under the references area
- Hover over the buttons on the top and the dates

#### menuItemColor
- Icons, month and year on the top in the iphone app
- Date and icons under the calendar (on top of the note of the selected day)

#### toolbarIconColor
- Icons of the iphone toolbar while editing a note

### standard styles

#### body
- Style of default text in the note body
- Settings: `color, font, size`

#### title(n)
- Style of headings
- Settings: `color, font, size, type`

#### title-mark(n)
- Style of markdown heading syntax
- Line spacing is the spacing for one line of the heading (only seen if you have multiple lines)
- Paragraph spacing is the spacing below the heading
- Paragraph spacing before is the spacing before the heading
- Settings: `color, font, lineSpacing, paragraphSpacing, paragraphSpacingBefore, size, type`

#### bold
- Style of bold text
- Settings: `color, font`

#### bold-left-mark / bold-right-mark
- Color of markdown bold syntax
- Settings: `color`

#### boldItalic
- Style of bold-italic text
- Settings: `color, font`

#### boldItalic-left-mark / boldItalic-right-mark
- Color of markdown bold-italic syntax
- Settings: `color`

#### italic
- Style of italic text
- Settings: `color, font`

#### italic-left-mark / bold-italic-mark
- Color of markdown italic syntax
- Settings: `color`

#### code
- Style of inline code
- Settings: `color, font, size`

#### code-left-backtick / code-right-backtick
- Color of the markdown backticks for the inline code block
- Settings: `color`

#### quote-mark
- Style of the quote dash on the left of a qoute
- Attention: Don't change font of "noteplanstate"
- Settings: `color, font, headIndent, size`

#### quote-content
- Color of the quote content
- Settings: `color`

#### todo
- Style of the task circle, bullet and numbering
- Attention: Don't change font of "noteplanstate"
- Settings: `color, font, headIndent, size`

#### checked
- Color of completed and scheduled tasks
- Settings: `color, headIndent`

#### checked-todo-characters
- Front and size of checked tasks (including the icon)
- Attention: Don't change font of "noteplanstate"
- Settings: `font, headIndent, size`

#### special-char
- The markdown characters `*` and `-` during the initial input (before they change to the icon)
- Attention: According to the official documentation one should not change the font "Menlo-Regular"
- Settings: `font, size`

#### link
* Attention: Don't add settings here, otherwise you have it styled but can't click the link at least on macOS
* Style of a link
* Settings: `color, size, type`

#### schedule-to-date-link
* Attention: Don't add settings here, otherwise you have it styled but can't click the link at least on macOS
* Style of a date link of a scheduled task
* Settings: `color, size, type`

#### schedule-from-date-link
* Attention: Don't add settings here, otherwise you have it styled but can't click the link at least on macOS
* Style of a date link of a rescheduled task
* Settings: `color, size, type`

#### code-fence
* Style of the code fence
* You can e.g. add a predefined theme (look at official documentation), add border radius etc.
* Settings: `corner-radius, body.font, body.backgroundColor, language-speficier.font, language-specifier.color, fence-open.color, fence-close.color`

#### tabbed
- I don't know

#### done
- I don't know

### custom styles via regex
You can create custom styles via regex, e.g. highlight text, strikethrough text or hide text on a certain pattern.

#### example: highlight text `::text::`
```
"highlighted": {
  "backgroundColor": "#1057E8",
  "color": "#D2D2D3",
  "isRevealOnCursorRange": true,
  "matchPosition": 2,
  "regex": "(::)([^:]{1,})(::)"
},
"highlighted-left-colon": {
  "isHiddenWithoutCursor": true,
  "isMarkdownCharacter": true,
  "isRevealOnCursorRange": true,
  "matchPosition": 1,
  "regex": "(::)([^:]{1,})(::)"
},
"highlighted-right-colon": {
  "isHiddenWithoutCursor": true,
  "isMarkdownCharacter": true,
  "isRevealOnCursorRange": true,
  "matchPosition": 3,
  "regex": "(::)([^:]{1,})(::)"
},
```

### example: strikethrough text `~~text~~`
```
"strikethrough": {
  "color": "#78787B",
  "isRevealOnCursorRange": true,
  "matchPosition": 2,
  "regex": "(~~)([^~]{1,})(~~)",
  "strikethroughStyle": 1,
},
"strikethrough-left-tilde": {
  "color": "#78787B",
  "isHiddenWithoutCursor": true,
  "isMarkdownCharacter": true,
  "isRevealOnCursorRange": true,
  "matchPosition": 1,
  "regex": "(~~)([^~]{1,})(~~)"
},
"strikethrough-right-tilde": {
  "color": "#78787B",
  "isHiddenWithoutCursor": true,
  "isMarkdownCharacter": true,
  "isRevealOnCursorRange": true,
  "matchPosition": 3,
  "regex": "(~~)([^~]{1,})(~~)"
},
```
