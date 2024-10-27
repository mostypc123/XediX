import wx
import subprocess

class Tool:
    def __init__(self, name, command):
        self.name = name
        self.command = command

class ToolRunnerApp(wx.Frame):
    def __init__(self, parent, title):
        super(ToolRunnerApp, self).__init__(parent, title=title, size=(400, 300))
        
        # Define tools with the filenames to execute
        self.tools = [
            Tool("Markdown Preview & JSON Visualization", "python tools/md_preview.py"),
            Tool("Install Extensions", "python tools/extensions.py"),
        ]

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # ListBox to display tools
        self.tool_list = wx.ListBox(panel, choices=[tool.name for tool in self.tools])
        vbox.Add(self.tool_list, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)

        # Run Button
        self.run_button = wx.Button(panel, label="Run Tool")
        self.run_button.Bind(wx.EVT_BUTTON, self.on_run_tool)
        vbox.Add(self.run_button, flag=wx.ALIGN_CENTER | wx.BOTTOM, border=10)

        panel.SetSizer(vbox)
        self.Centre()

    def on_run_tool(self, event):
        # Get selected tool
        selection = self.tool_list.GetSelection()
        if selection != wx.NOT_FOUND:
            tool = self.tools[selection]
            try:
                # Run the tool command
                subprocess.Popen(tool.command, shell=True)
                wx.MessageBox(f"Running {tool.name}...", "Info", wx.OK | wx.ICON_INFORMATION)
            except Exception as e:
                wx.MessageBox(f"Failed to run {tool.name}: {e}", "Error", wx.OK | wx.ICON_ERROR)
        else:
            wx.MessageBox("Please select a tool to run.", "Error", wx.OK | wx.ICON_ERROR)

if __name__ == "__main__":
    app = wx.App()
    frame = ToolRunnerApp(None, "Tool Runner")
    frame.Show()
    app.MainLoop()
