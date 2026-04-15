# 📊 NewShop – Sales Analytics System (Raspberry Pi + MySQL + Flask)

NewShop is a data analytics system designed to simulate a real retail environment.

The project demonstrates how sales data can be generated, stored, processed, and visualized using a full data pipeline — from raw data to business insights.

💡 The system runs on a Raspberry Pi, acting as a lightweight data server.

---

## 🚀 What I built

In this project, I implemented:

- a data generation system simulating real sales (purchases, sales, stock)
- a MySQL database with structured business data
- SQL views for analytical queries (sales, customers, products)
- a Flask-based dashboard for data visualization
- automated data processing scripts
- integration of Python + SQL + web visualization

---

## 📈 Business value

The system provides insights such as:

- daily sales performance
- top customers and products
- profit and margin analysis
- inventory status and stock alerts
- Pareto (80/20) analysis
- stock turnover metrics

---

## 🧠 What I learned

- building end-to-end data pipelines
- working with SQL (views, aggregation, analysis)
- designing data models for business scenarios
- connecting backend data with frontend dashboards
- simulating realistic datasets
- deploying a system on Raspberry Pi
---

## ⚙️ Systemübersicht

| Komponente | Beschreibung |
|-------------|---------------|
| **Datenbank (MySQL)** | Tabellen: `kunden`, `artikel`, `lieferanten`, `verkauf`, `verkauf_artikel` |
| **Python-Module** | Datengenerierung (`generate_history.py`, `sale.py`, `purchase.py`) + Web-Frontend |
| **Flask Dashboard** | Visualisierung der Daten (Umsatz, Marge, Lagerbestand usw.) |
| **Raspberry Pi 5** | Host-System mit MySQL-Server und Python-Umgebung |
| **Chart.js** | Visualisierung und Diagramme im Browser |

---

## 📂 Projektstruktur

```plaintext
newshop/
├── python/
│   ├── auth/              → Login-System
│   ├── generators/        → Datengenerierung & Simulation (Verkauf, Einkauf, Lager)
│   │   ├── generate_history.py
│   │   ├── sale.py
│   │   └── purchase.py
│   ├── reports/           → Alle Analyseberichte (Umsatz, Pareto, Lager, u.a.)
│   │   ├── routes.py
│   │   ├── service.py
│   │   └── templates/
│   ├── dashboard.py       → Haupt-App (Flask)
│   └── db.py              → Verbindung zu MySQL
│
├── sql/                   → SQL-Dateien für Tabellen, Views, Trigger
│   ├── create_tables.sql
│   ├── v_sales.sql
│   ├── v_sales_by_day.sql
│   ├── v_sales_by_customer.sql
│   └── v_umschlag_90tage.sql
│
├── .env                   → Umgebungsvariablen (DB_USER, DB_PASSWORD, DB_HOST)
├── ER.drawio              → Datenmodell (ER-Diagramm)
├── README.md
└── notes.md
```
---


## 🚀 **Installation & Start**

### Voraussetzungen
- Raspberry Pi 4 oder 5 mit **Raspberry Pi OS**
- **Python 3.11+**
- **MySQL 8.x**
- Virtuelle Umgebung `.venv` (optional)

### 1. Setup der Umgebung

```bash
git clone https://github.com/KaterynaSavelieva/newshopdb.git
cd newshopdb
python -m venv .venv
source .venv/bin/activate  
pip install -r requirements.txt
```

### 2. MySQL-Datenbank erstellen

```
CREATE DATABASE newshopdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE newshopdb;
SOURCE sql/create_tables.sql;
SOURCE sql/data.sql;
SOURCE sql/v_sales.sql;
SOURCE sql/v_sales_by_day.sql;
SOURCE sql/v_sales_by_customer.sql;
SOURCE sql/v_umschlag_90tage.sql;
```

### 3. Historische Daten generieren

> ⚠️ Trigger sollten dabei deaktiviert sein, da der Python-Code Lagerbestand und Durchschnittskosten selbst aktualisiert.

```python -m python.generators.generate_history```
Dadurch werden Lagerstände und Durchschnittskosten automatisch berechnet
und Verkaufsdaten für mehrere Monate erzeugt.


### 4. Web-Dashboard starten
```python dashboard.py```

Dann im Browser öffnen:

```http://localhost:5000```

oder (bei Raspberry Pi im Netzwerk):

```http://<Raspberry-IP>:5000```


### 📈 Analyseberichte im Dashboard

| Bericht | Beschreibung |
|-------------|---------------|
| Dashboard | Übersicht aller Verkäufe |
| Umsatz pro Tag | Tagesstatistik der Verkäuf|
| Umsatz pro Kunde | Top Kunden, Umsatz & Marge |
| Umsatz pro Artikel | tikelanalyse mit Filter & Zeitreihen |
| Lagerwarnung | Artikel mit niedrigem Bestand |
| Pareto 80/20| Umsatz- oder Marge-Verteilung (nach Artikel, Kunde, Kundentyp) |
| Umschlag 90 Tage | Lagerumschlag und durchschnittliche Lagerdauer | 	


    
### 🎯 Lernziele / Fokus
   - Datenbankmodellierung (MySQL, Views, Trigger, Constraints)
   - Python-Programmierung (Datenanalyse, Simulation, Flask)
   - Chart.js-Visualisierung & Responsive Webdesign
   - Filtern, Aggregieren & Darstellen betrieblicher Kennzahlen (Umsatz, Marge, Lager)
   - Einsatz von Raspberry Pi als lokaler Datenserver
   - Präsentation vollständiger Datenprozesskette (Daten → Analyse → Visualisierung)

### 👩‍💻 Autorin

**Kateryna Savelieva**

📍 Zeltweg, Österreich

🎓 Weiterbildung im SZF  – Fachbereich IT

💡 Ziel: Berufseinstieg als Data Analystin



📅 Projektzeitraum: September – November 2025

🕓 Letzte Aktualisierung: November 2025

