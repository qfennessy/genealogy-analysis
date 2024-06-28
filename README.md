# GEDCOM Parser and Validator

## Overview
This Python script parses GEDCOM (Genealogical Data Communication) files, extracts relevant information about individuals and families, and performs advanced data validation to identify logical inconsistencies in genealogical data.

## Features
- Parses GEDCOM files and extracts information about individuals and families
- Validates and cleans data during parsing
- Performs advanced data validation, including:
  - Checking for logical inconsistencies in birth and death dates
  - Validating parent-child relationships
  - Verifying marriage dates against individual birth dates
- Provides a list of validation issues for further investigation

## Requirements
- Python 3.6+
- `python-gedcom` library

## Installation
1. Ensure you have Python 3.6 or higher installed on your system.
2. Install the required library:
   ```
   pip install python-gedcom
   ```

## Usage
1. Save the `gedcom_parser.py` script to your local machine.
2. Replace `"path_to_your_gedcom_file.ged"` in the script with the actual path to your GEDCOM file.
3. Run the script:
   ```
   python gedcom_parser.py
   ```
4. The script will output:
   - Total number of individuals and families parsed
   - A list of any validation issues found

## Code Structure
- `GedcomParser` class: The main class for parsing and validating GEDCOM data
  - `parse()`: Parses the GEDCOM file
  - `validate_data()`: Performs advanced data validation
  - `get_parsed_data()`: Returns the parsed data
  - `get_validation_issues()`: Returns a list of validation issues

## Data Validation
The script performs the following validations:
1. Date Validation:
   - Birth date after death date
   - Death date in the future
   - Birth date in the future
2. Family Relationship Validation:
   - Parent born after child
3. Marriage Date Validation:
   - Marriage date before spouse's birth
   - Marriage date after child's birth

## Future Improvements
- Expand validation to include more checks (e.g., age gaps between siblings, self-ancestry)
- Implement severity levels for validation issues (e.g., error, warning)
- Develop suggestions for correcting common validation issues
- Create a structured report generation feature
- Add support for exporting parsed data to various formats (e.g., CSV, JSON)
- Implement a graphical user interface for easier interaction

## Contributing
Contributions to improve the parser or extend its functionality are welcome. Please feel free to submit pull requests or open issues for bugs and feature requests.

## License
[Specify your chosen license here]

## Disclaimer
This parser is provided as-is and may not cover all possible GEDCOM structures or edge cases. Always verify the parsed data against the original GEDCOM file for critical applications.