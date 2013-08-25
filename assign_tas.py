import csv
import lp_maker as lpm
import lpsolve55 as lps
from argparse import ArgumentParser

CSV_OUT = 'out.csv'
LP_OUT = 'out.lp'
SECTION_CAP = 1 # currently set to 1 for assigning TAs, real cap is 32
SECTS_PER_TA = 2 # currently set to 2 for assigning TAs, use 2 for class
SECTIONS = tuple(i for i in range(11, 44))
CONCURR_SECTIONS = ((11, 12, 13), (14, 15, 16), (17, 18, 19), (20, 21),
                    (22, 23), (24, 25), (26, 27, 28), (30, 31, 32),
                    (33, 34, 35), (36, 37, 38), (39, 40, 41), (29, 43))
CONCURR_SECTIONS = tuple(tuple(map(lambda s: SECTIONS.index(s), t))
                         for t in CONCURR_SECTIONS)
DEFAULT_RANK = 10

class TA:
    priorities = []

    def __init__(self, name, sid, email, rankings,
                 num_sections=SECTS_PER_TA, priority=0):
        self.name = name
        self.sid = sid
        self.email = email
        self.num_sections = num_sections
        self.rankings = rankings
        self.priority = priority
        self.sections = set()
        TA.priorities.append(priority)

    @staticmethod
    def display(tas):
        for ta in tas:
            print ta

    def __repr__(self):
        return 'TA({0}, {1})'.format(self.name, self.sid, self.email,
                                          self.rankings)

    def __str__(self):
        return '{0}: {1}'.format(self.name, ', '.join((str(s) for s in
                                                       self.sections)))

    def __eq__(self, other):
        if not isinstance(other, TA):
            raise TypeError('can only compare with a TA')
        return other.name == self.name and other.email == self.email

    def __hash__(self):
        return hash(self.name + str(self.sid))


def import_tas(csv_file, prioritize=False, analyze=False):
    """
    Returns a list of tas with their specified rankings.
    """
    tas = set()
    with open(csv_file, 'rU') as f:
        csvreader = csv.reader(f)
        num_s = len(csvreader.next()) - 3 # ignore first line -- headers
        for row in csvreader:
            name = row[1]
            sid = int(row[3])
            email = row[2]
            if prioritize:
                rankings = convert_to_rankings(row[4:-2])
                num_sections = int(row[-2])
                priority = int(row[-1])
                ta = TA(name, sid, email, rankings, num_sections, priority)
                tas.discard(ta)
                tas.add(ta)
                if analyze:
                    ta.prefs = [int(s.split()[0]) for s in row[4:-2]]
            else:
                rankings = convert_to_rankings(row[4:-1])
                num_sections = int(row[-1])
                ta = TA(name, sid, email, rankings, num_sections)
                tas.discard(ta)
                tas.add(ta)
                if analyze:
                    ta.prefs = [int(s.split()[0]) for s in row[4:-1]]
    return sorted(tas, key=lambda s: s.name.split()[-1])

def convert_to_rankings(pref_list):
    """
    Takes in a list of sections, ranking in decreasing order of preference.
    Returns a list of rankings, in increasing order of sections.
    """
    rankings = [DEFAULT_RANK for _ in SECTIONS]
    for i, s in enumerate(pref_list):
        section = int(s.split()[0])
        rankings[SECTIONS.index(section)] = i
    return rankings

def parse_results(res, tas, M, analyze=False):
    """
    Parses the results from the LPSolver and assigns TAs to those sections.
    """
    i = 0
    if analyze:
        ranks = []
    for ta in tas:
        for section in range(M):
            if res[i] == 1:
                chosen_sect = SECTIONS[section]
                ta.sections.add(chosen_sect)
                if analyze:
                    try:
                        rank = ta.prefs.index(chosen_sect)
                        ranks.append(rank)
                        print '{}: ranked section {} as {}'.format(
                                ta.name, chosen_sect, rank+1)
                    except ValueError:
                        ranks.append(DEFAULT_RANK+1)
                        print '{}: ranked section {} as {}'.format(
                                ta.name, chosen_sect, DEFAULT_RANK+1)
            i += 1
    if analyze:
        print 'min: {0}, max: {1}, mean: {2}'.format(min(ranks), max(ranks),
                                                     sum(ranks)/len(ranks))

