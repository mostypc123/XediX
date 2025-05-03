import sys
import os
import subprocess
import tempfile
import shutil
import json

# Dictionary of available extensions with their GitHub repositories
EXTENSION_REPOS = {
    "test": "mostypc123/xedix-test-extension"
}

def get_extension(extension_name):
    """Force interactive path input exactly as user demands"""
    if extension_name not in EXTENSION_REPOS:
        print(f"Extension '{extension_name}' not found")
        list_extensions()
        return

    repo_url = f"https://github.com/{EXTENSION_REPOS[extension_name]}"
    print(f"Installing {extension_name} from {repo_url}")

    temp_dir = tempfile.mkdtemp()
    try:
        # Clone repo
        subprocess.run(
            ["git", "clone", repo_url, temp_dir],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        print("\nYou will be prompted to enter a path of your extension file.")
        subprocess.run(
            [sys.executable, os.path.join(temp_dir, "install.py")],
            stdin=sys.stdin,   # Direct keyboard input
            stdout=sys.stdout, # Direct console output
            stderr=sys.stderr
        )

    except subprocess.CalledProcessError as e:
        print(f"Failed to clone repository: {e.stderr.decode()}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
    finally:
        def del_rw(action, name, exc):
            os.chmod(name, 0o777)
            os.remove(name)
        shutil.rmtree(temp_dir, onerror=del_rw)

def list_extensions():
    """
    List available extensions
    """
    print("Available extensions:")
    for ext, repo in EXTENSION_REPOS.items():
        print(f"  - {ext} ({repo})")

def main():
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "get":
            if len(sys.argv) > 2:
                extension = sys.argv[2]
                get_extension(extension)
            else:
                print("Error: Please specify an extension to install")
                print("Usage: python xepm.py get <extension_name>")
        
        elif command == "list":
            list_extensions()
        
        else:
            print(f"Unknown command: {command}")
            print("Usage: python xepm.py [get|list]")
    else:
        print("Usage: python xepm.py [get|list]")

if __name__ == "__main__":
    main()
