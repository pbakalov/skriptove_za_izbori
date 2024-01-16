import matplotlib.pylab as plt
import seaborn as sb

plt.ion()

def count_machine_stations(polling_stations):
    m = 0
    tot = 0
    tot = len(polling_stations)
    for polling_station in polling_stations:
        m+= int(polling_station[-1])

    return m, tot

def load_stations_data(filename):
    f = open(filename, 'r')
    text = f.read().rstrip('\n').split('\n')
    f.close()
    polling_stations = [line.split(';') for line in text]
    return polling_stations

def get_machine_stations(polling_stations):
    machine_station_ids = []
    for polling_station in polling_stations:
        if int(polling_station[-1]) == 1:
            machine_station_ids.append(int(polling_station[0]))
    return machine_station_ids


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

def get_filtered_results(filename, station_ids):
    f = open(filename, 'r')
    text = f.read().rstrip('\n').split('\n')
    f.close()

    results = []
    for i in range(27):
        results.append([i+1,0,0])

    for line in text:
        station_id = int(line.split(';')[0])

        if station_id in station_ids:
            line = [int(x) for x in line.split(';')[2:]]
            for i in range(27):
                results[i][1] += line[i*3+1]
                results[i][2] += line[i*3+2]
        
    return results

def get_filtered_results_by_station(filename, station_ids):
    f = open(filename, 'r')
    text = f.read().rstrip('\n').split('\n')
    f.close()

    results = []
    for line in text:
        station_id = int(line.split(';')[0])

        if station_id in station_ids:
            station_results = []
            for i in range(27):
                station_results.append([i+1,0,0])

            line = [int(x) for x in line.split(';')[2:]]
            for i in range(27):
                station_results[i][1] += line[i*3+1]
                station_results[i][2] += line[i*3+2]
            
            results.append([station_id, station_results])
        
    return results

def get_totals_from_station_resolved(station_resolved_results):
    results = []
    for i in range(27):
        results.append([i+1,0,0])

    for station_result in station_resolved_results:
        station_result = station_result[1]
        for i in range(27):
            results[i][1] +=  station_result[i][1]
            results[i][2] +=  station_result[i][2]

    return results

def get_percentage_machine(results_by_station, machine_results_by_station):
    if len(results_by_station) != len(machine_results_by_station):
        print "unequal number of stations"
        return 0 
    percentage_by_station =  []
    for i in range(len(results_by_station)):
        if results_by_station[i][0] != machine_results_by_station[i][0]:
            print "station numbers don't mach. Skipping."
            continue

        percentage_by_station.append([])
        proportion = []
        results1 = results_by_station[i][1]
        results2 = machine_results_by_station[i][1]
        
        #print "{:<3}{:>12}{:>7}{:>7}{:>5}{:>12}".format("no", "station id", "res 1", "res 2", "p1", "p2")
        for j in range(27):
            try:
                proportion.append([j+1, results2[j][1]*1./results1[j][1]])
                #print "{:<3d}{:>12d}{:>7d}{:>7d}{:>5d}{:>12f}".format(j, results1[j][0], results1[j][1], results2[j][1], proportion[-1][0], proportion[-1][1])
            except ZeroDivisionError:
                proportion.append([j+1, -1.])
            #print "{:<3d}{:>12d}{:>7d}{:>7d}{:>5d}{:>12f}".format(j+1, results_by_station[i][0], results1[j][1], results2[j][1], proportion[-1][0], proportion[-1][1])

        percentage_by_station[-1].append(results_by_station[i][0])
        percentage_by_station[-1].append(proportion)

        #print percentage_by_station[-1][0]
        #print percentage_by_station[-1][1]
        #raw_input()

    return percentage_by_station
        
    

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


polling_stations =  load_stations_data('sections.txt')
machine_station_ids = get_machine_stations(polling_stations)
print machine_station_ids[:10]
results_in_machine_stations = get_filtered_results('votes.txt', machine_station_ids)

print "Filtered:"
results_in_machine_stations = sorted(results_in_machine_stations, key = lambda x: x[1], reverse=True)
for result in results_in_machine_stations:
    print "{:<3d}{:>10d}{:>10d}".format(result[0],result[1], result[2])


results_by_station = get_filtered_results_by_station("votes.txt", machine_station_ids)
machine_results_by_station = get_filtered_results_by_station("votes_mv.txt", machine_station_ids)


##checks
#print len(results_by_station), len(machine_results_by_station)
#
#results_in_machine_stations2 = get_totals_from_station_resolved(results_by_station)
#machine_results2 = get_totals_from_station_resolved(machine_results_by_station)
#
#print "votes_mv.txt check:"
#machine_results2 = sorted(machine_results2, key = lambda x: x[1], reverse=True)
#for result in machine_results2:
#    print "{:<3d}{:>10d}{:>10d}".format(result[0],result[1], result[2])
#
#
#print "Filtered check:"
#results_in_machine_stations = sorted(results_in_machine_stations2, key = lambda x: x[1], reverse=True)
#for result in results_in_machine_stations:
#    print "{:<3d}{:>10d}{:>10d}".format(result[0],result[1], result[2])


percentage_machine_by_station = get_percentage_machine(results_by_station, machine_results_by_station)

party_hist = []
machine_hist = []
total_hist = []
for i in range(27):
    party_hist.append([])
    machine_hist.append([])
    total_hist.append([])

print percentage_machine_by_station[-1]
print machine_results_by_station[-1]

#for p in percentage_machine_by_station:
#    for i in range(27):
#        party_hist[i].append(p[1][i][1])

for p in machine_results_by_station:
    for i in range(27):
        machine_hist[i].append(p[1][i][1])

for p in results_by_station:
    for i in range(27):
        total_hist[i].append(p[1][i][1])
    

for i,p in enumerate(machine_hist):
    plt.figure(i+1)
    #plt.hist(p, bins=20, range =(0.,1.))
    sb.violinplot( data = [p, total_hist[i]], split=True)
    raw_input()

raw_input()
