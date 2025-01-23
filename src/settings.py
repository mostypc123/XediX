import wx
import wx.adv

class SettingsApp(wx.Frame):
    def __init__(self, *args, **kw):
        super(SettingsApp, self).__init__(*args, **kw)
        
        self.themes = ['dark', 'night', 'light', 'obsidian', 'github-dark', 'github-light', 
                      'github-dimmed', 'solarized-light', 'solarized-dark']
        self.initUI()
        
    def initUI(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # Theme setting
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        st1 = wx.StaticText(panel, label='Theme:')
        hbox1.Add(st1, flag=wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, border=8)
        self.theme_choice = wx.Choice(panel, choices=self.themes)
        hbox1.Add(self.theme_choice, proportion=1)
        vbox.Add(hbox1, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)
        
        # Header Active setting
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        st2 = wx.StaticText(panel, label='Header Active Color:')
        hbox2.Add(st2, flag=wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, border=8)
        self.header_active_text = wx.TextCtrl(panel)
        hbox2.Add(self.header_active_text, proportion=1)
        self.header_active_btn = wx.Button(panel, label='Choose Color', size=(100, -1))
        hbox2.Add(self.header_active_btn, flag=wx.LEFT, border=5)
        vbox.Add(hbox2, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)
        
        # Header Inactive setting
        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        st3 = wx.StaticText(panel, label='Header Inactive Color:')
        hbox3.Add(st3, flag=wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, border=8)
        self.header_inactive_text = wx.TextCtrl(panel)
        hbox3.Add(self.header_inactive_text, proportion=1)
        self.header_inactive_btn = wx.Button(panel, label='Choose Color', size=(100, -1))
        hbox3.Add(self.header_inactive_btn, flag=wx.LEFT, border=5)
        vbox.Add(hbox3, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)

        # Discord Presence setting
        hbox4 = wx.BoxSizer(wx.HORIZONTAL)
        st4 = wx.StaticText(panel, label='Use Discord Presence:')
        hbox4.Add(st4, flag=wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, border=8)
        self.discord_checkbox = wx.CheckBox(panel)
        hbox4.Add(self.discord_checkbox)
        vbox.Add(hbox4, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)
        
        # Save button
        hbox5 = wx.BoxSizer(wx.HORIZONTAL)
        btn_save = wx.Button(panel, label='Save', size=(70, 30))
        hbox5.Add(btn_save)
        vbox.Add(hbox5, flag=wx.ALIGN_RIGHT|wx.RIGHT|wx.BOTTOM, border=10)
        
        panel.SetSizer(vbox)
        
        self.load_settings()
        
        btn_save.Bind(wx.EVT_BUTTON, self.on_save)
        self.header_active_btn.Bind(wx.EVT_BUTTON, self.on_active_color)
        self.header_inactive_btn.Bind(wx.EVT_BUTTON, self.on_inactive_color)
        
        self.SetSize((500, 280))
        self.SetTitle('Settings App')
        self.Centre()
        
    def load_settings(self):
        try:
            with open('theme.xcfg', 'r') as file:
                theme_value = file.read().strip()
                if theme_value in self.themes:
                    self.theme_choice.SetSelection(self.themes.index(theme_value))
        except FileNotFoundError:
            self.theme_choice.SetSelection(0)
        
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

        try:
            with open('discord.xcfg', 'r') as file:
                use_discord = file.read().strip()
                self.discord_checkbox.SetValue(use_discord.lower() == 'true')
        except FileNotFoundError:
            self.discord_checkbox.SetValue(True)
    
    def on_active_color(self, event):
        color_dialog = wx.ColourDialog(self)
        if color_dialog.ShowModal() == wx.ID_OK:
            color = color_dialog.GetColourData().GetColour()
            hex_color = '#{:02x}{:02x}{:02x}'.format(color.Red(), color.Green(), color.Blue())
            self.header_active_text.SetValue(hex_color)
        color_dialog.Destroy()
        
    def on_inactive_color(self, event):
        color_dialog = wx.ColourDialog(self)
        if color_dialog.ShowModal() == wx.ID_OK:
            color = color_dialog.GetColourData().GetColour()
            hex_color = '#{:02x}{:02x}{:02x}'.format(color.Red(), color.Green(), color.Blue())
            self.header_inactive_text.SetValue(hex_color)
        color_dialog.Destroy()
    
    def on_save(self, event):
        theme_value = self.themes[self.theme_choice.GetSelection()]
        header_active_color = self.header_active_text.GetValue().strip()
        header_inactive_color = self.header_inactive_text.GetValue().strip()
        
        with open('theme.xcfg', 'w') as file:
            file.write(theme_value)
        
        with open('xedix.xcfg', 'w') as file:
            file.write(f'headerActive:{header_active_color};\n')
            file.write(f'headerInactive:{header_inactive_color};\n')

        with open('discord.xcfg', 'w') as file:
            file.write(str(self.discord_checkbox.GetValue()))
        
        wx.MessageBox('Settings saved successfully', 'Info', wx.OK | wx.ICON_INFORMATION)
    
def main():
    app = wx.App()
    frame = SettingsApp(None)
    frame.Show()
    app.MainLoop()