import sys
import os
import random
import time
import wx
import wx.adv
import subprocess

# ----------- Globals for splash -----------

wx_app = None
splash = None
splash_status = None

# ----------- Splash screen setup -----------

def create_wx_app():
    global wx_app
    if wx.App.IsMainLoopRunning():
        # wx.App already running
        return
    if not wx.App.GetInstance():
        wx_app = wx.App(False)

def setup_splash():
    global splash, splash_status

    splash_dir = "assets/splash/"
    pngs = [f for f in os.listdir(splash_dir) if f.lower().endswith(".png")]
    if not pngs:
        print("DEBUG: No PNG splash images found.")
        return

    splash_path = os.path.join(splash_dir, random.choice(pngs))
    bitmap = wx.Bitmap(splash_path, wx.BITMAP_TYPE_PNG)

    splash = wx.adv.SplashScreen(
        bitmap,
        wx.adv.SPLASH_CENTRE_ON_SCREEN | wx.adv.SPLASH_NO_TIMEOUT,
        0,
        None, -1
    )

    panel = wx.Panel(splash)
    width, height = bitmap.GetWidth(), bitmap.GetHeight()

    panel.Layout()
    splash.Show()

    # Force events to update splash immediately
    for _ in range(50):
        wx_app.Yield()
        time.sleep(0.01)

def update_splash(text):
    try:
        if splash and splash_status:
            splash_status.SetLabel(text)
            splash_status.Parent.Layout()
            wx_app.Yield()
    except Exception:
        pass

def close_splash():
    try:
        if splash:
            splash.Destroy()
    except Exception:
        pass

# ----------- Installer and import helpers -----------

def try_install(package_name):
    update_splash(f"Trying to install {package_name}...")
    commands = [
        f"{sys.executable} -m pip install {package_name}",
        f"{sys.executable} -m pip3 install {package_name}",
        f"pip install {package_name}",
        f"pip3 install {package_name}"
    ]
    for cmd in commands:
        print(f"DEBUG: Trying install command: {cmd}")
        if os.system(cmd) == 0:
            print(f"DEBUG: Installed '{package_name}' successfully with: {cmd}")
            return True
    print(f"DEBUG: All install attempts for '{package_name}' failed.")
    return False

def safe_import(module_name, package_name=None):
    if package_name is None:
        package_name = module_name
    update_splash(f"Importing {module_name}...")
    try:
        return __import__(module_name)
    except ImportError:
        print(f"DEBUG: Module '{module_name}' not found. Attempting install as '{package_name}'...")
        if try_install(package_name):
            try:
                return __import__(module_name)
            except ImportError:
                print(f"DEBUG: Import failed after installation of '{package_name}'. Exiting.")
                close_splash()
                sys.exit(1)
        else:
            close_splash()
            sys.exit(1)

# --------------------- Config Auto-Generation ---------------------

def auto_generate_pac_config():
    update_splash("Checking package manager config...")
    filename = "package-manager-pac.xcfg"
    print(f"DEBUG: Checking for existing system package manager config at '{filename}'")
    try:
        with open(filename, "r") as f:
            if any(line.strip() for line in f):
                print(f"DEBUG: Found non-empty {filename}, skipping auto-generation.")
                return
    except FileNotFoundError:
        print(f"DEBUG: {filename} not found, proceeding to generate.")

    import platform
    system = platform.system().lower()
    distro = platform.platform().lower()

    if "arch" in distro or "manjaro" in distro:
        default_cmds = ["sudo pacman -S --noconfirm {package}"]
        source = "Arch/Manjaro"
    elif "ubuntu" in distro or "debian" in distro:
        default_cmds = ["sudo apt install -y {package}"]
        source = "Debian/Ubuntu"
    elif "fedora" in distro or "redhat" in distro:
        default_cmds = ["sudo dnf install -y {package}"]
        source = "Fedora/RedHat"
    else:
        print()
        print(" ⚠️  Not able to find the package manager of your system.")
        print(" ❓  Please enter the syntax of your package manager (use '{package}' as placeholder).")
        if sys.stdin and sys.stdin.isatty():
            user_input = input("\n  ❯  ").strip()
        else:
            user_input = ""
        if user_input:
            default_cmds = [user_input]
            source = "User provided"
        else:
            default_cmds = []
            source = "No input given, empty config"

    with open(filename, "w") as f:
        for cmd in default_cmds:
            f.write(cmd + "\n")

    if default_cmds:
        print(f"DEBUG: Auto-generated '{filename}' using default for {source}: {default_cmds}")
    else:
        print(f"DEBUG: No system package manager syntax provided. '{filename}' left empty.")

def auto_generate_pyt_config():
    update_splash("Checking Python package manager config...")
    filename = "package-manager-pyt.xcfg"
    print(f"DEBUG: Checking for existing Python package manager config at '{filename}'")
    try:
        with open(filename, "r") as f:
            if any(line.strip() for line in f):
                print(f"DEBUG: Found non-empty {filename}, skipping auto-generation.")
                return
    except FileNotFoundError:
        print(f"DEBUG: {filename} not found, proceeding to generate.")

    default_cmds = [
        "python -m pip install {package}",
        "python3 -m pip install {package}",
        "pip install {package}",
        "pip3 install {package}"
    ]

    with open(filename, "w") as f:
        for cmd in default_cmds:
            f.write(cmd + "\n")

    print(f"DEBUG: Auto-generated '{filename}' with standard pip commands:")
    for cmd in default_cmds:
        print(f"DEBUG:   - {cmd}")

auto_generate_pac_config()
auto_generate_pyt_config()

# --------------------- Config-Aware Installer Logic ---------------------

def load_package_managers(config_file, default_commands):
    try:
        with open(config_file, "r") as f:
            lines = [line.strip() for line in f if line.strip()]
        if lines:
            print(f"DEBUG: Loaded commands from {config_file}: {lines}")
            return lines
        else:
            print(f"DEBUG: {config_file} is empty. Using defaults.")
    except FileNotFoundError:
        print(f"DEBUG: {config_file} not found. Using defaults.")
    return default_commands

def get_python_install_commands(package):
    default = [
        "python -m pip install {package}",
        "python3 -m pip install {package}",
        "pip install {package}",
        "pip3 install {package}",
    ]
    return [cmd.format(package=package).split() for cmd in load_package_managers("package-manager-pyt.xcfg", default)]

def get_system_install_commands(package):
    import platform
    distro = platform.platform().lower()
    if "ubuntu" in distro or "debian" in distro:
        default = ["sudo apt install -y {package}"]
    elif "arch" in distro or "manjaro" in distro:
        default = ["sudo pacman -S --noconfirm {package}"]
    elif "fedora" in distro or "redhat" in distro:
        default = ["sudo dnf install -y {package}"]
    else:
        default = []
    return [cmd.format(package=package).split() for cmd in load_package_managers("package-manager-pac.xcfg", default)]

def import_or_install(package_name, import_name=None, is_python=True):
    if import_name is None:
        import_name = package_name

    update_splash(f"Importing {import_name}...")
    try:
        globals()[import_name] = __import__(import_name)
        print(f"DEBUG: Successfully imported '{import_name}'.")
        return
    except ImportError:
        print(f"DEBUG: '{import_name}' not found. Attempting to install '{package_name}'...")

    commands = get_python_install_commands(package_name) if is_python else get_system_install_commands(package_name)

    for cmd in commands:
        try:
            print(f"DEBUG: Running install command: {' '.join(cmd)}")
            subprocess.check_call(cmd)
            break
        except Exception as e:
            print(f"DEBUG: Command failed: {' '.join(cmd)} — {e}")
    else:
        print(f"DEBUG: All install methods failed for '{package_name}'")
        close_splash()
        sys.exit(1)

    try:
        globals()[import_name] = __import__(import_name)
        print(f"DEBUG: Successfully imported '{import_name}' after installation.")
    except ImportError:
        print(f"DEBUG: Still could not import '{import_name}' after installation. Exiting.")
        close_splash()
        sys.exit(1)

# --------------------- Main Routine ---------------------

def main():
    create_wx_app()
    setup_splash()
    update_splash("Preparing environment...")

    import_or_install("psutil")
    import_or_install("requests")

    # wxPython special handling (should already be imported, but just in case)
    try:
        import wx
        import wx.stc as stc
        print("DEBUG: wxPython imported successfully.")
    except ImportError:
        print("DEBUG: wxPython not found. Attempting install...")
        import_or_install("wxPython", "wx")

    # Windows-specific modules
    if "wx" in globals() and hasattr(wx, "Platform") and wx.Platform == "__WXMSW__":
        import_or_install("pypresence")
        from pypresence import Presence
        import_or_install("pywinstyles")

    # Standard modules (import only — should exist)
    import_or_install("webbrowser")
    import_or_install("hashlib")
    import_or_install("threading")
    import_or_install("time")
    
    update_splash("All dependencies imported and initialized.")
    time.sleep(1)
    close_splash()

    print("DEBUG: All dependencies successfully imported and initialized.")

if __name__ == "__main__":
    main()

import extension_menubar
import extension_mainfn
import extension_mainclass
import extension_themes
import requirements
import git_integration
import settings
import github
import init_project
import error_checker
import merge_resolver