def assign_sections(tas, prioritize=False, analyze=False):
    """
    tas: a list of ta objects
    i = index of sections
    j = index of tas
    The columns, x_i_j, go as follows:
        x_0_0, x_1_0, x_2_0, ..., x_0_1, ..., x_M_N
    """

    M = len(tas[0].rankings) # number of section
    N = len(tas)             # number of tas

    f = make_obj_f(tas, prioritize)
    A = make_coeff_m(M, N)
    b = make_b_v(tas, M, N)
    e = make_e_v(M, N)
    v = [1 for _ in range(M*N)]

    lp = lpm.lp_maker(f, A, b, e, None, v)

    # set branch and bound depth
    lps.lpsolve('set_bb_depthlimit', lp, 0)
    # set all variables to binary
    lps.lpsolve('set_binary', lp, v)
    # set lp to minimize the objective function
    lps.lpsolve('set_minim', lp)

    lps.lpsolve('write_lp', lp, LP_OUT)
    lps.lpsolve('solve', lp)
    res = lps.lpsolve('get_variables', lp)[0]
    lps.lpsolve('delete_lp', lp)
    parse_results(res, tas, M, analyze)

def make_obj_f(tas, prioritize):
    """
    Returns a list of coefficients for the objective function.
    """
    coeffs = []
    for ta in tas:
        if prioritize:
            s_rankings = [(r+1) * (max(ta.priorities)-ta.priority+1)
                          for r in ta.rankings]
        else:
            s_rankings = [r+1 for r in ta.rankings]
        coeffs.extend(s_rankings)
    return coeffs

def make_coeff_m(M, N):
    """
    Returns a list of coefficients for the constraints matrix.
    """
    m = []
    # COEFFICIENTS FOR CONSTRAINTS ON SECTION CAPS
    for x in range(M):
        tmp_zeroes = [0 for _ in range(M*N)]
        for y in range(x, M*N, M):
            tmp_zeroes[y] = 1
        m.append(tmp_zeroes)
    # COEFFICIENTS FOR CONSTRAINTS ON NUMBER OF SECTIONS PER ta
    for x in range(N):
        tmp_zeroes = [0 for _ in range(M*N)]
        for y in range(x*M, (x+1)*M):
            tmp_zeroes[y] = 1
        m.append(tmp_zeroes)
    # COEFFICIENTS TO PREVENT CONCURRENT SECTION ASSIGNMENT
    if SECTS_PER_TA > 1:
        for x in range(N):
            for concurr_s in CONCURR_SECTIONS:
                tmp_zeroes = [0 for _ in range(M*N)]
                for s in concurr_s:
                    tmp_zeroes[x*M+s] = 1
                m.append(tmp_zeroes)
    return m

def make_b_v(tas, M, N):
    """
    Returns a list of coefficients for the b vector for constraints.
    """
    v = [SECTION_CAP for _ in range(M)] + [ta.num_sections for ta in tas]
    if SECTS_PER_TA > 1:
        v += [1 for _ in range(len(CONCURR_SECTIONS) * N)]
    return v

def make_e_v(M, N):
    """
    Returns a list of coefficients for the equality vector for constraints.
    """
    v = [-1 for _ in range(M)] + [0 for _ in range(N)]
    if SECTS_PER_TA > 1:
        v += [-1 for _ in range(len(CONCURR_SECTIONS) * N)]
    return v

def main(csv_file, prioritize, analyze):
    tas = import_tas(csv_file, prioritize, analyze)
    assign_sections(tas, prioritize, analyze)
    TA.display(tas)

if __name__ == '__main__':
    parser = ArgumentParser(description='creates optimal section assignment')
    parser.add_argument('-p', '--prioritize', action='store_true', help='adjusts the objective function for priorities')
    parser.add_argument('-a', '--analyze', action='store_true', help='analyze results')
    parser.add_argument('csv_file', help='csv file with section rankings')
    args = parser.parse_args()
    main(args.csv_file, args.prioritize, args.analyze)
