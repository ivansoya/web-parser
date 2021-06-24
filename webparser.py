import re
import requests
import sys
import os
import threading
from bs4 import BeautifulSoup

class Date:
    def get(self):
        date_string = str(self.year) + '-'
        if self.month < 10:
            new_month = '0' + str(self.month)
            date_string += new_month + '-'
        else:
            date_string += str(self.month) + '-'
        if self.day < 10:
            new_day = '0' + str(self.day)
            date_string += new_day
        else:
            date_string += str(self.day)
        return date_string

    def set_new_month(self):
        self.day = 1
        self.month += 1
        if self.month > 12:
            self.year += 1
            self.month = 1
    
    def compare(self, action):
        if self.month in [1, 3, 5, 7, 8, 10, 12]:
            if self.day > 31:
                return action()
        if self.month in [4, 6, 9, 11]:
            if self.day > 30:
                return action()
        if self.month == 2:
            if int(self.year) % 4 == 0:
                if self.day > 29:
                    return action()
            else:
                if self.day > 28:
                    return action()
        return 0

    def get_days(self, other):
        temp_day = Date(self.get())
        days = 0
        if temp_day >= other:
            return -1
        while temp_day.get() != other.get():
            temp_day.increase_by_day()
            days += 1
        del temp_day
        return days

    def increase_by_day(self, counter = 1):
        for i in range(counter):
            self.day += 1
            self.compare(self.set_new_month)
    
    def check_correctness(self):
        if self.year < 1997:
            return 1
        if self.month > 12 or self.month < 1:
            return 1
        if self.day < 1 or self.day > 31:
            return 1
        return self.compare(lambda: 1)

    def __ge__(self, other):
        if self.year < other.year:
            return False
        if self.year > other.year:
            return True
        if self.year == other.year:
            if self.month < other.month:
                return False
            if self.month > other.month:
                return True
            if self.month == other.month:
                if self.day < other.day:
                    return False
                else:
                    return True
    
    def __init__(self, date):
        temp = date.split('-')
        if len(temp) != 3:
            print('Incorrect type of Date!')
            exit()
        try:
            self.year = int(temp[0])
            self.month = int(temp[1])
            self.day = int(temp[2])
        except ValueError:
            print('Incorrect type of Date!')
            exit()

# ---------------------- Класс потока ----------------------

class ParseThread(threading.Thread):
    def __init__(self, name, id, date, days):
       threading.Thread.__init__(self)
       self.threadID = id
       self.name = name
       self.date = Date(date.get())
       self.days = days

    def run(self):
        name = self.date.get() + '.tsv'
        with open(name, 'w') as output_file:
            for counter in range(self.days):
                page = ''
                number = 1
                news_list = []
                while True:
                    url = 'https://gazetazp.ru/archive/%s%s' % (self.date.get(), page) # url страницы
                    page = ""
                    while True:
                        try:
                            page = requests.get(url, timeout = 5)
                            if page.status_code == 200:
                                break
                        except:
                            continue
                    soup = BeautifulSoup(page.text, features="html.parser")
                    news = soup.find_all('h3')
                    news_list.extend(news)
                    if len(news) == 27:
                        number += 1
                        page = "?page=" + str(number)
                        continue
                    else:
                        break
                for item in news_list:
                    href = item.find('a').get('href')
                    output_file.write(parse_new(href))
                self.date.increase_by_day()
        print("Thread %i was completed!" % (self.threadID))
       

# ---------------------- Функция вычисления делителей -------------------------

def compute_divider(integer):
    dividers = []
    for i in range(1, integer + 1):
        if integer % i == 0:
            dividers.append(i)
    if len(dividers) > 7:
        return dividers[len(dividers) // 2 - len(dividers) // 4]
    if len(dividers) > 0:
        return dividers[len(dividers) // 2]
    else:
        return -1


# ---------------------- Функция парсера ----------------------

def parse_new(href):
    request = ""
    while True:
        try:
            request = requests.get(href, timeout = 5)
            if request.status_code == 200:
                break
        except:
            continue
    soup = BeautifulSoup(request.text, features = "html.parser")
    body = soup.find('article', {'class': 'post'})
    time = soup.find('span', {'class': 'time'})
    name = body.find('h2', {'style': 'text-align: center'})
    all_items = body.find_all(['p', 'h3', 'h4'], {'class': None})
    items_p = []
    for i in all_items:
        if i.text not in items_p:
            items_p.append(i.text)
    texts = ""
    for item in items_p:
        if item != '':
            text = re.sub("^\s+|\n|\t|\r|\s+$", '', item)
            if text.endswith('.') == False:
                text += '.'
            texts += text
    title = re.sub("^\s+|\n|\t|\r|\s+$", '', name.text)
    time_text = re.sub("^\s+|\n|\t|\r|\s+$", '', time.get('title'))
    row = title + '\t' + time_text + '\t' + href + '\t' + texts + '\n'
    return row

# ---------------------- Main ----------------------

if len(sys.argv) != 3:
    print("There are not enough arguments!")
    exit()
date = Date(sys.argv[1]) #ID банка на сайте banki.ru
finish_date = Date(sys.argv[2])
days = date.get_days(finish_date)
if days == -1:
    print('Start date must be earlier than finish date!')
    exit()
if date.check_correctness() == 1 or finish_date.check_correctness() == 1:
    print("Date is incorrect!")
    exit()
divider = int(compute_divider(days))
interval = days // divider
print("%d threads was created" % (divider))
dates = []
threads = []
for i in range(divider):
    dates.append(date.get())
    if i == divider - 1:
        interval += 1
    threads.append(ParseThread("Thread", i, date, interval))
    date.increase_by_day(interval)
for i in range(divider):
    threads[i].start()
for i in range(divider):
    threads[i].join()
with open('result.tsv', 'w') as result_file:
    for item in dates:
        file_name = item + '.tsv'
        file = open(file_name, 'r')
        for row in file:
            result_file.write(row)
        os.remove(file_name)
exit()