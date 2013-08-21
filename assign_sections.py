import csv
from argparse import ArgumentParser

SECTION_CAP = 1    # currently set to 1 for assigning TAs, real cap is 32
SECTS_P_STUD = 2 # currently set to 1 for assigning TAs, real is 1

class Student:
    count = 0

    def __init__(self, name, rankings):
        self.rankings = rankings
        self.section1, self.section2 = None, None
        self.rank1, self.rank2 = 0, 0
        self.sid = Student.count
        Student.count += 1

    def __repr__(self):
        return 'Student({0}, {1})'.format(self.name, self.rankings)

    def __str__(self):
        return 'Student({0})'.format(self.name)

class Section:
    count = 0

    def __init__(self, sect_id, capacity=SECTION_CAPACITY):
        self.sect_id = sect_id
        self.capacity = SECTION_CAPACITY
        self.students = []
        self.sid = Section.count
        Section.count += 1

    def __repr__(self):
        return 'Section({0})'.format(self.sect_id)

    def add(self, student):
        self.students.append(student)

    def pop_random(self):
        return self.students.pop(random.randint(0, len(self.students) - 1))

    @property
    def overcapacity(self):
        return len(self.students) > self.capacity

def import_students(csv_file):
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

def assign_sections(students):
    """
    students: a list of student objects
    sections: a list of section numbers

    The columns, x_i_j, go as follows:
        x_0_0, x_1_0, x_2_0, ..., x_0_1, ..., x_i_j
    """

    M = len(students[0].rankings) # number of sections, each represented by i
    N = len(students)             # number of students, each represented by j

    # SET UP LPSOLVE
    lp = lpsolve('make_lp', M, M*N)
    lpsolve('set_verbose', lp, IMPORTANT)
    lpsolve('set_obj_fn', lp, make_obj_f(students))

    # ADD CONSTRAINTS FOR SECTION CAPACITY
    for i in range(M):
        lpsolve('add_constraint', lp, [1 for k in range(M*N)], LE, SECTION_CAP)

    # ADD CONSTRAINTS FOR NUMBER OF SECTIONS ASSIGNED TO EACH STUDENT
    for i in range(N):
        lpsolve('add_constraint', lp, [1 for k in range(M*N)], EQ, SECTS_P_STUD)

    for k in range(M*N):
        lpsolve('setupbo', lp, k, 1)

    lpsolve('write_lp', lp, 'a.lp')
    print lpsolve('get_mat', lp, 1, 2)
    lpsolve('solve', lp)
    print lpsolve('get_objective', lp)
    print lpsolve('get_variables', lp)[0]
    print lpsolve('get_constraints', lp)[0]
    lpsolve('delete_lp', lp)

def make_obj_f(students):
    l = []
    for student in students:
        l.extend(student.rankings)
    return l

def main(csv_file):
    students = import_students(csv_file)
    assign_sections(students)

if __name__ == '__main__':
    parser = ArgumentParser(description='creates optimal section assignment')
    parser.add_argument('csv_file', help='csv file with section rankings')
    args = parser.parse_args()
    main(args.csv_file)
