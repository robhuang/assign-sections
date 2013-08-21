import csv
import random
from argparse import ArgumentParser

SECTION_CAPACITY = 1  # currently set to 1 for assigning TAs, real cap is 32

class Student:
    def __init__(self, name, rankings):
        self.rankings = rankings
        self.section1, self.section2 = None, None
        self.rank1, self.rank2 = 0, 0

    def __repr__(self):
        return 'Student({0}, {1})'.format(self.name, self.rankings)

    def __str__(self):
        return 'Student({0})'.format(self.name)

class Section:
    def __init__(self, sect_id, capacity=SECTION_CAPACITY):
        self.sect_id = sect_id
        self.capacity = SECTION_CAPACITY
        self.students = []

    def __repr__(self):
        return 'Section({0})'.format(self.sect_id)

    def add(self, student):
        self.students.append(student)

    def pop_random(self):
        return self.students.pop(random.randint(0, len(self.students) - 1))

    @property
    def overcapacity(self):
        return len(self.students) > self.capacity

def import_rankings(csv_file):
    """
    Returns a list of students with their specified rankings.
    """
    with open(csv_file, 'rU') as f:
        csvreader = csv.reader(f)
        students = []
        for row in csvreader:
            students.append(Student(row[0], [int(s) for s in row[1:]]))
    return students

def assign_sections(students):
    """
    Returns a dictionary of sections mapped to their students.
    """
    sections = {}
    for student in students:
        preferred = student.rankings[0]
        if not in sections:
            new_section = Section(preferred)
            new_section.add(student)
            sections[preferred] = new_section
        else:
            sections[preferred].add(student)
    while True:
        studs_to_reassign = []
        for section in filter(lambda s: s.overflowing, sections):
            while section.overflowing:
                studs_to_reassign.append(section.pop_random())
        for student in studs_to_reassign:
            pass
        break

def section_overflow(sections):
    """
    Given a list of sections, returns whether any section is over capacity.
    """
    for section in section:
        if section.overcapacity:
            return True
    return False

def main(csv_file):
    import_rankings(csv_file)

if __name__ == '__main__':
    parser = ArgumentParser(description='creates optimal section assignment')
    parser.add_argument('csv_file', help='csv file with section rankings')
    args = parser.parse_args()
    main(args.csv_file)
