# PartiallyTransparentImage

A simple tool to make an image partially transparent.
Useful when, for example, making a heightfield image partially transparent to make a hole in terrain.
(See https://github.com/taKana671/TerrainWithHole)

# Requirements
* numpy 2.1.2
* opencv-contrib-python 4.10.0.84
* opencv-python 4.10.0.84
* pillow 11.0.0
  
# Environment
* Python 3.11
* Windows11

# Usage
* Execute a command below on your command line.
```
>>>cd image_editor
>>>python image_editor.py
```

1. Click [File > Open] to select an image file.
2. Select the area that you want make transparent by mouse dragging.
3. Click [File > Save] to save the image. The image made partially transparent will be output.
4. Click [Edit > Undo] and select transparent area to undo the changes.
5. Input alpha value in the range from 0 to 255 into the alpha field to change transparency.

![demo1](https://github.com/user-attachments/assets/60eecb27-3b44-4509-b23f-cf61acda89b5)

output file

![result](https://github.com/user-attachments/assets/feb1163d-4c17-4f0b-8a3a-b98edaad8d38)

