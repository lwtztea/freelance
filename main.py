import configparser
import pandas as pd
from transliterate import translit
from googletrans import Translator
import re

before_title = "Russian language. "
before_desc = "Please feel free to request a detailed description. Short description: "
after_desc = " We have thousands of titles and often several copies of each title may be available. \
Please contact us for details on condition of available copies of the book. SKU"
after_lang = " (unless indicated otherwise by the description)"


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
    res1 = re.sub(r' [a-zA-Z] ', ' ', res0)  # убираем односимвольные слова
    res2 = re.sub(r' [a-zA-Z] ', ' ', res1)  # убираем односимвольные слова
    for _, article in articles.iterrows():
        pattern = ' ' + article[0] + ' '
        res2 = re.sub(pattern, ' ', res2)
    res = re.sub(r'\s+', ' ', res2)  # убираем повторяющиеся пробелы
    if len(res) > 255:
        return res[:255]
    return res


def transform_description(desc, code):
    translation = translator.translate(desc)
    res = before_desc + translation.text + after_desc + code
    return res


def transform_title(translation, text):
    transliteration = translit(text, 'ru', reversed=True)
    res = before_title + translation.text + '/ ' + transliteration
    if len(res) > 750:
        return res[:750]
    return res


config = configparser.ConfigParser()
config.read("settings.ini")

source_path = config["NAME"]["source"]
destination_path = config["NAME"]["destination"]
articles_path = config["NAME"]["articles"]
rub = float(config["NAME"]["ruble"])

articles = pd.read_excel(articles_path)

df = pd.read_excel(source_path)
translator = Translator()

columns = df.columns
new_df = pd.DataFrame({columns[i]: [] for i in range(columns.size)})

for index, row in df.iterrows():
    pr, dp = row["PR|"], row["DP|"]
    row["PR|"] = transform_price(pr, dp)
    ur, nt = row["UR|"], row["NT|"]
    row["NT|"] = transform_description(nt, ur)
    ti, lg = row["TI|"], row["LG|"]
    translated = translator.translate(ti)
    row["TI|"] = transform_title(translated, ti)
    row["KE|"] = transform_ke(translated.text)
    if not pd.isna(lg):
        row["LG|"] = lg + after_lang
    new_df = new_df.append(row)

new_df.to_excel(destination_path)
