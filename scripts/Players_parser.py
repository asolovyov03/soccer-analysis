import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from random import uniform
from fake_headers import Headers
from tqdm import tqdm


def get_soup(url):
    '''
        Функция передает html-код

        Args:
            proxies: использованная для парсинга прокси
            headers: генерация случайных браузеров для подключения
        Returns:
            soup: cоздается объект BeautifulSoup, HTML-данные передаются конструктору
            Fals: ошибка, в случае если ответ не 200
    '''
    try:
        proxies = {
       'http': 'http://ag7xTx:QhsBbH@196.18.222.112:8000',
    }
        headers = Headers(headers=True).generate()
        response = requests.get(url, headers=headers, proxies=proxies)
        response.raise_for_status()
        with open('test.html', 'w') as f:
            f.write(response.text)
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup
    except requests.RequestException:
        return False


def get_links(url_null):
     '''
        Функция собирает необходимые ссылки на команды, чтобы далее собирать данные игроков
        Цикл использован, так как классы у необходимых поссылок различаются

        Args:
            class_name: создает необходимые классы, как существующие, так и пустые
            all_urls: собирает информацию с классом
            first: отбирает окончание ссылки и заменяет 'overview' на 'squad' для последующего поиска
        Returns:
            links_null: cоздается список с нужными окончаниями ссылок для последующего парсинга
    '''
    soup = get_soup(url_null)
    links_null = []
    all_clubs = soup.find('ul', class_='block-list-5 block-list-3-m block-list-1-s block-list-1-xs block-list-padding dataContainer')
    for club in all_clubs.find_all('li'):
        url = club.find('a')['href'].replace('overview', 'squad')
        links_null.append(url)
    return links_null



def write_down(data):
    '''
        Функция добавляет в tsv файл собранные данные
        Если файла не существует, создается новый

        Args:
            information: имя json файла, в который требуется добавить данные
            data: данные, которые запишутся в файл
    '''
    df = pd.DataFrame(data)
    df.to_csv('information.tsv', sep='\t', index=False)
    print(df)

def parse_data():
    '''
    Собираем данные с помощью парсинга. 

    Args:
        all_links: формируется html, который содержит все ссылки на страницы игроков
        players: создается файл с ссылками на страницы всех игроков
        regex: компилируется шаблон регулярного выражения для поиска совпадений
        all_data: собирается словарь с данными об игроке
        all_teams: возвращает список из команды, игрока, его поизиции и роста
'''
    links_parser = get_links('https://www.premierleague.com/clubs')
    all_teams = []
    for u in tqdm(links_parser):
        url = f'https://www.premierleague.com{u}'
        soup = get_soup(url)
        team_name = soup.find('h1', class_='team js-team')
        all_links = soup.find_all('a', class_='playerOverviewCard active')
        players = [i['href'].strip() for i in all_links]
        for l in players:
            link = f'https://www.premierleague.com{l}'
            soup_player = get_soup(link)
            player_name = soup_player.find('div', class_='name t-colour')
            all_height = soup_player.find_all('div', class_='info')
            position = list(filter(lambda x: x.text in ['Goalkeeper', 'Defender', 'Midfielder', 'Forward'], all_height))[0]
            height = list(filter(lambda x: 'cm' in x.text, all_height))
            if not height:
                height = 'None'
            else:
                height = height[0].text

            all_data = {
                'Команда': team_name.text,
                'Игрок': player_name.text,
                'Позиция': position.text,
                'Рост': height,
                }
            all_teams.append(all_data)
    return all_teams


if __name__ == '__main__':
    all_teams = parse_data()
    write_down(all_teams)
   





