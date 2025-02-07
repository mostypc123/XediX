import wx
import os
import requests
from urllib.parse import urlparse

class GitHubExtensionDownloaderFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(GitHubExtensionDownloaderFrame, self).__init__(*args, **kwargs)
        panel = wx.Panel(self)

        # Create labels and input controls:
        github_repo_label = wx.StaticText(panel, label="GitHub Repo URL:")
        self.github_repo_text = wx.TextCtrl(panel)
        
        branch_label = wx.StaticText(panel, label="Branch Name:")
        self.branch_text = wx.TextCtrl(panel, value="main")
        
        ext_path_label = wx.StaticText(panel, label="Extension File Path in Repo:")
        self.ext_path_text = wx.TextCtrl(panel)
        
        local_repo_label = wx.StaticText(panel, label="Local Repository Directory:")
        self.local_repo_text = wx.TextCtrl(panel)
        local_repo_btn = wx.Button(panel, label="Browse Local Directory")
        
        type_label = wx.StaticText(panel, label="Select Extension Type:")
        self.radio = wx.RadioBox(panel,
                                 choices=["ext_mainfn", "mainclass", "menubar"],
                                 majorDimension=1,
                                 style=wx.RA_SPECIFY_COLS)
        
        download_append_btn = wx.Button(panel, label="Download and Append Extension Code")

        # Layout using sizers:
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(github_repo_label, 0, wx.ALL, 5)
        sizer.Add(self.github_repo_text, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(branch_label, 0, wx.ALL, 5)
        sizer.Add(self.branch_text, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(ext_path_label, 0, wx.ALL, 5)
        sizer.Add(self.ext_path_text, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(local_repo_label, 0, wx.ALL, 5)
        sizer.Add(self.local_repo_text, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(local_repo_btn, 0, wx.ALL, 5)
        sizer.Add(type_label, 0, wx.ALL, 5)
        sizer.Add(self.radio, 0, wx.ALL, 5)
        sizer.Add(download_append_btn, 0, wx.ALL, 5)
        panel.SetSizer(sizer)

        # Bind events:
        local_repo_btn.Bind(wx.EVT_BUTTON, self.onBrowseLocalRepo)
        download_append_btn.Bind(wx.EVT_BUTTON, self.onDownloadAndAppend)

        self.SetTitle("GitHub Extension Downloader and Appender")
        self.SetSize((500, 450))
        self.Centre()

    def onBrowseLocalRepo(self, event):
        """Open a directory dialog to choose the local repository directory."""
        dlg = wx.DirDialog(self, "Choose Local Repository Directory")
        if dlg.ShowModal() == wx.ID_OK:
            self.local_repo_text.SetValue(dlg.GetPath())
        dlg.Destroy()

    def onDownloadAndAppend(self, event):
        """Download the extension code from GitHub and append it to the target file."""
        github_url = self.github_repo_text.GetValue().strip()
        branch = self.branch_text.GetValue().strip() or "main"
        ext_path_in_repo = self.ext_path_text.GetValue().strip()
        local_repo = self.local_repo_text.GetValue().strip()
        ext_type = self.radio.GetStringSelection()

        # Validate local repository directory:
        if not os.path.isdir(local_repo):
            wx.MessageBox("Invalid local repository directory!", "Error", wx.OK | wx.ICON_ERROR)
            return

        # Parse GitHub URL:
        parsed_url = urlparse(github_url)
        path_parts = parsed_url.path.strip("/").split("/")
        if len(path_parts) < 2:
            wx.MessageBox("Invalid GitHub repository URL!", "Error", wx.OK | wx.ICON_ERROR)
            return
        owner, repo_name = path_parts[0], path_parts[1]

        # Construct the raw URL:
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo_name}/{branch}/{ext_path_in_repo}"
        
        try:
            response = requests.get(raw_url)
            if response.status_code != 200:
                wx.MessageBox(f"Failed to download file from GitHub.\nStatus code: {response.status_code}", "Error", wx.OK | wx.ICON_ERROR)
                return
            code = response.text
        except Exception as e:
            wx.MessageBox(f"Error fetching the file: {e}", "Error", wx.OK | wx.ICON_ERROR)
            return

        # Determine the target file based on the selected extension type:
        if ext_type == "ext_mainfn":
            target_filename = "extension_mainfn.py"
        elif ext_type == "mainclass":
            target_filename = "extension_mainclass.py"
        elif ext_type == "menubar":
            target_filename = "extension_menubar.py"
        else:
            wx.MessageBox("Unknown extension type selected!", "Error", wx.OK | wx.ICON_ERROR)
            return

        target_file_path = os.path.join(local_repo, target_filename)

        try:
            with open(target_file_path, 'a') as target_file:
                target_file.write("\n# Appended extension code from GitHub:\n")
                target_file.write(code)
            wx.MessageBox("Extension code appended successfully!", "Success", wx.OK | wx.ICON_INFORMATION)
        except Exception as e:
            wx.MessageBox(f"Error appending to target file: {e}", "Error", wx.OK | wx.ICON_ERROR)

if __name__ == '__main__':
    app = wx.App(False)
    frame = GitHubExtensionDownloaderFrame(None)
    frame.Show()
    app.MainLoop()

