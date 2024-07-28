# How to Use
***Overview***
This script converts .vmt files (Valve Material Type) to .vmat files (Valve Material Asset) and optionally processes .vtf files (Valve Texture Format) for use in Source 2 engine environments. 
It automates the conversion of materials to a format compatible with Source 2 tools.

# Prerequisites	
 ***Python 3.x***: Ensure you have Python 3.x installed on your system. You can download it from python.org.

***Required Python Libraries***: The script uses standard Python libraries. No additional installations are required unless specified otherwise.
Installation

**1 Clone the Repository**
Open your terminal or command prompt and clone the repository to your local machine:

		git clone https://github.com/oskarmikey/Vmt-to-Vmat-converter-with-Gui.git

**2 Navigate to the Script Directory**
Change to the directory containing the script:

	 cd your repository
# Usage
Command-Line Interface
The script can be executed from the command line with the following syntax:

	python sourcce2_material_converter.py [options]

## **Options**
##### --input-dir <directory>: Specify the directory containing .vmt and .vtf files to be converted. The script will process all files in this directory.
	python sourcce2_material_converter.py --input-dir path/to/input

##### --output-dir <directory>: Specify the directory where the converted .vmat files will be saved. If not provided, the converted files will be saved in the same directory as the input files.
	python sourcce2_material_converter.py --input-dir path/to/input --output-dir path/to/output

##### --verbose: Enable verbose logging to see detailed output and debugging information.
	python sourcce2_material_converter.py --input-dir path/to/input --verbose


### **Example**
To convert all .vmt files in the materials directory and save the output to the converted_materials directory, use:

	python sourcce2_material_converter.py --input-dir materials --output-dir converted_materials

### File Structure
Input Directory: Place your .vmt and .vtf files here.
Output Directory: Converted .vmat files will be saved here.
Notes

The script assumes that all .vmt files have corresponding .vtf files in the same directory. 

Ensure that texture files are present for accurate conversion.
If a .vmt file does not have an associated .vtf file, the script will log a warning but continue processing other files.



## Troubleshooting
***File Not Found Errors***: Ensure that the input directory path is correct and that it contains .vmt and .vtf files.

***Permission Issues***: Ensure you have the necessary read/write permissions for the directories involved.

i aint ading more shait here

## License
This script is licensed under the MIT License.

## Contact
For questions or issues, please open an issue on the GitHub repository or contact the repository maintainer. 
actually don't i made all of this from a template cause im tired of dealing with this crap for two days. ima probably change the name of the repo and purpose of it later anyway to include more parts of the proces of converting source 1 stuff to source 2 cause im tired of crapy ones and cant find good ones
		

i almost forgot
BIG CREDITS TO https://github.com/AlpyneDreams/source2utils/blob/master/utils/vmt_to_vmat.py
christe i had mamny isues with the first way i trid to make the script until i took a look at how they did it.






