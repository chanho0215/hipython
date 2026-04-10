from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import mysql.connector

# ✅ MySQL 연결
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1234",
    database="quotes_db"
)

cursor = conn.cursor()

quotes_list = []

# ---------------------------
# 크롤링
# ---------------------------
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto('https://quotes.toscrape.com/')

    soup = BeautifulSoup(page.content(), 'lxml')

    for q in soup.select('div.quote'):
        quote = q.select_one('span.text').get_text(strip=True)
        author = q.select_one('small.author').get_text(strip=True)

        quotes_list.append({
            'quote': quote,
            'author': author
        })

    browser.close()

# ---------------------------
# DB INSERT
# ---------------------------
sql = """
INSERT INTO quotes (quote, author)
VALUES (%s, %s)
"""

data = [(q['quote'], q['author']) for q in quotes_list]

cursor.executemany(sql, data)
conn.commit()

print(f"{cursor.rowcount}개 명언 저장 완료!")

cursor.close()
conn.close()