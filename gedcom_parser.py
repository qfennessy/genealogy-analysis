from gedcom.element.individual import IndividualElement
from gedcom.element.family import FamilyElement
from gedcom.parser import Parser
from collections import defaultdict
import re
from datetime import datetime, date

class GedcomParser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.individuals = defaultdict(lambda: defaultdict(lambda: None))
        self.families = defaultdict(lambda: defaultdict(lambda: None))
        self.gedcom_parser = Parser()
        self.validation_issues = []

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
        self.individuals[ind_id]['name'] = self._validate_name(individual.get_name())
        self.individuals[ind_id]['sex'] = self._validate_sex(self._get_sex(individual))
        self.individuals[ind_id]['birth'] = self._validate_event(self._get_event_details(individual, 'BIRT'))
        self.individuals[ind_id]['death'] = self._validate_event(self._get_event_details(individual, 'DEAT'))
        self.individuals[ind_id]['occupation'] = self._validate_list(self._get_occupation(individual))
        self.individuals[ind_id]['education'] = self._validate_list(self._get_education(individual))
        self.individuals[ind_id]['residence'] = self._validate_list(self._get_residence(individual))

    def _parse_family(self, family):
        fam_id = family.get_pointer()
        self.families[fam_id]['id'] = fam_id
        self.families[fam_id]['husband'] = self._validate_id(self._get_family_member(family, 'HUSB'))
        self.families[fam_id]['wife'] = self._validate_id(self._get_family_member(family, 'WIFE'))
        self.families[fam_id]['children'] = self._validate_list(self._get_family_members(family, 'CHIL'))
        self.families[fam_id]['marriage'] = self._validate_event(self._get_event_details(family, 'MARR'))
        self.families[fam_id]['divorce'] = self._validate_event(self._get_event_details(family, 'DIV'))

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
        return [child.get_value() for child in individual.get_child_elements() if child.get_tag() == 'OCCU']

    def _get_education(self, individual):
        return [child.get_value() for child in individual.get_child_elements() if child.get_tag() == 'EDUC']

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
        return residences

    def _get_family_member(self, family, member_tag):
        for child in family.get_child_elements():
            if child.get_tag() == member_tag:
                return child.get_value()
        return None

    def _get_family_members(self, family, member_tag):
        return [child.get_value() for child in family.get_child_elements() if child.get_tag() == member_tag]

    # Validation methods
    def _validate_name(self, name):
        if not name:
            return "Unknown"
        if isinstance(name, tuple):
            # If name is a tuple, join its non-empty parts
            return ' '.join(part for part in name if part)
        elif isinstance(name, str):
            # If name is a string, remove extra spaces
            return ' '.join(name.split())
        else:
            # If name is neither tuple nor string, return as is
            return str(name)

    def _validate_sex(self, sex):
        if sex in ['M', 'F']:
            return sex
        return 'U'  # Unknown

    def _validate_date(self, date_str):
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%d %b %Y").date()
        except ValueError:
            try:
                return datetime.strptime(date_str, "%b %Y").date().replace(day=1)
            except ValueError:
                try:
                    return datetime.strptime(date_str, "%Y").date().replace(month=1, day=1)
                except ValueError:
                    return None

    def _validate_place(self, place):
        if not place:
            return None
        return place.strip()

    def _validate_event(self, event):
        if not event:
            return None
        return {
            'date': self._validate_date(event.get('date')),
            'place': self._validate_place(event.get('place'))
        }

    def _validate_list(self, items):
        if not items:
            return []
        return [item for item in items if item]

    def _validate_id(self, id_str):
        if not id_str:
            return None
        return id_str if re.match(r'@[^@]+@', id_str) else None

    def get_parsed_data(self):
        return {
            'individuals': dict(self.individuals),
            'families': dict(self.families)
        }
    
    def validate_data(self):
        self._validate_dates()
        self._validate_family_relationships()
        self._validate_marriage_dates()


    def _validate_dates(self):
        for ind_id, individual in self.individuals.items():
            name = individual['name']
            birth_date = individual['birth']['date'] if individual['birth'] else None
            death_date = individual['death']['date'] if individual['death'] else None

            if birth_date and death_date and birth_date > death_date:
                self.validation_issues.append(
                    f"Individual {ind_id} ({name}): Birth date ({birth_date}) is after death date ({death_date})")

            if death_date and death_date > date.today():
                self.validation_issues.append(
                    f"Individual {ind_id} ({name}): Death date ({death_date}) is in the future")

            if birth_date and birth_date > date.today():
                self.validation_issues.append(
                    f"Individual {ind_id} ({name}): Birth date ({birth_date}) is in the future")


    def _get_individual_info(self, ind_id):
        if ind_id and ind_id in self.individuals:
            ind = self.individuals[ind_id]
            name = ind['name']
            birth = ind['birth']['date'] if ind['birth'] else 'Unknown'
            return f"{ind_id}: {name}, born {birth}"
        return "Unknown"

    def _validate_family_relationships(self):
        for fam_id, family in self.families.items():
            father_id = family['husband']
            mother_id = family['wife']
            children_ids = family['children']

            father_info = self._get_individual_info(father_id)
            mother_info = self._get_individual_info(mother_id)

            family_description = f"Family {fam_id} - Father: {father_info}, Mother: {mother_info}"

            if father_id:
                father = self.individuals[father_id]
                father_birth = father['birth']['date'] if father['birth'] else None

                for child_id in children_ids:
                    child = self.individuals[child_id]
                    child_name = child['name']
                    child_birth = child['birth']['date'] if child['birth'] else None

                    if father_birth and child_birth and father_birth > child_birth:
                        self.validation_issues.append(
                            f"{family_description}\n"
                            f"  Issue: Father born after child ({child_id}: {child_name}, born {child_birth})")

            if mother_id:
                mother = self.individuals[mother_id]
                mother_birth = mother['birth']['date'] if mother['birth'] else None

                for child_id in children_ids:
                    child = self.individuals[child_id]
                    child_name = child['name']
                    child_birth = child['birth']['date'] if child['birth'] else None

                    if mother_birth and child_birth and mother_birth > child_birth:
                        self.validation_issues.append(
                            f"{family_description}\n"
                            f"  Issue: Mother born after child ({child_id}: {child_name}, born {child_birth})")

    def _validate_marriage_dates(self):
        for fam_id, family in self.families.items():
            marriage_date = family['marriage']['date'] if family['marriage'] else None
            husband_id = family['husband']
            wife_id = family['wife']

            father_info = self._get_individual_info(husband_id)
            mother_info = self._get_individual_info(wife_id)

            family_description = f"Family {fam_id} - Father: {father_info}, Mother: {mother_info}"

            if marriage_date:
                if husband_id:
                    husband = self.individuals[husband_id]
                    husband_birth = husband['birth']['date'] if husband['birth'] else None
                    if husband_birth and marriage_date < husband_birth:
                        self.validation_issues.append(
                            f"{family_description}\n"
                            f"  Issue: Marriage date ({marriage_date}) before husband's birth")

                if wife_id:
                    wife = self.individuals[wife_id]
                    wife_birth = wife['birth']['date'] if wife['birth'] else None
                    if wife_birth and marriage_date < wife_birth:
                        self.validation_issues.append(
                            f"{family_description}\n"
                            f"  Issue: Marriage date ({marriage_date}) before wife's birth")

                for child_id in family['children']:
                    child = self.individuals[child_id]
                    child_name = child['name']
                    child_birth = child['birth']['date'] if child['birth'] else None
                    if child_birth and marriage_date > child_birth:
                        self.validation_issues.append(
                            f"{family_description}\n"
                            f"  Issue: Marriage date ({marriage_date}) after child's birth "
                            f"({child_id}: {child_name}, born {child_birth})")

    def get_validation_issues(self):
        return self.validation_issues

