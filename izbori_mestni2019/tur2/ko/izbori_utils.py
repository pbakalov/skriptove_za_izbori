#coding=utf-8
import matplotlib.pylab as plt
import seaborn as sb
from numpy import arange
import plotly.graph_objects as go
import pandas as pd

#plt.ion()



def load_station_ids(filename, municipal_code): #2246 = Столична
    f = open(filename, 'r')
    text = f.read().rstrip('\n').split('\n')
    f.close()
    filtered_ids = []
    
    polling_stations = [line.split(';') for line in text]
    ctr = 1
    for station in polling_stations:
        if str(municipal_code) == station[0][:4]:
            filtered_ids.append(station[0])
            #print ctr, station[0], station[3], station[-2]
            ctr +=1
    return filtered_ids



def get_filtered_results_by_station(filename, station_ids):
    f = open(filename, 'r')
    text = f.read().rstrip('\n').split('\n')
    f.close()

    results = []
    totals = [0,0]
    fanduk = []
    maya = []
    fnm = []
    section_ctr = 0
    extreme_votes = 0
    extreme_diff = 0
    extreme_stations = 0
    for line in text:
        #station_id = int(line.split(';')[0])
        station_id = line.split(';')[0]

        if station_id in station_ids[:]:
            #print station_id
            section_ctr +=1

            line = [int(x) for x in line.split(';')[2:]]
            #sanity checks for sofia:
            if line[0] != 68 or line[3]!=75: 
                print "Unexpected candidate codes in station", station_id
                print line
                raw_input()

            station_results = line[:]
            
            results.append([station_id, station_results])
            totals[0] += line[1]
            totals[1] += line[4]
            fanduk.append(line[1]*100./(line[1] + line[4]))
            maya.append(line[4]*100./(line[1] + line[4]))
            fnm.append((fanduk[-1], maya[-1], line[1] + line[4]))

            if fanduk[-1]>70:  
                extreme_votes += line[1]
                extreme_diff += line[1] - line[4]
                extreme_stations +=1
                print extreme_stations, station_id, line[1], line[4]

    print fnm[-1]
    fnm = sorted( fnm, key = lambda x: x[0])
    maya = [x[1] for x in fnm]
    fanduk  = [x[0] for x in fnm]
    section_votes = [x[2] for x in fnm]
    print len(section_votes), section_ctr
    cumul_votes = [sum(section_votes[:i]) for i in range(len(section_votes))]
    print section_votes[:3]
    print cumul_votes[:3]
    print cumul_votes[-3:]

    #x_pos = arange(section_ctr)    # equally spaced bars
    #width = .9       # the width of the bars: can also be len(x) sequence
    x_pos = [sum(section_votes[:i])+ 0.5*section_votes[i] for i in range(len(section_votes))]
    width = [0.95*x  for x in section_votes ]
    
    p1 = plt.bar(x_pos, fanduk, width, color = 'b')
    p2 = plt.bar(x_pos, maya, width, color = 'g',
                 bottom=fanduk)
    
    plt.title('Резултати по секции (в проценти)'.decode('utf-8'), size = 20)
    plt.legend((p1[0], p2[0]), ('Фандъкова'.decode('utf-8'), 'Манолова'.decode('utf-8')), loc = 'best', fontsize = 20)

    print "fanduk, maya"
    print totals[0], totals[1]
    print totals[0] + totals[1] 
    print "extreme votes", extreme_votes
    print "extreme diff", extreme_diff
    print "extreme stations", extreme_stations
    return results, maya, fanduk, x_pos, width



station_ids =  load_station_ids('sections_03.11.2019.txt', 2246) # 2246 = Столична община (22 = код на район, 46 = код на община)

fig1 = plt.figure(frameon = False) 

results_by_station, maya, fanduk, x_pos, width = get_filtered_results_by_station("votes_03.11.2019.txt", station_ids)

plt.xticks(size = 15)
plt.yticks(size = 15)
#plt.xlim(0, 398718)
plt.ylim(0, 100)
plt.xlabel("Общо гласове".decode('utf-8'), size = 20)

fig1.set_size_inches(10,6)
fig1.subplots_adjust(top = 0.9, bottom = 0.1, left = 0.07, right = 0.98)
plt.savefig("section_results.svg")
plt.savefig("section_results.png", dpi=1200)
plt.close()

#import plotly.graph_objects as go
#M=len(x_pos)
#animals= x_pos[:M]#['giraffes', 'orangutans', 'monkeys']
#
#fig = go.Figure(data=[
#    go.Bar(name='Фандъкова'.decode('utf-8'), x=animals, width=width[:M], y=fanduk[:M]),
#    go.Bar(name='Манолова'.decode('utf-8'), x=animals,  width=width[:M], y=maya[:M])
#])
## Change the bar mode
#fig.update_layout(barmode='stack')
#fig.write_html('section_results_bar_plot.html', auto_open=True)

print "reading addresses"
adresi = pd.read_excel('/Users/fun/Documents/skriptove_za_izobri/izbori_mestni2019/Sekcii-08.09.2019-KM-0.xlsx')
print "addresses read" 

print adresi.head()

raw_input()
