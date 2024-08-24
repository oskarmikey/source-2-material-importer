#
#
#
#
# i have no idea but this is a new implemenation of this if i remeber corectly the previous one is trash becaue
# i tried to do it with chat gpt without manualy telling it hyper specificly what the script should how  to do it
# and i dident course corect it enoughe and i had to give five times more examples. 
# but now i will comit and do that
#

import os
import re
from PIL import Image, ImageOps
import numpy as np

# Directories
base_materials_dir = 'D:/Game moding/vmt_converter_test/texture test/materials/'
output_texture_dir = 'D:/Game moding/vmt_converter_test/converted_textures/'
vmat_output_dir = 'D:/Game moding/vmt_converter_test/vmat_files/'

# Ensure directories exist
os.makedirs(output_texture_dir, exist_ok=True)
os.makedirs(vmat_output_dir, exist_ok=True)

def parse_vmt(vmt_content):
    attributes = {}
    proxies = {}
    inside_proxies = False

    for line in vmt_content:
        line = line.strip()

        if line.startswith("{") or line.startswith("}"):
            continue

        # Detect "Proxies" section
        if line.lower() == '"proxies"':
            inside_proxies = True
            continue
        elif inside_proxies and line.startswith("{"):
            continue
        elif inside_proxies and line.startswith("}"):
            inside_proxies = False
            continue

        if inside_proxies:
            match = re.match(r'"(\w+)"\s*{\s*"(\w+)"\s*"\$?(.*?)"', line, re.IGNORECASE)
            if match:
                proxy_type, var, value = match.groups()
                if proxy_type not in proxies:
                    proxies[proxy_type] = []
                proxies[proxy_type].append({var: value})
        else:
            match = re.match(r'"?\$?(\w+)"?\s*"?([\w/._\[\]]+)"?', line, re.IGNORECASE)
            if match:
                key, value = match.groups()
                attributes[key.lower()] = value

    return attributes, proxies

def convert_texture(texture_path, conversion_type):
    output_path = texture_path.replace('.png', f'_{conversion_type}.tga')
    if not os.path.exists(texture_path):
        print(f"Error: {texture_path} does not exist.")
        return None

    try:
        img = Image.open(texture_path).convert('L')  # Grayscale conversion
    except Exception as e:
        print(f"Failed to process {texture_path}: {e}")
        return None

    if conversion_type == 'roughness':
        img = ImageOps.invert(img)
    elif conversion_type == 'ao':
        img = ImageOps.autocontrast(img)
    elif conversion_type == 'height':
        img = ImageOps.equalize(img)
    elif conversion_type == 'ssbump_to_normal_height':
        img = ImageOps.invert(img)
    elif conversion_type == 'normal':
        normal_img = Image.fromarray(np.dstack((img, img, img)))
        normal_img.save(output_path)
        print(f"Generated {output_path}")
        return output_path

    img.save(output_path)
    print(f"Generated {output_path}")
    return output_path

def process_vmt_textures(vmt_file_path, attributes):
    base_texture = attributes.get("$basetexture", None)
    if not base_texture:
        print(f"No $basetexture found in {vmt_file_path}, skipping texture generation.")
        return {}

    base_texture_path = os.path.join(os.path.dirname(vmt_file_path), base_texture.replace("/", os.sep) + ".png")

    used_textures = {
        "basetexture": base_texture_path,
        "roughness": None,
        "normal": None,
        "ao": None,
        "selfillum": None
    }

    # Generate roughness map
    roughness_path = convert_texture(base_texture_path, 'roughness')
    used_textures["roughness"] = roughness_path

    # Generate normal map from ssbump
    if attributes.get("$ssbump", None) == "1":
        normal_path = convert_texture(base_texture_path, 'ssbump_to_normal_height')
        used_textures["normal"] = normal_path

    # Generate other maps if necessary
    if "$selfillum" in attributes:
        used_textures["selfillum"] = base_texture_path  # Assuming selfillum uses the same base texture

    return used_textures

def convert_vmt_to_vmat(vmt_file_path, used_textures, attributes, proxies):
    vmat_file_path = os.path.splitext(vmt_file_path)[0] + '.vmat'
    vmat_file_path = os.path.join(vmat_output_dir, os.path.basename(vmat_file_path))
    vmat_content = []

    shader_mapping = {
        "lightmappedgeneric": "csgo_complex.vfx",
        "vertexlitgeneric": "csgo_simple.vfx",
    }

    shader_type = attributes.get("shader", "lightmappedgeneric").lower()
    vmat_shader = shader_mapping.get(shader_type, "needs_manual_conversion")

    vmat_content.append('"Layer0" {')
    vmat_content.append(f'    "shader" "{vmat_shader}"')

    if used_textures.get("basetexture"):
        vmat_content.append(f'    "TextureColor" "{used_textures["basetexture"].replace("\\", "/")}"')
    if used_textures.get("normal"):
        vmat_content.append(f'    "TextureNormal" "{used_textures["normal"].replace("\\", "/")}"')
    if used_textures.get("roughness"):
        vmat_content.append(f'    "TextureRoughness" "{used_textures["roughness"].replace("\\", "/")}"')
    if used_textures.get("selfillum"):
        vmat_content.append(f'    "TextureSelfIllum" "{used_textures["selfillum"].replace("\\", "/")}"')

    if "$phong" in attributes and attributes["$phong"] == "1":
        vmat_content.append(f'    "g_flMetalness" "0.5"')

    # Add proxies conversion if needed
    for proxy_type, proxy_values in proxies.items():
        if proxy_type == "texturetransform":
            # Add transformation logic
            pass

    vmat_content.append('}')

    with open(vmat_file_path, 'w') as vmat_file:
        vmat_file.writelines(vmat_content)

    print(f"Converted {vmt_file_path} to {vmat_file_path}")

def process_vmt_to_vmat(vmt_file_path):
    with open(vmt_file_path, 'r') as vmt_file:
        vmt_content = vmt_file.readlines()

    attributes, proxies = parse_vmt(vmt_content)
    used_textures = process_vmt_textures(vmt_file_path, attributes)
    convert_vmt_to_vmat(vmt_file_path, used_textures, attributes, proxies)

def process_folder(folder_path):
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".vmt"):
                process_vmt_to_vmat(os.path.join(root, file))

# Example usage:
process_folder("path/to/your/vmt/folder")
