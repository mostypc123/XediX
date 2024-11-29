import wx
import main


# Create the wx.App first
app = wx.App()

# Now create the TextEditor instance
editor = main.TextEditor(None)

filename = input(">>> Enter the filename:")

# Show the editor
editor.Show()

# Set the selected file in the file list
editor.file_list.SetStringSelection(filename)

# Create a custom event to simulate file opening
event = wx.CommandEvent(wx.EVT_LISTBOX_DCLICK.typeId)

# Call OnFileOpen with the event
editor.OnFileOpen(event)

# Start the main event loop
app.MainLoop()
