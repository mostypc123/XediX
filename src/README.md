## Source Code of XediX
In this folder, you can find the source code of XediX. **Here is a explanation of what all the files mean.**

### main.py
really? do you need a description of a file that is called main?!
### tools.py
The tools selector in XediX, when you press <kbd>Ctrl</kbd>+<kbd>T</kbd>, or select _Tools_ / _Tools_ in the menu.
### requirements.py
A requirements.txt generator.
### tools/*
The tools included in XediX.
### git_integration.py
The Git integration in XediX
### github.py
Send notifications when a GitHub repository has a new issue/PR.
To set it up, use 
#### repo.ghicfg
The GitHub configuration file. Set repos as stated in the docs.
### settings.py
Settings for XediX.
### requirements.txt
The requirements to run XediX using Python. Run this to install:
```sh
# Windows
pip install -r reqiurements.txt
# macOS / Linux
pip3 install -r requirements.txt
```
### extension_*.py
The extension files.
### xedix.xcfg
Used to config colors of the header of the window.
### theme.xcfg
A XediX config file to set up themes.
Available themes: **Dark**, **Light**, **Obsidian** and **Night**.
As a default theme is set ```dark```.