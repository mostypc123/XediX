import sys
import os
import random
import time
import wx
import wx.adv
import subprocess
import wx.stc as stc
import requests
import webbrowser
import threading
import psutil
import hashlib
import json

if wx.Platform == "__WXMSW__":
    import pywinstyles
    from pypresence import Presence  # Discord Rich Presence

# ----------- Globals for splash -----------

wx_app = None
splash = None
splash_status = None

# ----------- Splash screen setup -----------

def create_wx_app():
    """
    Initializes a wx.App instance if one is not already running.
    
    Ensures that a wxPython application context exists before creating any GUI elements.
    """
    global wx_app
    if wx.App.IsMainLoopRunning():
        # wx.App already running
        return
    if not wx.App.GetInstance():
        wx_app = wx.App(False)

def setup_splash():
    """
    Displays the application splash screen with a randomly selected image, handling first-time user logic and squad preference weighting.
    
    On first run, selects a splash image from the "new-user" directory, saves the user's squad preference, and updates configuration files. On subsequent runs, selects from the "normal" splash directory, favoring images associated with the user's previously chosen squad. The splash screen is centered and shown until manually closed.
    """
    global splash, splash_status

    firsttime = False
    selected_squad = None

    # Handle firsttime config
    try:
        if not os.path.exists("firsttime.xcfg"):
            with open("firsttime.xcfg", "w") as f:
                f.write("True")

        with open("firsttime.xcfg", "r+") as f:
            content = f.read().strip()
            if content == "True":
                firsttime = True
                f.seek(0)
                f.write("False")
                f.truncate()
    except Exception as e:
        print(f"DEBUG: Error handling firsttime.xcfg: {e}")

    # Determine splash directory
    splash_dir = "assets/splash/new-user/" if firsttime else "assets/splash/normal/"
    pngs = [f for f in os.listdir(splash_dir) if f.lower().endswith(".png")]
    if not pngs:
        print("DEBUG: No PNG splash images found.")
        return

    # Map filenames to squads
    squad_map = {
        # new-user splashes
        "2.png": "Colory Mountains",
        "4.png": "Orange Front",
        "6.png": "Simplistic Developer",
        # normal splashes
        "1.png": "Colory Mountains",
        "7.png": "Orange Front",
        "3.png": "Simplistic Developer",
    }

    # Try reading existing squad choice
    saved_squad = None
    if not firsttime and os.path.exists("squad.xcfg"):
        try:
            with open("squad.xcfg", "r") as f:
                saved_squad = f.read().strip()
        except Exception as e:
            print(f"DEBUG: Failed to read squad.xcfg: {e}")

    # Assign weights to each image
    weights = []
    for fname in pngs:
        squad = squad_map.get(fname, None)
        if squad and squad == saved_squad:
            weights.append(4)  # Boost for user's squad
        else:
            weights.append(1)

    splash_file = random.choices(pngs, weights=weights, k=1)[0]
    splash_path = os.path.join(splash_dir, splash_file)
    bitmap = wx.Bitmap(splash_path, wx.BITMAP_TYPE_PNG)

    # If this is first time, save the chosen squad
    if firsttime:
        selected_squad = squad_map.get(splash_file, "Unknown Squad")
        try:
            with open("squad.xcfg", "w") as f:
                f.write(selected_squad)
        except Exception as e:
            print(f"DEBUG: Failed to write squad.xcfg: {e}")

    splash = wx.adv.SplashScreen(
        bitmap,
        wx.adv.SPLASH_CENTRE_ON_SCREEN | wx.adv.SPLASH_NO_TIMEOUT,
        0,
        None, -1
    )

    panel = wx.Panel(splash)
    panel.Layout()
    splash.Show()

    # Force splash screen to update
    for _ in range(50):
        wx.GetApp().Yield()
        time.sleep(0.01)


def update_splash(text):
    """
    Update the splash screen status label with the provided text.
    
    If the splash screen and its status label are available, updates the displayed message and refreshes the layout.
    """
    try:
        if splash and splash_status:
            splash_status.SetLabel(text)
            splash_status.Parent.Layout()
            wx_app.Yield()
    except Exception:
        pass

def close_splash():
    """
    Closes and destroys the splash screen window if it is currently displayed.
    """
    try:
        if splash:
            splash.Destroy()
    except Exception:
        pass

def main():
    """
    Displays the splash screen during application startup and closes it after a brief delay.
    """
    create_wx_app()
    setup_splash()
    update_splash("Preparing environment...")
    time.sleep(1)
    close_splash()
    print("DEBUG: Splash screen shown.")

if __name__ == "__main__":
    main()

import extension_menubar
import extension_mainfn
import extension_mainclass
import extension_themes
# import requirements <-- currently being recoded in rust
import git_integration
import settings
import github
import init_project
import error_checker
import merge_resolver

