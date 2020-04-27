import configparser
from json import JSONDecodeError
from time import sleep
import pandas as pd
from transliterate import translit
from googletrans import Translator
import regex
import requests
from lxml.html import fromstring

before_title = " language. "
before_desc = "Please feel free to request a detailed description. Short description: "
after_desc = " We have thousands of titles and often several copies of each title may be available. \
Please contact us for details on condition of available copies of the book. SKU"


def get_proxies():
    url = 'https://free-proxy-list.net/'
    response = requests.get(url)
    parser = fromstring(response.text)
    proxies = {}
    for i in parser.xpath('//tbody/tr')[:1000]:
        if i.xpath('.//td[7][contains(text(),"yes")]'):
            # добавляем IP и соответствующий PORT
            proxies[i.xpath('.//td[1]/text()')[0]] = i.xpath('.//td[2]/text()')[0]
    return proxies


def translate_text(text):
    translator = Translator(service_urls=['translate.google.com', 'translate.google.co.kr'], proxies=proxy)
    try:
        translation = translator.translate(text)
    except JSONDecodeError:
        print("Exception!! Your IP was blocked. Wait 60 second")
        sleep(60)
        return translate_text(text)
    return translation.text


def transform_price(price, date):
    if date <= 1860:
        res = 600
    elif date <= 1930:
        res = 400
    elif price <= 120000:
        res = price / rub * 2 + 100
    elif price <= 600000:
        res = price / rub * 1.5
    else:
        res = price / rub * 1.3
    if res % 100 != 0:
        res = ((res // 100) + 1) * 100
    return int(res) - 1


def transform_ke(text):
    res0 = re.sub(r'[^a-zA-Z0-9]', ' ', text)  # оставляем только буквы, цифры и пробелы
    res1 = re.sub(r' [a-zA-Z] ', ' ', res0)    # убираем односимвольные слова
    res2 = re.sub(r' [a-zA-Z] ', ' ', res1)    # убираем односимвольные слова
    for _, article in articles.iterrows():     # убираем артикли из списка артиклей
        pattern = ' ' + article[0] + ' '
        res2 = re.sub(pattern, ' ', res2)
    tmp = res2.split()
    res = ', '.join(tmp)
    if len(res) > 255:
        return res[:255]
    return res


def transform_description(desc, code):
    translation = translate_text(regex.sub('&', ' ', desc))
    res = before_desc + translation + after_desc + code
    return res


def transform_title(text, original, lang):
    transliteration = translit(original, 'ru', reversed=True)
    if not pd.isna(lang):
        res = lang + before_title + text + '/ ' + transliteration
    else:
        res = text + '/ ' + transliteration
    if len(res) > 750:
        return res[:750]
    return res


# Считываем заданные параметры
config = configparser.ConfigParser()
config.read("settings.ini")

# Я не знала, какие поля будут в файле с конфигами, поэтому взяла такие :)
source_path = config["NAME"]["source"]
destination_path = config["NAME"]["destination"]
articles_path = config["NAME"]["articles"]
rub = float(config["NAME"]["ruble"])

# набор артиклей, которые нужно будет убрать из description
articles = pd.read_excel(articles_path)
# исходные данные для преобразований
df = pd.read_excel(source_path)

# получаем набор IP и PORT, которые затем будут менятся в запросах
proxy = get_proxies()
print(proxy)

columns = df.columns
new_df = pd.DataFrame({columns[i]: [] for i in range(columns.size)})

with open(destination_path, 'w', encoding='utf-16le') as output:
    for index, row in df.iterrows():

        # преобразуем цену
        pr, dp = row["PR|"], row["DP|"]
        row["PR|"] = transform_price(int(pr), dp)

        # преобразуем описание (нужен перевод)
        ur, nt = row["UR|"], row["NT|"]
        row["NT|"] = transform_description(nt, ur)

        # преобразуем заголовок (нужен перевод)
        ti, lg = row["TI|"], row["LG|"]
        translated = translate_text(ti)
        row["TI|"] = transform_title(translated, ti, lg)
        row["KE|"] = transform_ke(translated)

        # записываем данные в выходной файл
        for i in range(size):
            if pd.isna(row[i]):
                output.writelines([columns[i], 'n/a'])
            else:
                output.writelines([columns[i], str(row[i])])
            output.write("\n")
        output.write("\n")
