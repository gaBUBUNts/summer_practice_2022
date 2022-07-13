import requests
from bs4 import BeautifulSoup
import httplib2
import apiclient
from oauth2client.service_account import ServiceAccountCredentials

"""Подключаем google sheet"""
# Читаем ключи из файла
credentials = ServiceAccountCredentials.from_json_keyfile_name("creds.json",
                                                               ['https://www.googleapis.com/auth/spreadsheets',
                                                                'https://www.googleapis.com/auth/drive'])
httpAuth = credentials.authorize(httplib2.Http())
service = apiclient.discovery.build('sheets', 'v4', http=httpAuth)

with open("spreadsheet_id.txt", "r") as temp:
    spreadsheet_id = temp.readline()[:-1]

"""Создание гугл таблицы"""
if spreadsheet_id == "":
    spreadsheet = service.spreadsheets().create(body={
        'properties': {'title': 'Practice', 'locale': 'ru_RU'},
        'sheets': [{'properties': {'sheetType': 'GRID',
                                   'sheetId': 0,
                                   'title': 'YandexLavka',
                                   'gridProperties': {'rowCount': 100, 'columnCount': 15}}}]
    }).execute()

    with open("spreadsheet_id.txt", "w") as file:
        file.write(spreadsheet_id := spreadsheet['spreadsheetId'])

    driveService = apiclient.discovery.build('drive', 'v3',
                                             http=httpAuth)  # Выбираем работу с Google Drive и 3 версию API
    access = driveService.permissions().create(
        fileId=spreadsheet_id,
        body={'type': 'user', 'role': 'writer', 'emailAddress': 'pro.ildar.9999@gmail.com'},
        # Открываем доступ на редактирование
        fields='id'
    ).execute()

"""Парсим данные из яндекс лавки"""
home_str = requests.get("https://lavka.yandex.ru/43/").text
home = BeautifulSoup(home_str, "lxml")
list_of_urls = []
products_category = []
for tag in home.find_all("a", class_="azs7ia1"):
    list_of_urls.append("https://lavka.yandex.ru" + tag["href"])
    products_category.append(
        tag.div.span.text.replace("\u200e", "").replace("\xa0", " ").replace("\xad", ""))

products_name = []
products_cost = []
new_products_category = []

for category_url, category_name in zip(list_of_urls, products_category):
    category = BeautifulSoup(requests.get(category_url).text, "lxml").find_all("div", class_="iw2of08")
    for product in category:
        new_products_category.append(category_name)
        products_name.append(product.h3.text)
        if product.find("span", class_="a1dq5c6d") is None:  # если на товар нет скидки
            temp_product_cost = product.find("span",
                                             class_="t18stym3 b1clo64h m493tk9 m1fg51qz tnicrlv l14lhr1r").text[:-1]
            products_cost.append(temp_product_cost.replace(" ", ""))
        else:  # если на товар есть скидка
            products_cost.append(product.find("span", class_="a1dq5c6d").text[15:])

"""Заносим данные в google sheet"""
service.spreadsheets().values().batchUpdate(
    spreadsheetId=spreadsheet_id,
    body={
        "valueInputOption": "USER_ENTERED",
        "data": [
            {"range": f"A1:C{len(products_name)}",
             "majorDimension": "COLUMNS",
             "values": [new_products_category, products_name, products_cost]}
        ]
    }
).execute()
