# MIT License
#
# Copyright (c) 2024 OSKARMICKEY
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.



import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from threading import Thread
from PIL import Image, ImageOps

# Constants
TEXTURE_FILEEXT = '.tga'
LOG_FILE = "conversion_log.txt"

def parse_dir(dir_name):
    files = []
    for root, dirs, file_names in os.walk(dir_name):
        for file_name in file_names:
            if file_name.lower().endswith('.vmt'):
                files.append(os.path.join(root, file_name))
    return files

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

def parse_vmt_parameter(line, parameters):
    words = line.split(None, 1)
    if len(words) < 2:
        return
    key = words[0].strip('"').lower()
    val = words[1].strip().split('//')[0].strip('"').strip()
    parameters[key] = val

def convert_vmt_to_vmat(vmt_file, base_path, log_file, backup_folder):
    parameters = parse_vmt_file(vmt_file)

    with open(log_file, "a") as log:
        log.write(f"\nProcessing VMT file: {vmt_file}\n")
        for key, value in parameters.items():
            log.write(f"{key}: {value}\n")

        missing_params = [param for param in ['$basetexture', '$detail', '$detailscale', '$detailblendmode', '$detailblendfactor', '$surfaceprop', '%keywords'] if not parameters.get(param)]
        if missing_params:
            log.write(f"+ WARNING: Missing parameters: {', '.join(missing_params)}\n")

    vmat_file = vmt_file.replace('.vmt', '.vmat')
    vmat_file_export = os.path.join(base_path, vmat_file)

    backup_vmt_dir = os.path.join(backup_folder, os.path.relpath(vmt_file, start=base_path))
    os.makedirs(os.path.dirname(backup_vmt_dir), exist_ok=True)
    shutil.copy2(vmt_file, backup_vmt_dir)

    with open(vmat_file_export, "w") as file:
        file.write("VMAT File Content Here\n")
        for key, value in parameters.items():
            file.write(f"{key}: {value}\n")

    try:
        os.remove(vmt_file)
        with open(log_file, "a") as log:
            log.write(f"Original VMT file removed: {vmt_file}\n")
    except Exception as e:
        with open(log_file, "a") as log:
            log.write(f"ERROR: Failed to remove original VMT file {vmt_file}: {e}\n")

    return vmat_file_export

def find_texture_file(texture_name, base_path, texture_format):
    texture_file = os.path.join(base_path, f"{texture_name}.{texture_format}")
    if os.path.isfile(texture_file):
        return texture_file
    return None

def generate_roughness_maps(directory, texture_format, darkness_value, generate_roughness):
    if not generate_roughness:
        return

    darkness_factor = 255 - int(darkness_value)

    for root, dirs, files in os.walk(directory):
        for file_name in files:
            if file_name.lower().endswith(texture_format):
                texture_path = os.path.join(root, file_name)
                
                try:
                    with Image.open(texture_path) as img:
                        grayscale_img = ImageOps.grayscale(img)
                        roughness_img = ImageOps.invert(grayscale_img)
                        roughness_img = Image.eval(roughness_img, lambda x: min(255, int(x * darkness_factor / 255)))
                        
                        base_name, ext = os.path.splitext(file_name)
                        roughness_file_name = f"{base_name}_roughness{texture_format}"
                        roughness_file_path = os.path.join(root, roughness_file_name)
                        
                        roughness_img.save(roughness_file_path)
                        print(f"Generated roughness map: {roughness_file_path}")

                except Exception as e:
                    print(f"Error processing {file_name}: {e}")

def main(target_folder, backup_folder, texture_format, overwrite_vmat, overwrite_tga, generate_roughness, darkness_value):
    global TEXTURE_FILEEXT
    TEXTURE_FILEEXT = texture_format
    log_file = os.path.join(target_folder, LOG_FILE)

    if not os.path.exists(target_folder):
        os.makedirs(target_folder)

    with open(log_file, "w") as log:
        log.write("Conversion Log\n")
        log.write("====================\n")

    file_list = parse_dir(target_folder)

    for vmt_file_name in file_list:
        parameters = parse_vmt_file(vmt_file_name)

        base_texture_name = parameters.get('$basetexture', '').replace('"', '')
        texture_file = find_texture_file(base_texture_name, target_folder, TEXTURE_FILEEXT.lstrip('.'))

        if texture_file:
            convert_vmt_to_vmat(vmt_file_name, target_folder, log_file, backup_folder)

            if overwrite_tga:
                texture_file_export = os.path.join(target_folder, texture_file.replace(f".{TEXTURE_FILEEXT.lstrip('.')}", TEXTURE_FILEEXT))
                os.makedirs(os.path.dirname(texture_file_export), exist_ok=True)
                shutil.copy2(texture_file, texture_file_export)

        else:
            with open(log_file, "a") as log:
                log.write(f"WARNING: Texture file for '{base_texture_name}' not found.\n")

    if generate_roughness:
        generate_roughness_maps(target_folder, TEXTURE_FILEEXT.lstrip('.'), darkness_value, generate_roughness)

    messagebox.showinfo("Process Completed", "The conversion from VMT to VMAT has been successfully completed!")

