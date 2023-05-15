import requests
from bs4 import BeautifulSoup 
import pandas as pd
import re
from random import uniform
from fake_headers import Headers



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
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup
    except requests.RequestException:
        return Fals


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
    links_null=[]
    for t in range(100):
        class_name='indexItem t'+str(t)
        all_urls=soup.find_all('a', class_ =class_name)
        first= [i['href'] for i in all_urls]  
        first=[item.replace('overview', 'squad') for item in first]
        links_null.append(first)
    links_null = list(filter(None, links_null))
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
    with open('information.tsv','w') as f:
        f.write('Игроки\n')  
        df.to_csv(f, index=False) 

'''
    Собираем данные с помощью парсинга. Функция не использована, так как оно не хочет работать быстро, а я не терпеливая.

    Args:
        all_links: формируется html, который содержит все ссылки на страницы игроков
        players: создается файл с ссылками на страницы всех игроков
        regex: компилируется шаблон регулярного выражения для поиска совпадений
        all_data: собирается словарь с данными об игроке
        all_teams: возвращает список из команды, игрока, его поизиции и роста
'''
links_parser=get_links('https://www.premierleague.com/clubs')
all_teams=[]
for u in links_parser:
        url='https://www.premierleague.com'+ u[0] 
        soup = get_soup(url)
        team_name=soup.find('h1', class_='team js-team')
        all_links=soup.find_all('a', class_ = 'playerOverviewCard active')
        players= [i['href'].strip() for i in all_links]
        for l in players:
            link='https://www.premierleague.com'+l
            try:
                soup_player = get_soup(link)
                player_name=soup_player.find('div', class_='name t-colour')
                all_height=soup_player.find_all('div', class_='info')
                regex = re.compile('cm')
                try:
                    if (regex.search(all_height[4].string) != None):
                        all_data = {'Команда': team_name.text, 'Игрок': player_name.text, 'Позиция': all_height[1].text,'Рост': all_height[4].text}
                except: 
                    pass
                try: 
                    if (regex.search(all_height[3].string) != None):
                        all_data = {'Команда': team_name.text, 'Игрок': player_name.text, 'Позиция': all_height[0].text,'Рост': all_height[3].text}
                except: 
                    pass
                if not all_data:
                    all_data = {'Команда': team_name.text, 'Игрок': player_name.text, 'Позиция': all_height[1].text,'Рост': 'None'}
                all_teams.append(all_data)
            except requests.RequestException:
                pass


write_down(all_teams)
df = pd.DataFrame(all_teams)
print(df)






