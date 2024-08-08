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
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageOps
import logging
import numpy as np
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing
import sys
import psutil
from queue import Queue

# Constants
LOG_FILE = "conversion_log.txt"
DEFAULT_CONCURRENT_THREADS = min(4, multiprocessing.cpu_count())
OO_SQRT_3 = 0.57735025882720947
BUMP_BASIS_TRANSPOSE = [
    [0.81649661064147949, -0.40824833512306213, -0.40824833512306213],
    [0.0, 0.70710676908493042, -0.7071068286895752],
    [OO_SQRT_3, OO_SQRT_3, OO_SQRT_3]
]

# Setup logging
def setup_logging(log_file):
    logging.basicConfig(
        filename=log_file,
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))  # Also print to console

def log_info(message):
    logging.info(message)

def log_warning(message):
    logging.warning(message)

def log_error(message):
    logging.error(message)

def validate_parameters(target_folder, backup_folder, texture_format):
    if not os.path.isdir(target_folder):
        raise ValueError("Target folder does not exist or is not a directory.")
    if not os.path.isdir(backup_folder):
        raise ValueError("Backup folder does not exist or is not a directory.")
    if texture_format not in ['tga', 'png', 'jpg', 'dds', 'bmp']:
        raise ValueError("Unsupported texture format.")

def parse_dir(dir_name):
    return [os.path.join(root, file_name) 
            for root, _, file_names in os.walk(dir_name) 
            for file_name in file_names 
            if file_name.lower().endswith('.vmt')]

def parse_vmt_file(filepath):
    parameters = {}
    try:
        with open(filepath, "r") as file:
            lines = file.readlines()

        shader_line = lines[0].strip().lower()
        parameters["shader"] = shader_line if shader_line in ["vertexlitgeneric", "lightmappedgeneric", "unlitgeneric", "lightmappedreflective"] else "unknown"

        current_context = parameters
        context_stack = []

        for line in lines[1:]:
            line = line.strip()
            if line.startswith('//') or not line:
                continue
            if line.startswith('{'):
                context_stack.append(current_context)
                current_context = {}
                continue
            if line.startswith('}'):
                previous_context = context_stack.pop()
                previous_context.update(current_context)
                current_context = previous_context
                continue

            if ' ' not in line:
                current_context[line] = {}
                continue

            key, val = line.split(None, 1)
            key = key.strip('"').lower()
            val = val.split('//')[0].strip().strip('"')
            current_context[key] = val

        log_info(f"Parsed VMT file '{filepath}': {parameters}")

    except Exception as e:
        log_error(f"Unable to open or parse {filepath}: {e}")
        parameters["ERROR"] = f"Unable to open or parse {filepath}: {e}"
    return parameters

def is_file_in_use(file_path):
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            for item in proc.open_files():
                if file_path == item.path:
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False

def copy_with_retry(src, dst, retries=5, delay=0.05):
    for attempt in range(retries):
        try:
            if not is_file_in_use(src):
                shutil.copy2(src, dst)
                return True
            else:
                log_warning(f"File {src} is in use, retrying...")
        except (PermissionError, FileNotFoundError) as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                log_error(f"Failed to copy {src} to {dst} after {retries} attempts: {e}")
                return False
        time.sleep(delay)
    return False

