import wx

class UnavailableFeatureApp(wx.App):
    def OnInit(self):
        # Create a frame
        frame = wx.Frame(None, title="Feature Unavailable", size=(300, 150))
        
        # Create a panel
        panel = wx.Panel(frame)

        # Create a static text to display the message
        message = wx.StaticText(panel, label="This feature is currently not available.", pos=(20, 30))

        # Create a button to close the window
        close_button = wx.Button(panel, label="Close", pos=(100, 70))
        close_button.Bind(wx.EVT_BUTTON, self.on_close)

        frame.Show()
        return True

    def on_close(self, event):
        self.GetTopWindow().Close()

if __name__ == "__main__":
    app = UnavailableFeatureApp()
    app.MainLoop()
