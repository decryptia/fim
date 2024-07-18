import glob
import hashlib
import os
import tkinter as tk
from tkinter.filedialog import askdirectory, asksaveasfilename
import customtkinter as ctk
import time
import threading
from tkinter import simpledialog
import winsound

baseline_dir = ""
folder = ""

name_hash = ""
baseline_path = ""

files_changed = []
files_added = []
files_removed = []
files_all = []

spaces = "                                                                        \n"

# Calculate hash from data in a file
def calcsha512hash(file_name):
    BUF_SIZE = 65536  
    sha = hashlib.sha512()
    
    with open(file_name, 'rb') as file:
        while True:
            data = file.read(BUF_SIZE)
            if not data:
                break
            sha.update(data)
        return sha.hexdigest()

# Calculate hash from name of a file
def calcNameHash(filename):
    md5 = hashlib.md5()
    md5.update(filename.encode())
    return md5.hexdigest()

# Get metadata of a file
def getfilemetadata(file_path):
    file_stats = os.stat(file_path)
    file_size = file_stats.st_size
    creation_time = time.ctime(file_stats.st_ctime)
    modification_time = time.ctime(file_stats.st_mtime)
    return f"Size: {file_size} bytes, Created: {creation_time}, Modified: {modification_time}"

# Updates baseline
def UpdateBaseline(dir, mode):
    if dir == "":
        label3.configure(text="Error: Folder not selected")
    elif baseline_dir == "":
        label3.configure(text="Error: Baseline directory not selected")
    elif os.path.isdir(baseline_dir) == False:
        label3.configure(text="Message: Baseline Folder doesn't exist, so creating it")
        os.makedirs(baseline_dir)
        label3.configure(text="Message: Updating Baseline...")
        UpdateBaselineHelper(dir, mode)
        label3.configure(text="Message: Updated Baseline Successfully")
    else:
        label3.configure(text="Message: Updating Baseline...")
        UpdateBaselineHelper(dir, mode)
        label3.configure(text="Message: Updated Baseline Successfully")

# Update Baseline Helper for [files in a folder] and [files in subfolders]
def UpdateBaselineHelper(dir, mode):
    global name_hash, baseline_path
    if(mode == 'w'):
        name_hash = calcNameHash(dir)
        baseline_path = os.path.join(baseline_dir, (name_hash + '.txt'))
    
    files = [os.path.abspath(f) for f in glob.glob(os.path.join(dir, '*')) if os.path.isfile(f)]
    with open(baseline_path, mode) as baseline:
        for f in files:
            hash = calcsha512hash(os.path.join(dir, f))
            baseline.write(f)
            baseline.write("=")
            baseline.write(str(hash))
            baseline.write("\n")
    
    directories = [d for d in glob.glob(os.path.join(dir, '*')) if os.path.isdir(d)]
    for d in directories:
        UpdateBaselineHelper(d, 'a')

# Returns dictionary containing keys as file name and values as their hashes
def getKeyHashesFromBaseline():
    global name_hash, baseline_path
    dict = {}
    with open(baseline_path, 'r') as baseline:
        for line in baseline:
            key, value = line.split('=')
            dict[key] = value[:-1]
    return dict

# Clears data in all 4 lists
def ClearData():
    files_changed.clear()
    files_added.clear()
    files_removed.clear()
    files_all.clear()
    fc.configure(text="Files Changed :" + spaces)
    fa.configure(text="Files Added :" + spaces)
    fr.configure(text="Files Removed :" + spaces)

# Save log to a file
def logsave():
    log_content = (
        "Files Changed:\n" + "\n".join(files_changed) + "\n\n" +
        "Files Added:\n" + "\n".join(files_added) + "\n\n" +
        "Files Removed:\n" + "\n".join(files_removed)
    )
    log_file = asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
    if log_file:
        with open(log_file, 'w') as file:
            file.write(log_content)

# Play notification sound
def PlaySound():
    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)

# Rescan at intervals
def RescanAtIntervals(interval):
    while True:
        time.sleep(interval)
        CheckIntegrity(folder, 1)
        PlaySound()

# Start rescan at intervals
def StartRescan():
    interval = simpledialog.askinteger("Input", "Enter rescan interval in seconds:", minvalue=1)
    if interval:
        threading.Thread(target=RescanAtIntervals, args=(interval,), daemon=True).start()

# Calculates hashes and Checks with the baseline
def CheckIntegrity(dir, number):
    ClearData()  # Clear data in all 4 lists
    if dir == "":
        label3.configure(text="Error: Folder not selected")
    else:
        CheckIntegrityHelper(dir, number)
        fc.configure(text=fc.cget("text") + '\n'.join(files_changed))
        fa.configure(text=fa.cget("text") + '\n'.join(files_added))
        fr.configure(text=fr.cget("text") + '\n'.join(files_removed))
        label3.configure(text="Message: Integrity Checked Successfully")
        PlaySound()

