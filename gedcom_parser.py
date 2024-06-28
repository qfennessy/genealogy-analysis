from gedcom.element.individual import IndividualElement
from gedcom.element.family import FamilyElement
from gedcom.parser import Parser
from collections import defaultdict

class GedcomParser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.individuals = defaultdict(lambda: defaultdict(lambda: None))
        self.families = defaultdict(lambda: defaultdict(lambda: None))
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
        self.individuals[ind_id]['id'] = ind_id
        self.individuals[ind_id]['name'] = individual.get_name()
        self.individuals[ind_id]['sex'] = self._get_sex(individual)
        self.individuals[ind_id]['birth'] = self._get_event_details(individual, 'BIRT')
        self.individuals[ind_id]['death'] = self._get_event_details(individual, 'DEAT')
        self.individuals[ind_id]['occupation'] = self._get_occupation(individual)
        self.individuals[ind_id]['education'] = self._get_education(individual)
        self.individuals[ind_id]['residence'] = self._get_residence(individual)

    def _parse_family(self, family):
        fam_id = family.get_pointer()
        self.families[fam_id]['id'] = fam_id
        self.families[fam_id]['husband'] = self._get_family_member(family, 'HUSB')
        self.families[fam_id]['wife'] = self._get_family_member(family, 'WIFE')
        self.families[fam_id]['children'] = self._get_family_members(family, 'CHIL')
        self.families[fam_id]['marriage'] = self._get_event_details(family, 'MARR')
        self.families[fam_id]['divorce'] = self._get_event_details(family, 'DIV')

    def _get_sex(self, individual):
        for child in individual.get_child_elements():
            if child.get_tag() == 'SEX':
                return child.get_value()
        return None

    def _get_event_details(self, element, event_tag):
        for child in element.get_child_elements():
            if child.get_tag() == event_tag:
                date = place = None
                for event_detail in child.get_child_elements():
                    if event_detail.get_tag() == 'DATE':
                        date = event_detail.get_value()
                    elif event_detail.get_tag() == 'PLAC':
                        place = event_detail.get_value()
                return {'date': date, 'place': place}
        return None

    def _get_occupation(self, individual):
        occupations = []
        for child in individual.get_child_elements():
            if child.get_tag() == 'OCCU':
                occupations.append(child.get_value())
        return occupations if occupations else None

    def _get_education(self, individual):
        education = []
        for child in individual.get_child_elements():
            if child.get_tag() == 'EDUC':
                education.append(child.get_value())
        return education if education else None

    def _get_residence(self, individual):
        residences = []
        for child in individual.get_child_elements():
            if child.get_tag() == 'RESI':
                date = place = None
                for resi_detail in child.get_child_elements():
                    if resi_detail.get_tag() == 'DATE':
                        date = resi_detail.get_value()
                    elif resi_detail.get_tag() == 'PLAC':
                        place = resi_detail.get_value()
                residences.append({'date': date, 'place': place})
        return residences if residences else None

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
        
        # Example: Print detailed information for the first individual
        first_individual = next(iter(parsed_data['individuals'].values()))
        print("\nExample Individual Details:")
        for key, value in first_individual.items():
            print(f"{key}: {value}")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("Please check that the GEDCOM file path is correct and the file is accessible.")