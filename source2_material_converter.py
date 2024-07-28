#I have no idea to write upp here
# This version is heavaly shait 
# Mostly because ive used ai
# oh this uses a big part of  https://github.com/AlpyneDreams/source2utils/blob/master/utils/vmt_to_vmat.py
# because ai is stobid and tries to do it a way that won't work so i "used" it to force chat bpt
# to work with the base of the github repo i linked.
#
#HOW TO USE
#
#
#

import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox
from threading import Thread

# Constants
TEXTURE_FILEEXT = '.tga'
EXPORT_FOLDER_NAME = "export"
LOG_FILE = "conversion_log.txt"

vmtSupportedShaders = [
    "vertexlitgeneric", "unlitgeneric", "unlittwotexture", "patch", "teeth",
    "eyes", "eyeball", "eyerefract", "modulate", "water", "refract", "worldvertextransition",
    "lightmappedgeneric", "lightmapped_4wayblend", "multiblend", "hero", "lightmappedtwotexture",
    "lightmappedreflective", "decalmodulate", "cables"
]
ignoreList = [
    "vertexlitgeneric_hdr_dx9", "vertexlitgeneric_dx9", "vertexlitgeneric_dx8", "vertexlitgeneric_dx7",
    "lightmappedgeneric_hdr_dx9", "lightmappedgeneric_dx9", "lightmappedgeneric_dx8", "lightmappedgeneric_dx7"
]

def parse_dir(dir_name):
    files = []
    for root, dirs, file_names in os.walk(dir_name):
        for file_name in file_names:
            if file_name.lower().endswith('.vmt'):
                files.append(os.path.join(root, file_name))
    return files

def parse_line(input_string):
    return input_string.lower().replace('"', '').replace("'", "").replace("\n", "").replace("\t", "").replace("{", "").replace("}", "").replace(" ", "")

def fix_texture_path(p, addon_string=""):
    ret_path = p.strip().strip('"')
    ret_path = ret_path.replace('\\', '/')
    ret_path = ret_path.replace('.vtf', '')
    return '"materials/' + ret_path + addon_string + TEXTURE_FILEEXT + '"'

def fix_vector(s, div_var=1):
    s = s.strip('"][}{ ').strip("'").replace("  ", " ").replace("   ", " ")
    parts = [str(float(i) / div_var) for i in s.split(' ')]
    extra = (' 0.0' * max(3 - s.count(' '), 0))
    return '"[' + ' '.join(parts) + extra + ']"'

def vector_to_array(s, div_var=1):
    s = s.strip('"][}{ ')
    parts = [float(i) / div_var for i in s.split(' ')]
    return parts

def text_parser(filepath, separator="="):
    return_dict = {}
    with open(filepath, "r") as f:
        for line in f:
            if not line.startswith("//"):
                line = line.replace('\t', '').replace('\n', '')
                line = line.split(separator)
                return_dict[line[0]] = line[1]
    return return_dict

def parse_vmt_path(input_path):
    return input_path.lower().replace(".vtf", "")

def add_folder_extension(file_path, base_path):
    relative_path = os.path.relpath(file_path, base_path)
    out_path = os.path.join(EXPORT_FOLDER_NAME, relative_path)
    return out_path

def parse_vmt_parameter(line, parameters):
    words = re.split(r'\s+', line, 2)
    words = list(filter(len, words))
    if len(words) < 2:
        return

    key = words[0].strip('"').lower()
    if key.startswith('/'):
        return

    if not key.startswith('$') and not key.startswith('%'):
        return

    val = words[1].strip('\n').lower()
    comment_tuple = val.partition('//')

    if not val.strip('"\''):
        parameters[key] = "No value"
        return

    if val.strip('"\'') == "0":
        parameters[key] = "Value is 0"
        return

    parameters[key] = comment_tuple[0].replace("'", "").replace('"', '').strip()

def parse_vmt_file(filepath):
    parameters = {}
    try:
        with open(filepath, "r") as file:
            vmt_shader = file.readline().strip()
            if vmt_shader.startswith("vertexlitgeneric"):
                vmt_shader = "vertexlitgeneric"
            elif vmt_shader.startswith("lightmappedgeneric"):
                vmt_shader = "lightmappedgeneric"
            else:
                vmt_shader = ""

            for line in file:
                line = line.strip()
                if line and not line.startswith('//') and not line.startswith('{') and not line.startswith('}'):
                    parse_vmt_parameter(line, parameters)
    except Exception as e:
        parameters["ERROR"] = f"Unable to open or parse {filepath}: {e}"
    return parameters

