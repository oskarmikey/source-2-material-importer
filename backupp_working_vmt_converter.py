import os
import shutil
from PIL import Image, ImageOps
import numpy as np

def generate_roughness_map(base_texture_path, output_path):
    """Generates a roughness map from the base texture and saves it as PNG."""
    base_texture = Image.open(base_texture_path).convert("RGBA")
    grayscale_texture = ImageOps.grayscale(base_texture)
    inverted_texture = ImageOps.invert(grayscale_texture)

    roughness_map_path = os.path.splitext(output_path)[0] + "_roughness.png"
    inverted_texture.save(roughness_map_path)
    return roughness_map_path

def convert_ssbump_to_normal(ssbump_path, output_path):
    """Converts an SSBump map to a normal map using vector transformation and saves it as PNG."""
    img = Image.open(ssbump_path).convert('RGB')
    width, height = img.size
    img_data = np.array(img) / 255.0  # Normalize pixel values to [0, 1]

    # Create an empty image for the normal map
    new_image = np.zeros_like(img_data)

    # Process each pixel
    for y in range(height):
        for x in range(width):
            pixel_vector = img_data[y, x]
            new_image[y, x, 0] = convert_vector(pixel_vector, 0)
            new_image[y, x, 1] = convert_vector(pixel_vector, 1)
            new_image[y, x, 2] = convert_vector(pixel_vector, 2)

    # Convert back to [0, 255] range and save as PNG
    new_image = (new_image * 255).astype(np.uint8)
    normal_map = Image.fromarray(new_image)
    
    # Save the normal map as PNG
    normal_map_path = output_path.replace("_height-ssbump", "_normal") + ".png"  # Ensure PNG extension
    normal_map.save(normal_map_path)
    print(f"Saved normal map to {normal_map_path}")
    return normal_map_path

def convert_vector(pixel, index):
    OO_SQRT_3 = 0.57735025882720947
    BUMP_BASIS_TRANSPOSE = np.array([
        [ 0.81649661064147949, -0.40824833512306213, -0.40824833512306213 ],
        [  0.0, 0.70710676908493042, -0.7071068286895752 ],
        [  OO_SQRT_3, OO_SQRT_3, OO_SQRT_3 ]
    ])
    # Convert pixel color vector using the dot product
    return int(((np.dot(pixel, BUMP_BASIS_TRANSPOSE[index]) * 0.5) + 0.5) * 255)

def parse_vmt(vmt_path):
    vmt_data = {}
    with open(vmt_path, 'r') as vmt_file:
        lines = vmt_file.readlines()
        for line in lines:
            if line.strip() and not line.startswith('//'):
                parts = line.split(maxsplit=1)
                if len(parts) == 2:
                    key, value = parts
                    key = key.strip().replace('"', '')  # Remove extra quotes
                    value = value.strip().replace('"', '')  # Remove extra quotes
                    vmt_data[key.lower()] = value
                    print(f"Found VMT attribute: {key} -> {value}")
    return vmt_data

def find_texture_file(materials_dir, texture_rel_path):
    """Tries to find the texture file in various formats, prioritizing PNG."""
    possible_extensions = ['.png', '.tga', '.jpg', '.jpeg', '.bmp']
    for ext in possible_extensions:
        texture_path = os.path.join(materials_dir, texture_rel_path + ext)
        if os.path.exists(texture_path):
            return texture_path
    return None

