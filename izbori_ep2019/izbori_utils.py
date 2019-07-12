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

sections = load_sections_data('sections.txt')

m, tot =  count_machine_sections(sections)
print m
print tot
