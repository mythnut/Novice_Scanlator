# Novice_Scanlator
This is a tool to assist in quick-and-dirty file scanlation. It is a WIP.

When run, it first prompts you to select the directory containing the image files to be scanlated. It is only set up to work with .png files currently.
It then prompts you to choose the first image file to scanlate.
Click and drag with the left mouse button to position the selection box around a block of text.
Add or delete selection boxes via the file menu or right click menu.
Both OCR and tranlsation are automatically run when you adjust the selection box.
You can adjust both the OCR text and the translated text manually, and manually re-run either process with their respective buttons.
When finished with an image file, you can click the export button to create a new image with the translated text.
You can save your work with the file menu.

Requires io, os, pytesseract, Pillow, googletrans, tkinter, json, glob