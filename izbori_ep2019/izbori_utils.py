def count_machine_sections(sections):
    m = 0
    tot = 0
    tot = len(sections)
    for section in sections:
        m+= int(section[-1])

    return m, tot

def load_sections_data(filename):
    f = open(filename, 'r')
    text = f.read().rstrip('\n').split('\n')
    f.close()
    sections = [line.split(';') for line in text]
    return sections

def get_results(filename):
    f = open(filename, 'r')
    text = f.read().rstrip('\n').split('\n')
    f.close()

    results = []
    for i in range(27):
        results.append([i+1,0,0])

    for line in text:
        line = [int(x) for x in line.split(';')[2:]]
        for i in range(27):
            results[i][1] += line[i*3+1]
            results[i][2] += line[i*3+2]
        
    return results
    

paper_results = get_results('votes.txt')
machine_results = get_results('votes_mv.txt')

print "votes.txt:"
paper_results = sorted(paper_results, key = lambda x: x[1], reverse=True)
for result in paper_results:
    print "{:<3d}{:>10d}{:>10d}".format(result[0],result[1], result[2])

print "votes_mv.txt:"
machine_results = sorted(machine_results, key = lambda x: x[1], reverse=True)
for result in machine_results:
    print "{:<3d}{:>10d}{:>10d}".format(result[0],result[1], result[2])

