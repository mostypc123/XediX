import wx
import wx.html  # For displaying HTML content
import markdown
import json
import matplotlib.pyplot as plt
import pywinstyles

"""
I know that this is not called XediX, and it is
a separate preview app, but this is a beta feature
and it is still not perfect, I wanted to add it
embedded in XediX.
"""

class XediX(wx.Frame):
    def __init__(self, *args, **kw):
        super(XediX, self).__init__(*args, **kw)
        pywinstyles.apply_style(self, "win7")

        self.SetTitle("Preview")
        self.SetSize(800, 600)

        # Create the text control for editing
        self.text_ctrl = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_RICH2)
        
        # Create the menu
        self.menu_bar = wx.MenuBar()
        self.file_menu = wx.Menu()
        self.preview_markdown_menu_item = self.file_menu.Append(wx.ID_ANY, 'Preview Markdown')
        self.visualize_json_menu_item = self.file_menu.Append(wx.ID_ANY, 'Visualize JSON Diagram')
        self.Bind(wx.EVT_MENU, self.on_preview_markdown, self.preview_markdown_menu_item)
        self.Bind(wx.EVT_MENU, self.on_visualize_json_diagram, self.visualize_json_menu_item)

        self.menu_bar.Append(self.file_menu, '&Preview')
        self.SetMenuBar(self.menu_bar)

        # Set the main sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.text_ctrl, 1, wx.EXPAND | wx.ALL, 10)
        self.SetSizer(main_sizer)

        # Show the frame
        self.Show()

    def on_preview_markdown(self, event):
        # Get the content from the text control
        markdown_text = self.text_ctrl.GetValue()
        
        # Convert Markdown to HTML
        html_text = markdown.markdown(markdown_text)

        # Create a new dialog to show the preview
        preview_dialog = wx.Dialog(self, title="Markdown Preview")
        preview_sizer = wx.BoxSizer(wx.VERTICAL)

        # Use a wx.html.HtmlWindow to display the HTML
        html_window = wx.html.HtmlWindow(preview_dialog)
        html_window.SetPage(html_text)

        preview_sizer.Add(html_window, 1, wx.EXPAND | wx.ALL, 10)
        preview_dialog.SetSizer(preview_sizer)
        preview_dialog.SetSize(600, 400)
        preview_dialog.ShowModal()
        preview_dialog.Destroy()

    def on_visualize_json_diagram(self, event):
        # Get the content from the text control
        json_text = self.text_ctrl.GetValue()

        try:
            # Parse JSON
            parsed_json = json.loads(json_text)
        except json.JSONDecodeError as e:
            wx.MessageBox(f"Invalid JSON: {e}", "Error", wx.OK | wx.ICON_ERROR)
            return

        # Create a tree diagram from the JSON
        plt.figure(figsize=(10, 6))
        self.draw_json_tree(parsed_json, 0, 0)

        # Show the plot
        plt.title('JSON Structure')
        plt.axis('off')  # Turn off the axis
        plt.show()

    def draw_json_tree(self, data, x, y):
        """Recursively draws the JSON tree."""
        if isinstance(data, dict):
            # Draw dictionary nodes
            for i, (key, value) in enumerate(data.items()):
                plt.text(x, y, key, ha='center', va='center', bbox=dict(boxstyle="round,pad=0.3", edgecolor='black', facecolor='lightgray'))
                if isinstance(value, (dict, list)):
                    new_x = x - 1 + (i * 2) / len(data)  # Calculate x position for children
                    new_y = y - 1  # Decrease y for the next level
                    plt.plot([x, new_x], [y, new_y], color='black')  # Draw line to child
                    self.draw_json_tree(value, new_x, new_y)  # Recursively draw child
                else:
                    plt.text(x, y - 1, str(value), ha='center', va='center', bbox=dict(boxstyle="round,pad=0.3", edgecolor='black', facecolor='lightyellow'))
                    plt.plot([x, x], [y, y - 1], color='black')  # Draw line to value
        elif isinstance(data, list):
            # Draw list nodes
            for i, item in enumerate(data):
                new_x = x - 1 + (i * 2) / len(data)  # Calculate x position for children
                new_y = y - 1  # Decrease y for the next level
                plt.text(new_x, new_y, f'Item {i}', ha='center', va='center', bbox=dict(boxstyle="round,pad=0.3", edgecolor='black', facecolor='lightblue'))
                plt.plot([x, new_x], [y, new_y], color='black')  # Draw line to item
                self.draw_json_tree(item, new_x, new_y)  # Recursively draw item

# Initialize the app and start
if __name__ == '__main__':
    app = wx.App(False)
    frame = XediX(None)
    app.MainLoop()
