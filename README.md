# 🛍️ **NewShop – Verkaufsanalyse mit Raspberry Pi**


### Ziel des Projekts

Dieses Projekt zeigt, wie ein kleiner **Raspberry Pi** als **Mini-Datenserver** für den Einzelhandel dienen kann.  
Der Pi generiert Verkaufsdaten automatisch, speichert sie in einer **MySQL-Datenbank**  
und stellt interaktive **Analysen im Web-Dashboard (Flask + Chart.js)** dar.

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

