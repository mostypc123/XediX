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

def add():
    try:
        # Use subprocess for safer command execution
        subprocess.run(['git', 'add', '.'], check=True)
        wx.MessageBox("Files added successfully!", "Success", wx.OK | wx.ICON_INFORMATION)
    
    except subprocess.CalledProcessError as e:
        wx.MessageBox(f"Git add failed: {e}", "Error", wx.OK | wx.ICON_ERROR)
    
    except Exception as e:
        wx.MessageBox(f"An error occurred: {e}", "Error", wx.OK | wx.ICON_ERROR)

def push():
    try:
        # Use subprocess for safer command execution
        subprocess.run(['git', 'push'], check=True)
        wx.MessageBox("Push successful!", "Success", wx.OK | wx.ICON_INFORMATION)

    except subprocess.CalledProcessError as e:
        wx.MessageBox(f"Git push failed: {e}", "Error", wx.OK | wx.ICON_ERROR)

    except Exception as e:
        wx.MessageBox(f"An error occurred: {e}", "Error", wx.OK | wx.ICON_ERROR)

def pull():
    try:
        # Use subprocess for safer command execution
        subprocess.run(['git', 'pull'], check=True)
        wx.MessageBox("Pull successful!", "Success", wx.OK | wx.ICON_INFORMATION)

    except subprocess.CalledProcessError as e:
        wx.MessageBox(f"Git pull failed: {e}", "Error", wx.OK | wx.ICON_ERROR)
    
    except Exception as e:
        wx.MessageBox(f"An error occurred: {e}", "Error", wx.OK | wx.ICON_ERROR)

def version():
    try:
        # Use subprocess for safer command execution
        version = subprocess.run(['git', '--version'], capture_output=True, text=True, check=True)
        wx.MessageBox(f"Git version: {version.stdout}", "Git Version", wx.OK | wx.ICON_INFORMATION)

    except subprocess.CalledProcessError as e:
        wx.MessageBox(f"Git version failed: {e}", "Error", wx.OK | wx.ICON_ERROR)

    except Exception as e:
        wx.MessageBox(f"An error occurred: {e}", "Error", wx.OK | wx.ICON_ERROR)

def status():
    try:
        # Use subprocess for safer command execution
        status = subprocess.run(['git', 'status'], capture_output=True, text=True, check=True)
        wx.MessageBox(f"Git status:\n{status.stdout}", "Git Status", wx.OK | wx.ICON_INFORMATION)
    
    except subprocess.CalledProcessError as e:
        wx.MessageBox(f"Git status failed: {e}", "Error", wx.OK | wx.ICON_ERROR)
    
    except Exception as e:
        wx.MessageBox(f"An error occurred: {e}", "Error", wx.OK | wx.ICON_ERROR)

def branch():
    try:
        # Use subprocess for safer command execution
        branch = subprocess.run(['git', 'branch'], capture_output=True, text=True, check=True)
        wx.MessageBox(f"Git branches:\n{branch.stdout}", "Git Branches", wx.OK | wx.ICON_INFORMATION)
    
    except subprocess.CalledProcessError as e:
        wx.MessageBox(f"Git branch failed: {e}", "Error", wx.OK | wx.ICON_ERROR)
    
    except Exception as e:
        wx.MessageBox(f"An error occurred: {e}", "Error", wx.OK | wx.ICON_ERROR)