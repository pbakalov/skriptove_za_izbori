#coding=utf-8

### Скрипт за изобразяване на изборни резултати от изборите за НС, 5 Октомври 2014 г. 
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rc('font', family='Arial')
#plt.ion()
from numpy import linspace, sin, zeros, arange

### В страната:
### първите две цифри са избирателен район
### вторите две са община
### третите две са админ. район
### последните три са номер на секция в този район
### 
### В чужбина:
### номерата на всички секции в чужбина започват с 32 (32 е номер на "район чужбина")
### вторите две цифри ("община") отговарят на страната 
### третата двойка цифри (адм. район) е 00 за всички секции в чужбина (?)
### последните три цифри са номер на секция 

#filetype = "png"
filetype = "svg"
show_first = 7 #покажи резултатите на първите n партии с най-много гласове
colors = ['green','blue','gold','lightskyblue','red','lightcoral','yellow','grey'] #, 'darkgreen','yellow','grey','violet','magenta','cyan']

### избери град, в който е имало секция
#city = "Лондон"
city = "Берн"
city = "Мадрид"
city = "Скопие"
city = "Берлин"
city = "Париж"
city = "Варшава"
city = "Рим"
city = "Атина"

#За градове в България е малко по триково. Използвай с повишено внимание.
city = "гр.Бургас"
city = "гр.Кърджали"
city = "гр.Разград"
city = "гр.Шумен"
city = "гр.София" 

city = "Лондон"
city = "Брюксел"
city = "Истанбул"

section_numbers =[]
section_names = []

### установи останалите секционни кодове в страната, в която е градът
file = open("sections_pe2014.txt", 'r')
nums = []
for line in file:
    if city in line:
        line = line.lstrip(";")
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

file = open("sections_pe2014.txt", 'r')
for line in file:
    for num in nums:
        if num[0:4] == line[0:4]:
            print line
            split_line = line.split(";")
            section_numbers.append(split_line[0])
            i = 2
            section_name = split_line[1]
            while (section_name in section_names):
                section_name = split_line[1]+" "+ str(i)
                i+=1
            section_names.append(section_name)
            #section_names.append(section_name.decode('utf-8'))

file.close()

for num, name in zip(section_numbers, section_names):
    print num, name

#raw_input()
totals_string="Общо за Белгия".decode('utf-8')
#totals_string="Totals".decode('utf-8')
votes_str = " (гласове: ".decode('utf-8')
#votes_str = " (votes: ".decode('utf-8')



def get_parties():
    parties = []
    party_nums = []
    file = open("parties_pe2014.txt", 'r')
    for line in file:
        split_line = line.split(";")
        parties.append(split_line[1])
        party_nums.append(split_line[0])
        print party_nums[-1], parties[-1]
    return [parties, party_nums]

parties, party_nums = get_parties()        
#raw_input()

cyrillic = u"абвгдежзийклмнопрстуфхцчшщъьюяАБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЬЮЯ "

for i in range(len(parties)):
    parties[i] = parties[i].decode('utf-8', 'ignore')
    cutoff_len = 13
    if len(parties[i])>cutoff_len:
        new_string = ""
#        for j in range(0,len(parties[i])-10,10):
#            new_string+=parties[i][j:j+10]+"\n"
#        new_string += parties[i][j+10:]
        split_name = parties[i].rstrip("\r\n ").split(" ")
        c = 1
        new_string +=split_name[0]
        for word in split_name[1:]:
            if len(new_string) + len(word) > cutoff_len*c:
                new_string+="\n"+word
                c+=1
            else:
                new_string+=" "+word
        parties[i] = new_string #rstrip("\r\n ")
    #print parties[i]
    print parties[i].encode('utf-8'), "\n"
    while parties[i][-1] not in cyrillic:
        parties[i] = parties[i][:-1]

        

#parties = ["Gerb".decode('utf-8'),
#"DPS".decode('utf-8'),
#"Zelenite".decode('utf-8'),
#"DSB".decode('utf-8'),
#"KB".decode('utf-8'),
#"DBG".decode('utf-8'),
#"VMRO".decode('utf-8'),
#"Other"]

#parties = ["Герб".decode('utf-8'),
#"ДПС".decode('utf-8'),
#"Зелените".decode('utf-8'),
#"Реф. блок".decode('utf-8'),
#"КБ".decode('utf-8'),
#"АБВ".decode('utf-8'),
#"ББЦ+ВМРО".decode('utf-8'),
#"Други".decode('utf-8')]

#party_nums = [16,24, 4, 9, 13, 12, 23]
#party_nums = [15,40, 26, 27, 5, 33, 18]

party_results = zeros([len(section_names),len(parties), 2], int) #действителни и недействителни гласове
results = zeros((len(parties),2), int)
total_votes = 0

for i,n in enumerate(section_numbers):
    #file = open("pe2013_pe_votes.txt", 'r')
    file = open("votes_pe2014.txt", 'r')
    for line in file:
        if str(n) in line:
            #print line
            #print line.split(";")[0::2]
            #print line.split(";")[1::2]
            words = line.split(";")[1:]
            for j in range(len(parties)): #гласове за подбраните партии
                party_results[i,j,0] = words[2*j]
                party_results[i,j,1] = words[2*j+1]
                results[j,0]+=party_results[i,j,0] #действителни
                results[j,1]+=party_results[i,j,1] #недействителни
            section_total=0
            for k in range(0,len(words)-1,2): #общо действителни гласове
                total_votes+=int(words[k])
                #print words[k-1], words[k]
                section_total +=int(words[k])

    #резултати по секции
    section_res, section_parties = (list(x) for x in zip(*sorted(zip(party_results[i,:,0], parties[:]), reverse = True))) #в низходящ ред
    leading_section_res = zeros(show_first+1, int)
    leading_section_res[:show_first] = section_res[:show_first]
    leading_section_res[-1] = sum(section_res[show_first:]) #действителни гласове за останалите партии  
    if sum(party_results[i,:,0])>500: #секции само с повече от 500 валидни гласа
        print section_names[i], "валидни:", sum(party_results[i,:,0]), "невалидни:", sum(party_results[i,:,1])
