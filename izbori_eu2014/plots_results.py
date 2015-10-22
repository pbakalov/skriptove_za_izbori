#coding=utf-8
import matplotlib.pyplot as plt
plt.ion()

from numpy import linspace, sin, zeros, arange
#x = linspace(-5,5,101)
#plt.plot(x, sin(x))

section_numbers =[320300007, 320300008, 320300009, 320300010, 320300011, 320300006]

totals_string="Общо за Белгия".decode('utf-8')
votes_str = " (гласове: ".decode('utf-8')
#totals_string="Totals".decode('utf-8')

#section_names = ["Brussels 1",
#"Brussels 2",
#"Brussels 3",
#"Brussels 4",
#"Gent",
#"Antwerp"]
section_names = ["Брюксел 1",
"Брюксел 2",
"Брюксел 3",
"Брюксел 4",
"Гент",
"Антверпен"]

#parties = ["Gerb".decode('utf-8'),
#"DPS".decode('utf-8'),
#"Zelenite".decode('utf-8'),
#"Ref. blok".decode('utf-8'),
#"Ataka".decode('utf-8'),
#"KB".decode('utf-8'),
#"Other"]
parties = ["Герб".decode('utf-8'),
"ДПС".decode('utf-8'),
"Зелените".decode('utf-8'),
"Реф. блок".decode('utf-8'),
#"Атака".decode('utf-8'),
"КБ".decode('utf-8'),
"АБВ".decode('utf-8'),
"ББЦ+ВМРО".decode('utf-8'),
"Други".decode('utf-8')]

party_nums = [16,24, 4, 9, 13, 12, 23]

party_results = zeros([len(section_names),len(parties)], int)
results = zeros(len(parties), int)
total_votes = 0

for i,n in enumerate(section_numbers):
    file = open("votes_eu2014.txt", 'r')
    for line in file:
        if str(n) in line:
            print line
            words = line.split(";")
            words = words[:-1]
            for word in words:
                word = int(word)
            for j in range(len(parties)-1): #гласове за подбраните партии
                party_results[i,j] = words[2*party_nums[j]-3]
                results[j]+=party_results[i,j]
            section_total=0
            for k in range(1,len(words),2): #общо действителни гласове
                total_votes+=int(words[k])
                section_total +=int(words[k])
            party_results[i,-1] = section_total-sum(party_results[i,:-1]) # действителни гласове за всички други партии
            results[-1]+=party_results[i,-1]
    #plt.figure(1)
    #plt.plot(party_results[i,:])
    plt.figure(1)
    plt.subplot(320+i+1)
    plt.title((section_names[i]).decode('utf-8') + votes_str + str(sum(party_results[i,:]))+")")
    plt.bar(range(len(parties)),party_results[i,:])
    plt.xticks(arange(len(parties))+0.8/2., parties )
    plt.figure(2)
    plt.subplot(320+i+1)
    plt.pie(party_results[i,:], labels = parties, autopct='%1.1f%%')
    plt.title((section_names[i]).decode('utf-8') + votes_str + str(sum(party_results[i,:]))+")")
    file.close()

fig = plt.figure(1)
fig.set_size_inches(12,18)
plt.savefig("sections_bar.png")
fig = plt.figure(2)
#plt.title("Section results. Total valid votes: " + str(total_votes))
fig.set_size_inches(12,18)
plt.savefig("sections_pie.png")

fig = plt.figure()
results[:-1], parties[:-1] = (list(x) for x in zip(*sorted(zip(results[:-1], parties[:-1]), reverse = True)))
plt.bar(arange(len(parties)),results)
total_votes_selection = float(sum(results))
plt.title(totals_string + " (" + str(total_votes) +" гласа)".decode('utf-8'))
plt.xticks(arange(len(parties))+0.8/2., parties )
fig.set_size_inches(10,6)
plt.savefig("totals_bar.png")

print total_votes_selection
print total_votes
for i,total in enumerate(results):
    print parties[i], results[i], results[i]/total_votes_selection

#results = results/total_votes_selection
fig=plt.figure()
patches, texts, autotexts = plt.pie(results, labels = parties, autopct='%1.1f%%')
autotexts[0].set_color('y')
plt.title(totals_string + " ("+str(total_votes) +" гласа)".decode('utf-8')) 
fig.set_size_inches(10,10)
plt.savefig("totals_pie.png")
raw_input()    
#for name, num in zip(parties, party_nums):
#    print name , num
