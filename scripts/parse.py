import requests
import bs4
import re
import json
import time
import os.path

LINKS_FILENAME = "match_links.json"
STATS_FILENAME = "match_stats.json"
SEASON_LINKS = [
    "https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures",
    "https://fbref.com/en/comps/9/2021-2022/schedule/2021-2022-Premier-League-Scores-and-Fixtures",
    "https://fbref.com/en/comps/9/2020-2021/schedule/2020-2021-Premier-League-Scores-and-Fixtures",
    "https://fbref.com/en/comps/9/2019-2020/schedule/2019-2020-Premier-League-Scores-and-Fixtures",
    "https://fbref.com/en/comps/9/2018-2019/schedule/2018-2019-Premier-League-Scores-and-Fixtures"
]


def dump_to_json(filename: str, data: list) -> None:
    '''
        Функция добавляет в json файл новые данные в список
        Для корректной работы нужно, чтобы в передаваемом json файле был список
        Если файла не существует, создается новый

        Args:
            filename: имя json файла, в который требуется добавить данные
            data: данные, которые дозапишутся в файл
    '''
    if os.path.isfile(filename):
        with open(filename, 'r') as file:
            file_data = json.loads(file.read())
    else:
        file_data = []

    file_data.extend(data)

    with open(filename, 'w') as file:
        file.write(json.dumps(file_data))


def percent_to_ratio(percent: str) -> float:
    '''
        Функция преобразует строку с процентом в долю

        Args:
            percent: строка, представляющая процент (например, "64%")

        Returns:
            ratio: доля
    '''

    return float(0) if percent == '%' else int(percent[:-1]) / 100


def get_match_data(html: str) -> dict:
    '''
        Функция возвращает словарь с статистикой матча из html страницы

        Args:
            html: html страница матча

        Returns:
            data: словарь с ключами home и guest, в которых перечислена статистика матча в виде словаря 
    '''

    data = {'home': {}, 'guest': {}}
    soup = bs4.BeautifulSoup(html, "html.parser")

    # Парсинг блока счёта и xG
    home_div = soup.find('div', {'class': 'scorebox'}).find('div')
    guest_div = soup.find('div', {'class': 'scorebox'}).find(
        'div').find_next_sibling('div')
    data['home']['team'] = home_div.find("a").text
    data['guest']['team'] = guest_div.find("a").text
    data['home']['score'] = int(home_div.find('div', {'class': 'score'}).text)
    data['guest']['score'] = int(
        guest_div.find('div', {'class': 'score'}).text)
    data['home']['xG'] = float(home_div.find(
        'div', {'class': 'score_xg'}).text)
    data['guest']['xG'] = float(guest_div.find(
        'div', {'class': 'score_xg'}).text)
    scorebox_meta = soup.find("div", {'class': 'scorebox_meta'})
    data['match_date'] = scorebox_meta.find(
        'span', {'class': 'venuetime'})['data-venue-date']
    data['match_week'] = int(re.findall(
        r'\d+', scorebox_meta.find_all('div')[1].text)[0])

    # Парсинг блока основной статистики
    params = ['possession', 'passing_accuracy', 'shots_on_target', 'saves']
    stats = soup.find('div', {'id': 'team_stats'}).find_all('strong')
    home = stats[::2]
    guest = stats[1::2]
    for h, g, p in zip(home, guest, params):
        data['home'][p] = percent_to_ratio(h.text)
        data['guest'][p] = percent_to_ratio(g.text)
    cards = soup.find_all('div', {'class': 'cards'})
    data['home']['yellow_cards_count'] = len(
        cards[0].find_all('span', {'class': 'yellow_card'}))
    data['home']['red_cards_count'] = len(
        cards[0].find_all('span', {'class': 'red_card'}))
    data['guest']['yellow_cards_count'] = len(
        cards[1].find_all('span', {'class': 'yellow_card'}))
    data['guest']['red_cards_count'] = len(
        cards[1].find_all('span', {'class': 'red_card'}))

    # Парсинг блока с дополнительной статистикой
    params = ['fouls', 'corners', 'crosses', 'touches', 'tackles', 'interceptions',
              'aerials_won', 'clearances', 'offsides', 'goal_kicks', 'throw_ins', 'long_balls']
    stats = soup.find('div', {'id': 'team_stats_extra'})
    divs = stats.find_all('div')
    divs = [div.text for div in divs]
    divs = [div for div in divs if div.isdigit()]
    home = divs[::2]
    guest = divs[1::2]
    for h, g, p in zip(home, guest, params):
        data['home'][p] = int(h)
        data['guest'][p] = int(g)

    return data


def scrap_match_links(league_page: str) -> None:
    '''
        Функция, которая собирает ссылки на страницы матчей определенного сезона и записывает их в json файл

        Args:
            league_page: html страница матча с fbref
    '''

    soup = bs4.BeautifulSoup(league_page, "html.parser")
    tds = soup.find("div", {'id': 'all_sched'}).find(
        "table").find_all("td", {'data-stat': 'score'})
    links = []
    for td in tds:
        a = td.find("a")
        if a:
            links.append("https://fbref.com/" + td.find("a")['href'])
    dump_to_json(LINKS_FILENAME, links)


def request_seasons(season_links: list) -> None:
    '''
        Функция получает ссылки на страницы сезонов с fbref и передает в scrap_match_links html страницу

        Args:
            season_links: ссылки на страницы сезонов с fbref
    '''

    responses = []
    for season_link in season_links:
        print(f"Requesting {season_link}:")
        response = requests.get(season_link)
        print(f"\tStatus code: {response.status_code}")
        if response.status_code == 200:
            scrap_match_links(response.text)
        time.sleep(3.1)


def request_matches(match_links: list) -> None:
    '''
        Функция запрашивает страницу матча с fbref и записывает в json статистику, полученную из get_match_data

        Args:
            match_links: ссылки на страницы матчей
    '''
    for i, link in enumerate(match_links):
        print(f"Requesting {i + 1} out of {len(match_links)}:")
        response = requests.get(link)
        print(f"\tStatus code: {response.status_code}")
        if response.status_code == 200:
            dump_to_json(STATS_FILENAME, [
                         get_match_data(response.text)])
        else:
            print(response.text)
        time.sleep(3.1)


request_seasons(SEASON_LINKS)

with open(LINKS_FILENAME, 'r') as file:
    match_links = json.loads(file.read())

request_matches(match_links)
