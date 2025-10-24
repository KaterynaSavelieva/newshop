# dashboard.py
# Простий Flask-додаток для перегляду останніх продажів із бази newshopdb

from flask import Flask, render_template_string   # імпортуємо Flask і функцію для створення HTML зі змінними
from db import get_conn                           # імпортуємо нашу функцію підключення до бази

app = Flask(__name__)                             # створюємо Flask-додаток

@app.route("/")                                   # маршрут: коли відкривається головна сторінка "/"
def index():                                      # функція, яка виконується при відкритті сайту
    conn = get_conn()                             # підключення до бази даних
    with conn.cursor() as cur:                    # відкриваємо курсор для запитів
        cur.execute("""                           # SQL-запит вибирає останні 20 продажів
            SELECT v.verkaufsdatum, a.produktname, va.verkaufsmenge, va.verkaufspreis
            FROM verkauf v
            JOIN verkaufartikel va ON v.verkaufID = va.verkaufID
            JOIN artikel a ON va.artikelID = a.artikelID
            ORDER BY v.verkaufsdatum DESC
            LIMIT 20;
        """)
        rows = cur.fetchall()                     # отримуємо всі результати
    conn.close()                                  # закриваємо з'єднання

    # 🧱 створюємо HTML-таблицю прямо в коді
    html = """
    <h1 style="font-family:sans-serif;">🧾 Verkauf Übersicht</h1>
    <table border="1" cellpadding="5">
        <tr><th>Datum</th><th>Artikel</th><th>Menge</th><th>Preis</th></tr>
        {% for r in rows %}
        <tr><td>{{r[0]}}</td><td>{{r[1]}}</td><td>{{r[2]}}</td><td>{{r[3]}}</td></tr>
        {% endfor %}
    </table>
    """

    return render_template_string(html, rows=rows)  # вставляємо дані у HTML і повертаємо сторінку

# ▶️ Запускаємо Flask-сервер (доступний для всіх у локальній мережі)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)  # запускає сервер на порту 5000
