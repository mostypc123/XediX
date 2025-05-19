import wx
import pyperclip
import pywinstyles

# List of symbols to display in the GUI
symbols = [
    "!",
    '"',
    "#",
    "$",
    "%",
    "&",
    "'",
    "(",
    ")",
    "*",
    "+",
    ",",
    "-",
    ".",
    "/",
    ":",
    ";",
    "<",
    "=",
    ">",
    "?",
    "@",
    "[",
    "\\",
    "]",
    "^",
    "_",
    "`",
    "{",
    "|",
    "}",
    "~",
    "¢",
    "£",
    "¥",
    "€",
    "©",
    "®",
    "™",
    "§",
    "¶",
    "•",
    "†",
    "‡",
    "°",
    "‰",
    "∞",
    "√",
    "≈",
    "≠",
    "≤",
    "≥",
    "±",
    "÷",
    "×",
    "∑",
    "∏",
    "∫",
    "∆",
    "Ω",
    "λ",
    "π",
    "µ",
    "∂",
    "↔",
    "←",
    "↑",
    "→",
    "↓",
    "↩",
    "⇧",
    "⌘",
    "♠",
    "♣",
    "♥",
    "♦",
    "☺",
    "☹",
    "♀",
    "♂",
    "⚛",
    "✈",
    "☎",
    "✉",
    "✓",
    "✔",
    "✖",
    "★",
    "☆",
    "♩",
    "♪",
    "♫",
    "♬",
]


class SymbolCopyApp(wx.Frame):
    def __init__(self, *args, **kw):
        super(SymbolCopyApp, self).__init__(*args, **kw)
        pywinstyles.apply_style(self, "win7")

        self.InitUI()

    def InitUI(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        instructions = wx.StaticText(
            panel, label="Click a symbol to copy it to clipboard"
        )
        vbox.Add(instructions, flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=10)

        # Create a grid to display symbols with only columns defined
        grid_sizer = wx.GridSizer(cols=10, hgap=10, vgap=10)

        for symbol in symbols:
            button = wx.Button(panel, label=symbol, size=(50, 40))
            button.Bind(wx.EVT_BUTTON, self.OnCopyToClipboard)
            grid_sizer.Add(button, 0, wx.EXPAND)

        vbox.Add(grid_sizer, proportion=1, flag=wx.ALL | wx.EXPAND, border=10)
        panel.SetSizer(vbox)

        self.SetSize((500, 400))
        self.SetTitle("Symbol Copier")
        self.Centre()

    def OnCopyToClipboard(self, event):
        button = event.GetEventObject()
        symbol = button.GetLabel()
        pyperclip.copy(symbol)  # Copy symbol to clipboard
        wx.MessageBox(
            f"Copied '{symbol}' to clipboard!", "Copied", wx.OK | wx.ICON_INFORMATION
        )


def main():
    app = wx.App()
    frame = SymbolCopyApp(None)
    frame.Show()
    app.MainLoop()


if __name__ == "__main__":
    main()
