import csv
import os
import argparse
from gedcom.element.individual import IndividualElement
from gedcom.element.family import FamilyElement
from gedcom.parser import Parser
from collections import defaultdict, Counter
import re
from datetime import datetime, date
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple

@dataclass
class Event:
    type: str
    date: Optional[date] = None
    place: Optional[str] = None

@dataclass
class Individual:
    id: str
    name: str
    sex: str
    birth: Optional[Event] = None
    death: Optional[Event] = None
    events: List[Event] = field(default_factory=list)
    occupations: List[str] = field(default_factory=list)
    education: List[str] = field(default_factory=list)
    residences: List[Event] = field(default_factory=list)
    families_as_spouse: List[str] = field(default_factory=list)
    families_as_child: List[str] = field(default_factory=list)

@dataclass
class Family:
    id: str
    husband_id: Optional[str] = None
    wife_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    marriage: Optional[Event] = None
    divorce: Optional[Event] = None

class GedcomData:
    def __init__(self):
        self.individuals: Dict[str, Individual] = {}
        self.families: Dict[str, Family] = {}

    def add_individual(self, individual: Individual):
        self.individuals[individual.id] = individual

    def add_family(self, family: Family):
        self.families[family.id] = family

    def get_individual(self, id: str) -> Optional[Individual]:
        return self.individuals.get(id)

    def get_family(self, id: str) -> Optional[Family]:
        return self.families.get(id)
    
class AnalysisEngine:
    def __init__(self, gedcom_data: GedcomData):
        self.gedcom_data = gedcom_data

    def analyze_name_frequency(self) -> Dict[str, int]:
        """Analyze the frequency of first names."""
        first_names = [individual.name.split()[0] for individual in self.gedcom_data.individuals.values()]
        return dict(Counter(first_names))

    def analyze_surname_frequency(self) -> Dict[str, int]:
        """Analyze the frequency of surnames."""
        surnames = [individual.name.split()[-1] for individual in self.gedcom_data.individuals.values()]
        return dict(Counter(surnames))

    def analyze_birth_date_range(self) -> Tuple[date, date]:
        """Find the earliest and latest birth dates."""
        birth_dates = [ind.birth.date for ind in self.gedcom_data.individuals.values() if ind.birth and ind.birth.date]
        return min(birth_dates), max(birth_dates)

    def analyze_death_date_range(self) -> Tuple[date, date]:
        """Find the earliest and latest death dates."""
        death_dates = [ind.death.date for ind in self.gedcom_data.individuals.values() if ind.death and ind.death.date]
        return min(death_dates), max(death_dates)

    def analyze_location_statistics(self) -> Dict[str, int]:
        """Analyze the frequency of birth places."""
        birth_places = [ind.birth.place for ind in self.gedcom_data.individuals.values() if ind.birth and ind.birth.place]
        return dict(Counter(birth_places))

    def analyze_average_lifespan(self) -> float:
        """Calculate the average lifespan of individuals with known birth and death dates."""
        lifespans = []
        for individual in self.gedcom_data.individuals.values():
            if individual.birth and individual.birth.date and individual.death and individual.death.date:
                lifespan = (individual.death.date - individual.birth.date).days / 365.25
                lifespans.append(lifespan)
        return sum(lifespans) / len(lifespans) if lifespans else 0

    def analyze_family_sizes(self) -> Dict[int, int]:
        """Analyze the distribution of family sizes (number of children)."""
        family_sizes = [len(family.children_ids) for family in self.gedcom_data.families.values()]
        return dict(Counter(family_sizes))

    def find_largest_families(self, n: int = 5) -> List[Tuple[str, int]]:
        """Find the n largest families by number of children."""
        families = [(fam.id, len(fam.children_ids)) for fam in self.gedcom_data.families.values()]
        return sorted(families, key=lambda x: x[1], reverse=True)[:n]

    def analyze_marriage_age(self) -> Dict[str, float]:
        """Calculate the average age at first marriage for males and females."""
        male_ages = []
        female_ages = []
        for family in self.gedcom_data.families.values():
            if family.marriage and family.marriage.date:
                if family.husband_id:
                    husband = self.gedcom_data.individuals[family.husband_id]
                    if husband.birth and husband.birth.date:
                        age = (family.marriage.date - husband.birth.date).days / 365.25
                        male_ages.append(age)
                if family.wife_id:
                    wife = self.gedcom_data.individuals[family.wife_id]
                    if wife.birth and wife.birth.date:
                        age = (family.marriage.date - wife.birth.date).days / 365.25
                        female_ages.append(age)
        return {
            "male": sum(male_ages) / len(male_ages) if male_ages else 0,
            "female": sum(female_ages) / len(female_ages) if female_ages else 0
        }

    def find_most_common_occupation(self) -> Tuple[str, int]:
        """Find the most common occupation."""
        occupations = [occ for ind in self.gedcom_data.individuals.values() for occ in ind.occupations]
        return Counter(occupations).most_common(1)[0] if occupations else ("Unknown", 0)

    def analyze_generation_span(self) -> int:
        """Calculate the number of generations in the family tree."""
        def get_generation(individual_id: str, generation: int = 0) -> int:
            individual = self.gedcom_data.individuals[individual_id]
            child_generations = [get_generation(child_id, generation + 1) 
                                 for family_id in individual.families_as_spouse
                                 for child_id in self.gedcom_data.families[family_id].children_ids]
            return max(child_generations) if child_generations else generation

        root_individuals = [ind.id for ind in self.gedcom_data.individuals.values() if not ind.families_as_child]
        return max(get_generation(root_id) for root_id in root_individuals) + 1

