import csv
import lp_maker as lpm
import lpsolve55 as lps
from argparse import ArgumentParser
from collections import OrderedDict

CSV_OUT = 'out.csv'
LP_OUT = 'out.lp'
SECTION_CAP = 1 # currently set to 1 for assigning TAs, real cap is 32
SECTS_PER_STUD = 1 # currently set to 2 for assigning TAs, use 2 for class
SECTIONS = {'M 0330-0500 PM W 0400-0530 PM': (130, 131, 132),
            'M 0500-0630 PM W 0500-0630 PM': (135,),
            'M 0500-0630 PM W 0530-0700 PM': (133, 134),
            'M 0630-0800 PM W 0630-0800 PM': (138,),
            'M 0630-0800 PM W 0700-0830 PM': (136, 137),
            'Tu 0930-1100 AM Th 0930-1100 AM': (111, 112, 113),
            'Tu 1100-1230 PM Th 1100-1230 PM': (114, 115, 116),
            'Tu 1230-0200 PM Th 1230-0200 PM': (117, 118, 119),
            'Tu 0200-0330 PM Th 0200-0330 PM': (120, 121),
            'Tu 0330-0500 PM Th 0330-0500 PM': (122, 123),
            'Tu 0500-0630 PM Th 0500-0630 PM': (124, 125),
            'Tu 0630-0800 PM Th 0630-0800 PM': (126, 127, 128),
            'Tu 0800-0930 PM Th 0800-0930 PM': (139, 140, 141),
            'W 0830-1000 AM F 0830-1000 AM': (143,),
            'W 0900-1030 AM F 0930-1100 AM': (129,),
            'W 1030-1200 PM F 1100-1230 PM': (142,)}
SECTIONS = OrderedDict(SECTIONS)
CONCURR_SECTIONS = ()
DEFAULT_RANK = 6

class Student:
    priorities = []

    def __init__(self, name, sid, email, rankings,
                 num_sections=SECTS_PER_STUD, priority=0):
        self.name = name
        self.sid = sid
        self.email = email
        self.num_sections = num_sections
        self.rankings = rankings
        self.priority = priority
        self.sections = set()
        Student.priorities.append(priority)

    @staticmethod
    def display(students):
        for student in students:
            print student

    def __repr__(self):
        return 'Student({0}, {1})'.format(self.name, self.sid, self.email,
                                          self.rankings)

    def __str__(self):
        return '{0}: {1}'.format(self.name, ', '.join((str(s) for s in
                                                       self.sections)))

    def __eq__(self, other):
        if not isinstance(other, Student):
            raise TypeError('can only compare with a Student')
        return other.name == self.name and other.email == self.email

    def __hash__(self):
        return hash(self.name + str(self.sid))


def import_students(csv_file, prioritize=False):
    """
    Returns a list of students with their specified rankings.
    """
    students = set()
    with open(csv_file, 'rU') as f:
        csvreader = csv.reader(f)
        num_s = len(csvreader.next()) - 3 # ignore first line -- headers
        for row in csvreader:
            name = row[1]
            sid = int(row[3])
            email = row[2]
            if prioritize:
                rankings = convert_to_rankings(row[4:-2])
                priority = int(row[-1])
                stud = Student(name, sid, email, rankings, priority=priority)
                students.discard(stud)
                students.add(stud)
            else:
                rankings = convert_to_rankings(row[4:-1])
                stud = Student(name, sid, email, rankings)
                students.discard(stud)
                students.add(stud)
    return sorted(students, key=lambda s: s.name.split()[-1])

def convert_to_rankings(pref_list):
    rankings = [DEFAULT_RANK for _ in SECTIONS]
    for i, s in enumerate(pref_list):
        rankings[SECTIONS.keys().index(s)] = i
    return rankings

def parse_results(res, students, M):
    i = 0
    for student in students:
        for section in range(M):
            if res[i] == 1:
                student.sections.add(SECTIONS[section])
            i += 1

def assign_sections(students, prioritize=False):
    """
    students: a list of student objects
    i = index of sections
    j = index of students
    The columns, x_i_j, go as follows:
        x_0_0, x_1_0, x_2_0, ..., x_0_1, ..., x_M_N
    """

    M = len(students[0].rankings) # number of section
    N = len(students)             # number of students

    f = make_obj_f(students, prioritize)
    A = make_coeff_m(M, N)
    b = make_b_v(students, M, N)
    e = make_e_v(M, N)
    v = [1 for _ in range(M*N)]

    lp = lpm.lp_maker(f, A, b, e, None, v)

    # set all variables to binary
    lps.lpsolve('set_binary', lp, v)
    # set lp to minimize the objective function
    lps.lpsolve('set_minim', lp)

    lps.lpsolve('write_lp', lp, LP_OUT)
    lps.lpsolve('solve', lp)
    res = lps.lpsolve('get_variables', lp)[0]
    lps.lpsolve('delete_lp', lp)
    parse_results(res, students, M)

def make_obj_f(students, prioritize):
    coeffs = []
    for student in students:
        if prioritize:
            s_rankings = [(r+1) * (max(Student.priorities)-student.priority+1)
                          for r in student.rankings]
        else:
            s_rankings = [r+1 for r in student.rankings]
        coeffs.extend(s_rankings)
    return coeffs

def make_coeff_m(M, N):
    m = []
    # COEFFICIENTS FOR CONSTRAINTS ON SECTION CAPS
    for x in range(M):
        tmp_zeroes = [0 for _ in range(M*N)]
        for y in range(x, M*N, M):
            tmp_zeroes[y] = 1
        m.append(tmp_zeroes)
    # COEFFICIENTS FOR CONSTRAINTS ON NUMBER OF SECTIONS PER STUDENT
    for x in range(N):
        tmp_zeroes = [0 for _ in range(M*N)]
        for y in range(x*M, (x+1)*M):
            tmp_zeroes[y] = 1
        m.append(tmp_zeroes)
    # COEFFICIENTS TO PREVENT CONCURRENT SECTION ASSIGNMENT
    if SECTS_PER_STUD > 1:
        for x in range(N):
            for concurr_s in CONCURR_SECTIONS:
                tmp_zeroes = [0 for _ in range(M*N)]
                for s in concurr_s:
                    tmp_zeroes[x*M+s] = 1
                m.append(tmp_zeroes)
    return m

def make_b_v(students, M, N):
    v = [SECTION_CAP for _ in range(M)] + [student.num_sections for student
                                           in students]
    if SECTS_PER_STUD > 1:
        v += [1 for _ in range(len(CONCURR_SECTIONS) * N)]
    return v

def make_e_v(M, N):
    v = [-1 for _ in range(M)] + [0 for _ in range(N)]
    if SECTS_PER_STUD > 1:
        v += [-1 for _ in range(len(CONCURR_SECTIONS) * N)]
    return v

def main(csv_file, prioritize):
    students = import_students(csv_file, prioritize)
    assign_sections(students, prioritize)
    Student.display(students)

if __name__ == '__main__':
    parser = ArgumentParser(description='creates optimal section assignment')
    parser.add_argument('-p', '--prioritize', action='store_true', help='give students with seniority priority')
    parser.add_argument('csv_file', help='csv file with section rankings')
    args = parser.parse_args()
    main(args.csv_file, args.prioritize)