# Usage example
if __name__ == "__main__":
    try:
        parser = GedcomParser("path_to_your_gedcom_file.ged")
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

# New demonstration code
def demonstrate_validation(parsed_data):
    print("\nValidation Demonstration:")
    
    # Demonstrate name validation
    print("\n1. Name Validation:")
    for ind_id, individual in parsed_data['individuals'].items():
        print(f"  Individual {ind_id}: {individual['name']}")
        if len(parsed_data['individuals']) >= 3:  # Stop after 3 examples
            break

    # Demonstrate sex validation
    print("\n2. Sex Validation:")
    for ind_id, individual in parsed_data['individuals'].items():
        print(f"  Individual {ind_id}: Sex = {individual['sex']}")
        if len(parsed_data['individuals']) >= 3:  # Stop after 3 examples
            break

    # Demonstrate date validation
    print("\n3. Date Validation:")
    for ind_id, individual in parsed_data['individuals'].items():
        birth = individual['birth']
        death = individual['death']
        print(f"  Individual {ind_id}:")
        print(f"    Birth: {birth['date'] if birth else 'Unknown'}")
        print(f"    Death: {death['date'] if death else 'Unknown'}")
        if len(parsed_data['individuals']) >= 3:  # Stop after 3 examples
            break

    # Demonstrate place validation
    print("\n4. Place Validation:")
    for ind_id, individual in parsed_data['individuals'].items():
        birth = individual['birth']
        death = individual['death']
        print(f"  Individual {ind_id}:")
        print(f"    Birth Place: {birth['place'] if birth else 'Unknown'}")
        print(f"    Death Place: {death['place'] if death else 'Unknown'}")
        if len(parsed_data['individuals']) >= 3:  # Stop after 3 examples
            break

    # Demonstrate list validation (e.g., occupations)
    print("\n5. List Validation (Occupations):")
    for ind_id, individual in parsed_data['individuals'].items():
        occupations = individual['occupation']
        print(f"  Individual {ind_id}: Occupations = {occupations}")
        if len(parsed_data['individuals']) >= 3:  # Stop after 3 examples
            break

    # Demonstrate family validation
    print("\n6. Family Validation:")
    for fam_id, family in parsed_data['families'].items():
        print(f"  Family {fam_id}:")
        print(f"    Husband: {family['husband']}")
        print(f"    Wife: {family['wife']}")
        print(f"    Children: {family['children']}")
        print(f"    Marriage: {family['marriage']}")
        if len(parsed_data['families']) >= 3:  # Stop after 3 examples
            break

if __name__ == "__main__":
    try:
        parser = GedcomParser("path_to_your_gedcom_file.ged")
        parser.parse()
        parser.validate_data()
        parsed_data = parser.get_parsed_data()
        validation_issues = parser.get_validation_issues()
        
        print(f"Total individuals: {len(parsed_data['individuals'])}")
        print(f"Total families: {len(parsed_data['families'])}")
        
        print("\nValidation Issues:")
        if validation_issues:
            for issue in validation_issues:
                print(f"- {issue}")
        else:
            print("No validation issues found.")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("Please check that the GEDCOM file path is correct and the file is accessible.")