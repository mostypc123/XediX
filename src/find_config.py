import os

def main():
    current_dir = os.getcwd()
    root_dir = os.path.abspath(os.sep)

    while True:
        potential_path = os.path.join(current_dir, ".xedix")
        if os.path.isdir(potential_path):
            return potential_path

        if current_dir == root_dir:
            return None

        current_dir = os.path.dirname(current_dir)
        return current_dir
print("XediX Config Path:", main())