def move_with_retry(src, dst, retries=5, delay=0.05):
    for attempt in range(retries):
        try:
            shutil.move(src, dst)
            log_info(f"Moved file from {src} to {dst}")
            return True
        except (PermissionError, FileNotFoundError) as e:
            log_warning(f"Attempt {attempt + 1} failed to move {src} to {dst}: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                log_error(f"Failed to move {src} to {dst} after {retries} attempts: {e}")
                return False

def convert_ssbump_to_normal_and_height(ssbump_path, output_format='png'):
    try:
        log_info(f"Converting ssbump map to normal and height maps for: {ssbump_path}")
        img = Image.open(ssbump_path)
        width, height = img.size
        pixels = np.array(img)
        normal_image = Image.new('RGB', (width, height))
        normal_pixels = np.array(normal_image)

        height_image = Image.new('L', (width, height))
        height_pixels = np.array(height_image)

        for y in range(height):
            for x in range(width):
                pixel = pixels[y, x][:3] / 255.0
                pixel_vector = np.array([pixel[0], pixel[1], pixel[2]])
                normal_pixels[y, x, 0] = min(255, max(0, int(((np.dot(pixel_vector, BUMP_BASIS_TRANSPOSE[0]) * 0.55) + 0.5) * 255)))
                normal_pixels[y, x, 1] = min(255, max(0, int(((np.dot(pixel_vector, BUMP_BASIS_TRANSPOSE[1]) * 0.55) + 0.5) * 255)))
                normal_pixels[y, x, 2] = min(255, max(0, int(((np.dot(pixel_vector, BUMP_BASIS_TRANSPOSE[2]) * 0.55) + 0.5) * 255)))
                height_pixels[y, x] = int(255 * (1 - pixel[0]))  # Use red channel for height

        normal_image = Image.fromarray(normal_pixels)
        height_image = Image.fromarray(height_pixels)

        base_name, _ = os.path.splitext(ssbump_path)
        normal_map_path = f"{base_name.replace('-ssbump', '').replace('_height', '')}_normal.{output_format}"
        height_map_path = f"{base_name.replace('-ssbump', '').replace('_height', '')}_height.{output_format}"

        normal_image.save(normal_map_path)
        height_image.save(height_map_path)

        log_info(f"Generated normal map: {normal_map_path}")
        log_info(f"Generated height map: {height_map_path}")

        return normal_map_path, height_map_path
    except Exception as e:
        log_error(f"Error converting ssbump to normal and height: {e}")
        return None, None

def convert_vmt_to_vmat(vmt_file, base_path, backup_folder, texture_format, generate_height, generate_normal):
    parameters = parse_vmt_file(vmt_file)
    log_info(f"Processing VMT file: {vmt_file}")

    base_texture_name = parameters.get('$basetexture', '').replace('"', '')
    bumpmap_texture_name = parameters.get('$bumpmap', '').replace('"', '')
    normalmap_texture_name = parameters.get('$normalmap', '').replace('"', '')
    roughness_texture_name = f"{base_texture_name}_roughness.{texture_format}"
    parameters['$roughness'] = roughness_texture_name

    vmat_file = vmt_file.replace('.vmt', '.vmat')
    vmat_file_export = os.path.join(base_path, vmat_file)

    backup_vmt_dir = os.path.join(backup_folder, os.path.relpath(vmt_file, start=base_path))
    os.makedirs(os.path.dirname(backup_vmt_dir), exist_ok=True)
    if not move_with_retry(vmt_file, backup_vmt_dir):
        return

    normal_map_path = None
    height_map_path = None

    if bumpmap_texture_name and "-ssbump" in bumpmap_texture_name:
        bumpmap_file_path = find_texture_file(bumpmap_texture_name, base_path, texture_format)
        if bumpmap_file_path:
            log_info(f"Converting ssbump map to normal and height maps for: {bumpmap_texture_name}")
            normal_map_path, height_map_path = convert_ssbump_to_normal_and_height(bumpmap_file_path, texture_format)
            if normal_map_path:
                backup_ssbump_dir = os.path.join(backup_folder, os.path.relpath(bumpmap_file_path, start=base_path))
                os.makedirs(os.path.dirname(backup_ssbump_dir), exist_ok=True)
                move_with_retry(bumpmap_file_path, backup_ssbump_dir)

    try:
        with open(vmat_file_export, "w") as file:
            file.write("// THIS FILE IS AUTO-GENERATED\n\n")
            file.write("Layer0\n{\n")
            file.write('\tshader "csgo_environment.vfx"\n\n')

            # Add other parameters if available
            file.write('\t//---- Color ----\n')
            file.write('\tg_flModelTintAmount "1.000"\n')
            file.write('\tg_nScaleTexCoordUByModelScaleAxis "0" // None\n')
            file.write('\tg_nScaleTexCoordVByModelScaleAxis "0" // None\n')
            file.write('\tg_vColorTint "[1.000000 1.000000 1.000000 0.000000]"\n\n')

            file.write('\t//---- Fog ----\n')
            file.write('\tg_bFogEnabled "1"\n\n')

            file.write('\t//---- Material1 ----\n')
            file.write('\tg_flTexCoordRotation1 "0.000"\n')
            file.write('\tg_vTexCoordCenter1 "[0.500 0.500]"\n')
            file.write('\tg_vTexCoordOffset1 "[0.000 0.000]"\n')
            file.write('\tg_vTexCoordScale1 "[1.000 1.000]"\n')
            if '$basetexture' in parameters:
                file.write(f'\tTextureColor1 "materials/{parameters["$basetexture"].lower().replace("\\", "/")}.{texture_format}"\n')
            if normal_map_path:
                file.write(f'\tTextureNormal1 "materials/{normal_map_path.replace("\\", "/")}"\n')
            elif bumpmap_texture_name and generate_normal:
                file.write(f'\tTextureNormal1 "materials/{bumpmap_texture_name.lower().replace("-ssbump", "_normal").replace("\\", "/")}.{texture_format}"\n')
            else:
                file.write(f'\tTextureNormal1 "materials/default/default_normal.{texture_format}"\n')
            if generate_height and height_map_path:
                file.write(f'\tTextureHeight1 "materials/{height_map_path.replace("\\", "/")}"\n')
            file.write('\tTextureMetalness1 "materials/default/default_metal.tga"\n')
            file.write(f'\tTextureRoughness1 "materials/{roughness_texture_name.lower().replace("\\", "/")}"\n')
            file.write('\tTextureTintMask1 "materials/default/default_mask.tga"\n\n')

            file.write('\t//---- Texture Address Mode ----\n')
            file.write('\tg_nTextureAddressModeU "0" // Wrap\n')
            file.write('\tg_nTextureAddressModeV "0" // Wrap\n')

            file.write("}\n")
        log_info(f"VMAT file generated: {vmat_file_export}")
    except Exception as e:
        log_error(f"Error writing VMAT file {vmat_file_export}: {e}")

    return vmat_file_export

def find_texture_file(texture_name, base_path, texture_format):
    texture_file = os.path.join(base_path, f"{texture_name}.{texture_format}")
    if os.path.isfile(texture_file):
        return texture_file
    log_warning(f"Texture file for '{texture_name}' not found.")
    return None

def generate_roughness_maps(directory, texture_format, darkness_value):
    darkness_factor = 255 - int(darkness_value)

    for root, _, files in os.walk(directory):
        for file_name in files:
            if (file_name.lower().endswith(texture_format) and 
                '_normal' not in file_name.lower() and 
                '_noalpha' not in file_name.lower() and 
                '_roughness' not in file_name.lower() and 
                '_selfillum' not in file_name.lower() and 
                '_color' not in file_name.lower() and
                '-ssbump' not in file_name.lower() and 
                '_detail' not in file_name.lower()):
                texture_path = os.path.join(root, file_name)

                try:
                    with Image.open(texture_path) as img:
                        # Convert image to grayscale
                        grayscale_img = ImageOps.grayscale(img)

                        # Check if the surface should be shiny
                        roughness_img = ImageOps.invert(grayscale_img)
                        roughness_img = Image.eval(roughness_img, lambda x: min(255, int(x * darkness_factor / 255)))

                        # Save roughness map
                        base_name, _ = os.path.splitext(file_name)
                        roughness_file_name = f"{base_name}_roughness.{texture_format}"
                        roughness_file_path = os.path.join(root, roughness_file_name)

                        roughness_img.save(roughness_file_path)
                        log_info(f"Generated roughness map: {roughness_file_path}")

                except Exception as e:
                    log_error(f"Error processing {file_name}: {e}")

def adjust_roughness_for_shiny_surfaces(directory, texture_format):
    for root, _, files in os.walk(directory):
        for file_name in files:
            if file_name.lower().endswith(f"_roughness.{texture_format}"):
                roughness_path = os.path.join(root, file_name)

                try:
                    with Image.open(roughness_path) as img:
                        img_array = np.array(img)
                        # Make surfaces that are nearly black (high roughness) more prominent
                        shiny_mask = img_array < 30  # Adjust threshold as needed for shiny surfaces
                        img_array[shiny_mask] = 0  # Set shiny areas to zero roughness

                        shiny_img = Image.fromarray(img_array)
                        shiny_img.save(roughness_path)
                        log_info(f"Adjusted roughness map for shiny surfaces: {roughness_path}")

                except Exception as e:
                    log_error(f"Error adjusting roughness map {file_name}: {e}")

def worker_thread(queue, base_path, backup_folder, texture_format, overwrite_tga, generate_normal, generate_height, generate_roughness, darkness_value, retry_list):
    thread_name = threading.current_thread().name
    while not queue.empty():
        vmt_file_name = queue.get()
        if cancel_event.is_set():
            log_info(f"[{thread_name}] Cancelled processing.")
            break
        
        while not pause_event.is_set():
            time.sleep(0.1)
        
        try:
            start_time = time.time()
            log_info(f"[{thread_name}] Processing VMT file: {os.path.basename(vmt_file_name)}")
            parameters = parse_vmt_file(vmt_file_name)

            base_texture_name = parameters.get('$basetexture', '').replace('"', '')
            texture_file = find_texture_file(base_texture_name, base_path, texture_format)

            if texture_file:
                log_info(f"[{thread_name}] Found texture file for '{base_texture_name}': {texture_file}")
                convert_vmt_to_vmat(vmt_file_name, base_path, backup_folder, texture_format, generate_height, generate_normal)
                if overwrite_tga:
                    texture_file_export = os.path.join(base_path, f"{base_texture_name}.{texture_format}")
                    os.makedirs(os.path.dirname(texture_file_export), exist_ok=True)
                    if not copy_with_retry(texture_file, texture_file_export):
                        raise Exception(f"Failed to copy texture file: {texture_file}")
            else:
                log_warning(f"[{thread_name}] Texture file for '{base_texture_name}' not found.")
        except Exception as e:
            log_error(f"[{thread_name}] Error processing VMT file {vmt_file_name}: {e}")
            retry_list.append(vmt_file_name)

        end_time = time.time()
        elapsed_time = end_time - start_time
        if elapsed_time > 5:  # Arbitrary threshold for "long processing time"
            log_info(f"[{thread_name}] Warning: Processing of {os.path.basename(vmt_file_name)} took {elapsed_time:.2f} seconds")

    if generate_roughness:
        try:
            generate_roughness_maps(base_path, texture_format, darkness_value)
            adjust_roughness_for_shiny_surfaces(base_path, texture_format)
        except Exception as e:
            log_error(f"[{thread_name}] Error generating roughness maps: {e}")

    with progress_lock:
        progress_count[0] += 1

def estimate_time(total, processed, start_time):
    elapsed_time = time.time() - start_time
    if processed == 0:
        return "Calculating..."
    average_time_per_file = elapsed_time / processed
    estimated_remaining_time = average_time_per_file * (total - processed)
    minutes, seconds = divmod(estimated_remaining_time, 60)
    return f"{int(minutes)}m {int(seconds)}s remaining"

def main(target_folder, backup_folder, texture_format, overwrite_vmat, overwrite_tga, generate_normal, generate_height, generate_roughness, darkness_value):
    global progress_count, total_vmt_files, progress_lock, progress_label, progress_complete, start_time

    log_file = os.path.join(target_folder, LOG_FILE)
    progress_count = [0]
    progress_lock = threading.Lock()
    progress_complete = False
    retry_list = []

    try:
        validate_parameters(target_folder, backup_folder, texture_format)
    except ValueError as e:
        messagebox.showerror("Error", str(e))
        return

    setup_logging(log_file)

    if not os.path.exists(target_folder):
        os.makedirs(target_folder)

    file_list = parse_dir(target_folder)
    total_vmt_files = len(file_list)
    progress_label.config(text=f"Processed 0/{total_vmt_files}")

    queue = Queue()
    for file in file_list:
        queue.put(file)

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=DEFAULT_CONCURRENT_THREADS) as executor:
        futures = [executor.submit(worker_thread, queue, target_folder, backup_folder, texture_format, overwrite_tga, generate_normal, generate_height, generate_roughness, darkness_value, retry_list) for _ in range(DEFAULT_CONCURRENT_THREADS)]
        for future in as_completed(futures):
            future.result()
            with progress_lock:
                current_progress = progress_count[0]
                progress_label.config(text=f"Processed {current_progress}/{total_vmt_files} - {estimate_time(total_vmt_files, current_progress, start_time)}")
                if current_progress % 50 == 0:  # Update every 50 processed files
                    progress_label.config(text=f"Processed {current_progress}/{total_vmt_files} - {estimate_time(total_vmt_files, current_progress, start_time)}")

    # Retry failed files
    if retry_list:
        log_info("Retrying failed files...")
        with ThreadPoolExecutor(max_workers=DEFAULT_CONCURRENT_THREADS) as executor:
            futures = [executor.submit(worker_thread, queue, target_folder, backup_folder, texture_format, overwrite_tga, generate_normal, generate_height, generate_roughness, darkness_value, []) for _ in range(DEFAULT_CONCURRENT_THREADS)]
            for future in as_completed(futures):
                future.result()

    progress_complete = True
    progress_label.config(text=f"Processed {progress_count[0]}/{total_vmt_files} - Completed!")
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
    global progress_label, start_time, pause_event, cancel_event

    target_folder = source_folder_entry.get()
    backup_folder = backup_folder_entry.get()
    texture_format = texture_format_var.get()
    overwrite_vmat = overwrite_vmat_var.get()
    overwrite_tga = overwrite_tga_var.get()
    generate_normal = generate_normal_var.get()
    generate_height = generate_height_var.get()
    generate_roughness = generate_roughness_var.get()
    darkness_value = darkness_scale.get()

    if not target_folder or not backup_folder or not texture_format:
        messagebox.showerror("Error", "Please ensure all fields are filled in correctly!")
        return

    convert_button.config(state=tk.DISABLED)
    progress_label.config(text="Processing...")
    progress_bar.start()
    pause_button.config(state=tk.NORMAL)
    cancel_button.config(state=tk.NORMAL)

    pause_event = threading.Event()
    cancel_event = threading.Event()
    pause_event.set()  # Start in the running state

    def run_conversion():
        main(target_folder, backup_folder, texture_format, overwrite_vmat, overwrite_tga, generate_normal, generate_height, generate_roughness, darkness_value)
        progress_bar.stop()
        progress_label.config(text="Completed!")
        convert_button.config(state=tk.NORMAL)
        pause_button.config(state=tk.DISABLED)
        cancel_button.config(state=tk.DISABLED)

    threading.Thread(target=run_conversion).start()