class TextEditor(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(TextEditor, self).__init__(*args, **kwargs)
        
        if wx.Platform == "__WXMSW__":
            # Initialize RPC as None by default
            self.RPC = None

            # Load config values from the xcfg file
            config = self.load_config("xedix.xcfg")
            self.active_color = config.get("headerActive", "#EDF0F2") # Default values if not found
            self.inactive_color = config.get("headerInactive", "#b3d0e4") # Default values if not found

            # Apply style and set initial header color
            try:
                pywinstyles.apply_style(self, "mica")
                pywinstyles.change_header_color(self, color=self.active_color)
            except Exception:
                pass
            
            with open('discord.xcfg', 'r') as file:
                presence = file.read()

            
            if presence == "True":
                try:
                    CLIENT_ID = '1332012158376083528'
                    self.RPC = Presence(CLIENT_ID)  # Store as instance variable
                    self.RPC.connect()
                    self.RPC.update(
                        state="XediX",
                        details="Idling",
                        large_image="xedix_logo",
                        large_text="XediX",
                        small_text="XediX"
                    )
                except Exception as e:
                    print(f"Could not update Discord status: {e}")
                    try:
                        if self.RPC:
                            self.RPC.close()  # Properly close the connection
                    except:
                        pass
                    self.RPC = None
            
        # Bind focus events for dynamic color change
        self.Bind(wx.EVT_ACTIVATE, self.on_activate)

        self.output_window = None
        self.InitUI()
        self.return_values = []

    @staticmethod
    def load_config(filepath):
        """
        Load key-value pairs from a .xcfg file.
        """
        config = {}
        try:
            with open(filepath, "r") as file:
                content = file.read().strip()
                for pair in content.split(";"):
                    if ":" in pair:
                        key, value = pair.split(":", 1)
                        config[key.strip()] = value.strip()
        except FileNotFoundError:
            print(f"Config file {filepath} not found. Using defaults.")
        except Exception as e:
            print(f"Error reading config file: {e}")
        return config

    def on_activate(self, event):
        """Runs when the window is activated or deactivated."""
        try:
            if event.GetActive():
                pywinstyles.change_header_color(self, color=self.active_color)
            else:
                pywinstyles.change_header_color(self, color=self.inactive_color)
        except Exception:
            pass

        # Ensure event is processed further
        event.Skip()


    def InitUI(self):
        panel = wx.Panel(self)

        # Set window icon
        try:
            icon = wx.Icon("xedixlogo.ico", wx.BITMAP_TYPE_ICO)
            self.SetIcon(icon)
        except Exception as e:
            print("Error setting window icon:", e)

        splitter = wx.SplitterWindow(panel)

        self.sidebar = wx.Panel(splitter)
        self.sidebar.SetWindowStyleFlag(wx.NO_BORDER)

        # Add New File button
        new_file_btn = wx.Button(self.sidebar, label="New File")
        new_file_btn.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        new_file_btn.SetWindowStyleFlag(wx.NO_BORDER)
        new_file_btn.SetMinSize((150, 35))
        new_file_btn.SetMaxSize((150, 35))
        new_file_btn.Bind(wx.EVT_BUTTON, self.OnNewFile)

        self.file_list = wx.ListBox(self.sidebar)
        self.PopulateFileList()
        self.file_list.Bind(wx.EVT_RIGHT_DOWN, self.OnFileListRightClick)

        self.matching_brackets = {
            '(': ')',
            '[': ']',
            '{': '}',
            '"': '"',
            "'": "'",
        }

        # Create status bar
        self.CreateStatusBar(3)
        status_bar = self.GetStatusBar()
        status_bar.SetMinSize((-1, 22))
        status_font = wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        status_bar.SetFont(status_font)
        self.SetStatusText("    Welcome to XediX - Text Editor")
        self.SetStatusText("    Open a file first", 1)

        # Main panel content

        self.main_panel = wx.Panel(splitter)

        # Create horizontal sizer for icon + label
        icon_and_label_sizer = wx.BoxSizer(wx.HORIZONTAL)

        try:
            img = wx.Image("xedixlogo.ico", wx.BITMAP_TYPE_ICO)
            img = img.Scale(24, 24, wx.IMAGE_QUALITY_HIGH)  # scale icon size to 24x24 px
            bmp = wx.Bitmap(img)
            icon_bitmap = wx.StaticBitmap(self.main_panel, bitmap=bmp)
            icon_and_label_sizer.Add(icon_bitmap, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=8)
        except Exception as e:
            print("Error loading icon for label:", e)

        # Label "Open a File first"
        self.default_message = wx.StaticText(self.main_panel, label="Open a File first")
        font = self.default_message.GetFont()
        font.PointSize += 5
        font = font.Bold()
        self.default_message.SetFont(font)
        icon_and_label_sizer.Add(self.default_message, flag=wx.ALIGN_CENTER_VERTICAL)

        # Tip label below the main message
        self.tip_label = wx.StaticText(self.main_panel, label="Loading tip...")
        tip_font = self.tip_label.GetFont()
        tip_font.PointSize -= 1  # slightly smaller font
        self.tip_label.SetFont(tip_font)
        self.tip_label.SetForegroundColour(wx.Colour(100, 100, 100))  # subtle gray

        # Vertical sizer to center horizontally & vertically
        main_vbox = wx.BoxSizer(wx.VERTICAL)
        main_vbox.AddStretchSpacer(1)
        main_vbox.Add(icon_and_label_sizer, flag=wx.ALIGN_CENTER)
        main_vbox.Add(self.tip_label, flag=wx.ALIGN_CENTER | wx.TOP, border=5)
        main_vbox.AddStretchSpacer(1)

        self.main_panel.SetSizer(main_vbox)

        # Notebook for tabs (hidden by default)
        self.notebook = wx.Notebook(splitter)
        self.notebook.Hide()

        # Sidebar layout
        sidebar_vbox = wx.BoxSizer(wx.VERTICAL)
        sidebar_vbox.AddStretchSpacer(0)
        sidebar_vbox.Add(new_file_btn, proportion=0, flag=wx.EXPAND | wx.RIGHT | wx.BOTTOM, border=10)
        sidebar_vbox.Add(self.file_list, proportion=1, flag=wx.EXPAND | wx.RIGHT, border=10)
        self.sidebar.SetSizer(sidebar_vbox)

        # Splitter config
        splitter.SplitVertically(self.sidebar, self.main_panel)
        splitter.SetMinimumPaneSize(150)

        # Main layout
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(splitter, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
        panel.SetSizer(vbox)

        # Windows specific colors
        if wx.Platform == "__WXMSW__":
            self.sidebar.SetBackgroundColour("#fff")
            new_file_btn.SetBackgroundColour("#EDF0F2")
            new_file_btn.SetForegroundColour("#201f1f")
            status_bar.SetBackgroundColour("#EDF0F2")
            self.main_panel.SetBackgroundColour("#EDF0F2")
            self.notebook.SetBackgroundColour("#ffffff00")
            panel.SetBackgroundColour("#fff")

        self.SetTitle("XediX - Text Editor")
        self.SetSize((850, 600))
        self.Centre()

        # Bind double-click on file list to file open
        self.file_list.Bind(wx.EVT_LISTBOX_DCLICK, self.OnFileOpen)

        self.CreateMenuBar()

        # Fetch tips JSON and display a random tip
        try:
            url = "https://xedix.w3spaces.com/tips.json"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            tips = response.json()
            if tips:
                tip = random.choice(tips)
                self.tip_label.SetLabel(tip)
            else:
                self.tip_label.SetLabel("No tips available right now.")
        except Exception as e:
            print(f"Failed to fetch tips: {e}")
            self.tip_label.SetLabel("Welcome to XediX! Start coding.")


    def CreateMenuBar(self):
        menubar = wx.MenuBar()

        fileMenu = wx.Menu()
        save_item = fileMenu.Append(wx.ID_SAVE, '&Save\tCtrl+S', 'Save the file')
        run_item = fileMenu.Append(wx.ID_ANY, '&Run Code\tCtrl+R', 'Run the code')
        folder_item = fileMenu.Append(wx.ID_ANY, '&Open Folder\tCtrl+Shift+O', 'Open Folder')
        fileMenu.AppendSeparator()
        pylint_item = fileMenu.Append(wx.ID_ANY, '&Run PyLint\tCtrl+P', 'Run pylint on code')
        exit_item = fileMenu.Append(wx.ID_EXIT, '&Exit\tCtrl+Q', 'Exit application')

        editMenu = wx.Menu()
        cut_item = editMenu.Append(wx.ID_CUT, '&Cut\tCtrl+X', 'Cut selection')
        copy_item = editMenu.Append(wx.ID_COPY, '&Copy\tCtrl+C', 'Copy selection')
        paste_item = editMenu.Append(wx.ID_PASTE, '&Paste\tCtrl+V', 'Paste from clipboard')
        editMenu.AppendSeparator()

        find_replace_item = editMenu.Append(wx.ID_FIND, '&Find and Replace\tCtrl+F', 'Find and replace text')
        jump_line_item = editMenu.Append(wx.ID_ANY, '&Jump to Line\tCtrl+G', 'Jump to a specific line number')

        toolsMenu = wx.Menu()

        # Create the Deployment submenu
        deployment_submenu = wx.Menu()
        req_item = deployment_submenu.Append(wx.ID_ANY, 'Generate requirements.txt')
        toolsMenu.AppendSubMenu(deployment_submenu, 'Building Tools')

        # Create the Git submenu
        git_submenu = wx.Menu()  # This is a Menu, not a MenuItem
        commit_item = git_submenu.Append(wx.ID_ANY, 'Git Commit', 'Commit the code')
        add_item = git_submenu.Append(wx.ID_ANY, 'Git Add .', 'git add .')
        push_item = git_submenu.Append(wx.ID_ANY, 'Git Push', 'Push the code')
        pull_item = git_submenu.Append(wx.ID_ANY, 'Git Pull', 'git pull')
        clone_item = git_submenu.Append(wx.ID_ANY, 'Git Clone', 'Commit the code')
        git_submenu.AppendSeparator()

        # Add version and branch items
        version_item = git_submenu.Append(wx.ID_ANY, 'Git Version', 'Show git version')
        branch_item = git_submenu.Append(wx.ID_ANY, 'Git Branch', 'Show current branch')
        status_item = git_submenu.Append(wx.ID_ANY, 'Git Status', 'Show git status')
        
        # Merge Resolver
        git_submenu.AppendSeparator()
        merge_resolve_item = git_submenu.Append(wx.ID_ANY, "Merge Resolver", "Resolve Merge Conflicts")

        # Append the Git submenu to the tools menu
        toolsMenu.AppendSubMenu(git_submenu, "Git")

        helpMenu = wx.Menu()
        homepage_item = helpMenu.Append(wx.ID_ANY, "&Homepage", "Homepage")
        about_item = helpMenu.Append(wx.ID_ABOUT, '&About', 'About')
        docs_item = helpMenu.Append(wx.ID_ANY, "&Docs", "Open Documentation")

        configMenu = wx.Menu()
        customize_item = configMenu.Append(wx.ID_ANY, '&Customize manually\tCtrl+Shift+C', 'Customize the UI')
        settings_item = configMenu.Append(wx.ID_ANY, '&Settings', 'Open Settings')

        projectMenu = wx.Menu()
        init_project_item = projectMenu.Append(wx.ID_ANY, '&Init Project', 'Initialize a new project')
        init_python_item = projectMenu.Append(wx.ID_ANY, '&Init Python', 'Initialize a new Python project')
        init_git_item = projectMenu.Append(wx.ID_ANY, '&Init Git', 'Initialize a new Git project')

        menubar.Append(fileMenu, '&File')
        menubar.Append(editMenu, '&Edit')
        menubar.Append(toolsMenu,'&Tools')
        menubar.Append(configMenu, '&Config')
        menubar.Append(helpMenu, '&Help')
        menubar.Append(projectMenu, '&Project')
        # Define minsize
        self.SetMenuBar(menubar)

        # File operations
        self.Bind(wx.EVT_MENU, self.OnSave, save_item)
        self.Bind(wx.EVT_MENU, self.OnRunCode, run_item)
        self.Bind(wx.EVT_MENU, self.OnOpenFolder, folder_item)
        self.Bind(wx.EVT_MENU, self.OnRunPylint, pylint_item)
        self.Bind(wx.EVT_MENU, self.OnExit, exit_item)

        # Edit operations
        self.Bind(wx.EVT_MENU, self.OnCut, cut_item)
        self.Bind(wx.EVT_MENU, self.OnCopy, copy_item) 
        self.Bind(wx.EVT_MENU, self.OnPaste, paste_item)
        self.Bind(wx.EVT_MENU, self.OnFindReplace, find_replace_item)
        self.Bind(wx.EVT_MENU, self.OnJumpToLine, jump_line_item)

        # Git operations
        self.Bind(wx.EVT_MENU, self.gcommit, commit_item)
        self.Bind(wx.EVT_MENU, self.gadd, add_item)
        self.Bind(wx.EVT_MENU, self.gpush, push_item)
        self.Bind(wx.EVT_MENU, self.gpull, pull_item)
        self.Bind(wx.EVT_MENU, self.gversion, version_item)
        self.Bind(wx.EVT_MENU, self.gbranch, branch_item)
        self.Bind(wx.EVT_MENU, self.gstatus, status_item)
        self.Bind(wx.EVT_MENU, self.merge_resolving, merge_resolve_item)

        # Project operations
        self.Bind(wx.EVT_MENU, self.ginit, init_git_item)
        self.Bind(wx.EVT_MENU, self.pinit, init_python_item)
        self.Bind(wx.EVT_MENU, self.xinit, init_project_item)

        # Tools and settings
        self.Bind(wx.EVT_MENU, self.OnCustomize, customize_item)
        self.Bind(wx.EVT_MENU, self.RequirementsGeneration, req_item)
        self.Bind(wx.EVT_MENU, self.OnConfig, settings_item)

        # Help and documentation
        self.Bind(wx.EVT_MENU, self.About, about_item)
        self.Bind(wx.EVT_MENU, self.Docs, docs_item)
        self.Bind(wx.EVT_MENU, self.Homepage, homepage_item)
        
        extension_menubar.main()
    
    def gversion(self, event):
        git_integration.version()

    def gbranch(self, event):
        git_integration.branch()

    def gadd(self, event):
        git_integration.add()
    
    def gpush(self, event):
        git_integration.push()

    def gpull(self, event):
        git_integration.pull()

    def gstatus(self, event):
        git_integration.status()

    def gcommit(self, event):
        git_integration.commit()

    def ginit(self, event):
        init_project.git_init()

    def pinit(self, event):
        init_project.python_init()

    def xinit(self, event):
        init_project.xedix_init()
        
    def merge_resolving(self, event):
        merge_resolver.main()
    
    # The following functions are opening webpages
    def About(self, event):
        self.SetStatusText("    Opening webpage...", 2)
        time.sleep(1)
        webbrowser.open("https://xedix.w3spaces.com/about.html")
        self.SetStatusText("    Webpage opened", 2)

    def Docs(self, event):
        self.SetStatusText("    Opening webpage...", 2)
        time.sleep(1)
        webbrowser.open("https://github.com/mostypc123/XediX/wiki")
        self.SetStatusText("    Webpage opened", 2)

    def Homepage(self, event):
        self.SetStatusText("    Opening webpage...", 2)
        time.sleep(1)
        webbrowser.open("https://xedix.w3spaces.com")
        self.SetStatusText("    Webpage opened", 2)

    def OnConfig(self, event):
        settings.main()

    def OnOpenFolder(self, event, event_or_path):
        """Handle opening folders from both GUI and command line."""
        if isinstance(event_or_path, str):
            # Direct path provided
            path = event_or_path
        else:
            # Called from GUI event
            dlg = wx.DirDialog(self, "Choose a directory, if does not exist, it will be created",
                            style=wx.DD_DEFAULT_STYLE)
            
            if dlg.ShowModal() != wx.ID_OK:
                dlg.Destroy()
                return
                
            path = dlg.GetPath()
            dlg.Destroy()

        try:
            # Check if directory exists first
            if not os.path.exists(path):
                os.makedirs(path)
                
            # Change the working directory
            os.chdir(path)
            
            # Show confirmation message
            self.SetStatusText(f"    Changed directory to: {path}")
            
        except PermissionError:
            self.SetStatusText(f"    Error: No permission to create/access directory: {path}")
            return
        except OSError as e:
            self.SetStatusText(f"    Error creating/accessing directory: {e}")
            return

        # Clear the current file list
        self.file_list.Clear()

        # Populate the file list with files from the new directory
        self.PopulateFileList()

        self.current_dir = path

    def RequirementsGeneration(self, event):
        current_tab = self.notebook.GetCurrentPage()
        if current_tab:
            text_area = current_tab.GetChildren()[0]
            code = text_area.GetValue()
            with open("requirements.txt", "w") as file:
                file.write(requirements.main(code))
            self.SetStatusText("Saved requirements.txt")
        else:
            self.SetStatusText("Error saving requirements")

    def OnFileListRightClick(self, event):
        """Handle right-click events on file list items."""
        # Get the item that was clicked
        index = self.file_list.HitTest(event.GetPosition())
        if index != wx.NOT_FOUND:
            self.file_list.SetSelection(index)

            # Create and show the context menu
            menu = wx.Menu()
            rename_item = menu.Append(wx.ID_ANY, "Rename")
            delete_item = menu.Append(wx.ID_ANY, "Delete")

            # Bind menu events
            self.Bind(wx.EVT_MENU, self.OnRenameFile, rename_item)
            self.Bind(wx.EVT_MENU, self.OnDeleteFile, delete_item)

            # Show the popup menu
            self.PopupMenu(menu)
            menu.Destroy()

    def OnRenameFile(self, event):
        """Handle file rename operation."""
        selected_index = self.file_list.GetSelection()
        if selected_index != wx.NOT_FOUND:
            old_name = self.file_list.GetString(selected_index)

            # Show dialog to get new name
            dialog = wx.TextEntryDialog(self, "Enter new filename:", "Rename File", old_name)
            if dialog.ShowModal() == wx.ID_OK:
                new_name = dialog.GetValue()

                try:
                    # Rename the file
                    os.rename(old_name, new_name)

                    # Update the file list
                    self.file_list.SetString(selected_index, new_name)

                    # Update the notebook tab if the file is open
                    for i in range(self.notebook.GetPageCount()):
                        if self.notebook.GetPageText(i) == old_name:
                            self.notebook.SetPageText(i, new_name)

                    self.SetStatusText(f"    Renamed {old_name} to {new_name}")
                except OSError as e:
                    wx.MessageBox(f"Error renaming file: {str(e)}", "Error", 
                                wx.OK | wx.ICON_ERROR)

            dialog.Destroy()

    def OnDeleteFile(self, event):
        """Handle file delete operation."""
        selected_index = self.file_list.GetSelection()
        if selected_index != wx.NOT_FOUND:
            filename = self.file_list.GetString(selected_index)

            # Show confirmation dialog
            dialog = wx.MessageDialog(self, 
                                    f"Are you sure you want to delete '{filename}'?",
                                    "Confirm Delete",
                                    wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)

            if dialog.ShowModal() == wx.ID_YES:
                try:
                    # Close the file if it's open in the editor
                    for i in range(self.notebook.GetPageCount()):
                        if self.notebook.GetPageText(i) == filename:
                            self.notebook.DeletePage(i)
                            break

                    # Delete the file
                    os.remove(filename)

                    # Remove from file list
                    self.file_list.Delete(selected_index)

                    self.SetStatusText(f"    Deleted {filename}")
                except OSError as e:
                    wx.MessageBox(f"Error deleting file: {str(e)}", "Error", 
                                wx.OK | wx.ICON_ERROR)

            dialog.Destroy()

    def OnJumpToLine(self, event):
        """Jump to selected line of code."""
        current_tab = self.notebook.GetCurrentPage()
        if current_tab:
            text_area = current_tab.GetChildren()[0]

            # Create a dialog to get the line number
            line_dialog = wx.TextEntryDialog(self, "Enter line number:", "Jump to Line")
            # style  the  textentry
            if line_dialog.ShowModal() == wx.ID_OK:
                try:
                    # Convert the input to an integer line number
                    line_number = int(line_dialog.GetValue()) - 1  # Adjust for 0-based indexing

                    # Get the position of the specified line
                    line_pos = text_area.PositionFromLine(line_number)

                    # Scroll to the line and set the cursor
                    text_area.GotoPos(line_pos)
                    text_area.SetFocus()

                    # Highlight the line
                    text_area.EnsureCaretVisible()
                    text_area.SetSelection(line_pos, text_area.GetLineEndPosition(line_number))
                    # Update status bar
                    self.SetStatusText(f"Jumped to line {line_number + 1}")

                except ValueError:
                    # Handle invalid input
                    wx.MessageBox("Please enter a valid line number", "Error", wx.OK | wx.ICON_ERROR)
                except Exception as e:
                    # Handle any other potential errors
                    wx.MessageBox(f"Error jumping to line: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)

            line_dialog.Destroy()

    def OnCustomize(self, event):
        """Opens the manual customization."""
        file_name = "xedix.xcfg"
        file_path = os.path.join(os.getcwd(), file_name)

        try:
            with open(file_path, 'r') as file:
                content = file.read()
        except FileNotFoundError:
            wx.MessageBox(f"File '{file_name}' not found in the current directory.", "Error", wx.ICON_ERROR)
            return
        except Exception as e:
            wx.MessageBox(f"An error occurred while opening the file: {e}", "Error", wx.ICON_ERROR)
            return

        if not self.notebook.IsShown():
            # Hide default message and panel, replace with notebook
            self.default_message.Hide()
            self.main_panel.Hide()
            splitter = self.main_panel.GetParent()
            splitter.ReplaceWindow(self.main_panel, self.notebook)
            self.notebook.Show()
            self.notebook.SetBackgroundColour("#ffffff00")
            self.notebook.SetWindowStyleFlag(wx.NO_BORDER)

        # Create a new tab with a text editor to display file content
        tab = wx.Panel(self.notebook)
        text_area = stc.StyledTextCtrl(tab, style=wx.TE_MULTILINE)
        text_area.SetText(content)
        text_area.SetTabWidth(4)
        text_area.SetWindowStyleFlag(wx.NO_BORDER)

        self.SetStatusText(f"    Opened file: {file_name}")
        text_area.Bind(wx.EVT_CHAR, self.OnChar)

        # [IMP] Refactor this piece of code in next update
        with open("theme.xcfg", 'r') as file:
            theme = file.read()
            if theme == "dark":
                dark_bg_color = "#1B1F2B"
            elif theme == "light":
                dark_bg_color = "#FFFFFF"
                light_text_color = "#1e1e1e"
            elif theme == "night":
                dark_bg_color = "#2f3139"
            elif theme == "obsidian":
                dark_bg_color = "#212232"
            else:
                dark_bg_color = "#1B1F2B"

            if theme != "light":
                light_text_color = "#FFFFFF"

            text_area.StyleSetBackground(stc.STC_STYLE_DEFAULT, dark_bg_color)
            text_area.StyleSetForeground(stc.STC_STYLE_DEFAULT, light_text_color)
            text_area.StyleClearAll()  # Apply the default style to all text

             # Default style
            text_area.StyleSetSpec(stc.STC_P_DEFAULT, f"fore:{light_text_color},italic,back:{dark_bg_color}")

            # Adjust indentation guides
            text_area.SetIndentationGuides(True)
            text_area.StyleSetSpec(stc.STC_STYLE_LINENUMBER, f"fore:{light_text_color},italic,back:{dark_bg_color}")
            text_area.SetMarginType(1, stc.STC_MARGIN_NUMBER)
            text_area.SetMarginWidth(1, 30)

            tab_sizer = wx.BoxSizer(wx.VERTICAL)
            tab_sizer.Add(text_area, proportion=1, flag=wx.EXPAND)
            tab.SetSizer(tab_sizer)

            self.notebook.AddPage(tab, file_name)

    def OnRunPylint(self, event):
        """Runs pylint on code."""
        current_tab = self.notebook.GetCurrentPage()
        if current_tab:
            # Get the SplitterWindow and then the text area
            editor_splitter = current_tab.GetChildren()[0]  # SplitterWindow
            text_area = editor_splitter.GetChildren()[0]    # StyledTextCtrl
            code = text_area.GetValue()

            # Save current file to a temporary location before running pylint
            file_name = 'temp_code.py'
            with open(file_name, 'w') as file:
                file.write(code)

            # Run pylint using subprocess
            pylint_process = subprocess.Popen(
                ['pylint', file_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = pylint_process.communicate()

            # Show pylint output in the output window
            if self.output_window is None:
                self.output_window = wx.Dialog(self, title="pylint Output", size=(600, 400))
                pywinstyles.apply_style(self.output_window, "win7")
                output_panel = wx.Panel(self.output_window)
                output_vbox = wx.BoxSizer(wx.VERTICAL)

                self.output_text = wx.TextCtrl(output_panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
                output_vbox.Add(self.output_text, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
                output_panel.SetSizer(output_vbox)

            output_message = f"{stdout}\nErrors:\n{stderr}"
            self.output_text.SetValue(output_message)
            self.output_window.ShowModal()

    def OnFindReplace(self, event):
        """Opens a find/replace dialog."""
        self.SetStatusText("    Find and replace running")

        # Find dialog
        find_replace_dialog = wx.TextEntryDialog(self, "Find text:")
        self.SetStatusText("    Find and replace: find dialog running")
        if find_replace_dialog.ShowModal() == wx.ID_OK:
            # Replace dialog
            self.SetStatusText("    Find and replace: find dialog ran")
            find_text = find_replace_dialog.GetValue()
            replace_dialog = wx.TextEntryDialog(self, "Replace with:")
            self.SetStatusText("    Find and replace: replace dialog ran")
            if replace_dialog.ShowModal() == wx.ID_OK:
                replace_text = replace_dialog.GetValue()
                current_tab = self.notebook.GetCurrentPage()
                if current_tab:
                    # Gets the textarea object
                    text_area = current_tab.GetChildren()[0]

                    # Gets the content
                    content = text_area.GetValue()

                    # Replace text
                    new_content = content.replace(find_text, replace_text)

                    # Show the changes made in the textarea
                    text_area.SetText(new_content)
        self.SetStatusText("    Find and replace ran, or it was closed by the user")


    def PopulateFileList(self):
        """Populates the file list with the files in the current directory"""
        current_dir = os.getcwd()
        files = [f for f in os.listdir(current_dir) if os.path.isfile(os.path.join(current_dir, f))]
        self.file_list.AppendItems(files)
        # Style the files
        self.file_list.SetBackgroundColour('#fff')
        # border color
        self.file_list.SetForegroundColour('#201f1f')

    def ScanForViruses(self, file_name):
        """Thoroughly scans file against all VirusShare databases"""
        self.SetStatusText(f"    Scanning {file_name} for viruses...")
        
        try:
            # Get the full file path
            file_path = os.path.join(os.getcwd(), file_name)
            
            # Calculate MD5 hash of the file
            md5_hash = hashlib.md5()
            
            with open(file_path, 'rb') as f:
                # Read and update hash in chunks of 4K
                for byte_block in iter(lambda: f.read(4096), b""):
                    md5_hash.update(byte_block)
            
            file_md5 = md5_hash.hexdigest().lower()
            
            # Create a dialog to show scanning progress and results
            scan_dialog = wx.Dialog(self, title="Virus Scan Results", size=(500, 400))
            panel = wx.Panel(scan_dialog)
            vbox = wx.BoxSizer(wx.VERTICAL)
            
            # Add file information
            file_info = wx.StaticText(panel, label=f"File: {file_name}\nSize: {os.path.getsize(file_path)} bytes\nMD5: {file_md5}")
            vbox.Add(file_info, flag=wx.ALL, border=10)
            
            # Create a multi-line text control for scan results
            log_text = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(-1, 200))
            log_text.AppendText("Starting virus scan using VirusShare hash database...\n\n")
            
            vbox.Add(log_text, proportion=1, flag=wx.ALL|wx.EXPAND, border=10)
            
            # Add a gauge for progress
            gauge = wx.Gauge(panel, range=100, size=(-1, 20))
            vbox.Add(gauge, flag=wx.ALL|wx.EXPAND, border=10)
            
            # Add close button (disabled initially)
            close_btn = wx.Button(panel, label="Close")
            close_btn.Bind(wx.EVT_BUTTON, lambda evt: scan_dialog.EndModal(wx.ID_OK))
            close_btn.Disable()  # Disable until scan completes
            vbox.Add(close_btn, flag=wx.ALL|wx.CENTER, border=10)
            
            panel.SetSizer(vbox)
            scan_dialog.Show()
            
            # Create a simple temporary directory
            temp_dir = os.path.join(os.getcwd(), "temp_virusshare")
            if not os.path.exists(temp_dir):
                os.mkdir(temp_dir)
            log_text.AppendText(f"Created temporary directory for hash databases: {temp_dir}\n")
            
            def scan_thread():
                try:
                    # Check ALL hash databases (1-487)
                    total_db_files = 487
                    
                    # Function to download a hash file
                    def download_hash_file(file_num):
                        url = f"https://virusshare.com/hashfiles/VirusShare_{file_num:03d}.md5"
                        local_path = os.path.join(temp_dir, f"VirusShare_{file_num:03d}.md5")
                        
                        try:
                            log_text.AppendText(f"Downloading {url}...\n")
                            
                            # Download the file using requests
                            response = requests.get(url, stream=True)
                            
                            if response.status_code == 200:
                                with open(local_path, 'wb') as f:
                                    for chunk in response.iter_content(chunk_size=8192):
                                        f.write(chunk)
                                log_text.AppendText(f"Successfully downloaded {url}\n")
                                return local_path
                            else:
                                log_text.AppendText(f"Failed to download {url} (Status: {response.status_code})\n")
                                return None
                        except Exception as e:
                            log_text.AppendText(f"Error downloading {url}: {str(e)}\n")
                            return None
                    
                    # Function to check if a hash exists in a database file
                    def check_hash_in_file(hash_file_path, target_hash):
                        try:
                            with open(hash_file_path, 'r') as f:
                                # Skip the first few lines (header)
                                for _ in range(5):
                                    next(f, None)
                                
                                # Check each hash
                                for line in f:
                                    if line.strip().lower() == target_hash:
                                        return True
                            return False
                        except Exception as e:
                            log_text.AppendText(f"Error reading hash file {os.path.basename(hash_file_path)}: {str(e)}\n")
                            return False
                    
                    # Scan against ALL databases
                    found_match = False
                    
                    for i in range(1, total_db_files + 1):
                        # Update progress bar
                        gauge.SetValue(int((i-1) / total_db_files * 100))
                        wx.CallAfter(wx.Yield)
                        
                        # Download hash file
                        hash_file = download_hash_file(i)
                        
                        if hash_file:
                            log_text.AppendText(f"Checking file against {os.path.basename(hash_file)}...\n")
                            
                            if check_hash_in_file(hash_file, file_md5):
                                log_text.AppendText(f"\n⚠️ MATCH FOUND in database #{i}! This file matches a known malicious hash.\n")
                                found_match = True
                                break
                            
                            # Delete the file after checking to save disk space
                            os.remove(hash_file)
                    
                    if not found_match:
                        log_text.AppendText("\n✓ No matches found. File hash not present in any of the VirusShare databases.\n")
                    
                    # Set progress to 100% when done
                    gauge.SetValue(100)
                    log_text.AppendText("\nScan completed. Checked against all 487 VirusShare databases.\n")
                    
                    # Clean up temporary directory
                    log_text.AppendText("\nCleaning up temporary files...\n")
                    
                    # Delete any remaining files in the temp directory
                    for file in os.listdir(temp_dir):
                        file_path = os.path.join(temp_dir, file)
                        try:
                            os.remove(file_path)
                        except Exception as e:
                            log_text.AppendText(f"Error deleting {file}: {str(e)}\n")
                    
                    # Remove the directory itself
                    try:
                        os.rmdir(temp_dir)
                        log_text.AppendText("Temporary directory deleted.\n")
                    except Exception as e:
                        log_text.AppendText(f"Error removing temporary directory: {str(e)}\n")
                    
                    # Enable close button
                    wx.CallAfter(close_btn.Enable)
                    
                    # Update status bar
                    wx.CallAfter(self.SetStatusText, f"    Completed comprehensive virus scan for {file_name}")
                    
                except Exception as e:
                    log_text.AppendText(f"Error during scan: {str(e)}\n")
                    # Enable close button even if there was an error
                    wx.CallAfter(close_btn.Enable)
            
            # Start scanning in a separate thread to keep UI responsive
            thread = threading.Thread(target=scan_thread)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            wx.MessageBox(f"Error setting up scan: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
            self.SetStatusText(f"    Error scanning {file_name}")

    def RunWithAdminPrivileges(self, file_name):
        """Runs the executable with elevated privileges using only subprocess and os"""
        self.SetStatusText(f"    Launching {file_name} with admin privileges...")
        
        try:
            file_path = os.path.join(os.getcwd(), file_name)
            
            if sys.platform == "win32":
                # Windows - use the built-in elevate.exe utility or directly through cmd
                subprocess.Popen(['powershell', 'Start-Process', '-FilePath', file_path, 
                                '-Verb', 'RunAs'], shell=True)
            elif sys.platform == "darwin":
                # macOS - use sudo (will prompt for password in Terminal)
                subprocess.Popen(['sudo', file_path])
            else:
                # Linux - use sudo or similar (will prompt for password)
                for sudo_cmd in ['pkexec', 'sudo', 'gksudo', 'kdesudo']:
                    try:
                        subprocess.Popen([sudo_cmd, file_path])
                        break
                    except FileNotFoundError:
                        continue
            
            self.SetStatusText(f"    Launched {file_name} with admin privileges")
        except Exception as e:
            wx.MessageBox(f"Error launching with admin privileges: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
            self.SetStatusText(f"    Error launching {file_name}")

    def RunInTerminal(self, file_name):
        """Runs the executable in a separate terminal window with optional arguments"""
        # Prompt for command-line arguments
        arg_dialog = wx.TextEntryDialog(self, "Enter command-line arguments (optional):", "Run with Arguments")
        args = ""
        if arg_dialog.ShowModal() == wx.ID_OK:
            args = arg_dialog.GetValue()
        arg_dialog.Destroy()
        
        self.SetStatusText(f"    Launching {file_name} in terminal...")
        
        try:
            # Get the full file path
            file_path = os.path.join(os.getcwd(), file_name)
            
            if sys.platform == "win32":
                # Windows - use CMD to open a new console window
                subprocess.Popen(f'start cmd /k "{file_path} {args}"', shell=True)
            elif sys.platform == "darwin":
                # macOS - use Terminal.app
                subprocess.Popen(['open', '-a', 'Terminal', file_path, args])
            else:
                # Linux - try common terminal emulators
                for terminal in ['x-terminal-emulator', 'gnome-terminal', 'xterm', 'konsole']:
                    try:
                        subprocess.Popen([terminal, '-e', f"{file_path} {args}"])
                        break
                    except (FileNotFoundError, subprocess.SubprocessError):
                        continue
            
            self.SetStatusText(f"    Launched {file_name} in terminal")
        except Exception as e:
            wx.MessageBox(f"Error launching in terminal: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
            self.SetStatusText(f"    Error launching {file_name}")

    def RunInTerminalWithArgs(self, file_name):
        """Runs the executable in a separate terminal window with user-provided arguments"""
        # Prompt for command-line arguments
        arg_dialog = wx.TextEntryDialog(self, "Enter command-line arguments (optional):", "Run with Arguments")
        args = ""
        if arg_dialog.ShowModal() == wx.ID_OK:
            args = arg_dialog.GetValue()
        arg_dialog.Destroy()
        
        self.SetStatusText(f"    Launching {file_name} in terminal with arguments...")
        
        try:
            # Get the full file path
            file_path = os.path.join(os.getcwd(), file_name)
            
            if sys.platform == "win32":
                # Windows - use CMD to open a new console window
                subprocess.Popen(f'start cmd /k "{file_path} {args}"', shell=True)
            elif sys.platform == "darwin":
                # macOS - use Terminal.app
                # For macOS, we need to create a command string
                cmd_string = f"'{file_path}' {args}"
                subprocess.Popen(['open', '-a', 'Terminal', cmd_string])
            else:
                # Linux - try common terminal emulators
                cmd_string = f"{file_path} {args}"
                for terminal in ['x-terminal-emulator', 'gnome-terminal', 'xterm', 'konsole']:
                    try:
                        # Different terminals have different ways to execute commands
                        if terminal == 'gnome-terminal':
                            subprocess.Popen([terminal, '--', 'bash', '-c', f"{cmd_string}; exec bash"])
                        else:
                            subprocess.Popen([terminal, '-e', cmd_string])
                        break
                    except (FileNotFoundError, subprocess.SubprocessError):
                        continue
            
            self.SetStatusText(f"    Launched {file_name} in terminal with arguments")
        except Exception as e:
            wx.MessageBox(f"Error launching in terminal: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
            self.SetStatusText(f"    Error launching {file_name}")

    def OnFileOpen(self, event):
        """Opens a file in the current directory"""
        file_name = self.file_list.GetStringSelection()
        if file_name:
            if file_name == "xedix.xcfg" or file_name == "theme.xcfg":
                self.SetTitle("Customizing XediX")
                time.sleep(20)
                self.SetTitle("XediX - Text Editor")
            if file_name.endswith(".exe") or file_name.endswith(".bat") or file_name.endswith(".sh") or file_name.endswith(".msi"):
                # Add dialog to determine how to handle the executable
                dialog = wx.Dialog(self, title="Executable File Options", size=(400, 250))
                panel = wx.Panel(dialog)
                vbox = wx.BoxSizer(wx.VERTICAL)
                
                # Add descriptive text
                desc = wx.StaticText(panel, label=f"Selected executable: {file_name}\nHow would you like to proceed?")
                vbox.Add(desc, flag=wx.ALL|wx.EXPAND, border=10)
                
                # Add buttons
                btn_sizer = wx.BoxSizer(wx.VERTICAL)
                
                run_cli_btn = wx.Button(panel, label="Run in Terminal")
                run_args_btn = wx.Button(panel, label="Run with Arguments")
                run_admin_btn = wx.Button(panel, label="Run as Administrator")
                scan_virus_btn = wx.Button(panel, label="Scan for Viruses")
                cancel_btn = wx.Button(panel, label="Cancel")
                
                btn_sizer.Add(run_cli_btn, flag=wx.EXPAND|wx.BOTTOM, border=5)
                btn_sizer.Add(run_args_btn, flag=wx.EXPAND|wx.BOTTOM, border=5)
                btn_sizer.Add(run_admin_btn, flag=wx.EXPAND|wx.BOTTOM, border=5)
                btn_sizer.Add(scan_virus_btn, flag=wx.EXPAND|wx.BOTTOM, border=5)
                btn_sizer.Add(cancel_btn, flag=wx.EXPAND)
                
                vbox.Add(btn_sizer, flag=wx.ALL|wx.CENTER|wx.EXPAND, border=10)
                panel.SetSizer(vbox)
                
                # Bind events
                run_cli_btn.Bind(wx.EVT_BUTTON, lambda evt, f=file_name: (self.RunInTerminal(f), dialog.EndModal(wx.ID_OK)))
                run_args_btn.Bind(wx.EVT_BUTTON, lambda evt, f=file_name: (self.RunInTerminalWithArgs(f), dialog.EndModal(wx.ID_OK)))
                run_admin_btn.Bind(wx.EVT_BUTTON, lambda evt, f=file_name: (self.RunWithAdminPrivileges(f), dialog.EndModal(wx.ID_OK)))
                scan_virus_btn.Bind(wx.EVT_BUTTON, lambda evt, f=file_name: (self.ScanForViruses(f), dialog.EndModal(wx.ID_OK)))
                cancel_btn.Bind(wx.EVT_BUTTON, lambda evt: dialog.EndModal(wx.ID_CANCEL))
                
                # Show dialog
                dialog.ShowModal()
                dialog.Destroy()
                return  # Skip the rest of the file opening procedure for executables
            self.SetTitle(f"XediX - Text Editor - editing {file_name}")
            file_path = os.path.join(os.getcwd(), file_name)
            try:
                with open(file_path, 'r') as file:
                    content = file.read()
            except UnicodeDecodeError:
                try:
                    # If UTF-8 fails, try with a more permissive encoding
                    with open(file_path, 'r', encoding='latin-1') as file:
                        content = file.read()
                except Exception as e:
                    wx.MessageBox(f"Error reading file: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
                    return
            except Exception as e:
                wx.MessageBox(f"Error reading file: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
                return


            if not self.notebook.IsShown():
                # Hide, message and default screen
                self.default_message.Hide()
                self.main_panel.Hide()
                splitter = self.main_panel.GetParent()
                splitter.ReplaceWindow(self.main_panel, self.notebook)
                self.notebook.Show()
                self.notebook.SetBackgroundColour("#ffffff00")
                self.notebook.SetWindowStyleFlag(wx.NO_BORDER)


            tab = wx.Panel(self.notebook)
            editor_splitter = wx.SplitterWindow(tab)

            text_area = stc.StyledTextCtrl(editor_splitter, style=wx.TE_MULTILINE)
            text_area.SetText(content)
            text_area.SetTabWidth(4)
            text_area.SetWindowStyleFlag(wx.NO_BORDER)

            # Set up optimal coding font
            if wx.Platform == '__WXMSW__':  # Windows
                font_face = "Consolas"
            elif wx.Platform == '__WXMAC__':  # macOS
                font_face = "Menlo"
            else:                            # Linux and others
                font_face = "DejaVu Sans Mono"

            # Apply font settings to all styles
            text_area.StyleSetFont(stc.STC_STYLE_DEFAULT, 
            wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, 
            wx.FONTWEIGHT_NORMAL, False, font_face))
            text_area.StyleClearAll()  # Apply to all styles

            # Additional text rendering settings
            text_area.SetUseTabs(False)  # Use spaces instead of tabs
            text_area.SetViewWhiteSpace(stc.STC_WS_INVISIBLE)  # Hide whitespace markers
            text_area.SetViewEOL(False)  # Hide EOL markers
            text_area.SetCaretWidth(2)  # Slightly wider caret for better visibility

            # Create minimap
            minimap = stc.StyledTextCtrl(editor_splitter, style=wx.TE_MULTILINE | wx.TE_READONLY)
            minimap.SetText(content)
            minimap.SetZoom(-8)  # Make the text very small
            minimap.SetWindowStyleFlag(wx.NO_BORDER)
            minimap.SetMarginWidth(1, 0)  # Hide line numbers in minimap
            minimap.SetEditable(False)

            # Set minimap width
            minimap.SetMinSize((100, -1))
            minimap.SetMaxSize((100, -1))

            # Split the window
            editor_splitter.SplitVertically(text_area, minimap)
            editor_splitter.SetSashGravity(0.85)  # Set main editor to take up most space

            # Sync scrolling between main editor and minimap
            def on_scroll(event):
                first_visible_line = text_area.GetFirstVisibleLine()
                minimap.ScrollToLine(first_visible_line)
                event.Skip()

            text_area.Bind(wx.stc.EVT_STC_UPDATEUI, on_scroll)

            # Sync content changes
            def on_text_change(event):
                minimap.SetText(text_area.GetText())
                event.Skip()

            text_area.Bind(wx.stc.EVT_STC_CHANGE, on_text_change)
            text_area.SetText(content)
            text_area.SetTabWidth(4)
            text_area.SetWindowStyleFlag(wx.NO_BORDER)
            
            # Update Discord RPC only if it's initialized and connected
            try:
                if self.RPC:
                    self.RPC.update(
                        state="XediX",
                        details=f"Editing {file_name}",
                        large_image="xedix_logo",
                        large_text="XediX",
                        small_text="XediX"
                    )
            except Exception as e:
                print(f"Could not update Discord status: {e}")
                self.RPC = None  # Reset RPC if connection is lost

            self.SetStatusText(f"    Opened file: {file_name}")

            # Bind a key event to trigger autocomplete after typing
            text_area.Bind(wx.EVT_CHAR, self.OnChar)

            # Set theme colors for the entire control
            for text_area in (text_area, minimap):
                try:
                    with open("theme.xcfg", 'r') as file:
                        theme_content = file.read().strip()
                        
                    # Check if theme content is JSON
                    if theme_content.startswith('{'):
                        theme_data = json.loads(theme_content)
                        dark_bg_color = theme_data.get('background', "#1B1F2B")
                        light_text_color = theme_data.get('foreground', "#FFFFFF")
                        cmt_color = theme_data.get('comment', "#68C147")
                        keyword_color = theme_data.get('keyword', "#569CD6")
                        string_color = theme_data.get('string', "#BA9EFE")
                        number_color = theme_data.get('number', "#FFDD54")
                        operator_color = theme_data.get('operator', "#D4D4D4")
                        line_number_bg = theme_data.get('lineNumberBg', dark_bg_color)
                    else:
                        theme = theme_content
                        if theme == "dark":
                            dark_bg_color = "#1B1F2B"
                            light_text_color = "#FFFFFF"
                            cmt_color = "#68C147"
                            keyword_color = "#569CD6"
                            string_color = "#BA9EFE"
                            number_color = "#FFDD54"
                            operator_color = "#D4D4D4"
                        elif theme == "light":
                            dark_bg_color = "#FFFFFF"
                            light_text_color = "#000000"
                            cmt_color = "#008000"
                            keyword_color = "#0000FF"
                            string_color = "#A31515"
                            number_color = "#098658"
                            operator_color = "#000000"
                        elif theme == "night":
                            dark_bg_color = "#2f3139"
                            light_text_color = "#FFFFFF"
                            cmt_color = "#eab676"
                            keyword_color = "#569CD6"
                            string_color = "#BA9EFE"
                            number_color = "#FFDD54"
                            operator_color = "#D4D4D4"
                        elif theme == "obsidian":
                            dark_bg_color = "#212232"
                            light_text_color = "#FFFFFF"
                            cmt_color = "#EFC3CA"
                            keyword_color = "#569CD6"
                            string_color = "#BA9EFE"
                            number_color = "#FFDD54"
                            operator_color = "#D4D4D4"
                        elif theme == "solarized-light":
                            dark_bg_color = "#FDF6E3"
                            light_text_color = "#657B83"
                            cmt_color = "#93A1A1"
                            keyword_color = "#859900"
                            string_color = "#2AA198"
                            number_color = "#D33682"
                            operator_color = "#586E75"
                        elif theme == "solarized-dark":
                            dark_bg_color = "#002B36"
                            light_text_color = "#839496"
                            cmt_color = "#586E75"
                            keyword_color = "#859900"
                            string_color = "#2AA198"
                            number_color = "#D33682"
                            operator_color = "#93A1A1"
                        elif theme == "github-dark":
                            dark_bg_color = "#0D1117"
                            light_text_color = "#C9D1D9"
                            cmt_color = "#8B949E"
                            keyword_color = "#FF7B72"
                            string_color = "#A5D6FF"
                            number_color = "#79C0FF"
                            operator_color = "#C9D1D9"
                        elif theme == "github-dimmed":
                            dark_bg_color = "#22272E"
                            light_text_color = "#ADBAC7"
                            cmt_color = "#768390"
                            keyword_color = "#F47067"
                            string_color = "#96D0FF"
                            number_color = "#6CB6FF"
                            operator_color = "#ADBAC7"
                        elif theme == "github-light":
                            dark_bg_color = "#FFFFFF"
                            light_text_color = "#24292F"
                            cmt_color = "#6E7781"
                            keyword_color = "#CF222E"
                            string_color = "#0A3069"
                            number_color = "#0550AE"
                            operator_color = "#24292F"
                        
                        extension_themes.main()

                        line_number_bg = dark_bg_color

                except Exception as e:
                    print(f"Error loading theme: {e}")
                    # Default fallback colors
                    dark_bg_color = "#1B1F2B"
                    light_text_color = "#FFFFFF"
                    cmt_color = "#68C147"
                    keyword_color = "#569CD6"
                    string_color = "#BA9EFE"
                    number_color = "#FFDD54"
                    operator_color = "#D4D4D4"
                    line_number_bg = dark_bg_color

                text_area.StyleSetBackground(stc.STC_STYLE_DEFAULT, dark_bg_color)
                text_area.StyleSetForeground(stc.STC_STYLE_DEFAULT, light_text_color)
                text_area.StyleClearAll()

                if file_name.endswith(".py"):
                    self.SetStatusText("     Current languague: Python", 1)
                    text_area.SetLexer(stc.STC_LEX_PYTHON)
                    text_area.StyleSetSpec(stc.STC_P_COMMENTLINE, f"fore:{cmt_color},italic,back:{dark_bg_color}")
                    text_area.StyleSetSpec(stc.STC_P_STRING, f"fore:{string_color},italic,back:{dark_bg_color}")
                    text_area.StyleSetSpec(stc.STC_P_WORD, f"fore:{keyword_color},bold,back:{dark_bg_color}")
                    text_area.SetKeyWords(0, "def class return if else elif import from as not is try except finally for while in with pass lambda")
                    text_area.StyleSetSpec(stc.STC_P_IDENTIFIER, f"fore:{light_text_color},italic,back:{dark_bg_color}")
                    text_area.StyleSetSpec(stc.STC_P_OPERATOR, f"fore:{operator_color},bold,back:{dark_bg_color}")
                    text_area.StyleSetSpec(stc.STC_P_NUMBER, f"fore:{number_color},italic,back:{dark_bg_color}")
                    text_area.StyleSetSpec(stc.STC_P_DECORATOR, f"fore:{keyword_color},italic,back:{dark_bg_color}")

                    # Strings
                    text_area.StyleSetSpec(stc.STC_P_STRING, f"fore:{string_color},back:{dark_bg_color}")  # Regular strings
                    text_area.StyleSetSpec(stc.STC_P_CHARACTER, f"fore:#FF79C6,bold,back:{dark_bg_color}")  # Character strings (we'll use this for prefixed strings)
                    text_area.StyleSetSpec(stc.STC_P_TRIPLE, f"fore:{string_color},back:{dark_bg_color}")  # Triple quotes
                    text_area.StyleSetSpec(stc.STC_P_TRIPLEDOUBLE, f"fore:{string_color},back:{dark_bg_color}")  # Triple double quotes
                    text_area.StyleSetSpec(stc.STC_P_DEFNAME, f"fore:#50FA7B,back:{dark_bg_color}")

                    # Keywords
                    text_area.StyleSetSpec(stc.STC_P_WORD, f"fore:#569CD6,bold,back:{dark_bg_color}")
                    text_area.SetKeyWords(0,
                                        "def class return if else elif import from as not is try except finally for while in with pass lambda")
                    
                    # Functions and variables
                    text_area.StyleSetSpec(stc.STC_P_IDENTIFIER, f"fore:#7BCCE1,italic,back:{dark_bg_color}")
                    
                    # Operators
                    text_area.StyleSetSpec(stc.STC_P_OPERATOR, f"fore:#D4D4D4,bold,back:{dark_bg_color}")
                    
                    # Numbers
                    text_area.StyleSetSpec(stc.STC_P_NUMBER, f"fore:#FFDD54,italic,back:{dark_bg_color}")
                    
                    # Decorators
                    text_area.StyleSetSpec(stc.STC_P_DECORATOR, f"fore:#C586C0,italic,back:{dark_bg_color}")
                    
                elif file_name.endswith(".html"):
                    self.SetStatusText("    Current languague: HTML", 1)
                    # Set up HTML syntax highlighting
                    text_area.SetLexer(stc.STC_LEX_HTML)
                    
                    # Tags
                    text_area.StyleSetSpec(stc.STC_H_TAG, f"fore:#569CD6,bold,back:{dark_bg_color}")
                    
                    # Attributes
                    text_area.StyleSetSpec(stc.STC_H_ATTRIBUTE, f"fore:#D69D85,italic,back:{dark_bg_color}")
                    
                    # Attribute values
                    text_area.StyleSetSpec(stc.STC_H_VALUE, f"fore:#BA9EFE,italic,back:{dark_bg_color}")
                    
                    # Comments
                    text_area.StyleSetSpec(stc.STC_H_COMMENT,  f"fore:{cmt_color},italic,back:{dark_bg_color}")
                    
                    # Entities
                    text_area.StyleSetSpec(stc.STC_H_ENTITY, f"fore:#FFDD54,italic,back:{dark_bg_color}")
                    
                    # Numbers
                    text_area.StyleSetSpec(stc.STC_H_NUMBER, f"fore:#FFDD54,italic,back:{dark_bg_color}")
                    
                    # Operators (like '=')
                    text_area.StyleSetSpec(stc.STC_H_OTHER, f"fore:#D4D4D4,bold,back:{dark_bg_color}")
                    
                elif file_name.endswith(".json"):
                    self.SetStatusText("    JSON", 1)
                    # Set up JSON syntax highlighting
                    text_area.SetLexer(stc.STC_LEX_JSON)
                    
                    # Strings (e.g., "key" or "value")
                    text_area.StyleSetSpec(stc.STC_JSON_STRING, f"fore:#BA9EFE,italic,back:{dark_bg_color}")
                    
                    # Numbers (e.g., 123, 3.14)
                    text_area.StyleSetSpec(stc.STC_JSON_NUMBER, f"fore:#FFDD54,back:{dark_bg_color}")
                    
                    # Colons (e.g., in "key": "value")
                    text_area.StyleSetSpec(stc.STC_JSON_OPERATOR, f"fore:#D4D4D4,bold,back:{dark_bg_color}")
                    
                    # Keywords (e.g., true, false, null)
                    text_area.StyleSetSpec(stc.STC_JSON_KEYWORD, f"fore:#68C147,bold,back:{dark_bg_color}")
                elif file_name.endswith(".css"):
                    self.SetStatusText("    Current languague: CSS", 1)
                    # Set up CSS syntax highlighting
                    text_area.SetLexer(stc.STC_LEX_CSS)
                    
                    # Default text
                    text_area.StyleSetSpec(stc.STC_CSS_DEFAULT, f"fore:#D4D4D4,back:{dark_bg_color}")
                    
                    # Comments (e.g., /* This is a comment */)
                    text_area.StyleSetSpec(stc.STC_CSS_COMMENT,  f"fore:{cmt_color},italic,back:{dark_bg_color}")
                    
                    # Tag Names (e.g., body, h1, div)
                    text_area.StyleSetSpec(stc.STC_CSS_TAG, f"fore:#569CD6,bold,back:{dark_bg_color}")
                    
                    # Class and IDs (e.g., .className, #idName)
                    text_area.StyleSetSpec(stc.STC_CSS_CLASS, f"fore:#7BCCE1,italic,back:{dark_bg_color}")
                    text_area.StyleSetSpec(stc.STC_CSS_ID, f"fore:#FFAA33,italic,back:{dark_bg_color}")
                    
                    # Attributes (e.g., color, margin, padding)
                    text_area.StyleSetSpec(stc.STC_CSS_ATTRIBUTE, f"fore:#BA9EFE,bold,back:{dark_bg_color}")
                    
                    # Pseudo-classes and Elements (e.g., :hover, ::before)
                    text_area.StyleSetSpec(stc.STC_CSS_PSEUDOCLASS, f"fore:#C586C0,italic,back:{dark_bg_color}")
                    text_area.StyleSetSpec(stc.STC_CSS_PSEUDOELEMENT, f"fore:#C586C0,italic,back:{dark_bg_color}")
                    
                    # Property Values (e.g., red, 10px, 1em)
                    text_area.StyleSetSpec(stc.STC_CSS_VALUE, f"fore:#FFDD54,back:{dark_bg_color}")
                    
                    # Operators (e.g., :, ;, {, })
                    text_area.StyleSetSpec(stc.STC_CSS_OPERATOR, f"fore:#D4D4D4,bold,back:{dark_bg_color}")
                    
                    # Import Statement (e.g., @import)
                    text_area.StyleSetSpec(stc.STC_CSS_DIRECTIVE, f"fore:#68C147,bold,back:{dark_bg_color}")
                    
                elif file_name.endswith(".js"):
                    self.SetStatusText("    Current languague: Javascript", 1)
                    # Set up JavaScript syntax highlighting
                    text_area.SetLexer(stc.STC_LEX_ESCRIPT)
                    
                    # Default text
                    text_area.StyleSetSpec(stc.STC_ESCRIPT_DEFAULT, f"fore:#D4D4D4,back:{dark_bg_color}")
                    
                    # Comments (e.g., // This is a comment, /* multi-line */)
                    text_area.StyleSetSpec(stc.STC_ESCRIPT_COMMENT,  f"fore:{cmt_color},italic,back:{dark_bg_color}")
                    text_area.StyleSetSpec(stc.STC_ESCRIPT_COMMENTLINE, f"fore:{cmt_color},italic,back:{dark_bg_color}")
                    text_area.StyleSetSpec(stc.STC_ESCRIPT_COMMENTDOC, f"fore:{cmt_color},italic,back:{dark_bg_color}")
                    
                    # Keywords (e.g., var, let, const, function)
                    text_area.StyleSetSpec(stc.STC_ESCRIPT_WORD, f"fore:#569CD6,bold,back:{dark_bg_color}")
                    
                    # Strings (e.g., "text", 'text', `template literal`)
                    text_area.StyleSetSpec(stc.STC_ESCRIPT_STRING, f"fore:#BA9EFE,italic,back:{dark_bg_color}")
                    
                    # Numbers (e.g., 123, 3.14, 0xFF)
                    text_area.StyleSetSpec(stc.STC_ESCRIPT_NUMBER, f"fore:#FFDD54,back:{dark_bg_color}")
                    
                    # Identifiers (e.g., variables, function names)
                    text_area.StyleSetSpec(stc.STC_ESCRIPT_IDENTIFIER, f"fore:#D4D4D4,back:{dark_bg_color}")
                    
                    # Operators (e.g., =, +, -, *, /, &&, ||)
                    text_area.StyleSetSpec(stc.STC_ESCRIPT_OPERATOR, f"fore:#D4D4D4,bold,back:{dark_bg_color}")
                    
                    # Set JavaScript Keywords
                    text_area.SetKeyWords(0, "var let const function return if else for while do break continue switch case default try catch throw new this super class extends export import async await typeof instanceof delete")

                # Default style
                text_area.StyleSetSpec(stc.STC_P_DEFAULT, f"fore:{light_text_color},italic,back:{dark_bg_color}")

                # Adjust indentation guides
                text_area.SetIndentationGuides(True)
                # Set line number background
                text_area.StyleSetSpec(stc.STC_STYLE_LINENUMBER, f"fore:{light_text_color},back:{line_number_bg}")
                text_area.SetMarginType(1, stc.STC_MARGIN_NUMBER)
                text_area.SetMarginWidth(1, 30)

            tab_sizer = wx.BoxSizer(wx.VERTICAL)
            tab_sizer.Add(editor_splitter, proportion=1, flag=wx.EXPAND)
            tab.SetSizer(tab_sizer)

            self.notebook.AddPage(tab, file_name)

    def OnNewFile(self, event):
        filename = wx.TextEntryDialog(self, "File name:")
        fileext = wx.TextEntryDialog(self, "File extension (without the dot):")
        if filename.ShowModal() == wx.ID_OK:
            filename_value = filename.GetValue()
            if not filename_value:
                wx.MessageBox("File name cannot be empty.", "Error", wx.OK | wx.ICON_ERROR)
                return
            if fileext.ShowModal() == wx.ID_OK:
                fileext_value = fileext.GetValue()
                if not fileext_value:
                    errordialog = wx.MessageBox("File extension cannot be empty. If you want to create a file without a file extension, click OK.", "Error", wx.OK | wx.ICON_ERROR)
                    if errordialog == wx.ID_OK:
                        fileext_value = ""

        # Create an empty file name and open it
        if fileext_value:
            temp_file_path = filename_value + "." + fileext_value
        else:
            temp_file_path = filename_value

        # Check if notebook is hidden and show it
        if not self.notebook.IsShown():
            self.default_message.Hide()
            self.main_panel.Hide()
            splitter = self.main_panel.GetParent()
            splitter.ReplaceWindow(self.main_panel, self.notebook)
            self.notebook.Show()

        # Simulate "opening" an empty file by directly calling OnFileOpen with a file name
        with open(temp_file_path, 'w') as temp_file:
            temp_file.write('')  # Create an empty file

        # Add it to the list box so it can be selected
        self.file_list.Append(temp_file_path)
        self.file_list.SetStringSelection(temp_file_path)

        # Call OnFileOpen to handle everything else
        self.OnFileOpen(None)
        
    def OnRunCode(self, event):
        """Runs the code in the current text area based on file extension"""
        # Get the current tab
        current_tab = self.notebook.GetCurrentPage()
        if current_tab:
            # Get the text area from the splitter window
            editor_splitter = current_tab.GetChildren()[0]  # Get the splitter
            text_area = editor_splitter.GetChildren()[0]  # Get the main editor area
            code = text_area.GetValue()
            file_name = self.notebook.GetPageText(self.notebook.GetSelection())
            file_ext = os.path.splitext(file_name)[1].lower()

            # Start measuring time
            start_time = time.time()

            self.monitoring = True
            self.memory_usage = 0  # Reset memory usage
            self.memory_thread = threading.Thread(target=self.track_memory_usage, daemon=True)
            self.memory_thread.start()

            # Create temp file to execute
            temp_file = f"temp{file_ext}"
            with open(temp_file, 'w') as f:
                f.write(code)

            # Execute based on file extension
            if file_ext == '.py':
                self.process = subprocess.Popen(
                    ['python', temp_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            elif file_ext == '.duck':
                self.process = subprocess.Popen(
                    ['npm run compile -- --run', temp_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            elif file_ext == '.java':
                # Compile first
                compile_process = subprocess.run(['javac', temp_file], capture_output=True, text=True)
                if compile_process.returncode == 0:
                    # Run the compiled class
                    class_name = os.path.splitext(temp_file)[0]
                    self.process = subprocess.Popen(
                        ['java', class_name],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                else:
                    self.process = compile_process
            elif file_ext == '.js':
                self.process = subprocess.Popen(
                    ['node', temp_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            elif file_ext == '.cpp':
                # Compile first
                compile_process = subprocess.run(['g++', temp_file, '-o', 'temp.exe'], capture_output=True, text=True)
                if compile_process.returncode == 0:
                    self.process = subprocess.Popen(
                        ['./temp.exe'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                else:
                    self.process = compile_process
            else:
                wx.MessageBox(f"Unsupported file type: {file_ext}", "Error", wx.OK | wx.ICON_ERROR)
                return

            end_time = time.time()
            overall_time = (end_time - start_time) * 1000 

            # Start a thread to handle output and execution time
            threading.Thread(target=self.HandleExecution, args=(overall_time,), daemon=True).start()

            # Clean up temp files
            try:
                os.remove(temp_file)
                if file_ext == '.java':
                    os.remove(f"{os.path.splitext(temp_file)[0]}.class")
                elif file_ext == '.cpp':
                    os.remove('temp.exe')
            except Exception:
                pass

    def track_memory_usage(self):
        """Track memory usage during code execution."""
        process = psutil.Process()
        while self.monitoring:
            mem_info = process.memory_info()
            self.memory_usage = mem_info.rss / (1024 * 1024)  # Memory in MB
            time.sleep(0.5)  # Update every 0.5 seconds

    def HandleExecution(self, start_time):
        self.monitoring = False  # Stop memory monitoring
        stdout, stderr = self.process.communicate()
        end_time = time.time()
        execution_time = end_time - start_time

        # Capture the return value from stdout
        if stdout.strip():
            self.return_values.append(stdout.strip())  # Store return values

        # Create output dialog if it doesn't exist
        if self.output_window is None:
            self.output_window = wx.Dialog(self, title="Output Window", size=(600, 400))
            pywinstyles.apply_style(self.output_window, "mica")

            # Create output text area
            output_panel = wx.Panel(self.output_window)
            output_vbox = wx.BoxSizer(wx.VERTICAL)
            self.output_text = wx.TextCtrl(output_panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
            output_vbox.Add(self.output_text, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
            output_panel.SetSizer(output_vbox)

            # Create return values panel
            return_panel = wx.Panel(self.output_window)
            return_vbox = wx.BoxSizer(wx.VERTICAL)
            self.return_text = wx.TextCtrl(return_panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
            return_vbox.Add(self.return_text, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
            return_panel.SetSizer(return_vbox)

            # Add panels to main dialog
            main_sizer = wx.BoxSizer(wx.VERTICAL)
            main_sizer.Add(output_panel, 1, wx.EXPAND)
            main_sizer.Add(return_panel, 1, wx.EXPAND)
            self.output_window.SetSizer(main_sizer)

        # Prepare output message
        try:
            output_message = f"Errors:\n{stderr}\n"
            output_message += f"Execution Time: {execution_time:.4f} milliseconds\n"
            output_message += f"Memory Usage: {self.memory_usage:.2f} MB\n"
        except Exception as e:
            output_message = f"An error occurred: {str(e)}"

        # Update the output text area
        self.output_text.SetValue(output_message)

        # Update the return values visualization
        return_visualization = "\n".join(f"Return {i + 1}: {value}" for i, value in enumerate(self.return_values))
        self.return_text.SetValue(return_visualization)

        # Export output to HTML log file
        log_filename = "execution_log.html"
        self.export_to_html(log_filename, output_message, return_visualization)

        # Show the output dialog modally
        self.output_window.ShowModal()  # Show the output dialog modally

    def export_to_html(self, log_filename, output_message, return_visualization):
        """Export the output and return values to an HTML log file."""
        html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Log</title>
            </head>
            <body>
                <h1>Execution Log</h1>
                <h2>Output</h2>
                <pre>{output_message}</pre>
                <h2>Return Values</h2>
                <pre>{return_visualization}</pre>
            </body>
            </html>
            """

        # Save the HTML content to a file
        with open(log_filename, 'w') as log_file:
            log_file.write(html_content)

        self.SetStatusText(f"Saved execution log to: {log_filename}")

    def OnSave(self, event):
        current_tab = self.notebook.GetCurrentPage()
        if current_tab:
            # Get the correct text area from the splitter window
            editor_splitter = current_tab.GetChildren()[0]  # Get the splitter
            text_area = editor_splitter.GetChildren()[0]  # Get the main editor area
            content = text_area.GetValue()
            file_name = self.notebook.GetPageText(self.notebook.GetSelection())
            
            # Update Discord RPC only if it's initialized and connected
            try:
                if self.RPC:
                    self.RPC.update(
                        state="XediX",
                        details=f"Editing {file_name}",
                        large_image="xedix_logo",
                        large_text="XediX",
                        small_text="XediX"
                    )
            except Exception as e:
                print(f"Could not update Discord status: {e}")
                self.RPC = None  # Reset RPC if connection is lost

            # Add syntax checking for Python files
            if file_name.endswith('.py'):
                # Check syntax before saving
                if not hasattr(text_area, 'syntax_checker'):
                    text_area.syntax_checker = error_checker.SyntaxChecker(text_area)
                
                # Run syntax check
                text_area.syntax_checker.check_syntax()

            if file_name == "Untitled":
                # Handle saving as a new file
                save_dialog = wx.FileDialog(self, "Save File", "", "", wildcard="Python files (*.py)|*.py",
                                        style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
                if save_dialog.ShowModal() == wx.ID_OK:
                    file_name = save_dialog.GetPath()
                    with open(file_name, 'w') as file:
                        file.write(content)
                    self.notebook.SetPageText(self.notebook.GetSelection(), os.path.basename(file_name))
            else:
                # Overwrite the opened file
                with open(file_name, 'w') as file:
                    file.write(content)

    def OnChar(self, event):
        """Handle character input events including dynamic auto-completion and bracket matching."""
        self.SetStatusText("    Character pressed", 2)
        self.SetStatusText("    Showing recommendations")
        
        current_tab = self.notebook.GetCurrentPage()
        if current_tab:
            editor_splitter = current_tab.GetChildren()[0]
            text_area = editor_splitter.GetChildren()[0]
            key_code = event.GetKeyCode()
            try:
                # Auto-close brackets
                if chr(key_code) in self.matching_brackets:
                    pos = text_area.GetCurrentPos()
                    text_area.InsertText(pos, self.matching_brackets[chr(key_code)])
                    text_area.SetCurrentPos(pos)
                    text_area.SetSelection(pos, pos)

                if chr(key_code).isalpha() or key_code == ord('.'):
                    pos = text_area.GetCurrentPos()
                    word_start_pos = text_area.WordStartPosition(pos, True)
                    current_word = text_area.GetTextRange(word_start_pos, pos)
                    length = pos - word_start_pos

                    if length >= 0 or key_code == ord('.'):
                        # Get all words from current document
                        full_text = text_area.GetText()
                        words = set()
                        
                        # Extract words (including function names and variables)
                        import re
                        pattern = r'\b[a-zA-Z_]\w*\b'
                        words.update(re.findall(pattern, full_text))
                        
                        # Add relevant Python builtins based on context
                        python_completions = []
                        if key_code == ord('.'):
                            # Method suggestions after dot
                            python_completions = [
                                "append", "extend", "pop", "remove", "clear", "copy", 
                                "count", "index", "insert", "reverse", "sort", "update",
                                "keys", "values", "items", "get", "strip", "split", 
                                "join", "replace", "upper", "lower", "title"
                            ]
                        else:
                            # General Python functions and keywords
                            python_completions = [
                                "def", "class", "import", "from", "return", "raise",
                                "try", "except", "finally", "with", "as", "if", "elif",
                                "else", "for", "while", "break", "continue", "pass",
                                "print", "len", "range", "enumerate", "zip", "dict",
                                "list", "set", "tuple", "str", "int", "float", "bool",
                                "True", "False", "None", "self", "super"
                            ]

                        # Combine and sort completions
                        all_completions = sorted(list(words) + python_completions)
                        
                        # Filter by current word if any
                        if current_word:
                            all_completions = [w for w in all_completions if w.startswith(current_word)]
                        
                        # Show autocompletion if we have suggestions
                        if all_completions:
                            completions = " ".join(all_completions)
                            text_area.AutoCompShow(len(current_word), completions)

                        self.OnSave(wx.EVT_CHAR)
                        self.SetStatusText("    Autosaved", 2)
            except Exception as e:
                self.SetStatusText(f"    Error running onchar: {str(e)}", 2)

        event.Skip()  # Continue processing other key events
        
    def OnExit(self, event):
        self.SetStatusText("    Exiting XediX...")
        time.sleep(1)
        self.Close()

    def OnCut(self, event):
        current_tab = self.notebook.GetCurrentPage()
        if current_tab:
            text_area = current_tab.GetChildren()[0]
            text_area.Cut()

    def OnCopy(self, event):
        current_tab = self.notebook.GetCurrentPage()
        if current_tab:
            text_area = current_tab.GetChildren()[0]
            text_area.Copy()

    def OnPaste(self, event):
        current_tab = self.notebook.GetCurrentPage()
        if current_tab:
            text_area = current_tab.GetChildren()[0]
            text_area.Paste()

    extension_mainclass.main()

def main():
    """Defines the main process."""
    app = wx.App(False)
    frame = TextEditor(None)

    # Handle command line arguments
    args = sys.argv[1:]

    if args:
        # Show the frame first so everything is initialized
        frame.Show()
        if args[0] == "--open-folder":
            if len(args) > 1:
                # Get the folder path and change to it
                folder_path = args[1].strip('"')  # Remove any quotes
                frame.OnOpenFolder(folder_path)
        else:
            # Assume it's a file path
            file_path = args[0].strip('"')  # Remove any quotes
            
            # Change to the directory containing the file
            dir_path = os.path.dirname(os.path.abspath(file_path))
            os.chdir(dir_path)

            # Update file list and open the file
            frame.PopulateFileList()
            frame.file_list.SetStringSelection(os.path.basename(file_path))
            frame.OnFileOpen(None)

    else:
        frame.Show()
    try:
        extension_mainfn.main()
    except Exception:
        print("No mainfn extension file found.")

    app.MainLoop()
    
    try:
        with open("repo.ghicfg", "r") as file:
            content = file.read()
            if content:
                github.main()

    except FileNotFoundError:
        pass

if __name__ == '__main__':
    """Runs the main process."""
    main()
