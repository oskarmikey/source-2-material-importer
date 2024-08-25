# vmt to vmat enhanced GUI - Enhanced GUI Conversion Tool

# EXTREAM WARNING Im remaking this becasue if i remeber correctly this one doesn't work properly but i pushed away. allso i mainly have made this for tf2


**Warning:** This is an active project, and the current version may still be under development. Some functionalities or instructions might not be up-to-date or may change in future updates.

**Overview**

**vmt to vmat enhanced** is a versatile tool designed to convert `.vmt` files (Valve Material Type) to `.vmat` files (Valve Material Asset) and generate roughness maps from texture files. It is ideal for automating the conversion of materials to a format compatible with Source 2 tools, with the added capability of processing texture files for roughness mapping.

**Prerequisites**

- **Python 3.x:** Ensure you have Python 3.x installed on your system. You can download it from python.org.

- **Required Python Libraries:** This script uses the standard Python libraries and the `Pillow` library for image processing. You can install Pillow using:

		pip install pillow

**Installation**

**1. Clone the Repository**

Open your terminal or command prompt and clone the repository to your local machine:

	git clone https://github.com/oskarmikey/vmt-to-vmat-enhanced-GUI/blob/main/source2_vmt_material_converter.py

**2. Navigate to the Script Directory**

Change to the directory containing the script:

	cd source2_vmt_material_converter

**Usage**

**Graphical User Interface (GUI)**

The primary method of using **VMT2VMATPro** is through its graphical user interface (GUI). Run the script using:

	python source2_vmt_material_converter.py

**GUI Instructions**

1. **Material Directory:** Specify the directory containing `.vmt` files and textures.
2. **Backup Directory:** Set a directory where original `.vmt` files will be backed up.
3. **Texture Format:** Choose the texture format for conversion (e.g., `tga`, `png`, `jpg`, `dds`, `bmp`).
4. **Overwrite Options:** Select whether to overwrite existing `.vmat` files and texture files.
5. **Generate Roughness Maps:** Check this option to generate roughness maps along with the conversion.
6. **Darkness Value:** Adjust the darkness value for the roughness map generation.

Click **Convert** to start the process. The progress will be displayed on the GUI.

**Example**

To convert all `.vmt` files and generate roughness maps, simply follow the instructions on the GUI. The tool will handle the rest, including logging the progress and handling any issues.

**File Structure**

- **Input Directory:** Place your `.vmt` files and texture files here.
- **Backup Directory:** Backups of the original `.vmt` files will be saved here.
- **Output Directory:** Converted `.vmat` files and generated roughness maps will be saved here.

**Notes**

- Ensure that all `.vmt` files have corresponding texture files for accurate conversion.
- If a `.vmt` file does not have an associated texture file, the script will log a warning but continue processing other files.

**Troubleshooting**

- **File Not Found Errors:** Verify that the input directory path is correct and contains the necessary files.
- **Permission Issues:** Ensure you have the appropriate read/write permissions for the directories involved.

**License**

This script is licensed under the MIT License.

**Contact**

For questions or issues, please open an issue on the [GitHub repository](https://github.com/oskarmikey/vmt-to-vmat-enhanced-GUI/issues) or contact the repository maintainer.

**Credits**

**BIG CREDITS TO** [AlpyneDreams](https://github.com/AlpyneDreams/source2utils/blob/master/utils/vmt_to_vmat.py) for the foundational work on VMT to VMAT conversion. Their implementation was instrumental in developing this tool.
