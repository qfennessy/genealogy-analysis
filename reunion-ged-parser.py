import re
from collections import defaultdict
from datetime import datetime, date

class GedcomParser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.individuals = {}
        self.families = {}
        self.current_record = None
        self.current_tag = None

    def parse(self):
        with open(self.file_path, 'r') as file:
            for line in file:
                self._parse_line(line.strip())

    def _parse_line(self, line):
        parts = line.split(' ', 2)
        level = int(parts[0])
        
        if len(parts) > 2 and parts[1].startswith('@'):
            tag = parts[2]
            xref_id = parts[1]
        else:
            tag = parts[1]
            xref_id = None
        
        value = ' '.join(parts[2:]) if len(parts) > 2 else ''

        if level == 0:
            self._handle_level_0(tag, xref_id, value)
        elif level == 1:
            self._handle_level_1(tag, value)
        elif level == 2:
            self._handle_level_2(tag, value)

    def _handle_level_0(self, tag, xref_id, value):
        if tag == 'INDI':
            self.current_record = {'id': xref_id, 'type': 'INDI'}
            self.individuals[xref_id] = self.current_record
        elif tag == 'FAM':
            self.current_record = {'id': xref_id, 'type': 'FAM'}
            self.families[xref_id] = self.current_record

    def _handle_level_1(self, tag, value):
        if self.current_record:
            if tag in ['NAME', 'SEX', 'BIRT', 'DEAT', 'FAMS', 'FAMC']:
                self.current_tag = tag
                if tag not in ['BIRT', 'DEAT']:
                    self.current_record[tag] = value

    def _handle_level_2(self, tag, value):
        if self.current_record and self.current_tag:
            if self.current_tag in ['BIRT', 'DEAT'] and tag == 'DATE':
                self.current_record[self.current_tag] = {'DATE': self._parse_date(value)}

    def _parse_date(self, date_string):
        # This is a very basic date parser and would need to be more robust for real use
        try:
            return datetime.strptime(date_string, "%d %b %Y").date()
        except ValueError:
            return date_string  # Return as string if parsing fails

    def get_individuals(self):
        return self.individuals

    def get_families(self):
        return self.families

# Usage
parser = GedcomParser('whittemore-st-descendants.ged')
parser.parse()
individuals = parser.get_individuals()
families = parser.get_families()

# Print some basic information
print(f"Number of individuals: {len(individuals)}")
print(f"Number of families: {len(families)}")

# Print details of the first individual
first_individual = next(iter(individuals.values()))
print("\nFirst Individual:")
print(f"ID: {first_individual['id']}")
print(f"Name: {first_individual.get('NAME', 'Unknown')}")
print(f"Birth: {first_individual.get('BIRT', {}).get('DATE', 'Unknown')}")