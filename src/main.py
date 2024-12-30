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
import threading
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

class TextEditor(wx.Frame):
    def __init__(self, *args, **kwargs):

        super(TextEditor, self).__init__(*args, **kwargs)

        '''
        ===========Config Files For Customization===========
        '''
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
        # panel.SetBackgroundColour("#343947")
        icon = wx.Icon('xedixlogo.ico', wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)

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
        self.default_message.SetFont(font)

        main_vbox = wx.BoxSizer(wx.VERTICAL)
        self.main_panel.SetBackgroundColour("#EDF0F2")

        main_vbox.AddStretchSpacer(1)
        main_vbox.Add(self.default_message, proportion=0, flag=wx.ALIGN_CENTER)
        main_vbox.AddStretchSpacer(1)
        self.main_panel.SetSizer(main_vbox)
        #  Right Pane Background
        # self.main_panel.SetBackgroundColour("#2a72a3")
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
        vbox.Add(splitter, proportion=1, flag=wx.EXPAND | wx.ALL, border=10) #border 0 for minimalism

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
        # Add seperator

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

        # Append the Git submenu to the tools menu
        toolsMenu.AppendSubMenu(git_submenu, "Git")

        helpMenu = wx.Menu()
        homepage_item = helpMenu.Append(wx.ID_ANY, "&Homepage", "Homepage")
        about_item = helpMenu.Append(wx.ID_ABOUT, '&About', 'About')
        docs_item = helpMenu.Append(wx.ID_ANY, "&Docs", "Open Documentation")

        configMenu = wx.Menu()
        customize_item = configMenu.Append(wx.ID_ANY, '&Customize manually\tCtrl+Shift+C', 'Customize the UI')
        settings_item = configMenu.Append(wx.ID_ANY, '&Settings', 'Open Settings')

        menubar.Append(fileMenu, '&File')
        menubar.Append(editMenu, '&Edit')
        menubar.Append(toolsMenu,'&Tools')
        menubar.Append(configMenu, '&Config')
        menubar.Append(helpMenu, '&Help')
        # Define minsize
        self.SetMenuBar(menubar)

        # Give backgorund color to menubar

        self.Bind(wx.EVT_MENU, self.OnSave, save_item)
        self.Bind(wx.EVT_MENU, self.OnRunCode, run_item)
        self.Bind(wx.EVT_MENU, self.run_tools_script, tools_item)
        self.Bind(wx.EVT_MENU, self.OnCustomize, customize_item)
        self.Bind(wx.EVT_MENU, self.RequirementsGeneration, req_item)
        self.Bind(wx.EVT_MENU, self.gcommit, commit_item)
        self.Bind(wx.EVT_MENU, self.OnExit, exit_item)
        self.Bind(wx.EVT_MENU, self.OnCut, cut_item)
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


    def gcommit(self, event):
        git_integration.commit()
    
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
        dlg = wx.DirDialog(self, "Choose a directory:",
                        style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)

        if dlg.ShowModal() == wx.ID_OK:
            # Get the selected path
            path = dlg.GetPath()

            # Change directory using os.system
            os.system(f'cd "{path}"')

            # Also change the Python script's working directory
            os.chdir(path)

            # Show confirmation message
            self.SetStatusText(f"    Changed directory to: {path}")

            # Clear the current file list
            self.file_list.Clear()

            # Populate the file list with files from the new directory
            self.PopulateFileList()

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
            with open(file_path, 'r') as file:
                content = file.read()

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

            self.SetStatusText(f"    Opened file: {file_name}")

            # Bind a key event to trigger autocomplete after typing
            text_area.Bind(wx.EVT_CHAR, self.OnChar)

            # Set dark background and light text for the entire control
            for text_area in (text_area, minimap):
                with open("theme.xcfg", 'r') as file:
                    theme = file.read()

                if theme == "dark":
                    dark_bg_color = "#1B1F2B"
                    cmt_color = "#68C147"
                elif theme == "light":
                    dark_bg_color = "#FFFFFF"
                    light_text_color = "#1e1e1e"
                    cmt_color = "#063970"
                elif theme == "night":
                    dark_bg_color = "#2f3139"
                    cmt_color = "#eab676"
                elif theme == "obsidian":
                    dark_bg_color = "#212232"
                    cmt_color = "#EFC3CA"
                else:
                    dark_bg_color = "#1B1F2B"

                if theme != "light":
                    light_text_color = "#FFFFFF"

                text_area.StyleSetBackground(stc.STC_STYLE_DEFAULT, dark_bg_color)
                text_area.StyleSetForeground(stc.STC_STYLE_DEFAULT, light_text_color)
                text_area.StyleClearAll()  # Apply the default style to all text

                if file_name.endswith(".py"):
                    self.SetStatusText("    Python", 1)

                    # Set up Python syntax highlighting
                    text_area.SetLexer(stc.STC_LEX_PYTHON)

                    # Comments
                    text_area.StyleSetSpec(stc.STC_P_COMMENTLINE, f"fore:{cmt_color},italic,back:{dark_bg_color}")

                    # Strings
                    text_area.StyleSetSpec(stc.STC_P_STRING, f"fore:#BA9EFE,italic,back:{dark_bg_color}")

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
                    self.SetStatusText("    HTML", 1)
                    # Set up HTML syntax highlighting
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
                    self.SetStatusText("    JSON", 1)
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
                    self.SetStatusText("    CSS", 1)
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
                    self.SetStatusText("    Javascript", 1)
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
                    text_area.SetKeyWords(0, "var let const function return if else for while do break continue switch case default try catch throw new this super class extends export import async await typeof instanceof delete")


                # Default style
                text_area.StyleSetSpec(stc.STC_P_DEFAULT, f"fore:{light_text_color},italic,back:{dark_bg_color}")

                # Adjust indentation guides
                text_area.SetIndentationGuides(True)
                text_area.StyleSetSpec(stc.STC_STYLE_LINENUMBER, f"fore:{light_text_color},italic,back:{dark_bg_color}")
                text_area.SetMarginType(1, stc.STC_MARGIN_NUMBER)
                text_area.SetMarginWidth(1, 30)

            tab_sizer = wx.BoxSizer(wx.VERTICAL)
            tab_sizer.Add(editor_splitter, proportion=1, flag=wx.EXPAND)
            tab.SetSizer(tab_sizer)

            self.notebook.AddPage(tab, file_name)

    def OnNewFile(self, event):
        filename = wx.TextEntryDialog(self, "File name:")
        fileext = wx.TextEntryDialog(self, "File extension(without the dot):")
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
        """Runs the code in the current text area"""
        # Get the current tab
        current_tab = self.notebook.GetCurrentPage()
        if current_tab:
            # Get the text area from the current tab
            text_area = current_tab.GetChildren()[0]
            code = text_area.GetValue()

            # Start measuring time
            start_time = time.time()

            self.monitoring = True
            self.memory_usage = 0  # Reset memory usage
            self.memory_thread = threading.Thread(target=self.track_memory_usage, daemon=True)
            self.memory_thread.start()


            # Execute the code using Popen
            self.process = subprocess.Popen(
                ['python', '-c', code],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            end_time = time.time()
            overall_time = end_time - start_time

            # Start a thread to handle output and execution time
            threading.Thread(target=self.HandleExecution, args=(overall_time,), daemon=True).start()

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
            pywinstyles.apply_style(self.output_window, "win7")

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
        output_message = f"Errors:\n{stderr}\n"
        output_message += f"Execution Time: {execution_time:.4f} milliseconds\n"
        output_message += f"Memory Usage: {self.memory_usage:.2f} MB\n"

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
                <title>Execution Log</title>
                <style>
                    body {{
                        background-color: #1f2937;
                        color: #ffffff; /* White text color */
                        font-family: 'Arial', sans-serif;
                        margin: 20px;
                    }}
                    h1 {{
                        color: #f472b6; /* Pink color for headings */
                        font-size: 2rem;
                        margin-bottom: 1rem;
                    }}
                    h2 {{
                        color: #e5e7eb; /* Gray color for subheadings */
                        font-size: 1.5rem;
                        margin-top: 2rem;
                    }}
                    pre {{
                        background-color: #374151; /* Dark gray background for preformatted text */
                        padding: 10px;
                        border-radius: 5px;
                        overflow-x: auto; /* Allow horizontal scrolling */
                        white-space: pre-wrap; /* Wrap long lines */
                    }}
                </style>
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
            text_area = current_tab.GetChildren()[0]  # The text area is the first child of the tab
            content = text_area.GetValue()
            file_name = self.notebook.GetPageText(self.notebook.GetSelection())

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
        self.SetStatusText("    Character pressed",2)
        self.SetStatusText("    Showing recomendations")
        current_tab = self.notebook.GetCurrentPage()
        if current_tab:
            text_area = current_tab.GetChildren()[0]
            key_code = event.GetKeyCode()
            try:
                # Auto-close brackets
                if chr(key_code) in self.matching_brackets:
                    pos = text_area.GetCurrentPos()
                    text_area.InsertText(pos, self.matching_brackets[chr(key_code)])
                    text_area.SetCurrentPos(pos)
                    text_area.SetSelection(pos, pos)

                key_code = event.GetKeyCode()
                if chr(key_code).isalpha() or key_code == ord('.'):
                    pos = text_area.GetCurrentPos()
                    word_start_pos = text_area.WordStartPosition(pos, True)
                    length = pos - word_start_pos

                    # Show autocomplete after 3 characters or when a dot is typed
                    if length >= 0 or key_code == ord('.'):
                        # List of completions
                        completions_list = [
                            "abs", "all", "any", "bin", "bool", "bytearray", "bytes", "chr", "classmethod",
                            "compile", "complex", "delattr", "dict", "dir", "divmod", "enumerate", "eval",
                            "exec", "filter", "float", "format", "frozenset", "getattr", "globals",
                            "hasattr", "hash", "help", "hex", "id", "input", "int", "isinstance", "issubclass",
                            "iter", "len", "list", "locals", "map", "max", "memoryview", "min", "next",
                            "object", "oct", "open", "ord", "pow", "print", "property", "range", "repr",
                            "reversed", "round", "set", "setattr", "slice", "sorted", "staticmethod", "str",
                            "sum", "super", "tuple", "type", "vars", "zip", "__name__"
                        ]

                        # Convert the list of completions into a space-separated string
                        completions = " ".join(completions_list)

                        text_area.AutoCompShow(0, completions)  # Show the autocomplete list
                        self.OnSave(wx.EVT_CHAR)
                        self.SetStatusText("    Autosaved", 2)
            except Exception as e:
                self.SetStatusText("    Error running onchar", 2)

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