class GedcomParser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.gedcom_data = GedcomData()
        self.gedcom_parser = Parser()
        self.validation_issues = []
        self.issue_summary = defaultdict(int)

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
        ind = Individual(
            id=ind_id,
            name=self._validate_name(individual.get_name()),
            sex=self._validate_sex(self._get_sex(individual)),
            birth=self._validate_event(self._get_event_details(individual, 'BIRT')),
            death=self._validate_event(self._get_event_details(individual, 'DEAT')),
            occupations=self._validate_list(self._get_occupation(individual)),
            education=self._validate_list(self._get_education(individual)),
            residences=self._validate_list(self._get_residence(individual))
        )
        self.gedcom_data.add_individual(ind)

    def _parse_family(self, family):
        fam_id = family.get_pointer()
        fam = Family(
            id=fam_id,
            husband_id=self._validate_id(self._get_family_member(family, 'HUSB')),
            wife_id=self._validate_id(self._get_family_member(family, 'WIFE')),
            children_ids=self._validate_list(self._get_family_members(family, 'CHIL')),
            marriage=self._validate_event(self._get_event_details(family, 'MARR')),
            divorce=self._validate_event(self._get_event_details(family, 'DIV'))
        )
        self.gedcom_data.add_family(fam)

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
    
    def _validate_event(self, event_details):
        if not event_details:
            return None
        return Event(
            type=event_details.get('type', 'Unknown'),
            date=self._validate_date(event_details.get('date')),
            place=self._validate_place(event_details.get('place'))
        )

    def _validate_list(self, items):
        if not items:
            return []
        return [item for item in items if item]

    def _validate_id(self, id_str):
        if not id_str:
            return None
        return id_str if re.match(r'@[^@]+@', id_str) else None

    def get_parsed_data(self):
        return self.gedcom_data

    
    def validate_data(self):
        self._validate_dates()
        self._validate_family_relationships()
        self._validate_marriage_dates()


    def _validate_dates(self):
        for ind_id, individual in self.gedcom_data.individuals.items():
            name = individual.name
            birth_date = individual.birth.date if individual.birth else None
            death_date = individual.death.date if individual.death else None

            if birth_date and death_date and birth_date > death_date:
                self.validation_issues.append(
                    f"Individual {ind_id} ({name}): Birth date ({birth_date}) is after death date ({death_date})")

            if death_date and death_date > date.today():
                self.validation_issues.append(
                    f"Individual {ind_id} ({name}): Death date ({death_date}) is in the future")

            if birth_date and birth_date > date.today():
                self.validation_issues.append(
                    f"Individual {ind_id} ({name}): Birth date ({birth_date}) is in the future")

    def _validate_family_relationships(self):
        for fam_id, family in self.gedcom_data.families.items():
            father_id = family.husband_id
            mother_id = family.wife_id
            children_ids = family.children_ids

            father_info = self._get_individual_info(father_id)
            mother_info = self._get_individual_info(mother_id)

            family_description = f"Family {fam_id} - Father: {father_info}, Mother: {mother_info}"

            if father_id:
                father = self.gedcom_data.individuals[father_id]
                father_birth = father.birth.date if father.birth else None

                for child_id in children_ids:
                    child = self.gedcom_data.individuals[child_id]
                    child_name = child.name
                    child_birth = child.birth.date if child.birth else None

                    if father_birth and child_birth and father_birth > child_birth:
                        self.validation_issues.append(
                            f"{family_description}\n"
                            f"  Issue: Father born after child ({child_id}: {child_name}, born {child_birth})")


    def _get_individual_info(self, ind_id):
        if ind_id and ind_id in self.gedcom_data.individuals:
            ind = self.gedcom_data.individuals[ind_id]
            name = ind.name
            birth = ind.birth.date if ind.birth else 'Unknown'
            return f"{ind_id}: {name}, born {birth}"
        return "Unknown"

    def _validate_marriage_dates(self):
        for fam_id, family in self.gedcom_data.families.items():
            marriage_date = family.marriage.date if family.marriage else None
            husband_id = family.husband_id
            wife_id = family.wife_id

            father_info = self._get_individual_info(husband_id)
            mother_info = self._get_individual_info(wife_id)

            family_description = f"Family {fam_id} - Father: {father_info}, Mother: {mother_info}"

            if marriage_date:
                if husband_id:
                    husband = self.gedcom_data.individuals.get(husband_id)
                    if husband:
                        husband_birth = husband.birth.date if husband.birth else None
                        if husband_birth and marriage_date < husband_birth:
                            self.validation_issues.append(
                                f"{family_description}\n"
                                f"  Issue: Marriage date ({marriage_date}) before husband's birth")

                if wife_id:
                    wife = self.gedcom_data.individuals.get(wife_id)
                    if wife:
                        wife_birth = wife.birth.date if wife.birth else None
                        if wife_birth and marriage_date < wife_birth:
                            self.validation_issues.append(
                                f"{family_description}\n"
                                f"  Issue: Marriage date ({marriage_date}) before wife's birth")

                for child_id in family.children_ids:
                    child = self.gedcom_data.individuals.get(child_id)
                    if child:
                        child_name = child.name
                        child_birth = child.birth.date if child.birth else None
                        if child_birth and marriage_date > child_birth:
                            self.validation_issues.append(
                                f"{family_description}\n"
                                f"  Issue: Marriage date ({marriage_date}) after child's birth "
                                f"({child_id}: {child_name}, born {child_birth})")

    def get_validation_issues(self):
        return self.validation_issues
    

    def _categorize_issue(self, issue):
        if "born after child" in issue:
            return "Parent born after child"
        elif "Marriage date" in issue and "before" in issue:
            return "Marriage before birth"
        elif "Marriage date" in issue and "after child's birth" in issue:
            return "Child born before marriage"
        else:
            return "Other"

    def validate_data(self):
        self._validate_dates()
        self._validate_family_relationships()
        self._validate_marriage_dates()
        
        # Categorize issues and update summary
        for issue in self.validation_issues:
            category = self._categorize_issue(issue)
            self.issue_summary[category] += 1

    def get_summary_statistics(self):
        total_issues = len(self.validation_issues)
        return {
            "total_issues": total_issues,
            "issues_by_type": dict(self.issue_summary),
            "total_individuals": len(self.gedcom_data.individuals),
            "total_families": len(self.gedcom_data.families),
            "percent_families_with_issues": (len(set(issue.split(' - ')[0].split(' ')[1] for issue in self.validation_issues)) / len(self.gedcom_data.families)) * 100 if self.gedcom_data.families else 0
        }

    def generate_csv_report(self, output_file):
        summary_stats = self.get_summary_statistics()
        
        with open(output_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write summary statistics
            writer.writerow(["Summary Statistics"])
            writer.writerow(["Total Individuals", summary_stats["total_individuals"]])
            writer.writerow(["Total Families", summary_stats["total_families"]])
            writer.writerow(["Total Issues", summary_stats["total_issues"]])
            writer.writerow(["Percent of Families with Issues", f"{summary_stats['percent_families_with_issues']:.2f}%"])
            writer.writerow([])
            
            writer.writerow(["Issues by Type"])
            for issue_type, count in summary_stats["issues_by_type"].items():
                writer.writerow([issue_type, count])
            writer.writerow([])
            
            # Write individual issues
            writer.writerow(["Family ID", "Father", "Mother", "Issue"])
            for issue in self.validation_issues:
                family_info, issue_detail = issue.split('\n')
                family_id = family_info.split(' - ')[0].split(' ')[1]
                father = family_info.split('Father: ')[1].split(', Mother:')[0]
                mother = family_info.split('Mother: ')[1]
                writer.writerow([family_id, father, mother, issue_detail.strip()])

    def generate_html_report(self, output_file):
        summary_stats = self.get_summary_statistics()
        
        html_content = f"""
        <html>
        <head>
            <title>GEDCOM Validation Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
                th {{ background-color: #4CAF50; color: white; }}
                h1, h2 {{ color: #4CAF50; }}
            </style>
        </head>
        <body>
            <h1>GEDCOM Validation Report</h1>
            
            <h2>Summary Statistics</h2>
            <table>
                <tr><th>Metric</th><th>Value</th></tr>
                <tr><td>Total Individuals</td><td>{summary_stats["total_individuals"]}</td></tr>
                <tr><td>Total Families</td><td>{summary_stats["total_families"]}</td></tr>
                <tr><td>Total Issues</td><td>{summary_stats["total_issues"]}</td></tr>
                <tr><td>Percent of Families with Issues</td><td>{summary_stats["percent_families_with_issues"]:.2f}%</td></tr>
            </table>
            
            <h2>Issues by Type</h2>
            <table>
                <tr><th>Issue Type</th><th>Count</th></tr>
        """
        
        for issue_type, count in summary_stats["issues_by_type"].items():
            html_content += f"<tr><td>{issue_type}</td><td>{count}</td></tr>"
        
        html_content += """
            </table>
            
            <h2>Detailed Issues</h2>
            <table>
                <tr>
                    <th>Family ID</th>
                    <th>Father</th>
                    <th>Mother</th>
                    <th>Issue</th>
                </tr>
        """

        for issue in self.validation_issues:
            family_info, issue_detail = issue.split('\n')
            family_id = family_info.split(' - ')[0].split(' ')[1]
            father = family_info.split('Father: ')[1].split(', Mother:')[0]
            mother = family_info.split('Mother: ')[1]
            html_content += f"""
                <tr>
                    <td>{family_id}</td>
                    <td>{father}</td>
                    <td>{mother}</td>
                    <td>{issue_detail.strip()}</td>
                </tr>
            """

        html_content += """
            </table>
        </body>
        </html>
        """

        with open(output_file, 'w') as htmlfile:
            htmlfile.write(html_content)
    
def setup_argparser():
    parser = argparse.ArgumentParser(description='GEDCOM Parser and Validator')
    parser.add_argument('--gedcom_file', required=True, help='Path to the GEDCOM file')
    parser.add_argument('--demo', action='store_true', help='Run demonstration functions')
    return parser


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
        arg_parser = setup_argparser()
        args = arg_parser.parse_args()

        parser = GedcomParser(args.gedcom_file)
        parser.parse()

        if args.demo:
            parsed_data = parser.get_parsed_data()
            demonstrate_validation(parsed_data)
        else:
            parser.validate_data()
            summary_stats = parser.get_summary_statistics()
            
            print(f"Total individuals: {summary_stats['total_individuals']}")
            print(f"Total families: {summary_stats['total_families']}")
            print(f"Total issues: {summary_stats['total_issues']}")
            print(f"Percent of families with issues: {summary_stats['percent_families_with_issues']:.2f}%")
            
            print("\nIssues by Type:")
            for issue_type, count in summary_stats['issues_by_type'].items():
                print(f"- {issue_type}: {count}")
            
            # Generate reports
            script_dir = os.path.dirname(os.path.abspath(__file__))
            csv_report = os.path.join(script_dir, "gedcom_validation_report.csv")
            html_report = os.path.join(script_dir, "gedcom_validation_report.html")
            parser.generate_csv_report(csv_report)
            parser.generate_html_report(html_report)
            
            print(f"\nReports generated:")
            print(f"- CSV report: {csv_report}")
            print(f"- HTML report: {html_report}")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("Please check that the GEDCOM file path is correct and the file is accessible.")