import wx
import subprocess
import main

def commit():
    try:
        # Create text entry dialog to get commit message
        with wx.TextEntryDialog(None, "Enter Commit Message", "Git Commit") as msg_dialog:
            if msg_dialog.ShowModal() == wx.ID_OK:
                msg = msg_dialog.GetValue().strip()
                
                # Validate commit message
                if not msg:
                    wx.MessageBox("Commit message cannot be empty", "Error", wx.OK | wx.ICON_ERROR)
                    return
                
                try:
                    # Use subprocess for safer command execution
                    subprocess.run(['git', 'add', '.'], check=True)
                    subprocess.run(['git', 'commit', '-m', msg], check=True)
                    wx.MessageBox("Commit successful!", "Success", wx.OK | wx.ICON_INFORMATION)
                
                except subprocess.CalledProcessError as e:
                    wx.MessageBox(f"Git commit failed: {e}", "Error", wx.OK | wx.ICON_ERROR)
                
    except Exception as e:
        wx.MessageBox(f"An error occurred: {e}", "Error", wx.OK | wx.ICON_ERROR)
