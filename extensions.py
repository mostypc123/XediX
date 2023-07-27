import tkinter as tk
import sqlite3
import subprocess

# Funkcia na spustenie Python kódu
def run_python_code(code):
    try:
        exec(code)
    except Exception as e:
        print(f"Chyba pri spúšťaní Python kódu: {e}")

# Funkcia na spustenie Java kódu
def run_java_code(code):
    try:
        subprocess.run(['java', code], capture_output=True, text=True)
    except Exception as e:
        print(f"Chyba pri spúšťaní Java kódu: {e}")

# Funkcia pre pridanie nového rozšírenia do databázy
def add_extension():
    name = entry_name.get()
    code = text_code.get("1.0", tk.END).strip()
    ext_type = var.get()

    if name and code:
        conn = sqlite3.connect('extensions.db')
        c = conn.cursor()
        c.execute("INSERT INTO extensions (name, code, type) VALUES (?, ?, ?)", (name, code, ext_type))
        conn.commit()
        conn.close()
        refresh_extension_list()
        entry_name.delete(0, tk.END)
        text_code.delete("1.0", tk.END)
        var.set("python")

# Funkcia pre spustenie rozšírenia podľa názvu
def run_extension():
    name = listbox_extensions.get(listbox_extensions.curselection())
    conn = sqlite3.connect('extensions.db')
    c = conn.cursor()

    c.execute("SELECT code, type FROM extensions WHERE name=?", (name,))
    result = c.fetchone()

    if result:
        code, ext_type = result
        if ext_type == 'python':
            run_python_code(code)
        elif ext_type == 'java':
            run_java_code(code)
    else:
        print("Rozšírenie s týmto názvom neexistuje.")

    conn.close()

# Funkcia na získanie zoznamu existujúcich rozšírení
def refresh_extension_list():
    conn = sqlite3.connect('extensions.db')
    c = conn.cursor()

    c.execute("SELECT name FROM extensions")
    extensions = c.fetchall()

    listbox_extensions.delete(0, tk.END)
    for extension in extensions:
        listbox_extensions.insert(tk.END, extension[0])

    conn.close()

# Vytvorenie databázy a tabuľky, ak neexistujú
conn = sqlite3.connect('extensions.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS extensions
             (name TEXT, code TEXT, type TEXT)''')
conn.commit()
conn.close()

# GUI
root = tk.Tk()
root.title("Aplikácia s rozšíreniami")

frame_add_extension = tk.Frame(root)
frame_add_extension.pack(padx=10, pady=10)

label_name = tk.Label(frame_add_extension, text="Zadajte názov rozšírenia:")
label_name.grid(row=0, column=0, sticky=tk.W)

entry_name = tk.Entry(frame_add_extension)
entry_name.grid(row=0, column=1, padx=5, pady=5)

label_code = tk.Label(frame_add_extension, text="Zadajte kód rozšírenia:")
label_code.grid(row=1, column=0, sticky=tk.W)

text_code = tk.Text(frame_add_extension, height=10, width=50)
text_code.grid(row=1, column=1, padx=5, pady=5)

label_type = tk.Label(frame_add_extension, text="Typ rozšírenia:")
label_type.grid(row=2, column=0, sticky=tk.W)

var = tk.StringVar(value="python")
radio_python = tk.Radiobutton(frame_add_extension, text="Python", variable=var, value="python")
radio_python.grid(row=2, column=1, sticky=tk.W)

radio_java = tk.Radiobutton(frame_add_extension, text="Java", variable=var, value="java")
radio_java.grid(row=2, column=1, sticky=tk.E)

button_add_extension = tk.Button(frame_add_extension, text="Pridať rozšírenie", command=add_extension)
button_add_extension.grid(row=3, columnspan=2, pady=10)

frame_extension_list = tk.Frame(root)
frame_extension_list.pack(padx=10, pady=10)

listbox_extensions = tk.Listbox(frame_extension_list, selectmode=tk.SINGLE, width=30)
listbox_extensions.pack(side=tk.LEFT, padx=5)

scrollbar = tk.Scrollbar(frame_extension_list, command=listbox_extensions.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

listbox_extensions.config(yscrollcommand=scrollbar.set)

button_run_extension = tk.Button(root, text="Spustiť vybrané rozšírenie", command=run_extension)
button_run_extension.pack(pady=10)

# Aktualizujte zoznam rozšírení pri spustení aplikácie
refresh_extension_list()

root.mainloop()
