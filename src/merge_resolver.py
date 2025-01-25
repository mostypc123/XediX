import wx
import os
import subprocess
from wx import stc

class MergeResolver(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="Merge Conflict Resolver", size=(800, 600))
        
        self.panel = wx.Panel(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        
        # File selection
        file_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.file_picker = wx.FilePickerCtrl(self.panel)
        file_sizer.Add(wx.StaticText(self.panel, label="Select file:"), 0, wx.ALL, 5)
        file_sizer.Add(self.file_picker, 1, wx.EXPAND|wx.ALL, 5)
        self.sizer.Add(file_sizer, 0, wx.EXPAND)
        
        # Split view for conflict resolution
        self.splitter = wx.SplitterWindow(self.panel)
        
        # Current changes panel
        current_panel = wx.Panel(self.splitter)
        current_sizer = wx.BoxSizer(wx.VERTICAL)
        current_sizer.Add(wx.StaticText(current_panel, label="Current Changes"), 0, wx.ALL, 5)
        self.current_editor = stc.StyledTextCtrl(current_panel)
        current_sizer.Add(self.current_editor, 1, wx.EXPAND)
        current_panel.SetSizer(current_sizer)
        
        # Incoming changes panel
        incoming_panel = wx.Panel(self.splitter)
        incoming_sizer = wx.BoxSizer(wx.VERTICAL)
        incoming_sizer.Add(wx.StaticText(incoming_panel, label="Incoming Changes"), 0, wx.ALL, 5)
        self.incoming_editor = stc.StyledTextCtrl(incoming_panel)
        incoming_sizer.Add(self.incoming_editor, 1, wx.EXPAND)
        incoming_panel.SetSizer(incoming_sizer)
        
        self.splitter.SplitHorizontally(current_panel, incoming_panel)
        self.sizer.Add(self.splitter, 1, wx.EXPAND)
        
        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.accept_current = wx.Button(self.panel, label="Accept Current")
        self.accept_incoming = wx.Button(self.panel, label="Accept Incoming")
        self.custom_resolve = wx.Button(self.panel, label="Custom Resolve")
        
        btn_sizer.Add(self.accept_current, 0, wx.ALL, 5)
        btn_sizer.Add(self.accept_incoming, 0, wx.ALL, 5)
        btn_sizer.Add(self.custom_resolve, 0, wx.ALL, 5)
        
        self.sizer.Add(btn_sizer, 0, wx.CENTER)
        
        self.panel.SetSizer(self.sizer)
        
        # Bind events
        self.file_picker.Bind(wx.EVT_FILEPICKER_CHANGED, self.on_file_selected)
        self.accept_current.Bind(wx.EVT_BUTTON, self.on_accept_current)
        self.accept_incoming.Bind(wx.EVT_BUTTON, self.on_accept_incoming)
        self.custom_resolve.Bind(wx.EVT_BUTTON, self.on_custom_resolve)
        
        # Style editors
        self._setup_editors()
        
    def _setup_editors(self):
        """Configure the styled text controls"""
        for editor in [self.current_editor, self.incoming_editor]:
            editor.SetLexer(stc.STC_LEX_NULL)
            editor.StyleSetBackground(stc.STC_STYLE_DEFAULT, "#FFFFFF")
            editor.StyleSetForeground(stc.STC_STYLE_DEFAULT, "#000000")
            editor.StyleClearAll()
            editor.SetMarginType(1, stc.STC_MARGIN_NUMBER)
            editor.SetMarginWidth(1, 30)
    
    def on_file_selected(self, event):
        file_path = self.file_picker.GetPath()
        if not file_path:
            return
            
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Parse conflict markers
            current_changes = []
            incoming_changes = []
            in_conflict = False
            current_section = None
            
            for line in content.split('\n'):
                if line.startswith('<<<<<<<'):
                    in_conflict = True
                    current_section = current_changes
                elif line.startswith('=======') and in_conflict:
                    current_section = incoming_changes
                elif line.startswith('>>>>>>>'):
                    in_conflict = False
                    current_section = None
                elif current_section is not None:
                    current_section.append(line)
            
            self.current_editor.SetText('\n'.join(current_changes))
            self.incoming_editor.SetText('\n'.join(incoming_changes))
            
        except Exception as e:
            wx.MessageBox(f"Error loading file: {str(e)}", "Error")
            
    def on_accept_current(self, event):
        self._resolve_conflict(use_current=True)
        
    def on_accept_incoming(self, event):
        self._resolve_conflict(use_current=False)
        
    def on_custom_resolve(self, event):
        custom_dialog = CustomResolveDialog(self, 
                                          self.current_editor.GetText(),
                                          self.incoming_editor.GetText())
        if custom_dialog.ShowModal() == wx.ID_OK:
            resolved_text = custom_dialog.get_resolved_text()
            self._write_resolution(resolved_text)
        custom_dialog.Destroy()
        
    def _resolve_conflict(self, use_current):
        text = self.current_editor.GetText() if use_current else self.incoming_editor.GetText()
        self._write_resolution(text)
        
    def _write_resolution(self, text):
        file_path = self.file_picker.GetPath()
        if not file_path:
            return
            
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Replace conflict section with resolved text
            start_marker = '<<<<<<<'
            end_marker = '>>>>>>>'
            start_pos = content.find(start_marker)
            end_pos = content.find(end_marker) + len(end_marker)
            
            if start_pos != -1 and end_pos != -1:
                resolved_content = content[:start_pos] + text + content[end_pos:]
                
                with open(file_path, 'w') as f:
                    f.write(resolved_content)
                    
                wx.MessageBox("Conflict resolved successfully!", "Success")
                
        except Exception as e:
            wx.MessageBox(f"Error resolving conflict: {str(e)}", "Error")

class CustomResolveDialog(wx.Dialog):
    def __init__(self, parent, current_text, incoming_text):
        super().__init__(parent, title="Custom Resolve", size=(600, 400))
        
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.editor = stc.StyledTextCtrl(panel)
        self.editor.SetText(f"# Combine the changes as needed:\n\n# Current changes:\n{current_text}\n\n# Incoming changes:\n{incoming_text}")
        
        sizer.Add(self.editor, 1, wx.EXPAND|wx.ALL, 5)
        
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_btn = wx.Button(panel, wx.ID_OK, "Apply Resolution")
        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        
        btn_sizer.Add(ok_btn, 0, wx.ALL, 5)
        btn_sizer.Add(cancel_btn, 0, wx.ALL, 5)
        sizer.Add(btn_sizer, 0, wx.CENTER)
        
        panel.SetSizer(sizer)
        
    def get_resolved_text(self):
        return self.editor.GetText()

def main(parent=None):
    dialog = MergeResolver(parent)
    dialog.ShowModal()
    dialog.Destroy()