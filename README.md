# GEDCOM Parser, Analyzer, and Visualizer

## Overview
This Python script parses GEDCOM (Genealogical Data Communication) files, extracts relevant information about individuals and families, performs advanced data validation, analyzes the genealogical data, and generates visualizations.

## Features
- Parses GEDCOM files and extracts information about individuals and families
- Validates and cleans data during parsing
- Performs advanced data validation
- Analyzes genealogical data (e.g., name frequencies, birth date ranges, family sizes)
- Generates visualizations (e.g., name frequency charts, birth year distributions, family trees)
- Produces CSV and HTML reports of validation issues

## Requirements
- Python 3.6+
- Required libraries: `gedcom`, `matplotlib`, `networkx`

## Installation
1. Ensure you have Python 3.6 or higher installed on your system.
2. Install the required libraries:
3. pip install python-gedcom matplotlib networkx

## Usage
1. Save the script to your local machine.
2. Run the script with the following command-line arguments:
python gedcom_parser.py --gedcom_file path_to_your_gedcom_file.ged [--demo] [--visualize] [--tree_root ROOT_ID]
Copy- `--gedcom_file`: Path to your GEDCOM file (required)
- `--demo`: Run demonstration functions (optional)
- `--visualize`: Generate visualizations (optional)
- `--tree_root`: ID of the root individual for family tree visualization (optional)

## Code Structure
- `Event`, `Individual`, `Family`: Data classes for storing genealogical information
- `GedcomData`: Class for storing and accessing parsed GEDCOM data
- `VisualizationEngine`: Class for generating visualizations
- `AnalysisEngine`: Class for analyzing genealogical data
- `GedcomParser`: Main class for parsing and validating GEDCOM data

## Data Validation
The script performs various validations, including:
- Date consistency (birth, death, marriage)
- Logical family relationships
- Marriage date consistency

## Analysis
The script can perform various analyses, including:
- Name frequency analysis
- Birth and death date range analysis
- Family size analysis
- Average lifespan calculation
- Marriage age analysis

## Visualizations
The script can generate the following visualizations:
- Name frequency chart
- Birth year distribution
- Family size distribution
- Family tree

## Output
- Console output of basic statistics and analysis results
- CSV report of validation issues
- HTML report of validation issues
- Visualization files (PNG format)

## Future Improvements
- Implement more advanced validation checks
- Add more analysis functions
- Improve visualization capabilities
- Implement a graphical user interface

## Contributing
Contributions to improve the parser or extend its functionality are welcome. Please feel free to submit pull requests or open issues for bugs and feature requests.

## License
[Specify your chosen license here]

## Disclaimer
This parser is provided as-is and may not cover all possible GEDCOM structures or edge cases. Always verify the parsed data against the original GEDCOM file for critical applications.