def browse_source_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        source_folder_entry.delete(0, tk.END)
        source_folder_entry.insert(0, folder_selected)

def browse_backup_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        backup_folder_entry.delete(0, tk.END)
        backup_folder_entry.insert(0, folder_selected)

def start_conversion():
    target_folder = source_folder_entry.get()
    backup_folder = backup_folder_entry.get()
    texture_format = texture_format_var.get()
    overwrite_vmat = overwrite_vmat_var.get()
    overwrite_tga = overwrite_tga_var.get()
    generate_roughness = generate_roughness_var.get()
    darkness_value = darkness_scale.get()

    if not target_folder or not backup_folder or not texture_format:
        messagebox.showerror("Error", "Please ensure all fields are filled in correctly!")
        return

    convert_button.config(state=tk.DISABLED)
    progress_label.config(text="Processing...")

    def run_conversion():
        main(target_folder, backup_folder, texture_format, overwrite_vmat, overwrite_tga, generate_roughness, darkness_value)
        progress_label.config(text="Completed!")
        convert_button.config(state=tk.NORMAL)

    Thread(target=run_conversion).start()

def open_help():
    import webbrowser
    webbrowser.open('https://github.com/your-github-page')

# Create GUI
root = tk.Tk()
root.title("VMT To VMAT and RoughGen ")

# Help button
help_button = tk.Button(root, text="Help", command=open_help, bd=0, bg='lightgrey')
help_button.grid(row=0, column=2, padx=10, pady=5, sticky=tk.E)

# Material folder
tk.Label(root, text="Material Directory (containing VMT and texture files):").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
source_folder_entry = tk.Entry(root, width=50)
source_folder_entry.grid(row=1, column=1, padx=10, pady=5)
tk.Button(root, text="Browse", command=browse_source_folder).grid(row=1, column=2, padx=10, pady=5)

# Backup folder
tk.Label(root, text="Backup Directory for VMT files:").grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
backup_folder_entry = tk.Entry(root, width=50)
backup_folder_entry.grid(row=2, column=1, padx=10, pady=5)
tk.Button(root, text="Browse", command=browse_backup_folder).grid(row=2, column=2, padx=10, pady=5)

# Texture format
tk.Label(root, text="Texture Format (e.g., tga, png, jpg):").grid(row=3, column=0, padx=10, pady=5, sticky=tk.W)
texture_format_var = tk.StringVar(value='tga')
texture_format_menu = tk.OptionMenu(root, texture_format_var, 'tga', 'png', 'jpg', 'dds', 'bmp')
texture_format_menu.grid(row=3, column=1, padx=10, pady=5, sticky=tk.W)

# Overwrite options
overwrite_vmat_var = tk.BooleanVar(value=True)
tk.Checkbutton(root, text="Overwrite VMAT files", variable=overwrite_vmat_var).grid(row=4, column=0, padx=10, pady=5, sticky=tk.W)
overwrite_tga_var = tk.BooleanVar(value=True)
tk.Checkbutton(root, text="Overwrite texture files", variable=overwrite_tga_var).grid(row=4, column=1, padx=10, pady=5, sticky=tk.W)

# Roughness options
generate_roughness_var = tk.BooleanVar(value=True)
tk.Checkbutton(root, text="Generate Roughness Maps", variable=generate_roughness_var).grid(row=5, column=0, padx=10, pady=5, sticky=tk.W)

# Darkness value
tk.Label(root, text="Darkness Value (0-255):").grid(row=6, column=0, padx=10, pady=5, sticky=tk.W)
darkness_scale = tk.Scale(root, from_=0, to=255, orient=tk.HORIZONTAL)
darkness_scale.set(128)
darkness_scale.grid(row=6, column=0, columnspan=2, padx=150, pady=10, sticky=tk.W)  

# Convert button
convert_button = tk.Button(root, text="Convert", command=start_conversion, width=20, height=0)
convert_button.grid(row=6, column=0, columnspan=3, pady=10)

# Progress label
progress_label = tk.Label(root, text="Convert")
progress_label.grid(row=7, column=0, columnspan=3, pady=5)

root.mainloop()


root.mainloop()