def toggle_pause():
    if pause_event.is_set():
        pause_event.clear()  # Pause
        pause_button.config(text="Resume")
        progress_label.config(text="Paused")
    else:
        pause_event.set()  # Resume
        pause_button.config(text="Pause")

def cancel_conversion():
    cancel_event.set()
    progress_label.config(text="Cancelled")
    convert_button.config(state=tk.NORMAL)
    pause_button.config(state=tk.DISABLED)

def open_help():
    import webbrowser
    webbrowser.open('https://github.com/oskarmikey/vmt-to-vmat-enhanced-GUI/tree/main')

# Create GUI
root = tk.Tk()
root.title("VMT To VMAT and RoughGen")

# Console output
console_frame = tk.Frame(root)
console_frame.grid(row=0, column=0, columnspan=3, padx=10, pady=5, sticky=tk.W+tk.E)
console_output = tk.Text(console_frame, height=10, width=100, wrap=tk.WORD)
console_output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
console_scroll = tk.Scrollbar(console_frame, command=console_output.yview)
console_scroll.pack(side=tk.RIGHT, fill=tk.Y)
console_output.config(yscrollcommand=console_scroll.set)

# Redirect stdout and stderr to console
class ConsoleWriter:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.text_widget.tag_configure("stderr", foreground="#b22222")

    def write(self, message):
        self.text_widget.insert(tk.END, message)
        self.text_widget.see(tk.END)
        self.text_widget.update_idletasks()

    def flush(self):
        pass