def convert_vmt_to_vmat(vmt_file, base_path, export_folder, log_file):
    parameters = parse_vmt_file(vmt_file)

    with open(log_file, "a") as log:
        log.write(f"\nProcessing VMT file: {vmt_file}\n")
        for key, value in parameters.items():
            log.write(f"{key}: {value}\n")

        missing_params = []
        if not parameters.get('$basetexture'):
            missing_params.append('Base texture')
        if not parameters.get('$detail'):
            missing_params.append('Detail map')
        if not parameters.get('$detailscale'):
            missing_params.append('Detail scale')
        if not parameters.get('$detailblendmode'):
            missing_params.append('Detail blend mode')
        if not parameters.get('$detailblendfactor'):
            missing_params.append('Detail blend factor')
        if not parameters.get('$surfaceprop'):
            missing_params.append('Surface property')
        if not parameters.get('%keywords'):
            missing_params.append('Keywords')

        if missing_params:
            log.write(f"+ WARNING: Missing parameters: {', '.join(missing_params)}\n")

    vmat_file = add_folder_extension(vmt_file, base_path).replace('.vmt', '.vmat')
    vmat_file_export = os.path.join(export_folder, EXPORT_FOLDER_NAME, vmat_file)
    os.makedirs(os.path.dirname(vmat_file_export), exist_ok=True)
    
    with open(vmat_file_export, "w") as file:
        file.write("VMAT File Content Here\n")
        for key, value in parameters.items():
            file.write(f"{key}: {value}\n")

    return vmat_file_export

def main(target_folder, texture_format, export_folder, overwrite_vmat, overwrite_tga):
    global TEXTURE_FILEEXT
    TEXTURE_FILEEXT = f".{texture_format}"
    log_file = os.path.join(export_folder, LOG_FILE)

    export_folder_path = os.path.join(export_folder, EXPORT_FOLDER_NAME)
    if not os.path.exists(export_folder_path):
        os.makedirs(export_folder_path)

    with open(log_file, "w") as log:
        log.write("Conversion Log\n")
        log.write("====================\n")

    file_list = []
    vtf_list = []

    abs_file_path = os.path.abspath(target_folder)
    if os.path.isdir(abs_file_path):
        file_list.extend(parse_dir(abs_file_path))
    elif abs_file_path.lower().endswith('.vmt'):
        file_list.append(abs_file_path)
    elif abs_file_path.lower().endswith('.vtf'):
        vtf_list.append(abs_file_path)
    else:
        messagebox.showerror("Error", "File path is invalid.")
        return

    for vmt_file_name in file_list:
        convert_vmt_to_vmat(vmt_file_name, target_folder, export_folder, log_file)

    messagebox.showinfo("Process Finished", "The VMT to VMAT conversion has finished!")

def browse_source_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        source_folder_entry.delete(0, tk.END)
        source_folder_entry.insert(0, folder_selected)

def browse_export_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        export_folder_entry.delete(0, tk.END)
        export_folder_entry.insert(0, folder_selected)

def start_conversion():
    target_folder = source_folder_entry.get()
    texture_format = texture_format_var.get()
    export_folder = export_folder_entry.get()
    overwrite_vmat = overwrite_vmat_var.get()
    overwrite_tga = overwrite_tga_var.get()

    if not target_folder or not export_folder or not texture_format:
        messagebox.showerror("Error", "Please fill all fields!")
        return

    convert_button.config(state=tk.DISABLED)
    progress_label.config(text="Processing...")

    def run_conversion():
        main(target_folder, texture_format, export_folder, overwrite_vmat, overwrite_tga)
        progress_label.config(text="Done!")
        convert_button.config(state=tk.NORMAL)

    Thread(target=run_conversion).start()

def open_log_file():
    log_file_path = os.path.join(export_folder_entry.get(), EXPORT_FOLDER_NAME, LOG_FILE)
    if os.path.exists(log_file_path):
        os.startfile(log_file_path)
    else:
        messagebox.showerror("Error", "Log file not found!")

# Create GUI
root = tk.Tk()
root.title("VMT to VMAT Converter")

# Source folder
tk.Label(root, text="Source Folder:").grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
source_folder_entry = tk.Entry(root, width=50)
source_folder_entry.grid(row=0, column=1, padx=10, pady=5)
tk.Button(root, text="Browse", command=browse_source_folder).grid(row=0, column=2, padx=10, pady=5)

# Texture format
tk.Label(root, text="Texture Format:").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
texture_format_var = tk.StringVar(value='tga')
texture_format_menu = tk.OptionMenu(root, texture_format_var, 'tga', 'png', 'jpg')
texture_format_menu.grid(row=1, column=1, padx=10, pady=5, sticky=tk.W)

# Export folder
tk.Label(root, text="Export Folder:").grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
export_folder_entry = tk.Entry(root, width=50)
export_folder_entry.grid(row=2, column=1, padx=10, pady=5)
tk.Button(root, text="Browse", command=browse_export_folder).grid(row=2, column=2, padx=10, pady=5)

# Overwrite options
overwrite_vmat_var = tk.BooleanVar(value=True)
tk.Checkbutton(root, text="Overwrite VMAT files", variable=overwrite_vmat_var).grid(row=3, column=0, padx=10, pady=5, sticky=tk.W)
overwrite_tga_var = tk.BooleanVar(value=True)
tk.Checkbutton(root, text="Overwrite texture files", variable=overwrite_tga_var).grid(row=3, column=1, padx=10, pady=5, sticky=tk.W)

# Convert button
convert_button = tk.Button(root, text="Convert", command=start_conversion)
convert_button.grid(row=4, column=0, columnspan=2, pady=10)

# Open log button
open_log_button = tk.Button(root, text="Open Log File", command=open_log_file)
open_log_button.grid(row=4, column=2, pady=10)

# Progress label
progress_label = tk.Label(root, text="")
progress_label.grid(row=5, column=0, columnspan=3, pady=5)

root.mainloop()
