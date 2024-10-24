import wx
import wx.stc as stc
import os
import subprocess
import time
import threading
import pywinstyles


class TextEditor(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(TextEditor, self).__init__(*args, **kwargs)
        pywinstyles.apply_style(self, "win7")
        self.output_window = None
        self.InitUI()

    def InitUI(self):
        panel = wx.Panel(self)
        splitter = wx.SplitterWindow(panel)

        self.sidebar = wx.Panel(splitter)

        # Add New File button
        new_file_btn = wx.Button(self.sidebar, label="New File")
        new_file_btn.Bind(wx.EVT_BUTTON, self.OnNewFile)

        self.file_list = wx.ListBox(self.sidebar)
        self.PopulateFileList()

        self.main_panel = wx.Panel(splitter)
        self.default_message = wx.StaticText(self.main_panel, label="Open a file first", style=wx.ALIGN_CENTER)
        font = self.default_message.GetFont()
        font.PointSize += 4
        self.default_message.SetFont(font)

        main_vbox = wx.BoxSizer(wx.VERTICAL)
        main_vbox.AddStretchSpacer(1)
        main_vbox.Add(self.default_message, proportion=0, flag=wx.ALIGN_CENTER)
        main_vbox.AddStretchSpacer(1)
        self.main_panel.SetSizer(main_vbox)

        self.notebook = wx.Notebook(splitter)
        self.notebook.Hide()

        sidebar_vbox = wx.BoxSizer(wx.VERTICAL)

        # Add the New File button and file list to the sidebar layout
        sidebar_vbox.Add(new_file_btn, proportion=0, flag=wx.EXPAND | wx.ALL, border=5)
        sidebar_vbox.Add(self.file_list, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        self.sidebar.SetSizer(sidebar_vbox)

        splitter.SplitVertically(self.sidebar, self.main_panel)
        splitter.SetMinimumPaneSize(150)

        self.CreateMenuBar()
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(splitter, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        panel.SetSizer(vbox)

        self.SetTitle("XediX")
        self.SetSize((800, 600))
        self.Centre()

        self.file_list.Bind(wx.EVT_LISTBOX_DCLICK, self.OnFileOpen)

    def CreateMenuBar(self):
        menubar = wx.MenuBar()

        fileMenu = wx.Menu()
        save_item = fileMenu.Append(wx.ID_SAVE, '&Save\tCtrl+S', 'Save the file')
        run_item = fileMenu.Append(wx.ID_ANY, '&Run Code\tCtrl+R', 'Run the code')
        fileMenu.AppendSeparator()
        pylint_item = fileMenu.Append(wx.ID_ANY, '&Run pylint\tCtrl+P', 'Run pylint on code')
        exit_item = fileMenu.Append(wx.ID_EXIT, '&Exit\tCtrl+Q', 'Exit application')

        editMenu = wx.Menu()
        cut_item = editMenu.Append(wx.ID_CUT, '&Cut\tCtrl+X', 'Cut selection')
        copy_item = editMenu.Append(wx.ID_COPY, '&Copy\tCtrl+C', 'Copy selection')
        paste_item = editMenu.Append(wx.ID_PASTE, '&Paste\tCtrl+V', 'Paste from clipboard')
        find_replace_item = editMenu.Append(wx.ID_FIND, '&Find and Replace\tCtrl+F', 'Find and replace text')

        menubar.Append(fileMenu, '&File')
        menubar.Append(editMenu, '&Edit')
        self.SetMenuBar(menubar)

        self.Bind(wx.EVT_MENU, self.OnSave, save_item)
        self.Bind(wx.EVT_MENU, self.OnRunCode, run_item)
        self.Bind(wx.EVT_MENU, self.OnExit, exit_item)
        self.Bind(wx.EVT_MENU, self.OnCut, cut_item)
        self.Bind(wx.EVT_MENU, self.OnCopy, copy_item)
        self.Bind(wx.EVT_MENU, self.OnPaste, paste_item)
        self.Bind(wx.EVT_MENU, self.OnRunPylint, pylint_item)
        self.Bind(wx.EVT_MENU, self.OnFindReplace, find_replace_item)

    def OnRunPylint(self, event):
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
        find_replace_dialog = wx.TextEntryDialog(self, "Find text:")
        if find_replace_dialog.ShowModal() == wx.ID_OK:
            find_text = find_replace_dialog.GetValue()
            replace_dialog = wx.TextEntryDialog(self, "Replace with:")
            if replace_dialog.ShowModal() == wx.ID_OK:
                replace_text = replace_dialog.GetValue()
                current_tab = self.notebook.GetCurrentPage()
                if current_tab:
                    text_area = current_tab.GetChildren()[0]
                    content = text_area.GetValue()
                    new_content = content.replace(find_text, replace_text)
                    text_area.SetText(new_content)


    def PopulateFileList(self):
        current_dir = os.getcwd()
        files = [f for f in os.listdir(current_dir) if os.path.isfile(os.path.join(current_dir, f))]
        self.file_list.AppendItems(files)

    def OnChar(self, event):
        current_tab = self.notebook.GetCurrentPage()
        if current_tab:
            text_area = current_tab.GetChildren()[0]

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

        event.Skip()  # Continue processing other key events

    def OnFileOpen(self, event):
        file_name = self.file_list.GetStringSelection()
        if file_name:
            file_path = os.path.join(os.getcwd(), file_name)
            with open(file_path, 'r') as file:
                content = file.read()

            if not self.notebook.IsShown():
                self.default_message.Hide()
                self.main_panel.Hide()
                splitter = self.main_panel.GetParent()
                splitter.ReplaceWindow(self.main_panel, self.notebook)
                self.notebook.Show()

            tab = wx.Panel(self.notebook)
            text_area = stc.StyledTextCtrl(tab, style=wx.TE_MULTILINE)
            text_area.SetText(content)

            # Bind a key event to trigger autocomplete after typing
            text_area.Bind(wx.EVT_CHAR, self.OnChar)
            # Set dark background and light text for the entire control
            dark_bg_color = "#1E1E1E"
            light_text_color = "#FFFFFF"
            text_area.StyleSetBackground(stc.STC_STYLE_DEFAULT, dark_bg_color)
            text_area.StyleSetForeground(stc.STC_STYLE_DEFAULT, light_text_color)
            text_area.StyleClearAll()  # Apply the default style to all text

            # Set up Python syntax highlighting
            text_area.SetLexer(stc.STC_LEX_PYTHON)

            # Default style
            text_area.StyleSetSpec(stc.STC_P_DEFAULT, f"fore:{light_text_color},italic,back:{dark_bg_color}")

            # Comments
            text_area.StyleSetSpec(stc.STC_P_COMMENTLINE, "fore:#68C147,italic,back:#1E1E1E")

            # Strings
            text_area.StyleSetSpec(stc.STC_P_STRING, "fore:#BA9EFE,italic,back:#1E1E1E")

            # Keywords
            text_area.StyleSetSpec(stc.STC_P_WORD, "fore:#569CD6,bold,back:#1E1E1E")
            text_area.SetKeyWords(0,
                                  "def class return if else elif import from as not is try except finally for while in with pass lambda")

            # Functions and variables
            text_area.StyleSetSpec(stc.STC_P_IDENTIFIER, "fore:#7BCCE1,italic,back:#1E1E1E")

            # Operators
            text_area.StyleSetSpec(stc.STC_P_OPERATOR, "fore:#D4D4D4,bold,back:#1E1E1E")

            # Numbers
            text_area.StyleSetSpec(stc.STC_P_NUMBER, "fore:#FFDD54,italic,back:#1E1E1E")

            # Decorators
            text_area.StyleSetSpec(stc.STC_P_DECORATOR, "fore:#C586C0,italic,back:#1E1E1E")

            # Adjust indentation guides
            text_area.SetIndentationGuides(True)
            text_area.StyleSetSpec(stc.STC_STYLE_LINENUMBER, "fore:#858585,italic,back:#1E1E1E")
            text_area.SetMarginType(1, stc.STC_MARGIN_NUMBER)
            text_area.SetMarginWidth(1, 40)

            # Ensure code folding is enabled
            text_area.SetProperty("fold", "1")
            text_area.SetMarginType(2, stc.STC_MARGIN_SYMBOL)
            text_area.SetMarginMask(2, stc.STC_MASK_FOLDERS)
            text_area.SetMarginSensitive(2, True)
            text_area.SetMarginWidth(2, 16)

            # Set fold marker colors
            text_area.MarkerDefine(stc.STC_MARKNUM_FOLDEROPEN, stc.STC_MARK_MINUS, "#FFFFFF", "#1E1E1E")
            text_area.MarkerDefine(stc.STC_MARKNUM_FOLDER, stc.STC_MARK_PLUS, "#FFFFFF", "#1E1E1E")

            tab_sizer = wx.BoxSizer(wx.VERTICAL)
            tab_sizer.Add(text_area, proportion=1, flag=wx.EXPAND)
            tab.SetSizer(tab_sizer)

            self.notebook.AddPage(tab, file_name)

    def OnNewFile(self, event):
        # Create an empty file name and open it
        temp_file_path = os.path.join(os.getcwd(), "Untitled.py")

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

    def ApplyTextAreaDarkMode(self, text_area):
        dark_bg_color = wx.Colour(30, 30, 30)
        text_color = wx.Colour(255, 255, 255)
        text_area.SetBackgroundColour(dark_bg_color)
        text_area.SetForegroundColour(text_color)

    def OnRunCode(self, event):
        current_tab = self.notebook.GetCurrentPage()
        if current_tab:
            text_area = current_tab.GetChildren()[0]
            code = text_area.GetValue()

            # Start measuring time
            start_time = time.time()

            # Execute the code using Popen
            self.process = subprocess.Popen(
                ['python', '-c', code],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Start a thread to handle output and execution time
            threading.Thread(target=self.HandleExecution, args=(start_time,), daemon=True).start()

    def HandleExecution(self, start_time):
        stdout, stderr = self.process.communicate()
        end_time = time.time()
        execution_time = end_time - start_time

        # Create output dialog if it doesn't exist
        if self.output_window is None:
            self.output_window = wx.Dialog(self, title="Output Window", size=(600, 400))
            pywinstyles.apply_style(self.output_window, "win7")
            output_panel = wx.Panel(self.output_window)
            output_vbox = wx.BoxSizer(wx.VERTICAL)

            self.output_text = wx.TextCtrl(output_panel, style=wx.TE_MULTILINE | wx.TE_READONLY)

            output_vbox.Add(self.output_text, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
            output_panel.SetSizer(output_vbox)

        # Prepare output message with execution time
        output_message = f"{stdout}\nErrors:\n{stderr}\n"
        output_message += f"Execution Time: {execution_time:.4f} seconds\n"

        self.output_text.SetValue(output_message)
        self.output_window.ShowModal()  # Show the output dialog modally

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

    def OnExit(self, event):
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


def main():
    app = wx.App(False)
    frame = TextEditor(None)
    frame.Show()
    app.MainLoop()


if __name__ == '__main__':
    main()