sys.stdout = ConsoleWriter(console_output)
sys.stderr = ConsoleWriter(console_output)

# Help button
help_button = tk.Button(root, text="Help", command=open_help, bd=0, bg='lightgrey')
help_button.grid(row=1, column=2, padx=10, pady=5, sticky=tk.E)

# Material folder
tk.Label(root, text="Material Directory (containing VMT and texture files):").grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
source_folder_entry = tk.Entry(root, width=50)
source_folder_entry.grid(row=2, column=1, padx=10, pady=5)
tk.Button(root, text="Browse", command=browse_source_folder).grid(row=2, column=2, padx=10, pady=5)

# Backup folder
tk.Label(root, text="Backup Directory for VMT files:").grid(row=3, column=0, padx=10, pady=5, sticky=tk.W)
backup_folder_entry = tk.Entry(root, width=50)
backup_folder_entry.grid(row=3, column=1, padx=10, pady=5)
tk.Button(root, text="Browse", command=browse_backup_folder).grid(row=3, column=2, padx=10, pady=5)

# Texture format
tk.Label(root, text="Texture Format (e.g., tga, png, jpg):").grid(row=4, column=0, padx=10, pady=5, sticky=tk.W)
texture_format_var = tk.StringVar(value='tga')
texture_format_menu = tk.OptionMenu(root, texture_format_var, 'tga', 'png', 'jpg', 'dds', 'bmp')
texture_format_menu.grid(row=4, column=1, padx=10, pady=5, sticky=tk.W)

