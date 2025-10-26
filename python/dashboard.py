from flask import Flask, render_template_string, render_template   # додаємо render_template
from db import get_conn

app = Flask(__name__)

@app.route("/")
def index():
    # підключення до БД
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT v.verkaufsdatum, a.produktname, va.verkaufsmenge, va.verkaufspreis
            FROM verkauf v
            JOIN verkaufartikel va ON v.verkaufID = va.verkaufID
            JOIN artikel a ON va.artikelID = a.artikelID
            ORDER BY v.verkaufsdatum DESC
            LIMIT 20;
        """)
        rows = cur.fetchall()
    conn.close()

    # віддаємо HTML-шаблон (templates/dashboard.html)
    return render_template("dashboard.html", rows=rows, title="Дашборд")

# ▶️ Запускаємо Flask-сервер (доступний для всіх у локальній мережі)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)  # запускає сервер на порту 5000