def map_vmt_to_vmat_basic(vmt_data, vmt_dir, materials_dir):
    vmat_data = {
        "shader": "csgo_complex.vfx",
        "F_DETAIL_TEXTURE": "2",
        "g_bFogEnabled": "1",
        "g_nScaleTexCoordUByModelScaleAxis": "0",
        "g_nScaleTexCoordVByModelScaleAxis": "0",
        "g_nTextureAddressModeU": "0",
        "g_nTextureAddressModeV": "0",
        "g_flDetailBlendFactor": "1",
        "g_flDetailBlendToFull": "0",
        "g_flMetalness": "0",
        "g_flModelTintAmount": "1"
    }

    # Handle base texture
    if "$basetexture" in vmt_data:
        base_texture_rel_path = os.path.normpath(vmt_data["$basetexture"])
        base_texture_path = find_texture_file(materials_dir, base_texture_rel_path)
        if base_texture_path:
            print(f"Base texture found: {base_texture_path}")
            vmat_data["TextureColor"] = "materials/" + os.path.relpath(base_texture_path, materials_dir).replace(os.sep, "/")
            roughness_map_path = generate_roughness_map(base_texture_path, base_texture_path)
            vmat_data["TextureRoughness"] = "materials/" + os.path.relpath(roughness_map_path, materials_dir).replace(os.sep, "/")
        else:
            print(f"Base texture file does not exist: {base_texture_path}")
    else:
        print(f"No base texture found in VMT: {vmt_data}")

    # Handle bump map
    if "$bumpmap" in vmt_data:
        bumpmap_rel_path = os.path.normpath(vmt_data["$bumpmap"])
        bumpmap_path = find_texture_file(materials_dir, bumpmap_rel_path)
        if bumpmap_path:
            print(f"Bump map found: {bumpmap_path}")
            if "ssbump" in bumpmap_path.lower():
                normal_map_path = convert_ssbump_to_normal(bumpmap_path, bumpmap_path.replace("ssbump", "normal"))
                vmat_data["TextureNormal"] = "materials/" + os.path.relpath(normal_map_path, materials_dir).replace(os.sep, "/")
            else:
                vmat_data["TextureNormal"] = "materials/" + os.path.relpath(bumpmap_path, materials_dir).replace(os.sep, "/")
        else:
            print(f"Bump map file does not exist: {bumpmap_path}")
    else:
        print(f"No bump map found in VMT: {vmt_data}")

    # Compile textures section conditionally
    vmat_data["CompiledTextures"] = {
        "g_tColor": vmat_data.get("TextureColor", ""),
        "g_tNormal": vmat_data.get("TextureNormal", ""),
        "g_tRoughness": vmat_data.get("TextureRoughness", "")
    }

    # Filter out empty textures
    vmat_data["CompiledTextures"] = {k: v for k, v in vmat_data["CompiledTextures"].items() if v}

    # Add tags to help users
    vmat_data["Attributes"] = {
        "MaterialType": "Brick",  # Example, could be based on the material
        "Surface": "Rough",
        "ShaderType": "Complex",
        "Project": "UrbanEnvironment",
        "Author": "AutoConverted",  # This could be set dynamically
        "Notes": "Auto-generated from VMT",
        "Version": "1.0",
        "DateCreated": "2024-08-25"
    }

    return vmat_data

def write_vmat(vmat_path, vmat_data):
    """Writes out the basic VMAT structure with conditional attributes."""
    with open(vmat_path, 'w') as vmat_file:
        vmat_file.write(f'"Layer0"\n{{\n')
        vmat_file.write(f'    "shader"    "{vmat_data["shader"]}"\n')
        
        for key, value in vmat_data.items():
            if key not in ["CompiledTextures", "shader"]:
                vmat_file.write(f'    "{key}"    "{value}"\n')
        
        # Handle Compiled Textures
        if vmat_data["CompiledTextures"]:
            vmat_file.write(f'    "Compiled Textures"\n    {{\n')
            for texture, path in vmat_data["CompiledTextures"].items():
                if path:  # Only write if the path is not empty
                    vmat_file.write(f'        "{texture}"    "{path}"\n')
            vmat_file.write(f'    }}\n')
        
        vmat_file.write(f'}}\n')

def convert_vmt_folder(input_dir):
    """Recursively converts all VMT files in the input directory to VMAT files in the same directory."""
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.endswith(".vmt"):
                vmt_path = os.path.join(root, file)
                vmt_dir = os.path.dirname(vmt_path)
                materials_dir = input_dir  # Assuming input_dir is the materials directory
                vmat_output_path = os.path.splitext(vmt_path)[0] + ".vmat"
                
                vmt_data = parse_vmt(vmt_path)
                vmat_data = map_vmt_to_vmat_basic(vmt_data, vmt_dir, materials_dir)
                
                write_vmat(vmat_output_path, vmat_data)
                
                if "$basetexture" in vmt_data:
                    base_texture_path = find_texture_file(materials_dir, vmt_data["$basetexture"])
                    if base_texture_path:
                        generate_roughness_map(base_texture_path, base_texture_path)

# Example usage:
input_directory = r"C:\*********\materials"  # Replace with your input directory
convert_vmt_folder(input_directory)
