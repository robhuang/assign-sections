import csv
import random
import lp_maker as lpm
import lpsolve55 as lps
from argparse import ArgumentParser
from collections import OrderedDict

CSV_OUT = 'out.csv'
LP_OUT = 'out.lp'
SECTION_CAP = 32 # currently set to 1 for assigning TAs, real cap is 32
SECTS_PER_STUD = 1 # currently set to 2 for assigning TAs, use 2 for class
SECTIONS_TUP = (('M 0330-0500 PM W 0400-0530 PM', (30, 31, 32)),
                ('M 0500-0630 PM W 0500-0630 PM', (35,)),
                ('M 0500-0630 PM W 0530-0700 PM', (33, 34)),
                ('M 0630-0800 PM W 0630-0800 PM', (38,)),
                ('M 0630-0800 PM W 0700-0830 PM', (36, 37)),
                ('Tu 0930-1000 AM Th 0930-1000 AM', (11, 12, 13)),
                ('Tu 0100-0230 PM Th 0100-0230 PM', (14, 15, 16)),
                ('Tu 0230-0200 PM Th 0230-0200 PM', (17, 18, 19)),
                ('Tu 0200-0330 PM Th 0200-0330 PM', (20, 21)),
                ('Tu 0330-0500 PM Th 0330-0500 PM', (22, 23)),
                ('Tu 0500-0630 PM Th 0500-0630 PM', (24, 25)),
                ('Tu 0630-0800 PM Th 0630-0800 PM', (26, 27, 28)),
                ('Tu 0800-0930 PM Th 0800-0930 PM', (39, 40, 41)),
                ('W 0830-1000 AM F 0830-1000 AM', (43,)),
                ('W 0900-1030 AM F 0930-1100 AM', (29,)),
                ('W 1030-1200 PM F 1030-1200 PM', (42,)))
SECTIONS = OrderedDict(SECTIONS_TUP)
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


def import_students(csv_file, prioritize=False, analyze=False):
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
                if analyze:
                    stud.prefs = row[4:-2]
            else:
                rankings = convert_to_rankings(row[4:-1])
                stud = Student(name, sid, email, rankings)
                if analyze:
                    stud.prefs = row[4:-1]
            students.discard(stud)
            students.add(stud)
    return sorted(students, key=lambda s: s.name.split()[-1])

def convert_to_rankings(pref_list):
    rankings = [DEFAULT_RANK for _ in SECTIONS]
    for i, s in enumerate(pref_list):
        rankings[SECTIONS.keys().index(s)] = i
    return rankings

def parse_results(res, students, M, analyze=False):
    i = 0
    sects_enroll = dict((s, SECTION_CAP) for sects in SECTIONS.values() for s in
                        sects)
    if analyze:
        ranks = []
    for student in students:
        for section in range(M):
            if res[i] == 1:
                possible_sects = filter(lambda s: sects_enroll[s] > 0,
                                        SECTIONS[SECTIONS.keys()[section]])
                random_sect = random.choice(possible_sects)
                student.sections.add(random_sect)
                sects_enroll[random_sect] -= 1
                if analyze:
                    try:
                        ranks.append(student.prefs.index(
                                         SECTIONS.keys()[section]))
                    except ValueError:
                        ranks.append(DEFAULT_RANK)
            i += 1
    if analyze:
        print 'min: {0}, max: {1}, mean: {2}'.format(min(ranks), max(ranks),
                                                     sum(ranks)/len(ranks))

def assign_sections(students, prioritize=False, analyze=False):
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
    parse_results(res, students, M, analyze)

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
    v = [len(s) * SECTION_CAP for s in SECTIONS.values()] + \
        [student.num_sections for student in students]
    if SECTS_PER_STUD > 1:
        v += [1 for _ in range(len(CONCURR_SECTIONS) * N)]
    return v

def make_e_v(M, N):
    v = [-1 for _ in range(M)] + [0 for _ in range(N)]
    if SECTS_PER_STUD > 1:
        v += [-1 for _ in range(len(CONCURR_SECTIONS) * N)]
    return v

def main(csv_file, prioritize, analyze):
    students = import_students(csv_file, prioritize, analyze)
    assign_sections(students, prioritize, analyze)
    Student.display(students)

if __name__ == '__main__':
    parser = ArgumentParser(description='creates optimal section assignment')
    parser.add_argument('-p', '--prioritize', action='store_true', help='give students with seniority priority')
    parser.add_argument('-a', '--analyze', action='store_true', help='analyze results')
    parser.add_argument('csv_file', help='csv file with section rankings')
    args = parser.parse_args()
    main(args.csv_file, args.prioritize, args.analyze)
