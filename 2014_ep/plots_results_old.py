#coding=utf-8
import matplotlib.pyplot as plt
plt.ion()

from numpy import linspace, sin, zeros, arange
#x = linspace(-5,5,101)
#plt.plot(x, sin(x))

section_numbers =[320300007, 320300008, 320300009, 320300010, 320300011, 320300006]

section_names = ["Брюксел",
"Брюксел",
"Брюксел",
"Брюксел",
"Гент",
"Антверпен"]

parties = ["Герб".decode('utf-8'),
"ДПС".decode('utf-8'),
"Зелените".decode('utf-8'),
"Реф. блок".decode('utf-8'),
"Атака".decode('utf-8'),
"КБ".decode('utf-8')]

party_nums = [16,24, 4, 9, 18, 13]

party_results = zeros([len(section_names),len(parties)], int)
totals = zeros(len(parties), int)

for i,n in enumerate(section_numbers):
    file = open("votes_eu2014.txt", 'r')
    for line in file:
        if str(n) in line:
            print line
            words = line.split(";")
            words = words[:-1]
            for word in words:
                word = int(word)
            for j in range(len(parties)):
                party_results[i,j] = words[2*party_nums[j]-3]
                totals[j]+=party_results[i,j]
    #plt.figure(1)
    #plt.plot(party_results[i,:])
    plt.figure(i)
    plt.bar(range(len(parties)),party_results[i,:])
    plt.title((section_names[i]).decode('utf-8'))
    plt.xticks(arange(len(parties))+0.8/2., parties )
    file.close()

plt.figure(i+1)
plt.bar(range(len(parties)),totals)
plt.title("Общо".decode('utf-8'))
plt.xticks(arange(len(parties))+0.8/2., parties )
raw_input()    
#for name, num in zip(parties, party_nums):
#    print name , num
