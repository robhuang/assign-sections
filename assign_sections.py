import csv
import lp_maker as lpm
import lpsolve55 as lps
from argparse import ArgumentParser

CSV_OUT = 'out.csv'
LP_OUT = 'out.lp'
SECTION_CAP = 1 # currently set to 1 for assigning TAs, real cap is 32
SECTS_PER_STUD = 2 # currently set to 2 for assigning TAs, use 2 for class
SECTIONS = tuple(i for i in range(11, 44))
CONCURR_SECTIONS = ((11, 12, 13), (14, 15, 16), (17, 18, 19), (20, 21),
                    (22, 23), (24, 25), (26, 27, 28), (30, 31, 32),
                    (33, 34, 35), (36, 37, 38), (39, 40, 41), (29, 43))
CONCURR_SECTIONS = tuple(tuple(map(lambda s: SECTIONS.index(s), t))
                         for t in CONCURR_SECTIONS)
DEFAULT_RANK = 11
SEN_WEIGHT = 1.2

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

    def __repr__(self):
        return 'Student({0}, {1})'.format(self.name, self.sid, self.email,
                                          self.rankings)

    def __str__(self):
        return '{0}: {1}'.format(self.name, self.sections)

    @staticmethod
    def display(students):
        for student in students:
            print student

def import_students(csv_file):
    """
    Returns a list of students with their specified rankings.
    """
    with open(csv_file, 'rU') as f:
        csvreader = csv.reader(f)
        students = []
        num_s = len(csvreader.next()) - 3 # ignore first line -- headers
        for row in csvreader:
            name = row[1]
            sid = int(row[3])
            email = row[2]
            rankings = convert_to_rankings(row[4:-2])
            num_sections = int(row[-2])
            priority = int(row[-1])
            students.append(Student(name, sid, email, rankings,
                                    num_sections, priority))
    return students

def convert_to_rankings(pref_list):
    rankings = [DEFAULT_RANK for _ in SECTIONS]
    for i, s in enumerate(pref_list):
        section = int(s.split()[0])
        rankings[SECTIONS.index(section)] = i
    return rankings

def parse_results(res, students, M):
    i = 0
    for student in students:
        for section in range(M):
            if res[i] == 1:
                student.sections.add(SECTIONS[section])
            i += 1

def output_csv(students):
    with open(CSV_OUT, 'w') as f:
        f.write('student,sid,email,' + ','.join([str(i) for i in
                range(len(students[0].rankings))]) + '\n')
        for student in students:
            line = ['TRUE' if x in student.sections else '' for x in
                    range(len(student.rankings))]
            f.write(student.name + ',' + ','.join(line) + '\n')

def assign_sections(students):
    """
    students: a list of student objects
    i = index of sections
    j = index of students
    The columns, x_i_j, go as follows:
        x_0_0, x_1_0, x_2_0, ..., x_0_1, ..., x_M_N
    """

    M = len(students[0].rankings) # number of section
    N = len(students)             # number of students

    f = make_obj_f(students)
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

def make_obj_f(students):
    coeffs = []
    for student in students:
        s_rankings = [(r+1) * (max(Student.priorities)-student.priority+1)
                      for r in student.rankings]
        coeffs.extend(s_rankings)
    print coeffs
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

def main(csv_file):
    students = import_students(csv_file)
    assign_sections(students)
    Student.display(students)
    output_csv(students)

if __name__ == '__main__':
    parser = ArgumentParser(description='creates optimal section assignment')
    parser.add_argument('csv_file', help='csv file with section rankings')
    args = parser.parse_args()
    main(args.csv_file)
