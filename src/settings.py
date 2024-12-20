import wx

class SettingsApp(wx.Frame):
    def __init__(self, *args, **kw):
        super(SettingsApp, self).__init__(*args, **kw)
        
        self.initUI()
        
    def initUI(self):
        panel = wx.Panel(self)
        
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # Theme setting
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        st1 = wx.StaticText(panel, label='Theme Value:')
        hbox1.Add(st1, flag=wx.RIGHT, border=8)
        self.theme_text = wx.TextCtrl(panel)
        hbox1.Add(self.theme_text, proportion=1)
        vbox.Add(hbox1, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)
        
        # Header Active setting
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        st2 = wx.StaticText(panel, label='Header Active Color:')
        hbox2.Add(st2, flag=wx.RIGHT, border=8)
        self.header_active_text = wx.TextCtrl(panel)
        hbox2.Add(self.header_active_text, proportion=1)
        vbox.Add(hbox2, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)
        
        # Header Inactive setting
        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        st3 = wx.StaticText(panel, label='Header Inactive Color:')
        hbox3.Add(st3, flag=wx.RIGHT, border=8)
        self.header_inactive_text = wx.TextCtrl(panel)
        hbox3.Add(self.header_inactive_text, proportion=1)
        vbox.Add(hbox3, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)
        
        # Save button
        hbox4 = wx.BoxSizer(wx.HORIZONTAL)
        btn_save = wx.Button(panel, label='Save', size=(70, 30))
        hbox4.Add(btn_save)
        vbox.Add(hbox4, flag=wx.ALIGN_RIGHT|wx.RIGHT|wx.BOTTOM, border=10)
        
        panel.SetSizer(vbox)
        
        # Load initial values
        self.load_settings()
        
        # Bind the save button to the save function
        btn_save.Bind(wx.EVT_BUTTON, self.on_save)
        
        self.SetSize((400, 250))
        self.SetTitle('Settings App')
        self.Centre()
        
    def load_settings(self):
        try:
            with open('theme.xcfg', 'r') as file:
                theme_value = file.read().strip()
                self.theme_text.SetValue(theme_value)
        except FileNotFoundError:
            self.theme_text.SetValue('')
        
        try:
            with open('xedix.xcfg', 'r') as file:
                lines = file.readlines()
                for line in lines:
                    if line.startswith('headerActive:'):
                        self.header_active_text.SetValue(line.split(':')[1].strip())
                    elif line.startswith('headerInactive:'):
                        self.header_inactive_text.SetValue(line.split(':')[1].strip())
        except FileNotFoundError:
            self.header_active_text.SetValue('')
            self.header_inactive_text.SetValue('')
    
    def on_save(self, event):
        theme_value = self.theme_text.GetValue().strip()
        header_active_color = self.header_active_text.GetValue().strip()
        header_inactive_color = self.header_inactive_text.GetValue().strip()
        
        with open('theme.xcfg', 'w') as file:
            file.write(theme_value)
        
        with open('xedix.xcfg', 'w') as file:
            file.write(f'headerActive:{header_active_color};\n')
            file.write(f'headerInactive:{header_inactive_color};\n')
        
        wx.MessageBox('Settings saved successfully', 'Info', wx.OK | wx.ICON_INFORMATION)
    
def main():
    app = wx.App()
    frame = SettingsApp(None)
    frame.Show()
    app.MainLoop()