class TextEditor(wx.Frame):
    def __init__(self, *args, **kwargs):
        """
        Initializes the TextEditor window, applying platform-specific styles, loading configuration, and setting up Discord Rich Presence if enabled.
        
        On Windows, loads header color settings from configuration, applies Mica style, and initializes Discord Rich Presence based on user preference. Binds window activation events for dynamic header color changes, initializes the UI, and prepares internal state variables.
        """
        super(TextEditor, self).__init__(*args, **kwargs)
        
        if wx.Platform == "__WXMSW__":
            # Initialize RPC as None by default
            self.RPC = None

            # Load config values from the xcfg file
            config = self.load_config("xedix.xcfg")
            self.active_color = config.get("headerActive", "#EDF0F2") # Default values if not found
            self.inactive_color = config.get("headerInactive", "#b3d0e4") # Default values if not found

            # Apply style and set initial header color
            try:
                pywinstyles.apply_style(self, "mica")
                pywinstyles.change_header_color(self, color=self.active_color)
            except Exception:
                pass
            
            with open('discord.xcfg', 'r') as file:
                presence = file.read()

            
            if presence == "True":
                try:
                    CLIENT_ID = '1332012158376083528'
                    self.RPC = Presence(CLIENT_ID)  # Store as instance variable
                    self.RPC.connect()
                    self.RPC.update(
                        state="XediX",
                        details="Idling",
                        large_image="xedix_logo",
                        large_text="XediX",
                        small_text="XediX"
                    )
                except Exception as e:
                    print(f"Could not update Discord status: {e}")
                    try:
                        if self.RPC:
                            self.RPC.close()  # Properly close the connection
                    except:
                        pass
                    self.RPC = None
            
        # Bind focus events for dynamic color change
        self.Bind(wx.EVT_ACTIVATE, self.on_activate)

        self.output_window = None
        self.InitUI()

    @staticmethod
    def load_config(filepath):
        """
        Load key-value pairs from a .xcfg file.
        """
        config = {}
        try:
            with open(filepath, "r") as file:
                content = file.read().strip()
                for pair in content.split(";"):
                    if ":" in pair:
                        key, value = pair.split(":", 1)
                        config[key.strip()] = value.strip()
        except FileNotFoundError:
            print(f"Config file {filepath} not found. Using defaults.")
        except Exception as e:
            print(f"Error reading config file: {e}")
        return config

    def on_activate(self, event):
        """
        Handles window activation and deactivation events to update the window header color accordingly.
        
        Updates the header color based on whether the window is active or inactive, and ensures the event is propagated for further processing.
        """
        try:
            if event.GetActive():
                pywinstyles.change_header_color(self, color=self.active_color)
            else:
                pywinstyles.change_header_color(self, color=self.inactive_color)
        except Exception:
            pass

        # Ensure event is processed further
        event.Skip()


    def InitUI(self):
        """
        Initializes the main user interface components of the XediX text editor window.
        
        Sets up the window icon, sidebar with a file list and "New File" button, main panel with a welcome message and a random tip (fetched from a remote JSON source), a hidden notebook for file tabs, and a status bar. Arranges all elements using sizers and a splitter window for a responsive layout. Applies platform-specific colors and fonts, binds relevant UI events, and creates the application menu bar.
        """
        panel = wx.Panel(self)

        # Set window icon
        try:
            icon = wx.Icon("assets/icons/xedixlogo.ico", wx.BITMAP_TYPE_ICO)
            self.SetIcon(icon)
        except Exception as e:
            print("Error setting window icon:", e)

        splitter = wx.SplitterWindow(panel)

        self.sidebar = wx.Panel(splitter)
        self.sidebar.SetWindowStyleFlag(wx.NO_BORDER)
        self.sidebar_notebook = wx.Notebook(self.sidebar)

        # Files Tab
        self.files_tab = wx.Panel(self.sidebar_notebook)
        new_file_btn = wx.Button(self.files_tab, label="New File")
        new_file_btn.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        new_file_btn.SetWindowStyleFlag(wx.NO_BORDER)
        new_file_btn.SetMinSize((150, 35))
        new_file_btn.SetMaxSize((150, 35))
        new_file_btn.Bind(wx.EVT_BUTTON, self.OnNewFile)
        self.file_list = wx.ListBox(self.files_tab)
        self.PopulateFileList()
        self.file_list.Bind(wx.EVT_RIGHT_DOWN, self.OnFileListRightClick)
        files_vbox = wx.BoxSizer(wx.VERTICAL)
        files_vbox.Add(new_file_btn, proportion=0, flag=wx.EXPAND | wx.RIGHT | wx.BOTTOM, border=10)
        files_vbox.Add(self.file_list, proportion=1, flag=wx.EXPAND | wx.RIGHT, border=10)
        self.files_tab.SetSizer(files_vbox)

        # Extensions Tab (placeholder)
        self.extensions_tab = wx.Panel(self.sidebar_notebook)
        ext_vbox = wx.BoxSizer(wx.VERTICAL)
        ext_label = wx.StaticText(self.extensions_tab, label="Extensions coming soon...")
        ext_vbox.Add(ext_label, 1, wx.ALIGN_CENTER | wx.ALL, 10)
        self.extensions_tab.SetSizer(ext_vbox)

        # Git Commits Tab (with commit list)
        self.git_tab = wx.Panel(self.sidebar_notebook)
        git_vbox = wx.BoxSizer(wx.VERTICAL)
        self.commit_list = wx.ListBox(self.git_tab)
        git_vbox.Add(self.commit_list, 1, wx.EXPAND | wx.ALL, 10)
        self.git_tab.SetSizer(git_vbox)

        # Add tabs to sidebar notebook with Nerd Font icons
        nerd_font_big = wx.Font(17, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "JetBrainsMono Nerd Font")
        nerd_font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "JetBrainsMono Nerd Font")
        self.sidebar_notebook.AddPage(self.files_tab, " Files")
        self.sidebar_notebook.SetPageText(0, "")
        self.sidebar_notebook.SetFont(nerd_font_big)
        self.sidebar_notebook.AddPage(self.extensions_tab, "")
        self.sidebar_notebook.SetPageText(1, "")
        self.sidebar_notebook.AddPage(self.git_tab, "")
        self.sidebar_notebook.SetPageText(2, "")
        # Set file list font to nerd_font
        self.file_list.SetFont(nerd_font)

        # Sidebar layout
        sidebar_vbox = wx.BoxSizer(wx.VERTICAL)
        sidebar_vbox.Add(self.sidebar_notebook, 1, wx.EXPAND)
        self.sidebar.SetSizer(sidebar_vbox)

        self.matching_brackets = {
            '(': ')',
            '[': ']',
            '{': '}',
            '"': '"',
            "'": "'",
        }

        # Main panel content
        self.main_panel = wx.Panel(splitter)
        icon_and_label_sizer = wx.BoxSizer(wx.HORIZONTAL)
        try:
            img = wx.Image("assets/icons/xedixlogo.ico", wx.BITMAP_TYPE_ICO)
            img = img.Scale(24, 24, wx.IMAGE_QUALITY_HIGH)
            bmp = wx.Bitmap(img)
            icon_bitmap = wx.StaticBitmap(self.main_panel, bitmap=bmp)
            icon_and_label_sizer.Add(icon_bitmap, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=8)
        except Exception as e:
            print("Error loading icon for label:", e)
        self.default_message = wx.StaticText(self.main_panel, label="Open a File first")
        font = self.default_message.GetFont()
        font.PointSize += 5
        font = font.Bold()
        self.default_message.SetFont(font)
        icon_and_label_sizer.Add(self.default_message, flag=wx.ALIGN_CENTER_VERTICAL)
        self.tip_label = wx.StaticText(self.main_panel, label="Loading tip...")
        tip_font = self.tip_label.GetFont()
        tip_font.PointSize -= 1
        self.tip_label.SetFont(tip_font)
        self.tip_label.SetForegroundColour(wx.Colour(100, 100, 100))
        main_vbox = wx.BoxSizer(wx.VERTICAL)
        main_vbox.AddStretchSpacer(1)
        main_vbox.Add(icon_and_label_sizer, flag=wx.ALIGN_CENTER)
        main_vbox.Add(self.tip_label, flag=wx.ALIGN_CENTER | wx.TOP, border=5)
        main_vbox.AddStretchSpacer(1)
        self.main_panel.SetSizer(main_vbox)

        # Notebook for tabs (hidden by default)
        self.notebook = wx.Notebook(splitter)
        self.notebook.Hide()

        # Splitter config
        splitter.SplitVertically(self.sidebar, self.main_panel)
        splitter.SetMinimumPaneSize(150)
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(splitter, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
        panel.SetSizer(vbox)

        # Windows specific colors
        if wx.Platform == "__WXMSW__":
            self.sidebar.SetBackgroundColour("#fff")
            new_file_btn.SetBackgroundColour("#EDF0F2")
            new_file_btn.SetForegroundColour("#201f1f")
            self.main_panel.SetBackgroundColour("#EDF0F2")
            self.notebook.SetBackgroundColour("#ffffff00")
            panel.SetBackgroundColour("#fff")

        self.SetTitle("XediX - Text Editor")
        self.SetSize((850, 600))
        self.Centre()
        self.file_list.Bind(wx.EVT_LISTBOX_DCLICK, self.OnFileOpen)
        self.CreateMenuBar()
        try:
            url = "https://xedix.w3spaces.com/tips.json"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            tips = response.json()
            if tips:
                tip = random.choice(tips)
                self.tip_label.SetLabel(tip)
            else:
                self.tip_label.SetLabel("No tips available right now.")
        except Exception as e:
            print(f"Failed to fetch tips: {e}")
            self.tip_label.SetLabel("Welcome to XediX! Start coding.")


    def CreateMenuBar(self):
        """
        Creates and configures the application's menu bar with all main menus, submenus, and command bindings.
        
        This includes File, Edit, Tools (with Git and Build Tools submenus), Config, Help, and Project menus, each populated with relevant actions and event handlers for file operations, editing, code execution, Git integration, customization, help, and project management.
        """
        menubar = wx.MenuBar()

        fileMenu = wx.Menu()
        save_item = fileMenu.Append(wx.ID_SAVE, '&Save\tCtrl+S', 'Save the file')
        run_item = fileMenu.Append(wx.ID_ANY, '&Run Code\tCtrl+R', 'Run the code')
        folder_item = fileMenu.Append(wx.ID_ANY, '&Open Folder\tCtrl+Shift+O', 'Open Folder')
        fileMenu.AppendSeparator()
        pylint_item = fileMenu.Append(wx.ID_ANY, '&Run PyLint\tCtrl+P', 'Run pylint on code')
        exit_item = fileMenu.Append(wx.ID_EXIT, '&Exit\tCtrl+Q', 'Exit application')

        editMenu = wx.Menu()
        cut_item = editMenu.Append(wx.ID_CUT, '&Cut\tCtrl+X', 'Cut selection')
        copy_item = editMenu.Append(wx.ID_COPY, '&Copy\tCtrl+C', 'Copy selection')
        paste_item = editMenu.Append(wx.ID_PASTE, '&Paste\tCtrl+V', 'Paste from clipboard')
        editMenu.AppendSeparator()

        find_replace_item = editMenu.Append(wx.ID_FIND, '&Find and Replace\tCtrl+F', 'Find and replace text')
        jump_line_item = editMenu.Append(wx.ID_ANY, '&Jump to Line\tCtrl+G', 'Jump to a specific line number')

        toolsMenu = wx.Menu()

        # Create the Deployment submenu
        deployment_submenu = wx.Menu()
        req_item = deployment_submenu.Append(wx.ID_ANY, 'Generate requirements.txt')
        toolsMenu.AppendSubMenu(deployment_submenu, 'Building Tools')

        # Create the Git submenu
        git_submenu = wx.Menu()  # This is a Menu, not a MenuItem
        commit_item = git_submenu.Append(wx.ID_ANY, 'Git Commit', 'Commit the code')
        add_item = git_submenu.Append(wx.ID_ANY, 'Git Add .', 'git add .')
        push_item = git_submenu.Append(wx.ID_ANY, 'Git Push', 'Push the code')
        pull_item = git_submenu.Append(wx.ID_ANY, 'Git Pull', 'git pull')
        clone_item = git_submenu.Append(wx.ID_ANY, 'Git Clone', 'Commit the code')
        git_submenu.AppendSeparator()

        # Add version and branch items
        version_item = git_submenu.Append(wx.ID_ANY, 'Git Version', 'Show git version')
        branch_item = git_submenu.Append(wx.ID_ANY, 'Git Branch', 'Show current branch')
        status_item = git_submenu.Append(wx.ID_ANY, 'Git Status', 'Show git status')
        
        # Merge Resolver
        git_submenu.AppendSeparator()
        merge_resolve_item = git_submenu.Append(wx.ID_ANY, "Merge Resolver", "Resolve Merge Conflicts")

        # Append the Git submenu to the tools menu
        toolsMenu.AppendSubMenu(git_submenu, "Git")

        helpMenu = wx.Menu()
        homepage_item = helpMenu.Append(wx.ID_ANY, "&Homepage", "Homepage")
        about_item = helpMenu.Append(wx.ID_ABOUT, '&About', 'About')
        docs_item = helpMenu.Append(wx.ID_ANY, "&Docs", "Open Documentation")

        configMenu = wx.Menu()
        customize_item = configMenu.Append(wx.ID_ANY, '&Customize manually\tCtrl+Shift+C', 'Customize the UI')
        settings_item = configMenu.Append(wx.ID_ANY, '&Settings', 'Open Settings')

        projectMenu = wx.Menu()
        init_project_item = projectMenu.Append(wx.ID_ANY, '&Init Project', 'Initialize a new project')
        init_python_item = projectMenu.Append(wx.ID_ANY, '&Init Python', 'Initialize a new Python project')
        init_git_item = projectMenu.Append(wx.ID_ANY, '&Init Git', 'Initialize a new Git project')

        menubar.Append(fileMenu, '&File')
        menubar.Append(editMenu, '&Edit')
        menubar.Append(toolsMenu,'&Tools')
        menubar.Append(configMenu, '&Config')
        menubar.Append(helpMenu, '&Help')
        menubar.Append(projectMenu, '&Project')
        # Define minsize
        self.SetMenuBar(menubar)

        # File operations
        self.Bind(wx.EVT_MENU, self.OnSave, save_item)
        self.Bind(wx.EVT_MENU, self.OnRunCode, run_item)
        self.Bind(wx.EVT_MENU, self.OnOpenFolder, folder_item)
        self.Bind(wx.EVT_MENU, self.OnRunPylint, pylint_item)
        self.Bind(wx.EVT_MENU, self.OnExit, exit_item)

        # Edit operations
        self.Bind(wx.EVT_MENU, self.OnCut, cut_item)
        self.Bind(wx.EVT_MENU, self.OnCopy, copy_item) 
        self.Bind(wx.EVT_MENU, self.OnPaste, paste_item)
        self.Bind(wx.EVT_MENU, self.OnFindReplace, find_replace_item)
        self.Bind(wx.EVT_MENU, self.OnJumpToLine, jump_line_item)

        # Git operations
        self.Bind(wx.EVT_MENU, self.gcommit, commit_item)
        self.Bind(wx.EVT_MENU, self.gadd, add_item)
        self.Bind(wx.EVT_MENU, self.gpush, push_item)
        self.Bind(wx.EVT_MENU, self.gpull, pull_item)
        self.Bind(wx.EVT_MENU, self.gversion, version_item)
        self.Bind(wx.EVT_MENU, self.gbranch, branch_item)
        self.Bind(wx.EVT_MENU, self.gstatus, status_item)
        self.Bind(wx.EVT_MENU, self.merge_resolving, merge_resolve_item)

        # Project operations
        self.Bind(wx.EVT_MENU, self.ginit, init_git_item)
        self.Bind(wx.EVT_MENU, self.pinit, init_python_item)
        self.Bind(wx.EVT_MENU, self.xinit, init_project_item)

        # Tools and settings
        self.Bind(wx.EVT_MENU, self.OnCustomize, customize_item)
        self.Bind(wx.EVT_MENU, self.RequirementsGeneration, req_item)
        self.Bind(wx.EVT_MENU, self.OnConfig, settings_item)

        # Help and documentation
        self.Bind(wx.EVT_MENU, self.About, about_item)
        self.Bind(wx.EVT_MENU, self.Docs, docs_item)
        self.Bind(wx.EVT_MENU, self.Homepage, homepage_item)
        
        extension_menubar.main()
    
    def gversion(self, event):
        git_integration.version()

    def gbranch(self, event):
        git_integration.branch()

    def gadd(self, event):
        git_integration.add()
    
    def gpush(self, event):
        git_integration.push()

    def gpull(self, event):
        git_integration.pull()

    def gstatus(self, event):
        git_integration.status()

    def gcommit(self, event):
        git_integration.commit()

    def ginit(self, event):
        init_project.git_init()

    def pinit(self, event):
        init_project.python_init()

    def xinit(self, event):
        init_project.xedix_init()
        
    def merge_resolving(self, event):
        merge_resolver.main()
    
    # The following functions are opening webpages
    def About(self, event):
        webbrowser.open("https://xedix.w3spaces.com/about.html")

    def Docs(self, event):
        webbrowser.open("https://github.com/mostypc123/XediX/wiki")

    def Homepage(self, event):
        webbrowser.open("https://xedix.w3spaces.com")

    def OnConfig(self, event):
        settings.main()

    def OnOpenFolder(self, event, event_or_path):
        """Handle opening folders from both GUI and command line."""
        if isinstance(event_or_path, str):
            # Direct path provided
            path = event_or_path
        else:
            # Called from GUI event
            dlg = wx.DirDialog(self, "Choose a directory, if does not exist, it will be created",
                            style=wx.DD_DEFAULT_STYLE)
            
            if dlg.ShowModal() != wx.ID_OK:
                dlg.Destroy()
                return
                
            path = dlg.GetPath()
            dlg.Destroy()

        try:
            # Check if directory exists first
            if not os.path.exists(path):
                os.makedirs(path)
                
            # Change the working directory
            os.chdir(path)
            
        except PermissionError:
            return
        except OSError as e:
            return

        # Clear the current file list
        self.file_list.Clear()

        # Populate the file list with files from the new directory
        self.PopulateFileList()

        self.current_dir = path

    def RequirementsGeneration(self, event):
        current_tab = self.notebook.GetCurrentPage()
        if current_tab:
            text_area = current_tab.GetChildren()[0]
            code = text_area.GetValue()
            with open("requirements.txt", "w") as file:
                file.write(requirements.main(code))

    def OnFileListRightClick(self, event):
        """Handle right-click events on file list items."""
        # Get the item that was clicked
        index = self.file_list.HitTest(event.GetPosition())
        if index != wx.NOT_FOUND:
            self.file_list.SetSelection(index)

            # Create and show the context menu
            menu = wx.Menu()
            rename_item = menu.Append(wx.ID_ANY, "Rename")
            delete_item = menu.Append(wx.ID_ANY, "Delete")

            # Bind menu events
            self.Bind(wx.EVT_MENU, self.OnRenameFile, rename_item)
            self.Bind(wx.EVT_MENU, self.OnDeleteFile, delete_item)

            # Show the popup menu
            self.PopupMenu(menu)
            menu.Destroy()

    def OnRenameFile(self, event):
        """Handle file rename operation."""
        selected_index = self.file_list.GetSelection()
        if selected_index != wx.NOT_FOUND:
            old_name_with_icon = self.file_list.GetString(selected_index)
            # Extract filename without the icon
            space_index = old_name_with_icon.find(' ', 1)
            if space_index != -1:
                old_name = old_name_with_icon[space_index + 1:]
            else:
                old_name = old_name_with_icon

            # Show dialog to get new name
            dialog = wx.TextEntryDialog(self, "Enter new filename:", "Rename File", old_name)
            if dialog.ShowModal() == wx.ID_OK:
                new_name = dialog.GetValue()

                try:
                    # Rename the file
                    os.rename(old_name, new_name)

                    # Update the file list with icon
                    self.file_list.Clear()
                    self.PopulateFileList()

                    # Update the notebook tab if the file is open
                    for i in range(self.notebook.GetPageCount()):
                        if self.notebook.GetPageText(i) == old_name:
                            self.notebook.SetPageText(i, new_name)

                except OSError as e:
                    wx.MessageBox(f"Error renaming file: {str(e)}", "Error", 
                                wx.OK | wx.ICON_ERROR)

            dialog.Destroy()

    def OnDeleteFile(self, event):
        """Handle file delete operation."""
        selected_index = self.file_list.GetSelection()
        if selected_index != wx.NOT_FOUND:
            filename_with_icon = self.file_list.GetString(selected_index)
            # Extract filename without the icon
            space_index = filename_with_icon.find(' ', 1)
            if space_index != -1:
                filename = filename_with_icon[space_index + 1:]
            else:
                filename = filename_with_icon

            # Show confirmation dialog
            dialog = wx.MessageDialog(self, 
                                    f"Are you sure you want to delete '{filename}'?",
                                    "Confirm Delete",
                                    wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)

            if dialog.ShowModal() == wx.ID_YES:
                try:
                    # Close the file if it's open in the editor
                    for i in range(self.notebook.GetPageCount()):
                        if self.notebook.GetPageText(i) == filename:
                            self.notebook.DeletePage(i)
                            break

                    # Delete the file
                    os.remove(filename)

                    # Refresh the file list
                    self.file_list.Clear()
                    self.PopulateFileList()

                except OSError as e:
                    wx.MessageBox(f"Error deleting file: {str(e)}", "Error", 
                                wx.OK | wx.ICON_ERROR)

            dialog.Destroy()

    def OnJumpToLine(self, event):
        """Jump to selected line of code."""
        current_tab = self.notebook.GetCurrentPage()
        if current_tab:
            text_area = current_tab.GetChildren()[0]

            # Create a dialog to get the line number
            line_dialog = wx.TextEntryDialog(self, "Enter line number:", "Jump to Line")
            # style  the  textentry
            if line_dialog.ShowModal() == wx.ID_OK:
                try:
                    # Convert the input to an integer line number
                    line_number = int(line_dialog.GetValue()) - 1  # Adjust for 0-based indexing

                    # Get the position of the specified line
                    line_pos = text_area.PositionFromLine(line_number)

                    # Scroll to the line and set the cursor
                    text_area.GotoPos(line_pos)
                    text_area.SetFocus()

                    # Highlight the line
                    text_area.EnsureCaretVisible()
                    text_area.SetSelection(line_pos, text_area.GetLineEndPosition(line_number))
                    # Update status bar
                    self.SetStatusText(f"Jumped to line {line_number + 1}")

                except ValueError:
                    # Handle invalid input
                    wx.MessageBox("Please enter a valid line number", "Error", wx.OK | wx.ICON_ERROR)
                except Exception as e:
                    # Handle any other potential errors
                    wx.MessageBox(f"Error jumping to line: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)

            line_dialog.Destroy()

    def OnCustomize(self, event):
        """Opens the manual customization."""
        file_name = "xedix.xcfg"
        file_path = os.path.join(os.getcwd(), file_name)

        try:
            with open(file_path, 'r') as file:
                content = file.read()
        except FileNotFoundError:
            wx.MessageBox(f"File '{file_name}' not found in the current directory.", "Error", wx.ICON_ERROR)
            return
        except Exception as e:
            wx.MessageBox(f"An error occurred while opening the file: {e}", "Error", wx.ICON_ERROR)
            return

        if not self.notebook.IsShown():
            # Hide default message and panel, replace with notebook
            self.default_message.Hide()
            self.main_panel.Hide()
            splitter = self.main_panel.GetParent()
            splitter.ReplaceWindow(self.main_panel, self.notebook)
            self.notebook.Show()
            self.notebook.SetBackgroundColour("#ffffff00")
            self.notebook.SetWindowStyleFlag(wx.NO_BORDER)

        # Create a new tab with a text editor to display file content
        tab = wx.Panel(self.notebook)
        text_area = stc.StyledTextCtrl(tab, style=wx.TE_MULTILINE)
        text_area.SetText(content)
        text_area.SetTabWidth(4)
        text_area.SetWindowStyleFlag(wx.NO_BORDER)

        # [IMP] Refactor this piece of code in next update
        with open("theme.xcfg", 'r') as file:
            theme = file.read()
            if theme == "dark":
                dark_bg_color = "#1B1F2B"
            elif theme == "light":
                dark_bg_color = "#FFFFFF"
                light_text_color = "#1e1e1e"
            elif theme == "night":
                dark_bg_color = "#2f3139"
            elif theme == "obsidian":
                dark_bg_color = "#212232"
            else:
                dark_bg_color = "#1B1F2B"

            if theme != "light":
                light_text_color = "#FFFFFF"

            text_area.StyleSetBackground(stc.STC_STYLE_DEFAULT, dark_bg_color)
            text_area.StyleSetForeground(stc.STC_STYLE_DEFAULT, light_text_color)
            text_area.StyleClearAll()  # Apply the default style to all text

             # Default style
            text_area.StyleSetSpec(stc.STC_P_DEFAULT, f"fore:{light_text_color},italic,back:{dark_bg_color}")

            # Adjust indentation guides
            text_area.SetIndentationGuides(True)
            text_area.StyleSetSpec(stc.STC_STYLE_LINENUMBER, f"fore:{light_text_color},italic,back:{dark_bg_color}")
            text_area.SetMarginType(1, stc.STC_MARGIN_NUMBER)
            text_area.SetMarginWidth(1, 30)

            tab_sizer = wx.BoxSizer(wx.VERTICAL)
            tab_sizer.Add(text_area, proportion=1, flag=wx.EXPAND)
            tab.SetSizer(tab_sizer)

            self.notebook.AddPage(tab, file_name)

    def OnRunPylint(self, event):
        """Runs pylint on code."""
        current_tab = self.notebook.GetCurrentPage()
        if current_tab:
            # Get the SplitterWindow and then the text area
            editor_splitter = current_tab.GetChildren()[0]  # SplitterWindow
            text_area = editor_splitter.GetChildren()[0]    # StyledTextCtrl
            code = text_area.GetValue()

            # Save current file to a temporary location before running pylint
            file_name = 'temp_code.py'
            with open(file_name, 'w') as file:
                file.write(code)

            # Run pylint using subprocess
            pylint_process = subprocess.Popen(
                ['pylint', file_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = pylint_process.communicate()

            # Show pylint output in the output window
            if self.output_window is None:
                self.output_window = wx.Dialog(self, title="pylint Output", size=(600, 400))
                pywinstyles.apply_style(self.output_window, "win7")
                output_panel = wx.Panel(self.output_window)
                output_vbox = wx.BoxSizer(wx.VERTICAL)

                self.output_text = wx.TextCtrl(output_panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
                output_vbox.Add(self.output_text, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
                output_panel.SetSizer(output_vbox)

            output_message = f"{stdout}\nErrors:\n{stderr}"
            self.output_text.SetValue(output_message)
            self.output_window.ShowModal()

    def OnFindReplace(self, event):
        """Opens a find/replace dialog."""

        find_replace_dialog = wx.TextEntryDialog(self, "Find text:")
        if find_replace_dialog.ShowModal() == wx.ID_OK:
            # Replace dialog
            find_text = find_replace_dialog.GetValue()
            replace_dialog = wx.TextEntryDialog(self, "Replace with:")
            if replace_dialog.ShowModal() == wx.ID_OK:
                replace_text = replace_dialog.GetValue()
                current_tab = self.notebook.GetCurrentPage()
                if current_tab:
                    # Gets the textarea object
                    text_area = current_tab.GetChildren()[0]

                    # Gets the content
                    content = text_area.GetValue()

                    # Replace text
                    new_content = content.replace(find_text, replace_text)

                    # Show the changes made in the textarea
                    text_area.SetText(new_content)

    def PopulateFileList(self):
        """Populates the file list with the files in the current directory with Nerd Font icons"""
        current_dir = os.getcwd()
        files = [f for f in os.listdir(current_dir) if os.path.isfile(os.path.join(current_dir, f))]
        # Nerd Font icons for file types
        file_icons = {
            '.py': '', '.js': '', '.ts': '', '.jsx': '', '.tsx': '', '.java': '', '.cpp': '', '.c': '', '.cs': '', '.php': '', '.rb': '', '.go': '', '.rs': '', '.swift': '', '.kt': '', '.scala': '', '.r': 'ﳒ', '.m': '', '.pl': '', '.sh': '', '.bash': '', '.zsh': '', '.fish': '', '.ps1': '', '.bat': '', '.cmd': '',
            '.html': '', '.htm': '', '.css': '', '.scss': '', '.sass': '', '.less': '', '.vue': '﵂', '.svelte': '',
            '.json': '', '.xml': '謹', '.yaml': '', '.yml': '', '.toml': '', '.csv': '', '.sql': '',
            '.md': '', '.txt': '', '.pdf': '', '.doc': '', '.docx': '', '.rtf': '', '.tex': 'ﭨ',
            '.png': '', '.jpg': '', '.jpeg': '', '.gif': '', '.svg': 'ﰟ', '.ico': '', '.bmp': '', '.webp': '',
            '.mp3': '', '.wav': '', '.flac': '', '.mp4': '', '.avi': '', '.mkv': '', '.mov': '',
            '.zip': '', '.rar': '', '.tar': '', '.gz': '', '.7z': '', '.bz2': '',
            '.conf': '', '.cfg': '', '.ini': '', '.env': '', '.gitignore': '', '.dockerfile': '', '.lock': '',
            '.exe': '', '.msi': '', '.deb': '', '.rpm': '', '.dmg': '', '.app': '', '.appimage': '',
            '.ttf': '', '.otf': '', '.woff': '', '.woff2': '',
            '.git': '', '.gitconfig': '', '.gitmodules': '',
            'makefile': '', 'cmake': '', '.gradle': '', 'package.json': '', 'composer.json': '', 'requirements.txt': '', 'poetry.lock': '', 'cargo.toml': '', 'gemfile': '',
        }
        default_icon = ''
        files_with_icons = []
        for file in files:
            _, ext = os.path.splitext(file.lower())
            if not ext:
                if file.lower() in file_icons:
                    icon = file_icons[file.lower()]
                elif file.lower() == 'readme':
                    icon = ''
                elif file.lower() == 'license':
                    icon = ''
                elif file.startswith('.'):
                    icon = ''
                else:
                    icon = default_icon
            else:
                if file.lower() in file_icons:
                    icon = file_icons[file.lower()]
                elif file.lower() in ['.gitignore', '.gitconfig', '.gitmodules']:
                    icon = file_icons[file.lower()]
                else:
                    icon = file_icons.get(ext, default_icon)
            files_with_icons.append(f"{icon} {file}")
        self.file_list.Clear()
        self.file_list.AppendItems(files_with_icons)
        nerd_font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "JetBrainsMono Nerd Font")
        self.file_list.SetFont(nerd_font)
        self.file_list.SetBackgroundColour('#fff')
        self.file_list.SetForegroundColour('#201f1f')

    def PopulateCommitList(self):
        """Populates the commit list with recent git commit messages and prints debug info."""
        import subprocess
        self.commit_list = getattr(self, 'commit_list', None)
        if self.commit_list is None:
            self.commit_list = wx.ListBox(self.git_tab)
            git_vbox = self.git_tab.GetSizer()
            if git_vbox:
                git_vbox.Add(self.commit_list, 1, wx.EXPAND | wx.ALL, 10)
            else:
                git_vbox = wx.BoxSizer(wx.VERTICAL)
                git_vbox.Add(self.commit_list, 1, wx.EXPAND | wx.ALL, 10)
                self.git_tab.SetSizer(git_vbox)
        self.commit_list.Clear()
        try:
            git_root = None
            try:
                result = subprocess.run(['git', 'rev-parse', '--show-toplevel'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=os.getcwd())
                if result.returncode == 0:
                    git_root = result.stdout.strip()
                else:
                    self.commit_list.Append(f"Not a git repo: {result.stderr.strip()}")
                    return
            except FileNotFoundError:
                self.commit_list.Append("git command not found. Is git installed?")
                return
            except Exception as e:
                self.commit_list.Append(f"Error finding git root: {e}")
                return
            if git_root:
                try:
                    cmd = ['git', 'log', '--pretty=format:%h %s', '--abbrev-commit', '-n', '30']
                    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=git_root)
                    if result.returncode == 0 and result.stdout.strip():
                        commits = result.stdout.strip().split('\n')
                        self.commit_list.AppendItems(commits)
                    elif result.returncode == 0:
                        self.commit_list.Append("No git commits found.")
                    else:
                        self.commit_list.Append(f"git log error: {result.stderr.strip()}")
                except FileNotFoundError:
                    self.commit_list.Append("git command not found. Is git installed?")
                except Exception as e:
                    self.commit_list.Append(f"Error running git log: {e}")
            else:
                self.commit_list.Append("Not a git repository.")
        except Exception as e:
            self.commit_list.Append(f"Error: {e}")
        self.commit_list.SetBackgroundColour('#fff')
        self.commit_list.SetForegroundColour('#201f1f')
        self.commit_list.Show()
        self.git_tab.Layout()

    def ScanForViruses(self, file_name):
        """Thoroughly scans file against all VirusShare databases"""
        
        try:
            # Get the full file path
            file_path = os.path.join(os.getcwd(), file_name)
            
            # Calculate MD5 hash of the file
            md5_hash = hashlib.md5()
            
            with open(file_path, 'rb') as f:
                # Read and update hash in chunks of 4K
                for byte_block in iter(lambda: f.read(4096), b""):
                    md5_hash.update(byte_block)
            
            file_md5 = md5_hash.hexdigest().lower()
            
            # Create a dialog to show scanning progress and results
            scan_dialog = wx.Dialog(self, title="Virus Scan Results", size=(500, 400))
            panel = wx.Panel(scan_dialog)
            vbox = wx.BoxSizer(wx.VERTICAL)
            
            # Add file information
            file_info = wx.StaticText(panel, label=f"File: {file_name}\nSize: {os.path.getsize(file_path)} bytes\nMD5: {file_md5}")
            vbox.Add(file_info, flag=wx.ALL, border=10)
            
            # Create a multi-line text control for scan results
            log_text = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(-1, 200))
            log_text.AppendText("Starting virus scan using VirusShare hash database...\n\n")
            
            vbox.Add(log_text, proportion=1, flag=wx.ALL|wx.EXPAND, border=10)
            
            # Add a gauge for progress
            gauge = wx.Gauge(panel, range=100, size=(-1, 20))
            vbox.Add(gauge, flag=wx.ALL|wx.EXPAND, border=10)
            
            # Add close button (disabled initially)
            close_btn = wx.Button(panel, label="Close")
            close_btn.Bind(wx.EVT_BUTTON, lambda evt: scan_dialog.EndModal(wx.ID_OK))
            close_btn.Disable()  # Disable until scan completes
            vbox.Add(close_btn, flag=wx.ALL|wx.CENTER, border=10)
            
            panel.SetSizer(vbox)
            scan_dialog.Show()
            
            # Create a simple temporary directory
            temp_dir = os.path.join(os.getcwd(), "temp_virusshare")
            if not os.path.exists(temp_dir):
                os.mkdir(temp_dir)
            log_text.AppendText(f"Created temporary directory for hash databases: {temp_dir}\n")
            
            def scan_thread():
                try:
                    # Check ALL hash databases (1-487)
                    total_db_files = 487
                    
                    # Function to download a hash file
                    def download_hash_file(file_num):
                        url = f"https://virusshare.com/hashfiles/VirusShare_{file_num:03d}.md5"
                        local_path = os.path.join(temp_dir, f"VirusShare_{file_num:03d}.md5")
                        
                        try:
                            log_text.AppendText(f"Downloading {url}...\n")
                            
                            # Download the file using requests
                            response = requests.get(url, stream=True)
                            
                            if response.status_code == 200:
                                with open(local_path, 'wb') as f:
                                    for chunk in response.iter_content(chunk_size=8192):
                                        f.write(chunk)
                                log_text.AppendText(f"Successfully downloaded {url}\n")
                                return local_path
                            else:
                                log_text.AppendText(f"Failed to download {url} (Status: {response.status_code})\n")
                                return None
                        except Exception as e:
                            log_text.AppendText(f"Error downloading {url}: {str(e)}\n")
                            return None
                    
                    # Function to check if a hash exists in a database file
                    def check_hash_in_file(hash_file_path, target_hash):
                        try:
                            with open(hash_file_path, 'r') as f:
                                # Skip the first few lines (header)
                                for _ in range(5):
                                    next(f, None)
                                
                                # Check each hash
                                for line in f:
                                    if line.strip().lower() == target_hash:
                                        return True
                            return False
                        except Exception as e:
                            log_text.AppendText(f"Error reading hash file {os.path.basename(hash_file_path)}: {str(e)}\n")
                            return False
                    
                    # Scan against ALL databases
                    found_match = False
                    
                    for i in range(1, total_db_files + 1):
                        # Update progress bar
                        gauge.SetValue(int((i-1) / total_db_files * 100))
                        wx.CallAfter(wx.Yield)
                        
                        # Download hash file
                        hash_file = download_hash_file(i)
                        
                        if hash_file:
                            log_text.AppendText(f"Checking file against {os.path.basename(hash_file)}...\n")
                            
                            if check_hash_in_file(hash_file, file_md5):
                                log_text.AppendText(f"\n⚠️ MATCH FOUND in database #{i}! This file matches a known malicious hash.\n")
                                found_match = True
                                break
                            
                            # Delete the file after checking to save disk space
                            os.remove(hash_file)
                    
                    if not found_match:
                        log_text.AppendText("\n✓ No matches found. File hash not present in any of the VirusShare databases.\n")
                    
                    # Set progress to 100% when done
                    gauge.SetValue(100)
                    log_text.AppendText("\nScan completed. Checked against all 487 VirusShare databases.\n")
                    
                    # Clean up temporary directory
                    log_text.AppendText("\nCleaning up temporary files...\n")
                    
                    # Delete any remaining files in the temp directory
                    for file in os.listdir(temp_dir):
                        file_path = os.path.join(temp_dir, file)
                        try:
                            os.remove(file_path)
                        except Exception as e:
                            log_text.AppendText(f"Error deleting {file}: {str(e)}\n")
                    
                    # Remove the directory itself
                    try:
                        os.rmdir(temp_dir)
                        log_text.AppendText("Temporary directory deleted.\n")
                    except Exception as e:
                        log_text.AppendText(f"Error removing temporary directory: {str(e)}\n")
                    
                    # Enable close button
                    wx.CallAfter(close_btn.Enable)
                    
                except Exception as e:
                    log_text.AppendText(f"Error during scan: {str(e)}\n")
                    wx.CallAfter(close_btn.Enable)
            
            # Start scanning in a separate thread to keep UI responsive
            thread = threading.Thread(target=scan_thread)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            wx.MessageBox(f"Error setting up scan: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
            self.SetStatusText(f"    Error scanning {file_name}")

    def RunWithAdminPrivileges(self, file_name):
        """Runs the executable with elevated privileges using only subprocess and os"""
        
        try:
            file_path = os.path.join(os.getcwd(), file_name)
            
            if sys.platform == "win32":
                # Windows - use the built-in elevate.exe utility or directly through cmd
                subprocess.Popen(['powershell', 'Start-Process', '-FilePath', file_path, 
                                '-Verb', 'RunAs'], shell=True)
            elif sys.platform == "darwin":
                # macOS - use sudo (will prompt for password in Terminal)
                subprocess.Popen(['sudo', file_path])
            else:
                # Linux - use sudo or similar (will prompt for password)
                for sudo_cmd in ['pkexec', 'sudo', 'gksudo', 'kdesudo']:
                    try:
                        subprocess.Popen([sudo_cmd, file_path])
                        break
                    except FileNotFoundError:
                        continue
            
        except Exception as e:
            wx.MessageBox(f"Error launching with admin privileges: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)

    def RunInTerminal(self, file_name):
        """Runs the executable in a separate terminal window with optional arguments"""
        # Prompt for command-line arguments
        arg_dialog = wx.TextEntryDialog(self, "Enter command-line arguments (optional):", "Run with Arguments")
        args = ""
        if arg_dialog.ShowModal() == wx.ID_OK:
            args = arg_dialog.GetValue()
        arg_dialog.Destroy()
        
        try:
            # Get the full file path
            file_path = os.path.join(os.getcwd(), file_name)
            
            if sys.platform == "win32":
                # Windows - use CMD to open a new console window
                subprocess.Popen(f'start cmd /k "{file_path} {args}"', shell=True)
            elif sys.platform == "darwin":
                # macOS - use Terminal.app
                subprocess.Popen(['open', '-a', 'Terminal', file_path, args])
            else:
                # Linux - try common terminal emulators
                for terminal in ['x-terminal-emulator', 'gnome-terminal', 'xterm', 'konsole']:
                    try:
                        subprocess.Popen([terminal, '-e', f"{file_path} {args}"])
                        break
                    except (FileNotFoundError, subprocess.SubprocessError):
                        continue
            
        except Exception as e:
            wx.MessageBox(f"Error launching in terminal: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)

    def RunInTerminalWithArgs(self, file_name):
        """Runs the executable in a separate terminal window with user-provided arguments"""
        # Prompt for command-line arguments
        arg_dialog = wx.TextEntryDialog(self, "Enter command-line arguments (optional):", "Run with Arguments")
        args = ""
        if arg_dialog.ShowModal() == wx.ID_OK:
            args = arg_dialog.GetValue()
        arg_dialog.Destroy()
        
        try:
            # Get the full file path
            file_path = os.path.join(os.getcwd(), file_name)
            
            if sys.platform == "win32":
                # Windows - use CMD to open a new console window
                subprocess.Popen(f'start cmd /k "{file_path} {args}"', shell=True)
            elif sys.platform == "darwin":
                # macOS - use Terminal.app
                # For macOS, we need to create a command string
                cmd_string = f"'{file_path}' {args}"
                subprocess.Popen(['open', '-a', 'Terminal', cmd_string])
            else:
                # Linux - try common terminal emulators
                cmd_string = f"{file_path} {args}"
                for terminal in ['x-terminal-emulator', 'gnome-terminal', 'xterm', 'konsole']:
                    try:
                        # Different terminals have different ways to execute commands
                        if terminal == 'gnome-terminal':
                            subprocess.Popen([terminal, '--', 'bash', '-c', f"{cmd_string}; exec bash"])
                        else:
                            subprocess.Popen([terminal, '-e', cmd_string])
                        break
                    except (FileNotFoundError, subprocess.SubprocessError):
                        continue
            
        except Exception as e:
            wx.MessageBox(f"Error launching in terminal: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)

    def OnFileOpen(self, event):
        """
        Opens the selected file from the file list and displays it in a new editor tab with syntax highlighting and theming.
        
        If the selected file is a configuration file ("xedix.xcfg" or "theme.xcfg"), temporarily changes the window title. For executable files (.exe, .bat, .sh, .msi), presents a dialog with options to run, run with arguments, run as administrator, or scan for viruses. For text files, reads the file content (with fallback encoding), creates a new tab with a main editor and minimap, applies syntax highlighting and theme colors based on file type and user theme, and updates Discord Rich Presence if enabled. Handles file reading errors and updates the status bar accordingly.
        """
        file_name_with_icon = self.file_list.GetStringSelection()
        if file_name_with_icon:
            # Extract filename without the icon (remove icon and space)
            if file_name_with_icon.startswith(' ') or len(file_name_with_icon) > 0:
                # Find the first space after the icon and get the filename
                space_index = file_name_with_icon.find(' ', 1)  # Start searching after first character
                if space_index != -1:
                    file_name = file_name_with_icon[space_index + 1:]  # Get filename after the space
                else:
                    file_name = file_name_with_icon  # Fallback to full string if no space found
            else:
                file_name = file_name_with_icon
            if file_name == "xedix.xcfg" or file_name == "theme.xcfg":
                self.SetTitle("Customizing XediX")
                time.sleep(20)
                self.SetTitle("XediX - Text Editor")
            if file_name.endswith(".exe") or file_name.endswith(".bat") or file_name.endswith(".sh") or file_name.endswith(".msi"):
                # Add dialog to determine how to handle the executable
                dialog = wx.Dialog(self, title="Executable File Options", size=(400, 250))
                panel = wx.Panel(dialog)
                vbox = wx.BoxSizer(wx.VERTICAL)
                
                # Add descriptive text
                desc = wx.StaticText(panel, label=f"Selected executable: {file_name}\nHow would you like to proceed?")
                vbox.Add(desc, flag=wx.ALL|wx.EXPAND, border=10)
                
                # Add buttons
                btn_sizer = wx.BoxSizer(wx.VERTICAL)
                
                run_cli_btn = wx.Button(panel, label="Run in Terminal")
                run_args_btn = wx.Button(panel, label="Run with Arguments")
                run_admin_btn = wx.Button(panel, label="Run as Administrator")
                scan_virus_btn = wx.Button(panel, label="Scan for Viruses")
                cancel_btn = wx.Button(panel, label="Cancel")
                
                btn_sizer.Add(run_cli_btn, flag=wx.EXPAND|wx.BOTTOM, border=5)
                btn_sizer.Add(run_args_btn, flag=wx.EXPAND|wx.BOTTOM, border=5)
                btn_sizer.Add(run_admin_btn, flag=wx.EXPAND|wx.BOTTOM, border=5)
                btn_sizer.Add(scan_virus_btn, flag=wx.EXPAND|wx.BOTTOM, border=5)
                btn_sizer.Add(cancel_btn, flag=wx.EXPAND)
                
                vbox.Add(btn_sizer, flag=wx.ALL|wx.CENTER|wx.EXPAND, border=10)
                panel.SetSizer(vbox)
                
                # Bind events
                run_cli_btn.Bind(wx.EVT_BUTTON, lambda evt, f=file_name: (self.RunInTerminal(f), dialog.EndModal(wx.ID_OK)))
                run_args_btn.Bind(wx.EVT_BUTTON, lambda evt, f=file_name: (self.RunInTerminalWithArgs(f), dialog.EndModal(wx.ID_OK)))
                run_admin_btn.Bind(wx.EVT_BUTTON, lambda evt, f=file_name: (self.RunWithAdminPrivileges(f), dialog.EndModal(wx.ID_OK)))
                scan_virus_btn.Bind(wx.EVT_BUTTON, lambda evt, f=file_name: (self.ScanForViruses(f), dialog.EndModal(wx.ID_OK)))
                cancel_btn.Bind(wx.EVT_BUTTON, lambda evt: dialog.EndModal(wx.ID_CANCEL))
                
                # Show dialog
                dialog.ShowModal()
                dialog.Destroy()
                return  # Skip the rest of the file opening procedure for executables
            self.SetTitle(f"XediX - Text Editor - editing {file_name}")
            file_path = os.path.join(os.getcwd(), file_name)
            try:
                with open(file_path, 'r') as file:
                    content = file.read()
            except UnicodeDecodeError:
                try:
                    # If UTF-8 fails, try with a more permissive encoding
                    with open(file_path, 'r', encoding='latin-1') as file:
                        content = file.read()
                except Exception as e:
                    wx.MessageBox(f"Error reading file: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
                    return
            except Exception as e:
                wx.MessageBox(f"Error reading file: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
                return


            if not self.notebook.IsShown():
                # Hide, message and default screen
                self.default_message.Hide()
                self.main_panel.Hide()
                splitter = self.main_panel.GetParent()
                splitter.ReplaceWindow(self.main_panel, self.notebook)
                self.notebook.Show()
                self.notebook.SetBackgroundColour("#ffffff00")
                self.notebook.SetWindowStyleFlag(wx.NO_BORDER)


            tab = wx.Panel(self.notebook)
            editor_splitter = wx.SplitterWindow(tab)

            text_area = stc.StyledTextCtrl(editor_splitter, style=wx.TE_MULTILINE)
            text_area.SetText(content)
            text_area.SetTabWidth(4)
            text_area.SetWindowStyleFlag(wx.NO_BORDER)

            # Set up optimal coding font
            if wx.Platform == '__WXMSW__':  # Windows
                font_face = "Consolas"
            elif wx.Platform == '__WXMAC__':  # macOS
                font_face = "Menlo"
            else:                            # Linux and others
                font_face = "DejaVu Sans Mono"

            # Apply font settings to all styles
            text_area.StyleSetFont(stc.STC_STYLE_DEFAULT, 
            wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, 
            wx.FONTWEIGHT_NORMAL, False, font_face))
            text_area.StyleClearAll()  # Apply to all styles

            # Additional text rendering settings
            text_area.SetUseTabs(False)  # Use spaces instead of tabs
            text_area.SetViewWhiteSpace(stc.STC_WS_INVISIBLE)  # Hide whitespace markers
            text_area.SetViewEOL(False)  # Hide EOL markers
            text_area.SetCaretWidth(2)  # Slightly wider caret for better visibility

            # Create minimap
            minimap = stc.StyledTextCtrl(editor_splitter, style=wx.TE_MULTILINE | wx.TE_READONLY)
            minimap.SetText(content)
            minimap.SetZoom(-8)  # Make the text very small
            minimap.SetMaxSize((100, -1))

            # Split the window
            editor_splitter.SplitVertically(text_area, minimap)
            editor_splitter.SetSashGravity(0.85)  # Set main editor to take up most space

            # Sync scrolling between main editor and minimap
            def on_scroll(event):
                first_visible_line = text_area.GetFirstVisibleLine()
                minimap.ScrollToLine(first_visible_line)
                event.Skip()

            text_area.Bind(wx.stc.EVT_STC_UPDATEUI, on_scroll)

            # Sync content changes
            def on_text_change(event):
                minimap.SetText(text_area.GetText())
                event.Skip()

            text_area.Bind(wx.stc.EVT_STC_CHANGE, on_text_change)
            text_area.SetText(content)
            text_area.SetTabWidth(4)
            text_area.SetWindowStyleFlag(wx.NO_BORDER)
            
            # Update Discord RPC only if it's initialized and connected
            try:
                if self.RPC:
                    self.RPC.update(
                        state="XediX",
                        details=f"Editing {file_name}",
                        large_image="xedix_logo",
                        large_text="XediX",
                        small_text="XediX"
                    )
            except Exception as e:
                print(f"Could not update Discord status: {e}")
                self.RPC = None  # Reset RPC if connection is lost

            # Bind a key event to trigger autocomplete after typing
            text_area.Bind(wx.EVT_CHAR, self.OnChar)

            # Set theme colors for the entire control
            for text_area in (text_area, minimap):
                try:
                    with open("theme.xcfg", 'r') as file:
                        theme_content = file.read().strip()
                        
                    # Check if theme content is JSON
                    if theme_content.startswith('{'):
                        theme_data = json.loads(theme_content)
                        dark_bg_color = theme_data.get('background', theme_data.get('dark_bg_color', "#1F1F1F"))
                        light_text_color = theme_data.get('foreground', theme_data.get('light_text_color', "#FFFFFF"))
                        cmt_color = theme_data.get('comment', theme_data.get('cmt_color', "#68C147"))
                        keyword_color = theme_data.get('keyword', theme_data.get('keyword_color', "#569CD6"))
                        string_color = theme_data.get('string', theme_data.get('string_color', "#BA9EFE"))
                        number_color = theme_data.get('number', theme_data.get('number_color', "#FFDD54"))
                        operator_color = theme_data.get('operator', theme_data.get('operator_color', "#D4D4D4"))
                        line_number_bg = theme_data.get('lineNumberBg', dark_bg_color)
                    else:
                        theme = theme_content
                        if theme == "dark":
                            dark_bg_color = "#1B1F2B"
                            light_text_color = "#FFFFFF"
                            cmt_color = "#68C147"
                            keyword_color = "#569CD6"
                            string_color = "#BA9EFE"
                            number_color = "#FFDD54"
                            operator_color = "#D4D4D4"
                        elif theme == "light":
                            dark_bg_color = "#FFFFFF"
                            light_text_color = "#000000"
                            cmt_color = "#008000"
                            keyword_color = "#0000FF"
                            string_color = "#A31515"
                            number_color = "#098658"
                            operator_color = "#000000"
                        elif theme == "night":
                            dark_bg_color = "#2f3139"
                            light_text_color = "#FFFFFF"
                            cmt_color = "#eab676"
                            keyword_color = "#569CD6"
                            string_color = "#BA9EFE"
                            number_color = "#FFDD54"
                            operator_color = "#D4D4D4"
                        elif theme == "obsidian":
                            dark_bg_color = "#212232"
                            light_text_color = "#FFFFFF"
                            cmt_color = "#EFC3CA"
                            keyword_color = "#569CD6"
                            string_color = "#BA9EFE"
                            number_color = "#FFDD54"
                            operator_color = "#D4D4D4"
                        elif theme == "solarized-light":
                            dark_bg_color = "#FDF6E3"
                            light_text_color = "#657B83"
                            cmt_color = "#93A1A1"
                            keyword_color = "#859900"
                            string_color = "#2AA198"
                            number_color = "#D33682"
                            operator_color = "#586E75"
                        elif theme == "solarized-dark":
                            dark_bg_color = "#002B36"
                            light_text_color = "#839496"
                            cmt_color = "#586E75"
                            keyword_color = "#859900"
                            string_color = "#2AA198"
                            number_color = "#D33682"
                            operator_color = "#93A1A1"
                        elif theme == "github-dark":
                            dark_bg_color = "#0D1117"
                            light_text_color = "#C9D1D9"
                            cmt_color = "#8B949E"
                            keyword_color = "#FF7B72"
                            string_color = "#A5D6FF"
                            number_color = "#79C0FF"
                            operator_color = "#C9D1D9"
                        elif theme == "github-dimmed":
                            dark_bg_color = "#22272E"
                            light_text_color = "#ADBAC7"
                            cmt_color = "#768390"
                            keyword_color = "#F47067"
                            string_color = "#96D0FF"
                            number_color = "#6CB6FF"
                            operator_color = "#ADBAC7"
                        elif theme == "github-light":
                            dark_bg_color = "#FFFFFF"
                            light_text_color = "#24292F"
                            cmt_color = "#6E7781"
                            keyword_color = "#CF222E"
                            string_color = "#0A3069"
                            number_color = "#0550AE"
                            operator_color = "#24292F"
                        
                        # Popular IDE Themes
                        elif theme == "vscode-dark":
                            dark_bg_color = "#1E1E1E"
                            light_text_color = "#D4D4D4"
                            cmt_color = "#6A9955"
                            keyword_color = "#569CD6"
                            string_color = "#CE9178"
                            number_color = "#B5CEA8"
                            operator_color = "#D4D4D4"
                        elif theme == "vscode-light":
                            dark_bg_color = "#FFFFFF"
                            light_text_color = "#000000"
                            cmt_color = "#008000"
                            keyword_color = "#0000FF"
                            string_color = "#A31515"
                            number_color = "#098658"
                            operator_color = "#000000"
                        elif theme == "atom-one-dark":
                            dark_bg_color = "#282C34"
                            light_text_color = "#ABB2BF"
                            cmt_color = "#5C6370"
                            keyword_color = "#C678DD"
                            string_color = "#98C379"
                            number_color = "#D19A66"
                            operator_color = "#56B6C2"
                        elif theme == "atom-one-light":
                            dark_bg_color = "#FAFAFA"
                            light_text_color = "#383A42"
                            cmt_color = "#A0A1A7"
                            keyword_color = "#A626A4"
                            string_color = "#50A14F"
                            number_color = "#986801"
                            operator_color = "#0184BC"
                        elif theme == "sublime-monokai":
                            dark_bg_color = "#272822"
                            light_text_color = "#F8F8F2"
                            cmt_color = "#75715E"
                            keyword_color = "#F92672"
                            string_color = "#E6DB74"
                            number_color = "#AE81FF"
                            operator_color = "#F8F8F2"
                        elif theme == "sublime-mariana":
                            dark_bg_color = "#343D46"
                            light_text_color = "#D8DEE9"
                            cmt_color = "#65737E"
                            keyword_color = "#C594C5"
                            string_color = "#99C794"
                            number_color = "#F99157"
                            operator_color = "#5FB3B3"
                        elif theme == "intellij-darcula":
                            dark_bg_color = "#2B2B2B"
                            light_text_color = "#A9B7C6"
                            cmt_color = "#808080"
                            keyword_color = "#CC7832"
                            string_color = "#6A8759"
                            number_color = "#6897BB"
                            operator_color = "#A9B7C6"
                        elif theme == "intellij-light":
                            dark_bg_color = "#FFFFFF"
                            light_text_color = "#000000"
                            cmt_color = "#808080"
                            keyword_color = "#000080"
                            string_color = "#008000"
                            number_color = "#0000FF"
                            operator_color = "#000000"
                        
                        # Popular Dark Themes
                        elif theme == "dracula":
                            dark_bg_color = "#282A36"
                            light_text_color = "#F8F8F2"
                            cmt_color = "#6272A4"
                            keyword_color = "#FF79C6"
                            string_color = "#F1FA8C"
                            number_color = "#BD93F9"
                            operator_color = "#FF79C6"
                        elif theme == "nord":
                            dark_bg_color = "#2E3440"
                            light_text_color = "#D8DEE9"
                            cmt_color = "#616E88"
                            keyword_color = "#81A1C1"
                            string_color = "#A3BE8C"
                            number_color = "#B48EAD"
                            operator_color = "#88C0D0"
                        elif theme == "material-dark":
                            dark_bg_color = "#263238"
                            light_text_color = "#EEFFFF"
                            cmt_color = "#546E7A"
                            keyword_color = "#C792EA"
                            string_color = "#C3E88D"
                            number_color = "#F78C6C"
                            operator_color = "#89DDFF"
                        elif theme == "material-ocean":
                            dark_bg_color = "#0F111A"
                            light_text_color = "#8F93A2"
                            cmt_color = "#464B5D"
                            keyword_color = "#C792EA"
                            string_color = "#C3E88D"
                            number_color = "#F78C6C"
                            operator_color = "#89DDFF"
                        elif theme == "material-palenight":
                            dark_bg_color = "#292D3E"
                            light_text_color = "#A6ACCD"
                            cmt_color = "#676E95"
                            keyword_color = "#C792EA"
                            string_color = "#C3E88D"
                            number_color = "#F78C6C"
                            operator_color = "#89DDFF"
                        elif theme == "gruvbox-dark":
                            dark_bg_color = "#282828"
                            light_text_color = "#EBDBB2"
                            cmt_color = "#928374"
                            keyword_color = "#FB4934"
                            string_color = "#B8BB26"
                            number_color = "#D3869B"
                            operator_color = "#8EC07C"
                        elif theme == "one-dark-pro":
                            dark_bg_color = "#1E2127"
                            light_text_color = "#ABB2BF"
                            cmt_color = "#5C6370"
                            keyword_color = "#E95678"
                            string_color = "#98C379"
                            number_color = "#D19A66"
                            operator_color = "#56B6C2"
                        elif theme == "tokyo-night":
                            dark_bg_color = "#1A1B26"
                            light_text_color = "#C0CAF5"
                            cmt_color = "#565F89"
                            keyword_color = "#BB9AF7"
                            string_color = "#9ECE6A"
                            number_color = "#FF9E64"
                            operator_color = "#7DCFFF"
                        elif theme == "synthwave-84":
                            dark_bg_color = "#2A2139"
                            light_text_color = "#FFFFFF"
                            cmt_color = "#8B8B8B"
                            keyword_color = "#FF7EDB"
                            string_color = "#F97E72"
                            number_color = "#FFEE80"
                            operator_color = "#36F9F6"
                        elif theme == "cyberpunk":
                            dark_bg_color = "#0A0A0A"
                            light_text_color = "#00FF41"
                            cmt_color = "#008F11"
                            keyword_color = "#FF1744"
                            string_color = "#FFFF00"
                            number_color = "#FF6EC7"
                            operator_color = "#00E5FF"
                        elif theme == "palenight":
                            dark_bg_color = "#292D3E"
                            light_text_color = "#BFC7D5"
                            cmt_color = "#697098"
                            keyword_color = "#C792EA"
                            string_color = "#C3E88D"
                            number_color = "#F78C6C"
                            operator_color = "#89DDFF"
                        elif theme == "ayu-dark":
                            dark_bg_color = "#0B0E14"
                            light_text_color = "#B3B1AD"
                            cmt_color = "#626A73"
                            keyword_color = "#FF8F40"
                            string_color = "#AAD94C"
                            number_color = "#D2A6FF"
                            operator_color = "#39BAE6"
                        elif theme == "night-owl":
                            dark_bg_color = "#011627"
                            light_text_color = "#D6DEEB"
                            cmt_color = "#637777"
                            keyword_color = "#C792EA"
                            string_color = "#ECC48D"
                            number_color = "#F78C6C"
                            operator_color = "#7FDBCA"
                        elif theme == "moonlight":
                            dark_bg_color = "#212337"
                            light_text_color = "#C8D3F5"
                            cmt_color = "#636DA6"
                            keyword_color = "#C099FF"
                            string_color = "#C3E88D"
                            number_color = "#FF966C"
                            operator_color = "#86E1FC"
                        elif theme == "dark-plus":
                            dark_bg_color = "#1E1E1E"
                            light_text_color = "#D4D4D4"
                            cmt_color = "#6A9955"
                            keyword_color = "#569CD6"
                            string_color = "#CE9178"
                            number_color = "#B5CEA8"
                            operator_color = "#D4D4D4"
                        elif theme == "horizon":
                            dark_bg_color = "#1C1E26"
                            light_text_color = "#E3E6EE"
                            cmt_color = "#6C6F93"
                            keyword_color = "#E95678"
                            string_color = "#29D398"
                            number_color = "#FAB795"
                            operator_color = "#59E3E3"
                        elif theme == "oceanic-next":
                            dark_bg_color = "#1B2B34"
                            light_text_color = "#CDD3DE"
                            cmt_color = "#65737E"
                            keyword_color = "#C594C5"
                            string_color = "#99C794"
                            number_color = "#F99157"
                            operator_color = "#5FB3B3"

                        elif theme == "spacegray":
                            dark_bg_color = "#2C2C2C"
                            light_text_color = "#B7B7B7"
                            cmt_color = "#6C7986"
                            keyword_color = "#96CBFE"
                            string_color = "#A8FF60"
                            number_color = "#FF6C60"
                            operator_color = "#FFFFB6"
                        elif theme == "blackboard":
                            dark_bg_color = "#0C1021"
                            light_text_color = "#F8F8F8"
                            cmt_color = "#AEAEAE"
                            keyword_color = "#FBDE2D"
                            string_color = "#61CE3C"
                            number_color = "#D8FA3C"
                            operator_color = "#FF6400"
                        elif theme == "cobalt":
                            dark_bg_color = "#002240"
                            light_text_color = "#FFFFFF"
                            cmt_color = "#7F7F7F"
                            keyword_color = "#FF9D00"
                            string_color = "#3AD900"
                            number_color = "#FF628C"
                            operator_color = "#80FFBB"
                        elif theme == "tomorrow-night":
                            dark_bg_color = "#1D1F21"
                            light_text_color = "#C5C8C6"
                            cmt_color = "#969896"
                            keyword_color = "#B294BB"
                            string_color = "#B5BD68"
                            number_color = "#DE935F"
                            operator_color = "#8ABEB7"
                        elif theme == "tomorrow-night-blue":
                            dark_bg_color = "#002451"
                            light_text_color = "#FFFFFF"
                            cmt_color = "#7285B7"
                            keyword_color = "#EBBBFF"
                            string_color = "#D1F1A9"
                            number_color = "#FFEAA7"
                            operator_color = "#99FFFF"
                        elif theme == "tomorrow-night-bright":
                            dark_bg_color = "#000000"
                            light_text_color = "#EAEAEA"
                            cmt_color = "#969896"
                            keyword_color = "#B294BB"
                            string_color = "#B5BD68"
                            number_color = "#DE935F"
                            operator_color = "#8ABEB7"
                        elif theme == "monokai-pro":
                            dark_bg_color = "#2D2A2E"
                            light_text_color = "#FCFCFA"
                            cmt_color = "#727072"
                            keyword_color = "#FF6188"
                            string_color = "#FFD866"
                            number_color = "#AB9DF2"
                            operator_color = "#78DCE8"
                        elif theme == "shades-of-purple":
                            dark_bg_color = "#2D2B55"
                            light_text_color = "#A599E9"
                            cmt_color = "#B362FF"
                            keyword_color = "#FF9500"
                            string_color = "#4D9375"
                            number_color = "#FF628C"
                            operator_color = "#FAD000"
                        elif theme == "plastic":
                            dark_bg_color = "#21252B"
                            light_text_color = "#ABB2BF"
                            cmt_color = "#5C6370"
                            keyword_color = "#E06C75"
                            string_color = "#98C379"
                            number_color = "#D19A66"
                            operator_color = "#56B6C2"
                        elif theme == "city-lights":
                            dark_bg_color = "#181E24"
                            light_text_color = "#718CA1"
                            cmt_color = "#41505E"
                            keyword_color = "#5EC4FF"
                            string_color = "#92D192"
                            number_color = "#F2777A"
                            operator_color = "#FFB454"
                        elif theme == "material-darker":
                            dark_bg_color = "#212121"
                            light_text_color = "#EEFFFF"
                            cmt_color = "#545454"
                            keyword_color = "#C792EA"
                            string_color = "#C3E88D"
                            number_color = "#F78C6C"
                            operator_color = "#89DDFF"
                        elif theme == "andromeda":
                            dark_bg_color = "#262A33"
                            light_text_color = "#F7F7F7"
                            cmt_color = "#C5C8C6"
                            keyword_color = "#96E072"
                            string_color = "#FFE66D"
                            number_color = "#C74DED"
                            operator_color = "#00E8C6"
                        elif theme == "winter-is-coming-dark":
                            dark_bg_color = "#0E2A44"
                            light_text_color = "#ACCDDF"
                            cmt_color = "#4A5863"
                            keyword_color = "#569CD6"
                            string_color = "#CE9178"
                            number_color = "#B5CEA8"
                            operator_color = "#D4D4D4"
                        
                        # Light Themes
                        elif theme == "gruvbox-light":
                            dark_bg_color = "#FBF1C7"
                            light_text_color = "#3C3836"
                            cmt_color = "#928374"
                            keyword_color = "#9D0006"
                            string_color = "#79740E"
                            number_color = "#8F3F71"
                            operator_color = "#427B58"
                        elif theme == "material-light":
                            dark_bg_color = "#FAFAFA"
                            light_text_color = "#546E7A"
                            cmt_color = "#AABFC9"
                            keyword_color = "#7C4DFF"
                            string_color = "#91B859"
                            number_color = "#F76D47"
                            operator_color = "#39ADB5"
                        elif theme == "ayu-light":
                            dark_bg_color = "#FAFAFA"
                            light_text_color = "#5C6773"
                            cmt_color = "#ABB0B6"
                            keyword_color = "#FF6A00"
                            string_color = "#86B300"
                            number_color = "#A37ACC"
                            operator_color = "#4CBF99"
                        elif theme == "github-clean":
                            dark_bg_color = "#FFFFFF"
                            light_text_color = "#24292E"
                            cmt_color = "#6A737D"
                            keyword_color = "#D73A49"
                            string_color = "#032F62"
                            number_color = "#005CC5"
                            operator_color = "#24292E"
                        elif theme == "xcode-light":
                            dark_bg_color = "#FFFFFF"
                            light_text_color = "#000000"
                            cmt_color = "#0F7B0F"
                            keyword_color = "#9B2393"
                            string_color = "#C41A16"
                            number_color = "#1C00CF"
                            operator_color = "#000000"
                        elif theme == "winter-is-coming-light":
                            dark_bg_color = "#F7F9FB"
                            light_text_color = "#0E2A44"
                            cmt_color = "#4A5863"
                            keyword_color = "#0068D6"
                            string_color = "#B80E0E"
                            number_color = "#0068D6"
                            operator_color = "#0E2A44"
                        elif theme == "quiet-light":
                            dark_bg_color = "#F5F5F5"
                            light_text_color = "#333333"
                            cmt_color = "#AAAAAA"
                            keyword_color = "#4078F2"
                            string_color = "#50A14F"
                            number_color = "#986801"
                            operator_color = "#A626A4"
                        elif theme == "solarized-high-contrast":
                            dark_bg_color = "#FDF6E3"
                            light_text_color = "#002B36"
                            cmt_color = "#93A1A1"
                            keyword_color = "#859900"
                            string_color = "#2AA198"
                            number_color = "#D33682"
                            operator_color = "#586E75"
                        elif theme == "atom-light":
                            dark_bg_color = "#FFFFFF"
                            light_text_color = "#333333"
                            cmt_color = "#A0A1A7"
                            keyword_color = "#A626A4"
                            string_color = "#50A14F"
                            number_color = "#986801"
                            operator_color = "#0184BC"
                        elif theme == "base16-light":
                            dark_bg_color = "#F8F8F8"
                            light_text_color = "#383838"
                            cmt_color = "#B8B8B8"
                            keyword_color = "#AB4642"
                            string_color = "#A1B56C"
                            number_color = "#F7CA88"
                            operator_color = "#7CAFC2"
                        elif theme == "tomorrow":
                            dark_bg_color = "#FFFFFF"
                            light_text_color = "#4D4D4C"
                            cmt_color = "#8E908C"
                            keyword_color = "#8959A8"
                            string_color = "#718C00"
                            number_color = "#F5871F"
                            operator_color = "#3E999F"
                        elif theme == "github-plus":
                            dark_bg_color = "#FFFFFF"
                            light_text_color = "#24292F"
                            cmt_color = "#6E7781"
                            keyword_color = "#CF222E"
                            string_color = "#0A3069"
                            number_color = "#0550AE"
                            operator_color = "#24292F"
                        
                        # High Contrast Themes
                        elif theme == "high-contrast":
                            dark_bg_color = "#000000"
                            light_text_color = "#FFFFFF"
                            cmt_color = "#7CA668"
                            keyword_color = "#569CD6"
                            string_color = "#CE9178"
                            number_color = "#B5CEA8"
                            operator_color = "#D4D4D4"
                        elif theme == "high-contrast-light":
                            dark_bg_color = "#FFFFFF"
                            light_text_color = "#000000"
                            cmt_color = "#008000"
                            keyword_color = "#0000FF"
                            string_color = "#A31515"
                            number_color = "#098658"
                            operator_color = "#000000"
                        elif theme == "kimbie-dark":
                            dark_bg_color = "#221A0F"
                            light_text_color = "#D3AF86"
                            cmt_color = "#A57A4C"
                            keyword_color = "#DC3958"
                            string_color = "#889B4A"
                            number_color = "#F79A32"
                            operator_color = "#7EB2B1"
                        elif theme == "paraiso-dark":
                            dark_bg_color = "#2F1B69"
                            light_text_color = "#A39E9B"
                            cmt_color = "#776E71"
                            keyword_color = "#EF6155"
                            string_color = "#48B685"
                            number_color = "#FEC418"
                            operator_color = "#06B6EF"
                        elif theme == "railscasts":
                            dark_bg_color = "#2B2B2B"
                            light_text_color = "#E6E1DC"
                            cmt_color = "#BC9458"
                            keyword_color = "#CC7833"
                            string_color = "#A5C261"
                            number_color = "#A5C261"
                            operator_color = "#DA4939"
                        elif theme == "textmate":
                            dark_bg_color = "#171717"
                            light_text_color = "#F8F8F8"
                            cmt_color = "#AEAEAE"
                            keyword_color = "#CDA869"
                            string_color = "#8F9D6A"
                            number_color = "#CF6A4C"
                            operator_color = "#F8F8F8"
                        elif theme == "clouds":
                            dark_bg_color = "#FFFFFF"
                            light_text_color = "#000000"
                            cmt_color = "#BCC8BA"
                            keyword_color = "#AF956F"
                            string_color = "#5D90CD"
                            number_color = "#46A609"
                            operator_color = "#484848"
                        elif theme == "clouds-midnight":
                            dark_bg_color = "#191919"
                            light_text_color = "#929292"
                            cmt_color = "#3C403B"
                            keyword_color = "#927C5D"
                            string_color = "#5D90CD"
                            number_color = "#46A609"
                            operator_color = "#E92E2E"
                        
                        # Unique/Special Themes
                        elif theme == "matrix":
                            dark_bg_color = "#000000"
                            light_text_color = "#00FF41"
                            cmt_color = "#008F11"
                            keyword_color = "#00FF41"
                            string_color = "#32CD32"
                            number_color = "#00FF00"
                            operator_color = "#00FF41"
                        elif theme == "retro-green":
                            dark_bg_color = "#001100"
                            light_text_color = "#00FF00"
                            cmt_color = "#008800"
                            keyword_color = "#00FF00"
                            string_color = "#00DD00"
                            number_color = "#00BB00"
                            operator_color = "#00FF00"
                        elif theme == "amber-terminal":
                            dark_bg_color = "#1A0E00"
                            light_text_color = "#FFB000"
                            cmt_color = "#FF8800"
                            keyword_color = "#FFD700"
                            string_color = "#FFA500"
                            number_color = "#FF9500"
                            operator_color = "#FFB000"
                        elif theme == "blue-terminal":
                            dark_bg_color = "#000033"
                            light_text_color = "#00AAFF"
                            cmt_color = "#0088DD"
                            keyword_color = "#00CCFF"
                            string_color = "#0099EE"
                            number_color = "#00BBFF"
                            operator_color = "#00AAFF"
                        elif theme == "hacker":
                            dark_bg_color = "#000000"
                            light_text_color = "#00FF00"
                            cmt_color = "#006600"
                            keyword_color = "#FF0000"
                            string_color = "#FFFF00"
                            number_color = "#00FFFF"
                            operator_color = "#FF00FF"
                        elif theme == "neon":
                            dark_bg_color = "#0C0C0C"
                            light_text_color = "#00FFFF"
                            cmt_color = "#808080"
                            keyword_color = "#FF1493"
                            string_color = "#32CD32"
                            number_color = "#FFD700"
                            operator_color = "#FF69B4"
                        elif theme == "outrun":
                            dark_bg_color = "#0F0208"
                            light_text_color = "#F2F2F2"
                            cmt_color = "#A64AC9"
                            keyword_color = "#FCEE0A"
                            string_color = "#72FDFF"
                            number_color = "#FE4450"
                            operator_color = "#F92AAD"
                        elif theme == "vaporwave":
                            dark_bg_color = "#170F1E"
                            light_text_color = "#F7F3FF"
                            cmt_color = "#7D7D7D"
                            keyword_color = "#FF71CE"
                            string_color = "#01CDFE"
                            number_color = "#05FFA1"
                            operator_color = "#B967DB"
                        elif theme == "forest":
                            dark_bg_color = "#0F2419"
                            light_text_color = "#E8F4E8"
                            cmt_color = "#5F8A5F"
                            keyword_color = "#7CB342"
                            string_color = "#81C784"
                            number_color = "#A5D6A7"
                            operator_color = "#66BB6A"
                        elif theme == "desert":
                            dark_bg_color = "#2B1B0F"
                            light_text_color = "#F4E4BC"
                            cmt_color = "#A0814B"
                            keyword_color = "#D2691E"
                            string_color = "#CD853F"
                            number_color = "#DEB887"
                            operator_color = "#BC8F8F"
                        elif theme == "ocean-deep":
                            dark_bg_color = "#001122"
                            light_text_color = "#88CCEE"
                            cmt_color = "#4477AA"
                            keyword_color = "#0077BB"
                            string_color = "#33BBEE"
                            number_color = "#009988"
                            operator_color = "#66CCEE"
                        elif theme == "sunset":
                            dark_bg_color = "#2B1A0F"
                            light_text_color = "#FFEECC"
                            cmt_color = "#CC8844"
                            keyword_color = "#FF6633"
                            string_color = "#FFAA44"
                            number_color = "#FF9966"
                            operator_color = "#FFCC77"
                        elif theme == "aurora":
                            dark_bg_color = "#0E1419"
                            light_text_color = "#D5E4F7"
                            cmt_color = "#5C7E9B"
                            keyword_color = "#88C0D0"
                            string_color = "#A3BE8C"
                            number_color = "#D08770"
                            operator_color = "#81A1C1"
                        elif theme == "galaxy":
                            dark_bg_color = "#0D1117"
                            light_text_color = "#E1E4E8"
                            cmt_color = "#6A737D"
                            keyword_color = "#F97583"
                            string_color = "#9ECBFF"
                            number_color = "#79C0FF"
                            operator_color = "#B392F0"
                        elif theme == "coffee":
                            dark_bg_color = "#2B1810"
                            light_text_color = "#E8D5B7"
                            cmt_color = "#8B6914"
                            keyword_color = "#CD853F"
                            string_color = "#D2B48C"
                            number_color = "#DEB887"
                            operator_color = "#F4A460"
                        elif theme == "sepia":
                            dark_bg_color = "#F4F1E8"
                            light_text_color = "#704214"
                            cmt_color = "#8B7355"
                            keyword_color = "#A0522D"
                            string_color = "#8B4513"
                            number_color = "#CD853F"
                            operator_color = "#654321"
                        elif theme == "vintage":
                            dark_bg_color = "#F5F5DC"
                            light_text_color = "#2F4F4F"
                            cmt_color = "#808080"
                            keyword_color = "#8B0000"
                            string_color = "#006400"
                            number_color = "#B8860B"
                            operator_color = "#4682B4"
                        elif theme == "newspaper":
                            dark_bg_color = "#FFFFFF"
                            light_text_color = "#000000"
                            cmt_color = "#666666"
                            keyword_color = "#000080"
                            string_color = "#008000"
                            number_color = "#800080"
                            operator_color = "#000000"
                        elif theme == "terminal-green":
                            dark_bg_color = "#002200"
                            light_text_color = "#00AA00"
                            cmt_color = "#006600"
                            keyword_color = "#00FF00"
                            string_color = "#00CC00"
                            number_color = "#00DD00"
                            operator_color = "#00BB00"
                        elif theme == "red-alert":
                            dark_bg_color = "#220000"
                            light_text_color = "#FF6666"
                            cmt_color = "#AA4444"
                            keyword_color = "#FF0000"
                            string_color = "#FF9999"
                            number_color = "#FFAAAA"
                            operator_color = "#FF3333"
                        
                        extension_themes.main()

                        line_number_bg = dark_bg_color

                except Exception as e:
                    print(f"Error loading theme: {e}")
                    # Default fallback colors
                    dark_bg_color = "#1B1F2B"
                    light_text_color = "#FFFFFF"
                    cmt_color = "#68C147"
                    keyword_color = "#569CD6"
                    string_color = "#BA9EFE"
                    number_color = "#FFDD54"
                    operator_color = "#D4D4D4"
                    line_number_bg = dark_bg_color

                text_area.StyleSetBackground(stc.STC_STYLE_DEFAULT, dark_bg_color)
                text_area.StyleSetForeground(stc.STC_STYLE_DEFAULT, light_text_color)
                text_area.StyleClearAll()

                if file_name.endswith(".py"):
                    text_area.SetLexer(stc.STC_LEX_PYTHON)
                    text_area.StyleSetSpec(stc.STC_P_COMMENTLINE, f"fore:{cmt_color},italic,back:{dark_bg_color}")
                    text_area.StyleSetSpec(stc.STC_P_STRING, f"fore:{string_color},italic,back:{dark_bg_color}")
                    text_area.StyleSetSpec(stc.STC_P_WORD, f"fore:{keyword_color},bold,back:{dark_bg_color}")
                    text_area.SetKeyWords(0, "def class return if else elif import from as not is try except finally for while in with pass lambda")
                    text_area.StyleSetSpec(stc.STC_P_IDENTIFIER, f"fore:{light_text_color},italic,back:{dark_bg_color}")
                    text_area.StyleSetSpec(stc.STC_P_OPERATOR, f"fore:{operator_color},bold,back:{dark_bg_color}")
                    text_area.StyleSetSpec(stc.STC_P_NUMBER, f"fore:{number_color},italic,back:{dark_bg_color}")
                    text_area.StyleSetSpec(stc.STC_P_DECORATOR, f"fore:{keyword_color},italic,back:{dark_bg_color}")

                    # Strings
                    text_area.StyleSetSpec(stc.STC_P_STRING, f"fore:{string_color},back:{dark_bg_color}")  # Regular strings
                    text_area.StyleSetSpec(stc.STC_P_CHARACTER, f"fore:#FF79C6,bold,back:{dark_bg_color}")  # Character strings (we'll use this for prefixed strings)
                    text_area.StyleSetSpec(stc.STC_P_TRIPLE, f"fore:{string_color},back:{dark_bg_color}")  # Triple quotes
                    text_area.StyleSetSpec(stc.STC_P_TRIPLEDOUBLE, f"fore:{string_color},back:{dark_bg_color}")  # Triple double quotes
                    text_area.StyleSetSpec(stc.STC_P_DEFNAME, f"fore:#50FA7B,back:{dark_bg_color}")

                    # Keywords
                    text_area.StyleSetSpec(stc.STC_P_WORD, f"fore:#569CD6,bold,back:{dark_bg_color}")
                    text_area.SetKeyWords(0,
                                        "def class return if else elif import from as not is try except finally for while in with pass lambda")
                    
                    # Functions and variables
                    text_area.StyleSetSpec(stc.STC_P_IDENTIFIER, f"fore:#7BCCE1,italic,back:{dark_bg_color}")
                    
                    # Operators
                    text_area.StyleSetSpec(stc.STC_P_OPERATOR, f"fore:#D4D4D4,bold,back:{dark_bg_color}")
                    
                    # Numbers
                    text_area.StyleSetSpec(stc.STC_P_NUMBER, f"fore:#FFDD54,italic,back:{dark_bg_color}")
                    
                    # Decorators
                    text_area.StyleSetSpec(stc.STC_P_DECORATOR, f"fore:#C586C0,italic,back:{dark_bg_color}")
                    
                elif file_name.endswith(".html"):
                    text_area.SetLexer(stc.STC_LEX_HTML)
                    
                    # Tags
                    text_area.StyleSetSpec(stc.STC_H_TAG, f"fore:#569CD6,bold,back:{dark_bg_color}")
                    
                    # Attributes
                    text_area.StyleSetSpec(stc.STC_H_ATTRIBUTE, f"fore:#D69D85,italic,back:{dark_bg_color}")
                    
                    # Attribute values
                    text_area.StyleSetSpec(stc.STC_H_VALUE, f"fore:#BA9EFE,italic,back:{dark_bg_color}")
                    
                    # Comments
                    text_area.StyleSetSpec(stc.STC_H_COMMENT,  f"fore:{cmt_color},italic,back:{dark_bg_color}")
                    
                    # Entities
                    text_area.StyleSetSpec(stc.STC_H_ENTITY, f"fore:#FFDD54,italic,back:{dark_bg_color}")
                    
                    # Numbers
                    text_area.StyleSetSpec(stc.STC_H_NUMBER, f"fore:#FFDD54,italic,back:{dark_bg_color}")
                    
                    # Operators (like '=')
                    text_area.StyleSetSpec(stc.STC_H_OTHER, f"fore:#D4D4D4,bold,back:{dark_bg_color}")
                    
                elif file_name.endswith(".json"):
                    # Set up JSON syntax highlighting
                    text_area.SetLexer(stc.STC_LEX_JSON)
                    
                    # Strings (e.g., "key" or "value")
                    text_area.StyleSetSpec(stc.STC_JSON_STRING, f"fore:#BA9EFE,italic,back:{dark_bg_color}")
                    
                    # Numbers (e.g., 123, 3.14)
                    text_area.StyleSetSpec(stc.STC_JSON_NUMBER, f"fore:#FFDD54,back:{dark_bg_color}")
                    
                    # Colons (e.g., in "key": "value")
                    text_area.StyleSetSpec(stc.STC_JSON_OPERATOR, f"fore:#D4D4D4,bold,back:{dark_bg_color}")
                    
                    # Keywords (e.g., true, false, null)
                    text_area.StyleSetSpec(stc.STC_JSON_KEYWORD, f"fore:#68C147,bold,back:{dark_bg_color}")
                elif file_name.endswith(".css"):
                    # Set up CSS syntax highlighting
                    text_area.SetLexer(stc.STC_LEX_CSS)
                    
                    # Default text
                    text_area.StyleSetSpec(stc.STC_CSS_DEFAULT, f"fore:#D4D4D4,back:{dark_bg_color}")
                    
                    # Comments (e.g., /* This is a comment */)
                    text_area.StyleSetSpec(stc.STC_CSS_COMMENT,  f"fore:{cmt_color},italic,back:{dark_bg_color}")
                    
                    # Tag Names (e.g., body, h1, div)
                    text_area.StyleSetSpec(stc.STC_CSS_TAG, f"fore:#569CD6,bold,back:{dark_bg_color}")
                    
                    # Class and IDs (e.g., .className, #idName)
                    text_area.StyleSetSpec(stc.STC_CSS_CLASS, f"fore:#7BCCE1,italic,back:{dark_bg_color}")
                    text_area.StyleSetSpec(stc.STC_CSS_ID, f"fore:#FFAA33,italic,back:{dark_bg_color}")
                    
                    # Attributes (e.g., color, margin, padding)
                    text_area.StyleSetSpec(stc.STC_CSS_ATTRIBUTE, f"fore:#BA9EFE,bold,back:{dark_bg_color}")
                    
                    # Pseudo-classes and Elements (e.g., :hover, ::before)
                    text_area.StyleSetSpec(stc.STC_CSS_PSEUDOCLASS, f"fore:#C586C0,italic,back:{dark_bg_color}")
                    text_area.StyleSetSpec(stc.STC_CSS_PSEUDOELEMENT, f"fore:#C586C0,italic,back:{dark_bg_color}")
                    
                    # Property Values (e.g., red, 10px, 1em)
                    text_area.StyleSetSpec(stc.STC_CSS_VALUE, f"fore:#FFDD54,back:{dark_bg_color}")
                    
                    # Operators (e.g., :, ;, {, })
                    text_area.StyleSetSpec(stc.STC_CSS_OPERATOR, f"fore:#D4D4D4,bold,back:{dark_bg_color}")
                    
                    # Import Statement (e.g., @import)
                    text_area.StyleSetSpec(stc.STC_CSS_DIRECTIVE, f"fore:#68C147,bold,back:{dark_bg_color}")
                    
                elif file_name.endswith(".js"):
                    # Set up JavaScript syntax highlighting
                    text_area.SetLexer(stc.STC_LEX_ESCRIPT)
                    
                    # Default text
                    text_area.StyleSetSpec(stc.STC_ESCRIPT_DEFAULT, f"fore:#D4D4D4,back:{dark_bg_color}")
                    
                    # Comments (e.g., // This is a comment, /* multi-line */)
                    text_area.StyleSetSpec(stc.STC_ESCRIPT_COMMENT,  f"fore:{cmt_color},italic,back:{dark_bg_color}")
                    text_area.StyleSetSpec(stc.STC_ESCRIPT_COMMENTLINE, f"fore:{cmt_color},italic,back:{dark_bg_color}")
                    text_area.StyleSetSpec(stc.STC_ESCRIPT_COMMENTDOC, f"fore:{cmt_color},italic,back:{dark_bg_color}")
                    
                    # Keywords (e.g., var, let, const, function)
                    text_area.StyleSetSpec(stc.STC_ESCRIPT_WORD, f"fore:#569CD6,bold,back:{dark_bg_color}")
                    
                    # Strings (e.g., "text", 'text', `template literal`)
                    text_area.StyleSetSpec(stc.STC_ESCRIPT_STRING, f"fore:#BA9EFE,italic,back:{dark_bg_color}")
                    
                    # Numbers (e.g., 123, 3.14, 0xFF)
                    text_area.StyleSetSpec(stc.STC_ESCRIPT_NUMBER, f"fore:#FFDD54,back:{dark_bg_color}")
                    
                    # Identifiers (e.g., variables, function names)
                    text_area.StyleSetSpec(stc.STC_ESCRIPT_IDENTIFIER, f"fore:#D4D4D4,back:{dark_bg_color}")
                    
                    # Operators (e.g., =, +, -, *, /, &&, ||)
                    text_area.StyleSetSpec(stc.STC_ESCRIPT_OPERATOR, f"fore:#D4D4D4,bold,back:{dark_bg_color}")
                    
                    # Set JavaScript Keywords
                    text_area.SetKeyWords(0, "var let const function return if else for while do break continue switch case default try catch throw new this super")

                # Default style
                text_area.StyleSetSpec(stc.STC_P_DEFAULT, f"fore:{light_text_color},italic,back:{dark_bg_color}")

                # Adjust indentation guides
                text_area.SetIndentationGuides(True)
                # Set line number background
                text_area.StyleSetSpec(stc.STC_STYLE_LINENUMBER, f"fore:{light_text_color},back:{line_number_bg}")
                text_area.SetMarginType(1, stc.STC_MARGIN_NUMBER)
                text_area.SetMarginWidth(1, 30)

            tab_sizer = wx.BoxSizer(wx.VERTICAL)
            tab_sizer.Add(editor_splitter, proportion=1, flag=wx.EXPAND)
            tab.SetSizer(tab_sizer)

            self.notebook.AddPage(tab, file_name)

    def OnNewFile(self, event):
        filename = wx.TextEntryDialog(self, "File name:")
        fileext = wx.TextEntryDialog(self, "File extension (without the dot):")
        if filename.ShowModal() == wx.ID_OK:
            filename_value = filename.GetValue()
            if not filename_value:
                wx.MessageBox("File name cannot be empty.", "Error", wx.OK | wx.ICON_ERROR)
                return
            if fileext.ShowModal() == wx.ID_OK:
                fileext_value = fileext.GetValue()
                if not fileext_value:
                    errordialog = wx.MessageBox("File extension cannot be empty. If you want to create a file without a file extension, click OK.", "Error", wx.OK | wx.ICON_ERROR)
                    if errordialog == wx.ID_OK:
                        fileext_value = ""

        # Create an empty file name and open it
        if fileext_value:
            temp_file_path = filename_value + "." + fileext_value
        else:
            temp_file_path = filename_value

        # Check if notebook is hidden and show it
        if not self.notebook.IsShown():
            self.default_message.Hide()
            self.main_panel.Hide()
            splitter = self.main_panel.GetParent()
            splitter.ReplaceWindow(self.main_panel, self.notebook)
            self.notebook.Show()

        # Simulate "opening" an empty file by directly calling OnFileOpen with a file name
        with open(temp_file_path, 'w') as temp_file:
            temp_file.write('')  # Create an empty file

        # Add it to the list box so it can be selected
        self.file_list.Append(temp_file_path)
        self.file_list.SetStringSelection(temp_file_path)

        # Call OnFileOpen to handle everything else
        self.OnFileOpen(None)
        
    def OnRunCode(self, event):
        """Runs the code in the current text area based on file extension"""
        # Get the current tab
        current_tab = self.notebook.GetCurrentPage()
        if current_tab:
            # Get the text area from the splitter window
            editor_splitter = current_tab.GetChildren()[0]  # Get the splitter
            text_area = editor_splitter.GetChildren()[0]  # Get the main editor area
            code = text_area.GetValue()
            file_name = self.notebook.GetPageText(self.notebook.GetSelection())
            file_ext = os.path.splitext(file_name)[1].lower()

            # Start measuring time
            start_time = time.time()

            self.monitoring = True
            self.memory_usage = 0  # Reset memory usage
            self.memory_thread = threading.Thread(target=self.track_memory_usage, daemon=True)
            self.memory_thread.start()

            # Create temp file to execute
            temp_file = f"temp{file_ext}"
            with open(temp_file, 'w') as f:
                f.write(code)

            # Execute based on file extension
            if file_ext == '.py':
                self.process = subprocess.Popen(
                    ['python', temp_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            elif file_ext == '.duck':
                self.process = subprocess.Popen(
                    ['npm run compile -- --run', temp_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            elif file_ext == '.java':
                # Compile first
                compile_process = subprocess.run(['javac', temp_file], capture_output=True, text=True)
                if compile_process.returncode == 0:
                    # Run the compiled class
                    class_name = os.path.splitext(temp_file)[0]
                    self.process = subprocess.Popen(
                        ['java', class_name],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                else:
                    self.process = compile_process
            elif file_ext == '.js':
                self.process = subprocess.Popen(
                    ['node', temp_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            elif file_ext == '.cpp':
                # Compile first
                compile_process = subprocess.run(['g++', temp_file, '-o', 'temp.exe'], capture_output=True, text=True)
                if compile_process.returncode == 0:
                    self.process = subprocess.Popen(
                        ['./temp.exe'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                else:
                    self.process = compile_process
            else:
                wx.MessageBox(f"Unsupported file type: {file_ext}", "Error", wx.OK | wx.ICON_ERROR)
                return

            end_time = time.time()
            overall_time = (end_time - start_time) * 1000 

            # Start a thread to handle output and execution time
            threading.Thread(target=self.HandleExecution, args=(overall_time,), daemon=True).start()

            # Clean up temp files
            try:
                os.remove(temp_file)
                if file_ext == '.java':
                    os.remove(f"{os.path.splitext(temp_file)[0]}.class")
                elif file_ext == '.cpp':
                    os.remove('temp.exe')
            except Exception:
                pass

    def track_memory_usage(self):
        """Track memory usage during code execution."""
        process = psutil.Process()
        while self.monitoring:
            mem_info = process.memory_info()
            self.memory_usage = mem_info.rss / (1024 * 1024)  # Memory in MB
            time.sleep(0.5)  # Update every 0.5 seconds

    def HandleExecution(self, start_time):
        self.monitoring = False  # Stop memory monitoring
        stdout, stderr = self.process.communicate()
        end_time = time.time()
        execution_time = end_time - start_time

        # Capture the return value from stdout
        if stdout.strip():
            self.return_values.append(stdout.strip())  # Store return values

        # Create output dialog if it doesn't exist
        if self.output_window is None:
            self.output_window = wx.Dialog(self, title="Output Window", size=(600, 400))
            pywinstyles.apply_style(self.output_window, "mica")

            # Create output text area
            output_panel = wx.Panel(self.output_window)
            output_vbox = wx.BoxSizer(wx.VERTICAL)
            self.output_text = wx.TextCtrl(output_panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
            output_vbox.Add(self.output_text, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
            output_panel.SetSizer(output_vbox)

            # Create return values panel
            return_panel = wx.Panel(self.output_window)
            return_vbox = wx.BoxSizer(wx.VERTICAL)
            self.return_text = wx.TextCtrl(return_panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
            return_vbox.Add(self.return_text, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
            return_panel.SetSizer(return_vbox)

            # Add panels to main dialog
            main_sizer = wx.BoxSizer(wx.VERTICAL)
            main_sizer.Add(output_panel, 1, wx.EXPAND)
            main_sizer.Add(return_panel, 1, wx.EXPAND)
           
            self.output_window.SetSizer(main_sizer)

        # Prepare output message
        try:
            output_message = f"Errors:\n{stderr}\n"
            output_message += f"Execution Time: {execution_time:.4f} milliseconds\n"
            output_message += f"Memory Usage: {self.memory_usage:.2f} MB\n"
        except Exception as e:
            output_message = f"An error occurred: {str(e)}"

        # Update the output text area
        self.output_text.SetValue(output_message)

        # Update the return values visualization
        return_visualization = "\n".join(f"Return {i + 1}: {value}" for i, value in enumerate(self.return_values))
        self.return_text.SetValue(return_visualization)

        # Export output to HTML log file
        log_filename = "execution_log.html"
        self.export_to_html(log_filename, output_message, return_visualization)

        # Show the output dialog modally
        self.output_window.ShowModal()  # Show the output dialog modally

    def export_to_html(self, log_filename, output_message, return_visualization):
        """Export the output and return values to an HTML log file."""
        html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Log</title>
            </head>
            <body>
                <h1>Execution Log</h1>
                <h2>Output</h2>
                <pre>{output_message}</pre>
                <h2>Return Values</h2>
                <pre>{return_visualization}</pre>
            </body>
            </html>
            """

        # Save the HTML content to a file
        with open(log_filename, 'w') as log_file:
            log_file.write(html_content)

    def OnSave(self, event):
        current_tab = self.notebook.GetCurrentPage()
        if current_tab:
            # Get the correct text area from the splitter window
            editor_splitter = current_tab.GetChildren()[0]  # Get the splitter
            text_area = editor_splitter.GetChildren()[0]  # Get the main editor area
            code = text_area.GetValue()
            file_name = self.notebook.GetPageText(self.notebook.GetSelection())
            file_ext = os.path.splitext(file_name)[1].lower()

            # Check syntax before saving
            if not hasattr(text_area, 'syntax_checker'):
                text_area.syntax_checker = error_checker.SyntaxChecker(text_area)
                
                # Run syntax check
                text_area.syntax_checker.check_syntax()

            if file_name == "Untitled":
                # Handle saving as a new file
                save_dialog = wx.FileDialog(self, "Save File", "", "", wildcard="Python files (*.py)|*.py",
                                        style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
                if save_dialog.ShowModal() == wx.ID_OK:
                    file_name = save_dialog.GetPath()
                    with open(file_name, 'w') as file:
                        file.write(code)
                    self.notebook.SetPageText(self.notebook.GetSelection(), os.path.basename(file_name))
            else:
                # Overwrite the opened file
                with open(file_name, 'w') as file:
                    file.write(code)

    def OnChar(self, event):
        """Handle character input events including dynamic auto-completion and bracket matching."""
        
        current_tab = self.notebook.GetCurrentPage()
        if current_tab:
            editor_splitter = current_tab.GetChildren()[0]
            text_area = editor_splitter.GetChildren()[0]
            key_code = event.GetKeyCode()
            try:
                # Auto-close brackets
                if chr(key_code) in self.matching_brackets:
                    pos = text_area.GetCurrentPos()
                    text_area.InsertText(pos, self.matching_brackets[chr(key_code)])
                    text_area.SetCurrentPos(pos)
                    text_area.SetSelection(pos, pos)

                if chr(key_code).isalpha() or key_code == ord('.'):
                    pos = text_area.GetCurrentPos()
                    word_start_pos = text_area.WordStartPosition(pos, True)
                    current_word = text_area.GetTextRange(word_start_pos, pos)
                    length = pos - word_start_pos

                    if length >= 0 or key_code == ord('.'):
                        # Get all words from current document
                        full_text = text_area.GetText()
                        words = set()
                        
                        # Extract words (including function names and variables)
                        import re
                        pattern = r'\b[a-zA-Z_]\w*\b'
                        words.update(re.findall(pattern, full_text))
                        
                        # Add relevant Python builtins based on context
                        python_completions = []
                        if key_code == ord('.'):
                            # Method suggestions after dot
                            python_completions = [
                                "append", "extend", "pop", "remove", "clear", "copy", 
                                "count", "index", "insert", "reverse", "sort", "update",
                                "keys", "values", "items", "get", "strip", "split", 
                                "join", "replace", "upper", "lower", "title"
                            ]
                        else:
                            # General Python functions and keywords
                            python_completions = [
                                "def", "class", "import", "from", "return", "raise",
                                "try", "except", "finally", "with", "as", "if", "elif",
                                "else", "for", "while", "break", "continue", "pass",
                                "print", "len", "range", "enumerate", "zip", "dict",
                                "list", "set", "tuple", "str", "int", "float", "bool",
                                "True", "False", "None", "self", "super"
                            ]

                        # Combine and sort completions
                        all_completions = sorted(list(words) + python_completions)
                        
                        # Filter by current word if any
                        if current_word:
                            all_completions = [w for w in all_completions if w.startswith(current_word)]
                        
                        # Show autocompletion if we have suggestions
                        if all_completions:
                            completions = " ".join(all_completions)
                            text_area.AutoCompShow(len(current_word), completions)

                        self.OnSave(wx.EVT_CHAR)
            except Exception as e:
                print("well shit its broken again. you found the gem in the code")

        event.Skip()  # Continue processing other key events

    def on_activate(self, event):
        """
        Handles window activation and deactivation events to update the window header color accordingly.
        
        Updates the header color based on whether the window is active or inactive, and ensures the event is propagated for further processing.
        """
        try:
            if event.GetActive():
                pywinstyles.change_header_color(self, color=self.active_color)
            else:
                pywinstyles.change_header_color(self, color=self.inactive_color)
        except Exception:
            pass

        # Ensure event is processed further
        event.Skip()


    def OnExit(self, event):
        time.sleep(1)
        self.Close()

    def OnCut(self, event):
        current_tab = self.notebook.GetCurrentPage()
        if current_tab:
            text_area = current_tab.GetChildren()[0]
            text_area.Cut()

    def OnCopy(self, event):
        current_tab = self.notebook.GetCurrentPage()
        if current_tab:
            text_area = current_tab.GetChildren()[0]
            text_area.Copy()

    def OnPaste(self, event):
        current_tab = self.notebook.GetCurrentPage()
        if current_tab:
            text_area = current_tab.GetChildren()[0]
            text_area.Paste()

    extension_mainclass.main()

def main():
    """Defines the main process."""
    app = wx.App(False)
    frame = TextEditor(None)

    # Handle command line arguments
    args = sys.argv[1:]

    if args:
        # Show the frame first so everything is initialized
        frame.Show()
        if args[0] == "--open-folder":
            if len(args) > 1:
                # Get the folder path and change to it
                folder_path = args[1].strip('"')  # Remove any quotes
                frame.OnOpenFolder(folder_path)
        else:
            # Assume it's a file path
            file_path = args[0].strip('"')  # Remove any quotes
            
            # Change to the directory containing the file
            dir_path = os.path.dirname(os.path.abspath(file_path))
            os.chdir(dir_path)

            # Update file list and open the file
            frame.PopulateFileList()
            frame.file_list.SetStringSelection(os.path.basename(file_path))
            frame.OnFileOpen(None)

    else:
        frame.Show()
    try:
        extension_mainfn.main()
    except Exception:
        print("No mainfn extension file found.")

    app.MainLoop()
    
    try:
        with open("repo.ghicfg", "r") as file:
            content = file.read()
            if content:
                github.main()

    except FileNotFoundError:
        pass

if __name__ == '__main__':
    """Runs the main process."""
    main()
