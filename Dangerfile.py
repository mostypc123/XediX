import danger
from danger import markdown, warn, fail, message

# --- Rule 1: Editing Python files ---
if danger.git.modified_files.match("**/*.py"):
    files = danger.git.modified_files
    for file in files:
        with open(file) as f:
            content = f.read()
            if 'pyinstaller' not in content:
                warn(f"Consider ensuring this code works with PyInstaller in {file}.")
    markdown("Ensure original style is maintained.")

# --- Rule 2: Editing Markdown files ---
if danger.git.modified_files.match("**/*.md"):
    files = danger.git.modified_files
    for file in files:
        with open(file) as f:
            content = f.read()
            # Ensure Markdown files are clean but avoid grammar fixes
            if "grammar" in content.lower():
                message(f"Grammar fixes are not a high priority for {file}. Make sure to keep the structure clean.")

# --- Rule 3: Editing .iss files ---
if danger.git.modified_files.match("**/*.iss"):
    fail("Editing .iss files is not allowed.")

# --- Rule 4: Editing GitHub Action (.yml) workflows ---
if danger.git.modified_files.match("**/*.yml"):
    files = danger.git.modified_files
    for file in files:
        if file.endswith('.yml'):
            # Ensure the workflow file runs correctly (You can extend this with specific checks)
            message(f"Make sure the workflow in {file} works properly, as it is a GitHub Action.")

# --- Rule 5: Editing PNG files ---
if danger.git.modified_files.match("**/*.png"):
    message("Editing PNG files is not allowed unless the image is just too good.")
