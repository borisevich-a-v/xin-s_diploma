import requests
from bs4 import BeautifulSoup
import re
import csv

HEADERS = {
    'user-agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:84.0) Gecko/20100101 Firefox/84.0',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}


def get_html(url):
    html = requests.get(url, headers=HEADERS)
    return html


def get_issues_num(url, start=0, stop=0):
    html = get_html(url)
    soup = BeautifulSoup(html.text, 'html.parser')
    table = soup.find('tbody')
    links = table.find_all('a', class_='Link')
    if not stop:
        last = links[0].get_text()
        stop = int(re.search(r'\d+', last).group(0))
    issues_nums = []
    for i, link in enumerate(reversed(links)):
        if start > i or i > stop:
            continue
        n = re.search(r'/(\d+?)/udb', link.get('href'))[1]
        issues_nums.append(n)
        yield i, n


def get_data(html):
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table', class_='table').find_all('tr')
    what_we_find = ('Article Title', 'Source', 'Words', 'Persistent URL')
    parse_data = {}
    for row in table:
        row = row.find_all('td')
        try:
            string_name = row[0].get_text(strip=True)
            data = row[1].get_text().replace('\n', '')
            data = re.sub(r'\s+', ' ', data)
            if string_name in what_we_find:
                parse_data[string_name] = data
        except IndexError:
            return None
    return parse_data


def get_article_numbers(html, cur_url):
    next_url_tag = True
    article_numbers = []
    while next_url_tag:
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('tbody')
        goods = table.find_all('a', class_='Link')
        for article in goods:
            num = re.search(r'\d+', article.get('href'))[0]
            article_numbers.append(num)
        next_url_tag = soup.find('a', class_='Pagination-arrow--right')
        if next_url_tag:
            next_url = cur_url + next_url_tag.get('href')
            html = get_html(next_url).text
    return article_numbers


def parse(url):
    html = get_html(url)
    if html.status_code != 200:
        print('Страница не получена')
        return None
    article_id = get_article_numbers(html.text, url)

    data = []
    for i, article in enumerate(article_id):
        if i > 0:
            print('\r' * (4 + len(str(len(article_id))) + len(str(i + 1))),
                  end='')
        print(f'Обрабатываем статью {i + 1} из {len(article_id)}', end='')
        article_url = 'https://dlib.eastview.com/browse/doc/' + str(article)
        article_html = get_html(article_url)
        tmp_article = get_data(article_html.text)
        if tmp_article:
            data.append(tmp_article)
    return data


def write_to_file(n, items, path, write_type):
    with open(path, write_type, newline='') as fout:
        writer = csv.writer(fout, delimiter=';')
        for item in items:
            writer.writerow([
                n,
                item['Article Title'],
                item['Source'],
                item['Words'],
                item['Persistent URL'],
            ])


path = input('Куда сохранять?\n> ')
if input('Файл начать сначала? (напиши: "yes", если сначала)\n> ') == 'yes':
    header = [{'Article Title': 'Article Title',
               'Source': 'Source',
               'Words': 'Words',
               'Persistent URL': 'Persistent URL',
               }, ]
    write_to_file('Номер', header, path, 'w')

for ind, num in get_issues_num(input('Введите URL \n> '),
                               start=int(input('Откуда начать\n> '))-1,
                               stop=int(input('Где закончить\n> '))-1):
    print('=======================')
    url = 'https://dlib.eastview.com/browse/issue/' + num + '/udb/1'
    write_to_file(ind + 1, parse(url), path, 'a')
    print(f'\nЖурнал {ind + 1} обработан\n=======================')