# Helper function for Check Integrity
def CheckIntegrityHelper(dir, number):
    global name_hash, baseline_path
    if(number):
        name_hash = calcNameHash(dir)
        baseline_path = os.path.join(baseline_dir, (name_hash + '.txt'))
        try:
            with open(baseline_path, 'r') as baseline:
                random = 99
        except IOError:
            label3.configure(text='Error: Baseline file for specified folder not present')
            return
        
    files = [os.path.abspath(f) for f in glob.glob(os.path.join(dir, '*')) if os.path.isfile(f)]
    for x in files:
        files_all.append(x)
    dict = getKeyHashesFromBaseline()
    
    for f in files:
        # Checking for changed files
        temp_hash = calcsha512hash(os.path.join(dir, f))
        if str(os.path.join(dir, f)) in dict.keys() and temp_hash != dict[f]:
            files_changed.append(os.path.abspath(f).replace(os.path.abspath(folder), "."))
        
        # Checking for added files and getting their metadata
        if str(os.path.join(dir, f)) not in dict.keys():
            metadata = getfilemetadata(f)
            files_added.append(os.path.abspath(f).replace(os.path.abspath(folder), ".") + " | " + metadata)
    
    directories = [d for d in glob.glob(os.path.join(dir, '*')) if os.path.isdir(d)]
    for d in directories:
        CheckIntegrityHelper(d, 0)
    
    if number == 1:
        # checking for removed files
        for x in list(dict.keys()):
            if x not in files_all:
                files_removed.append(os.path.abspath(x).replace(os.path.abspath(folder), "."))

################################# GUI #################################

ctk.set_appearance_mode("dark")  # Modes: system (default), light, dark
ctk.set_default_color_theme("dark-blue")  # Themes: blue (default), dark-blue, green

# Some Variables
font_data = ("Raleway", 14)
label_text_clr = "#FFCF00"
btn_fg_clr = "#27ab55"
btn_text_clr = "#000000"
btn_hover_clr = "#148f3f"
error_label_clr = "#E94F37"

# Initialising root window
root = ctk.CTk()
root.title("HashLine - A File Integrity Monitor")
root.geometry("600x700")  # Set the width to 600 pixels and height to 700 pixels

def open_file():
    global folder
    folder = askdirectory()
    label2.configure(text=folder)

def select_baseline_dir():
    global baseline_dir
    baseline_dir = askdirectory()
    label4.configure(text="Baseline Dir: " + baseline_dir)

# UI Elements
label1 = ctk.CTkLabel(root, text="File Integrity Monitor", font=("Raleway", 24), text_color=label_text_clr)
label1.pack(pady=10)

button1 = ctk.CTkButton(root, text="Select Folder", command=open_file, fg_color=btn_fg_clr, text_color=btn_text_clr, hover_color=btn_hover_clr)
button1.pack(pady=8)

label2 = ctk.CTkLabel(root, text="", font=font_data, text_color=label_text_clr)
label2.pack(pady=9)

button4 = ctk.CTkButton(root, text="Select Baseline Directory", command=select_baseline_dir, fg_color=btn_fg_clr, text_color=btn_text_clr, hover_color=btn_hover_clr)
button4.pack(pady=10)

label4 = ctk.CTkLabel(root, text="Baseline Dir: ", font=font_data, text_color=label_text_clr)
label4.pack(pady=10)

button2 = ctk.CTkButton(root, text="Update Baseline", command=lambda: UpdateBaseline(folder, 'w'), fg_color=btn_fg_clr, text_color=btn_text_clr, hover_color=btn_hover_clr)
button2.pack(pady=10)

button3 = ctk.CTkButton(root, text="Check Integrity", command=lambda: CheckIntegrity(folder, 1), fg_color=btn_fg_clr, text_color=btn_text_clr, hover_color=btn_hover_clr)
button3.pack(pady=10)

button5 = ctk.CTkButton(root, text="Save Log", command=logsave, fg_color=btn_fg_clr, text_color=btn_text_clr, hover_color=btn_hover_clr)
button5.pack(pady=10)

button6 = ctk.CTkButton(root, text="Start Rescan at Intervals", command=StartRescan, fg_color=btn_fg_clr, text_color=btn_text_clr, hover_color=btn_hover_clr)
button6.pack(pady=7)

label3 = ctk.CTkLabel(root, text="", font=font_data, text_color=error_label_clr)
label3.pack(pady=5)

fc = ctk.CTkLabel(root, text="Files Changed :" + spaces, font=font_data, text_color=label_text_clr)
fc.pack(pady=5)

fa = ctk.CTkLabel(root, text="Files Added :" + spaces, font=font_data, text_color=label_text_clr)
fa.pack(pady=5)

fr = ctk.CTkLabel(root, text="Files Removed :" + spaces, font=font_data, text_color=label_text_clr)
fr.pack(pady=5)

root.mainloop()
