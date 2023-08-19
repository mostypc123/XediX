import tkinter as tk
from pylint import epylint as lint
from tkinter import messagebox

def test_save_text():
    with open("my_code.py", "w") as file:
        code = text_box.get("1.0", "end-1c")
        file.write(code)

def test_check_code():
    code = text_box.get("1.0", "end-1c")
    (pylint_stdout, pylint_stderr) = lint.py_run(code, return_std=True)

    # Zobrazenie chýb v Textboxe
    output = pylint_stdout.getvalue()
    messagebox.showerror("errors",output)
    

root = tk.Tk()
root.title("Text Editor")

text_box = tk.Text(root, wrap="word")
text_box.pack(expand=True, fill="both")

save_button = tk.Button(root, text="Save", command=test_save_text)
save_button.pack()

check_button = tk.Button(root, text="Check Code", command=test_check_code)
check_button.pack()

root.mainloop()