#    for k, party in enumerate(parties):
#        print party, party_results[i,k,0]
#    for party, res in  zip(section_parties, leading_section_res[:show_first]):
#        print party, res
    
    plt.figure(1)
    plt.subplot(17,8,i+1)
    plt.title((section_names[i]).decode('utf-8') + votes_str + str(sum(party_results[i,:,0])).decode('utf-8')+")")
    plt.bar(range(len(leading_section_res)),leading_section_res)
    plt.xticks(arange(len(leading_section_res))+0.8/2., section_parties[:show_first]+["Други".decode('utf-8')], rotation = 90)
    plt.subplots_adjust(left = 0.1, right = 0.95, top = 0.95, bottom = 0.1, wspace = 0.1, hspace = 0.4)
    
    plt.figure(2)
    #plt.subplot(420+i+1)
    plt.subplot(17,8,i+1)
    plt.pie(leading_section_res, labels = section_parties[:show_first]+["Други".decode('utf-8')], autopct='%1.1f%%')
    plt.title((section_names[i]).decode('utf-8') + votes_str + str(sum(party_results[i,:,0])).decode('utf-8')+")")
    
#    if "Льовен".decode('utf-8') in section_names[i].decode('utf-8'):
#        fig = plt.figure()
#        patches, texts, autotexts = plt.pie(leading_section_res, labels = section_parties[:show_first]+["Други".decode('utf-8')], autopct='%1.1f%%',labeldistance = 1.4, pctdistance = 0.8, colors = colors)
#        autotexts[0].set_color('y')
#        plt.title((section_names[i]).decode('utf-8') + votes_str + str(sum(party_results[i,:,0])).decode('utf-8')+")")
#        plt.subplots_adjust(left = 0.2, right = 0.8, top = 0.8, bottom = 0.2)
#        fig.set_size_inches(11,11)
#        plt.savefig("Leuven_res_pie.pdf")
#        
#        plt.figure()
#        plt.title((section_names[i]).decode('utf-8') + votes_str + str(sum(party_results[i,:,0])).decode('utf-8')+")")
#        barlist = plt.bar(range(len(leading_section_res)),leading_section_res)
#        for j, bar in enumerate(barlist):
#            bar.set_color(colors[j])
#        plt.xticks(arange(len(leading_section_res))+0.8/2., section_parties[:show_first]+["Други".decode('utf-8')], rotation = 90)
#        plt.subplots_adjust(left = 0.1, right = 0.9, top = 0.9, bottom = 0.3)
#        plt.savefig("Leuven_res_bar.pdf")
    file.close()

fig = plt.figure(1)
#plt.subplots_adjust(left = 0.1, right = 0.95, bottom = 0.2, wspace = 0.1, hspace = 0.2)
#plt.tight_layout()
fig.set_size_inches(24,36)
plt.savefig("sections_bar."+filetype)

fig = plt.figure(2)
#plt.title("Section results. Total valid votes: " + str(total_votes))
fig.set_size_inches(24,36)
plt.savefig("sections_pie."+filetype)

#подреждане по резултат (най-добър --> най-слаб)
results[:,0], parties[:] = (list(x) for x in zip(*sorted(zip(results[:,0], parties[:]), reverse = True)))

fig = plt.figure()
first_results = zeros(show_first+1, int)
first_results[:show_first] = results[:show_first, 0]
first_results[-1] = sum(results[show_first:, 0]) #действителни гласове за останалите партии
barlist = plt.bar(arange(show_first+1),first_results)
for j, bar in enumerate(barlist):
    bar.set_color(colors[j])
plt.title(totals_string + " (" + str(total_votes) +" гласа)".decode('utf-8'))
plt.xticks(arange(len(first_results))+0.8/2., parties[:show_first]+["Други".decode('utf-8')], rotation = 90)
plt.subplots_adjust(left = 0.1, right = 0.95, bottom = 0.3)
fig.set_size_inches(10,6)
plt.savefig("totals_bar."+filetype)

total_votes_selection = float(sum(results[:,0]))
print "\n", total_votes_selection
print total_votes, "\n"

for i,total in enumerate(results[:,0]):
    #print parties[i].encode('utf-8'), results[i,0], results[i,0]/total_votes_selection
    if results[i,0]>100:
        print parties[i].encode('utf-8'), results[i,0], results[i,0]/total_votes_selection

fig=plt.figure()
patches, texts, autotexts = plt.pie(first_results, labels = parties[:show_first]+["Други".decode('utf-8')], autopct='%1.1f%%', colors = colors, labeldistance = 1.25) #, startangle = 30)
autotexts[0].set_color('y')
plt.title(totals_string + " ("+str(total_votes) +" гласа)".decode('utf-8')) 
fig.set_size_inches(10,10)
plt.savefig("totals_pie."+filetype)

valid_and_invalid = sum(results)
print valid_and_invalid
#raw_input()    
#for name, num in zip(parties, party_nums):
#    print name , num