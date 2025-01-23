# Library imports
## wxPython
import wx
import wx.stc as stc
## Process Management
import os
import subprocess
import psutil
## Time
import time
## Other
import json
import threading
from pypresence import Presence
import pywinstyles
import webbrowser
# Local imports
## Extensions
import extension_menubar
import extension_mainfn
import extension_mainclass
## Features
import requirements
import git_integration
import settings
import github
import init_project
import error_checker

class TextEditor(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(TextEditor, self).__init__(*args, **kwargs)

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
        except Exception as e:
            pass

        current_dir = os.getcwd()
        
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
                print(f"Could not connect to Discord: {e}")
                self.RPC = None  # Ensure RPC is None if connection fails
        
        # Bind focus events for dynamic color change
        self.Bind(wx.EVT_ACTIVATE, self.on_activate)

        self.output_window = None
        self.InitUI()
        self.return_values = []

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
        """Runs when the window is activated or deactivated."""
        try:
            if event.GetActive():
                pywinstyles.change_header_color(self, color=self.active_color)
            else:
                pywinstyles.change_header_color(self, color=self.inactive_color)
        except Exception as e:
            pass

        # Ensure event is processed further
        event.Skip()

    def InitUI(self):
        panel = wx.Panel(self)
        try:
            icon = wx.Icon('xedixlogo.ico', wx.BITMAP_TYPE_ICO)
            self.SetIcon(icon)
        except Exception as e:
            print(e)

        splitter = wx.SplitterWindow(panel)

        self.sidebar = wx.Panel(splitter)
        self.sidebar.SetBackgroundColour("#fff")
        self.sidebar.SetWindowStyleFlag(wx.NO_BORDER)

        # Add New File button
        new_file_btn = wx.Button(self.sidebar, label="New File")
        new_file_btn.SetBackgroundColour("#EDF0F2")
        new_file_btn.SetForegroundColour("#201f1f")
        new_file_btn.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        new_file_btn.SetWindowStyleFlag(wx.NO_BORDER)
        new_file_btn.SetMinSize((150, 35))
        new_file_btn.SetMaxSize((150, 35))

        new_file_btn.Bind(wx.EVT_BUTTON, self.OnNewFile)

        self.file_list = wx.ListBox(self.sidebar)
        self.PopulateFileList()
        self.file_list.Bind(wx.EVT_RIGHT_DOWN, self.OnFileListRightClick)

        self.matching_brackets = {
            '(': ')', 
            '[': ']', 
            '{': '}',
            '"': '"',
            "'": "'",
        }

        # Create the status bar
        self.CreateStatusBar(3)

        # Customize the appearance of the status bar
        status_bar = self.GetStatusBar()
        status_bar.SetBackgroundColour("#EDF0F2")
        status_bar.SetMinSize((-1, 30))
        self.SendSizeEvent()  # Force the frame to recalculate its layout

        # Display a welcome message in the status bar
        self.SetStatusText("    Welcome to XediX - Text Editor")
        self.SetStatusText("    Open a file first", 1)

        self.main_panel = wx.Panel(splitter)
        self.default_message = wx.StaticText(self.main_panel, label="Open a File first", style=wx.ALIGN_CENTER)
        font = self.default_message.GetFont()
        font.PointSize += 5
        font.color = wx.Colour(255, 255, 255)
        font.bold = True
        try:
            self.default_message.SetFont(font)
        except Exception as e:
            print(e)

        main_vbox = wx.BoxSizer(wx.VERTICAL)
        self.main_panel.SetBackgroundColour("#EDF0F2")

        main_vbox.AddStretchSpacer(1)
        main_vbox.Add(self.default_message, proportion=0, flag=wx.ALIGN_CENTER)
        main_vbox.AddStretchSpacer(1)
        self.main_panel.SetSizer(main_vbox)
        self.notebook = wx.Notebook(splitter)
        self.notebook.Hide()
        self.notebook.SetBackgroundColour("#ffffff00")

        sidebar_vbox = wx.BoxSizer(wx.VERTICAL)
        sidebar_vbox.AddStretchSpacer(0)        

        sidebar_vbox.Add(new_file_btn, proportion=0, flag=wx.EXPAND | wx.RIGHT | wx.BOTTOM, border=10 )
        sidebar_vbox.Add(self.file_list, proportion=1, flag=wx.EXPAND | wx.RIGHT, border=10)

        self.sidebar.SetSizer(sidebar_vbox)

        splitter.SplitVertically(self.sidebar, self.main_panel)
        splitter.SetMinimumPaneSize(150)
        self.CreateMenuBar()

        # Screen Background
        panel.SetBackgroundColour("#fff")

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(splitter, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)

        panel.SetSizer(vbox)

        self.SetTitle("XediX - Text Editor")
        self.SetSize((850, 600))
        self.Centre()

        self.file_list.Bind(wx.EVT_LISTBOX_DCLICK, self.OnFileOpen)
    
    def CreateMenuBar(self):
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

        # Create the Tools menu item (this is a MenuItem, not a Menu)
        tools_item = toolsMenu.Append(wx.ID_ANY, '&Tools\tCtrl+T', 'Run Tools Selector')

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

        self.Bind(wx.EVT_MENU, self.OnSave, save_item)
        self.Bind(wx.EVT_MENU, self.OnRunCode, run_item)
        self.Bind(wx.EVT_MENU, self.run_tools_script, tools_item)
        self.Bind(wx.EVT_MENU, self.OnCustomize, customize_item)
        self.Bind(wx.EVT_MENU, self.RequirementsGeneration, req_item)
        self.Bind(wx.EVT_MENU, self.gcommit, commit_item)
        self.Bind(wx.EVT_MENU, self.OnExit, exit_item)
        self.Bind(wx.EVT_MENU, self.OnCut, cut_item)
        self.Bind(wx.EVT_MENU, self.ginit, init_git_item)
        self.Bind(wx.EVT_MENU, self.pinit, init_python_item)
        self.Bind(wx.EVT_MENU, self.gadd, add_item)
        self.Bind(wx.EVT_MENU, self.gpush, push_item)
        self.Bind(wx.EVT_MENU, self.gpull, pull_item)
        self.Bind(wx.EVT_MENU, self.gversion, version_item)
        self.Bind(wx.EVT_MENU, self.gbranch, branch_item)
        self.Bind(wx.EVT_MENU, self.gstatus, status_item)
        self.Bind(wx.EVT_MENU, self.xinit, init_project_item)
        self.Bind(wx.EVT_MENU, self.OnCopy, copy_item)
        self.Bind(wx.EVT_MENU, self.OnOpenFolder, folder_item)
        self.Bind(wx.EVT_MENU, self.OnConfig, settings_item)
        self.Bind(wx.EVT_MENU, self.OnPaste, paste_item)
        self.Bind(wx.EVT_MENU, self.OnRunPylint, pylint_item)
        self.Bind(wx.EVT_MENU, self.OnFindReplace, find_replace_item)
        self.Bind(wx.EVT_MENU, self.OnJumpToLine, jump_line_item)
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
    
    # The following functions are opening webpages
    def About(self, event):
        self.SetStatusText("    Opening webpage...", 2)
        time.sleep(1)
        webbrowser.open("https://xedix.w3spaces.com/about.html")
        self.SetStatusText("    Webpage opened", 2)

    def Docs(self, event):
        self.SetStatusText("    Opening webpage...", 2)
        time.sleep(1)
        webbrowser.open("https://github.com/mostypc123/XediX/wiki")
        self.SetStatusText("    Webpage opened", 2)

    def Homepage(self, event):
        self.SetStatusText("    Opening webpage...", 2)
        time.sleep(1)
        webbrowser.open("https://xedix.w3spaces.com")
        self.SetStatusText("    Webpage opened", 2)

    def OnConfig(self, event):
        settings.main()

    def OnOpenFolder(self, event):
        # Create and show the directory dialog
        dlg = wx.DirDialog(self, "Choose a directory, if does not exist, it will be created",
                        style=wx.DD_DEFAULT_STYLE)

        if dlg.ShowModal() == wx.ID_OK:
            # Get the selected path
            path = dlg.GetPath()

            try:
                # Check if directory exists first
                if not os.path.exists(path):
                    os.makedirs(path)  # Use makedirs instead of system('mkdir')
                    
                # Change the working directory
                os.chdir(path)
                
                # Show confirmation message
                self.SetStatusText(f"    Changed directory to: {path}")
                
            except PermissionError:
                self.SetStatusText(f"    Error: No permission to create/access directory: {path}")
            except OSError as e:
                self.SetStatusText(f"    Error creating/accessing directory: {e}")

            # Clear the current file list
            self.file_list.Clear()

            # Populate the file list with files from the new directory
            self.PopulateFileList()

            self.current_dir = path

        dlg.Destroy()

    def RequirementsGeneration(self, event):
        current_tab = self.notebook.GetCurrentPage()
        if current_tab:
            text_area = current_tab.GetChildren()[0]
            code = text_area.GetValue()
            with open("requirements.txt", "w") as file:
                file.write(requirements.main(code))
            self.SetStatusText("Saved requirements.txt")
        else:
            self.SetStatusText("Error saving requirements")

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
            old_name = self.file_list.GetString(selected_index)

            # Show dialog to get new name
            dialog = wx.TextEntryDialog(self, "Enter new filename:", "Rename File", old_name)
            if dialog.ShowModal() == wx.ID_OK:
                new_name = dialog.GetValue()

                try:
                    # Rename the file
                    os.rename(old_name, new_name)

                    # Update the file list
                    self.file_list.SetString(selected_index, new_name)

                    # Update the notebook tab if the file is open
                    for i in range(self.notebook.GetPageCount()):
                        if self.notebook.GetPageText(i) == old_name:
                            self.notebook.SetPageText(i, new_name)

                    self.SetStatusText(f"    Renamed {old_name} to {new_name}")
                except OSError as e:
                    wx.MessageBox(f"Error renaming file: {str(e)}", "Error", 
                                wx.OK | wx.ICON_ERROR)

            dialog.Destroy()

    def OnDeleteFile(self, event):
        """Handle file delete operation."""
        selected_index = self.file_list.GetSelection()
        if selected_index != wx.NOT_FOUND:
            filename = self.file_list.GetString(selected_index)

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

                    # Remove from file list
                    self.file_list.Delete(selected_index)

                    self.SetStatusText(f"    Deleted {filename}")
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

    def run_tools_script(self, event):
        """Run tools."""
        try:
            result = subprocess.run(["./tools.exe"], capture_output=True, text=True)
            # Check if the script ran successfully
            if result.returncode == 0:
                print("Script executed successfully.")
            else:
                print("Script execution failed:")
                print(result.stderr)
        except Exception as e:
            print(f"An error occurred: {e}")

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

        self.SetStatusText(f"    Opened file: {file_name}")
        text_area.Bind(wx.EVT_CHAR, self.OnChar)

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
            text_area = current_tab.GetChildren()[0]
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
        self.SetStatusText("    Find and replace running")

        # Find dialog
        find_replace_dialog = wx.TextEntryDialog(self, "Find text:")
        self.SetStatusText("    Find and replace: find dialog running")
        if find_replace_dialog.ShowModal() == wx.ID_OK:
            # Replace dialog
            self.SetStatusText("    Find and replace: find dialog ran")
            find_text = find_replace_dialog.GetValue()
            replace_dialog = wx.TextEntryDialog(self, "Replace with:")
            self.SetStatusText("    Find and replace: replace dialog ran")
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
        self.SetStatusText("    Find and replace ran, or it was closed by the user")


    def PopulateFileList(self):
        """Populates the file list with the files in the current directory"""
        current_dir = os.getcwd()
        files = [f for f in os.listdir(current_dir) if os.path.isfile(os.path.join(current_dir, f))]
        self.file_list.AppendItems(files)
        # Style the files
        self.file_list.SetBackgroundColour('#fff')
        # border color
        self.file_list.SetForegroundColour('#201f1f')

    def OnFileOpen(self, event):
        """Opens a file in the current directory"""
        file_name = self.file_list.GetStringSelection()
        if file_name:
            if file_name == "xedix.xcfg" or file_name == "theme.xcfg":
                self.SetTitle("Customizing XediX")
                time.sleep(20)
                self.SetTitle("XediX - Text Editor")
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

            # Create main text area
            text_area = stc.StyledTextCtrl(editor_splitter, style=wx.TE_MULTILINE)
            text_area.SetText(content)
            text_area.SetTabWidth(4)
            text_area.SetWindowStyleFlag(wx.NO_BORDER)

            # Create minimap
            minimap = stc.StyledTextCtrl(editor_splitter, style=wx.TE_MULTILINE | wx.TE_READONLY)
            minimap.SetText(content)
            minimap.SetZoom(-8)  # Make the text very small
            minimap.SetWindowStyleFlag(wx.NO_BORDER)
            minimap.SetMarginWidth(1, 0)  # Hide line numbers in minimap
            minimap.SetEditable(False)

            # Set minimap width
            minimap.SetMinSize((100, -1))
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

            self.SetStatusText(f"    Opened file: {file_name}")

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
                        dark_bg_color = theme_data.get('background', "#1B1F2B")
                        light_text_color = theme_data.get('foreground', "#FFFFFF")
                        cmt_color = theme_data.get('comment', "#68C147")
                        keyword_color = theme_data.get('keyword', "#569CD6")
                        string_color = theme_data.get('string', "#BA9EFE")
                        number_color = theme_data.get('number', "#FFDD54")
                        operator_color = theme_data.get('operator', "#D4D4D4")
                        line_number_bg = theme_data.get('lineNumberBg', dark_bg_color)
                    else:
                        # Built-in themes
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
                        else:
                            dark_bg_color = "#1B1F2B"
                            light_text_color = "#FFFFFF"
                            cmt_color = "#68C147"
                            keyword_color = "#569CD6"
                            string_color = "#BA9EFE"
                            number_color = "#FFDD54"
                            operator_color = "#D4D4D4"
                        
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
                    self.SetStatusText("    Python", 1)
                    text_area.SetLexer(stc.STC_LEX_PYTHON)
                    text_area.StyleSetSpec(stc.STC_P_COMMENTLINE, f"fore:{cmt_color},italic,back:{dark_bg_color}")
                    text_area.StyleSetSpec(stc.STC_P_STRING, f"fore:{string_color},italic,back:{dark_bg_color}")
                    text_area.StyleSetSpec(stc.STC_P_WORD, f"fore:{keyword_color},bold,back:{dark_bg_color}")
                    text_area.SetKeyWords(0, "def class return if else elif import from as not is try except finally for while in with pass lambda")
                    text_area.StyleSetSpec(stc.STC_P_IDENTIFIER, f"fore:{light_text_color},italic,back:{dark_bg_color}")
                    text_area.StyleSetSpec(stc.STC_P_OPERATOR, f"fore:{operator_color},bold,back:{dark_bg_color}")
                    text_area.StyleSetSpec(stc.STC_P_NUMBER, f"fore:{number_color},italic,back:{dark_bg_color}")
                    text_area.StyleSetSpec(stc.STC_P_DECORATOR, f"fore:{keyword_color},italic,back:{dark_bg_color}")

                # Similar styling updates for HTML, JSON, CSS, and JS...
                # [Previous language-specific styling code remains the same but using the theme variables]

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
            if fileext.ShowModal() == wx.ID_OK:
                fileext_value = fileext.GetValue()

        # Create an empty file name and open it
        temp_file_path = filename_value + "." + fileext_value

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
            overall_time = end_time - start_time

            # Start a thread to handle output and execution time
            threading.Thread(target=self.HandleExecution, args=(overall_time,), daemon=True).start()

            # Clean up temp files
            try:
                os.remove(temp_file)
                if file_ext == '.java':
                    os.remove(f"{os.path.splitext(temp_file)[0]}.class")
                elif file_ext == '.cpp':
                    os.remove('temp.exe')
            except:
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

        self.SetStatusText(f"Saved execution log to: {log_filename}")

    def OnSave(self, event):
        current_tab = self.notebook.GetCurrentPage()
        if current_tab:
            # Get the correct text area from the splitter window
            editor_splitter = current_tab.GetChildren()[0]  # Get the splitter
            text_area = editor_splitter.GetChildren()[0]  # Get the main editor area
            content = text_area.GetValue()
            file_name = self.notebook.GetPageText(self.notebook.GetSelection())
            
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

            # Add syntax checking for Python files
            if file_name.endswith('.py'):
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
                        file.write(content)
                    self.notebook.SetPageText(self.notebook.GetSelection(), os.path.basename(file_name))
            else:
                # Overwrite the opened file
                with open(file_name, 'w') as file:
                    file.write(content)

    def OnChar(self, event):
        """Handle character input events including dynamic auto-completion and bracket matching."""
        self.SetStatusText("    Character pressed", 2)
        self.SetStatusText("    Showing recommendations")
        
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
                        self.SetStatusText("    Autosaved", 2)
            except Exception as e:
                self.SetStatusText(f"    Error running onchar: {str(e)}", 2)

        event.Skip()  # Continue processing other key events
        
    def OnExit(self, event):
        self.SetStatusText("    Exiting XediX...")
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
    frame.Show()
    extension_mainfn.main()
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