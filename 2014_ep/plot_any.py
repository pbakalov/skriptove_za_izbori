#coding=utf-8

### Скрипт за изобразяване на изборни резултати от евроизборите през 2014 г. 
import matplotlib.pyplot as plt
plt.ion()
from numpy import linspace, sin, zeros, arange

### В страната:
### първите две цифри са избирателен район
### вторите две са община
### третите две са админ. район
### последните три са номер на секция в този район
### 
### В чужбина:
### номерата на всички секции в чужбина започват с 32 (номер на район)
### вторите две цифри ("община") отговарят на страната 
### третата двойка цифри (адм. район) е 00 за всички секции в чужбина (?)

### избери град, в който е имало секция
#city = "Лондон"
city = "Берн"
city = "Мадрид"
city = "Скопие"
city = "Истанбул"
city = "Берлин"
city = "Париж"
city = "Варшава"
city = "Рим"
city = "Атина"
city = "Брюксел"

#За градове в България е малко по триково. Използвай с повишено внимание.
city = "гр.Бургас"
city = "гр.Кърджали"
city = "гр.Разград"
city = "гр.Шумен"
city = "гр.София" 

section_numbers =[]
section_names = []

### установи останалите секционни кодове в страната, в която е градът
file = open("sections_eu2014.txt", 'r')
nums = []
for line in file:
    if city in line:
        num = line[:9]
        if len(nums)>0: 
            if num[:4] != nums[-1][:4]: 
                nums.append(num)
                print num
        else:
            nums.append(num)
            print num
file.close()

print nums

file = open("sections_eu2014.txt", 'r')
for line in file:
    for num in nums:
        if num[0:4] == line[0:4]:
            print line
            split_line = line.split(";")
            section_numbers.append(split_line[0])
            section_names.append(split_line[1])

file.close()

for num, name in zip(section_numbers, section_names):
    print num, name

raw_input()
#totals_string="Общо".decode('utf-8')
totals_string="Totals".decode('utf-8')
#votes_str = " (гласове: ".decode('utf-8')
votes_str = " (votes: ".decode('utf-8')


parties = ["Gerb".decode('utf-8'),
"DPS".decode('utf-8'),
"Zelenite".decode('utf-8'),
"Ref. blok".decode('utf-8'),
"KB".decode('utf-8'),
"ABV".decode('utf-8'),
"BBC+VMRO".decode('utf-8'),
"Other"]

#parties = ["Герб".decode('utf-8'),
#"ДПС".decode('utf-8'),
#"Зелените".decode('utf-8'),
#"Реф. блок".decode('utf-8'),
#"КБ".decode('utf-8'),
#"АБВ".decode('utf-8'),
#"ББЦ+ВМРО".decode('utf-8'),
#"Други".decode('utf-8')]

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

    #резултати по секции
#    plt.figure(1)
#    plt.subplot(320+i+1)
#    plt.title((section_names[i]).decode('utf-8') + votes_str + str(sum(party_results[i,:]))+")")
#    plt.bar(range(len(parties)),party_results[i,:])
#    plt.xticks(arange(len(parties))+0.8/2., parties )
#    plt.figure(2)
#    plt.subplot(320+i+1)
#    plt.pie(party_results[i,:], labels = parties, autopct='%1.1f%%')
#    plt.title((section_names[i]).decode('utf-8') + votes_str + str(sum(party_results[i,:]))+")")
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