# Overwrite options
overwrite_vmat_var = tk.BooleanVar(value=True)
tk.Checkbutton(root, text="Overwrite VMAT files", variable=overwrite_vmat_var).grid(row=5, column=0, padx=10, pady=5, sticky=tk.W)
overwrite_tga_var = tk.BooleanVar(value=True)
tk.Checkbutton(root, text="Overwrite texture files", variable=overwrite_tga_var).grid(row=5, column=1, padx=10, pady=5, sticky=tk.W)

# Normal and roughness options
generate_normal_var = tk.BooleanVar(value=False)
tk.Checkbutton(root, text="Generate Normal Maps", variable=generate_normal_var).grid(row=6, column=0, padx=10, pady=5, sticky=tk.W)
generate_height_var = tk.BooleanVar(value=False)
tk.Checkbutton(root, text="Generate Height Maps", variable=generate_height_var).grid(row=6, column=1, padx=10, pady=5, sticky=tk.W)
generate_roughness_var = tk.BooleanVar(value=True)
tk.Checkbutton(root, text="Generate Roughness Maps", variable=generate_roughness_var).grid(row=6, column=2, padx=10, pady=5, sticky=tk.W)

# Darkness value
tk.Label(root, text="Darkness Value (0-255):").grid(row=7, column=0, padx=10, pady=5, sticky=tk.W)
darkness_scale = tk.Scale(root, from_=0, to=255, orient=tk.HORIZONTAL)
darkness_scale.set(128)
darkness_scale.grid(row=7, column=0, columnspan=2, padx=150, pady=10, sticky=tk.W)

# Convert button
convert_button = tk.Button(root, text="Convert", command=start_conversion, width=20, height=0)
convert_button.grid(row=8, column=0, columnspan=3, pady=10)

# Pause button
pause_button = tk.Button(root, text="Pause", command=toggle_pause, state=tk.DISABLED)
pause_button.grid(row=9, column=0, pady=10)

# Cancel button
cancel_button = tk.Button(root, text="Cancel", command=cancel_conversion, state=tk.DISABLED)
cancel_button.grid(row=9, column=1, pady=10)

# Progress label and bar
progress_label = tk.Label(root, text="Progress: 0%")
progress_label.grid(row=10, column=0, columnspan=2, padx=10, pady=5, sticky=tk.W)
progress_bar = ttk.Progressbar(root, mode='indeterminate')
progress_bar.grid(row=11, column=0, columnspan=3, padx=10, pady=5, sticky=tk.W+tk.E)

root.mainloop()
