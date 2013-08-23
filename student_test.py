import random
import string

HEADER = 'Timestamp,What is your name?,What is your email?,What is your student ID number?,What is your top section time choice?,What is your second choice?,What is your third choice?,What is your fourth choice?,What is your fifth choice?'
TIMES = ('M 0330-0500 PM W 0400-0530 PM',
         'M 0500-0630 PM W 0500-0630 PM',
         'M 0500-0630 PM W 0530-0700 PM',
         'M 0630-0800 PM W 0630-0800 PM',
         'M 0630-0800 PM W 0700-0830 PM',
         'Tu 0930-100 AM Th 0930-100 AM',
         'Tu 100-230 PM Th 100-230 PM',
         'Tu 230-0200 PM Th 230-0200 PM',
         'Tu 0200-0330 PM Th 0200-0330 PM',
         'Tu 0330-0500 PM Th 0330-0500 PM',
         'Tu 0500-0630 PM Th 0500-0630 PM',
         'Tu 0630-0800 PM Th 0630-0800 PM',
         'Tu 0800-0930 PM Th 0800-0930 PM',
         'W 0830-000 AM F 0830-000 AM',
         'W 0900-030 AM F 0930-100 AM',
         'W 030-200 PM F 100-230 PM')
INDICES = list(i for i in range(len(TIMES)))

def random_name():
    return ''.join(random.choice(string.ascii_letters)
                   for _ in range(random.randint(5, 15)))

def random_student():
    random.shuffle(INDICES)
    name = random_name()
    return '{0},{1},{1}@berkeley.edu,{2},{3}'.format('8/8/2008 20:08:08',
           name, random.randint(0, 99999999), ','.join(TIMES[i] for i in
           INDICES[:5]))

def main():
    for _ in range(5):
        temp = []
        for _ in range(random.randint(1, 4)):
            temp.append(random.choice(INDICES))
        INDICES.extend(temp)
    with open('student_test.csv', 'w') as f:
        f.write(HEADER)
        for _ in range(1000):
            f.write('{}\n'.format(random_student()))

if __name__ == '__main__':
    main()
