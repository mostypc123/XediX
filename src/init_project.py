import main
import os


def xedix_init():
    current_dir = main.TextEditor().current_dir

    # Change directory using os.system
    os.system(f'cd "{current_dir}"')

    # Also change the Python script's working directory
    os.chdir(current_dir)

    # Create XediX Config files
    with open("theme.xcfg", "w") as f:
        f.write("dark")

    with open("xedix.xcfg", "w") as f:
        f.write("headerActive:#EDF0F2;")
        f.write("headerInactive:#b3d0e4;")

    # Create a Gthub Integration Config file
    with open("repo.ghicfg", "w") as f:
        f.write("")


def python_init():
    with open("requirements.txt", "w") as f:
        f.write("")


def git_init():
    with open(".gitignore", "w") as f:
        f.write("execution_log.html")

    os.system("git init")
