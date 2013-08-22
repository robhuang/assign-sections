import csv
import lp_maker as lpm
import lpsolve55 as lps
from argparse import ArgumentParser

CSV_OUT = 'out.csv'
LP_OUT = 'out.lp'
SECTION_CAP = 1 # currently set to 1 for assigning TAs, real cap is 32
SECTS_PER_STUD = 2 # currently set to 2 for assigning TAs, use 2 for class

class Student:
    def __init__(self, name, sid, email, rankings):
        self.name = name
        self.sid = sid
        self.email = email
        self.rankings = rankings
        self.sections = set()

    def __repr__(self):
        return 'Student({0}, {1})'.format(self.name, self.sections)

def import_students(csv_file):
    """
    Returns a list of students with their specified rankings.
    """
    with open(csv_file, 'rU') as f:
        csvreader = csv.reader(f)
        students = []
        num_s = len(csvreader.next()) - 1 # ignore first line -- headers
        for row in csvreader:
            students.append(Student(row[0],
                                    int(row[1]),
                                    row[2],
                                    [num_s - int(s) for s in row[1:]]))
    return students

def parse_results(res, students, M):
    i = 0
    for student in students:
        for section in range(M):
            if res[i] == 1:
                student.sections.add(section)
            i += 1

def output_csv(students):
    with open(CSV_OUT, 'w') as f:
        f.write(',' + ','.join([str(i) for i in
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
    b = make_b_v(M, N)
    e = make_e_v(M, N)
    v = [1 for _ in range(M*N)]

    lp = lpm.lp_maker(f, A, b, e, None, v)

    # set all variables to binary
    lps.lpsolve('set_binary', lp, v)

    lps.lpsolve('write_lp', lp, LP_OUT)
    lps.lpsolve('solve', lp)
    res = lps.lpsolve('get_variables', lp)[0]
    lps.lpsolve('delete_lp', lp)
    parse_results(res, students, M)

def make_obj_f(students):
    l = []
    for student in students:
        l.extend(student.rankings)
    return l

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
    return m

def make_b_v(M, N):
    return [SECTION_CAP for _ in range(M)] + [SECTS_PER_STUD for _ in range(N)]

def make_e_v(M, N):
    return [-1 for _ in range(M)] + [0 for _ in range(N)]

def main(csv_file):
    students = import_students(csv_file)
    assign_sections(students)
    print students
    output_csv(students)

if __name__ == '__main__':
    parser = ArgumentParser(description='creates optimal section assignment')
    parser.add_argument('csv_file', help='csv file with section rankings')
    args = parser.parse_args()
    main(args.csv_file)
