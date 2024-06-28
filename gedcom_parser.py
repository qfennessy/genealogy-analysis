from gedcom.element.individual import IndividualElement
from gedcom.element.family import FamilyElement
from gedcom.parser import Parser
from collections import defaultdict

class GedcomParser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.individuals = defaultdict(dict)
        self.families = defaultdict(dict)
        self.gedcom_parser = Parser()

    def parse(self):
        self.gedcom_parser.parse_file(self.file_path)
        root_child_elements = self.gedcom_parser.get_root_child_elements()

        for element in root_child_elements:
            if isinstance(element, IndividualElement):
                self._parse_individual(element)
            elif isinstance(element, FamilyElement):
                self._parse_family(element)

    def _parse_individual(self, individual):
        ind_id = individual.get_pointer()
        self.individuals[ind_id]['name'] = individual.get_name()
        self.individuals[ind_id]['birth'] = self._get_event_date(individual, 'BIRT')
        self.individuals[ind_id]['death'] = self._get_event_date(individual, 'DEAT')

    def _parse_family(self, family):
        fam_id = family.get_pointer()
        self.families[fam_id]['husband'] = self._get_family_member(family, 'HUSB')
        self.families[fam_id]['wife'] = self._get_family_member(family, 'WIFE')
        self.families[fam_id]['children'] = self._get_family_members(family, 'CHIL')

    def _get_event_date(self, individual, event_tag):
        for child in individual.get_child_elements():
            if child.get_tag() == event_tag:
                for date_element in child.get_child_elements():
                    if date_element.get_tag() == 'DATE':
                        return date_element.get_value()
        return None

    def _get_family_member(self, family, member_tag):
        for child in family.get_child_elements():
            if child.get_tag() == member_tag:
                return child.get_value()
        return None

    def _get_family_members(self, family, member_tag):
        members = []
        for child in family.get_child_elements():
            if child.get_tag() == member_tag:
                members.append(child.get_value())
        return members

    def get_parsed_data(self):
        return {
            'individuals': dict(self.individuals),
            'families': dict(self.families)
        }

# Usage example
if __name__ == "__main__":
    try:
        parser = GedcomParser("Fennessy.ged")
        parser.parse()
        parsed_data = parser.get_parsed_data()
        
        print(f"Total individuals: {len(parsed_data['individuals'])}")
        print(f"Total families: {len(parsed_data['families'])}")
        
        # Example: Print names of all individuals
        for ind_id, ind_data in parsed_data['individuals'].items():
            print(f"Individual {ind_id}: {ind_data['name']}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("Please check that the GEDCOM file path is correct and the file is accessible.")