## 🛍️ **NewShop – Verkaufsanalyse mit Raspberry Pi**

Ziel des Projekts ist es zu zeigen, wie ein kleiner Daten-Server auf Basis eines **Raspberry Pi**  
vollständig den Datenprozess eines Shops abbilden kann – von der Datenerzeugung bis zur Analyse.

---

## 🎯 **Projektziel**

Der Raspberry Pi fungiert als Mini-Server, der automatisch Verkaufs- und Einkaufsdaten generiert,  
in einer **MySQL-Datenbank** speichert und Analysen über ein **Flask-basiertes Web-Dashboard** anzeigt.  
So lässt sich der komplette Datenprozess in einem kleinen Unternehmen simulieren:

> **Datenfluss:**  
> Daten-Generierung → Speicherung in MySQL → Analyse → Visualisierung im Web-Dashboard

---

## ⚙️ **Systemübersicht**

| Komponente | Beschreibung |
|-------------|---------------|
| 🐍 **Python-Skripte** | Generierung von Verkäufen (`sale.py`), Einkäufen (`purchase.py`) und historischer Daten (`generate_history.py`) |
| 🧮 **MySQL-Datenbank** | Tabellen wie `kunden`, `lieferanten`, `artikel`, `verkauf`, `einkauf` usw. |
| 🌐 **Flask-Web-App** | Dashboard mit Analysen (Umsatz, Pareto 80/20, Lagerwarnung, Umschlag etc.) |
| 🍓 **Raspberry Pi 5** | Host-System mit MySQL-Server und Python-Umgebung |
| 📊 **Chart.js + Bootstrap 5** | Visualisierung und modernes UI im Browser |

---

## 🗂️ **Projektstruktur**
```
newshop/
├── python/
│ ├── db.py # Verbindung zur MySQL-Datenbank
│ ├── generators/
│ │ ├── sale.py # tägliche Generierung von Verkäufen
│ │ ├── purchase.py # automatische Nachbestellungen
│ │ └── generate_history.py # Erzeugt komplette historische Daten 2024–2025
│ ├── dashboard/
│ │ ├── routes.py # Flask-Routen
│ │ └── templates/ # HTML-Vorlagen (base.html, pareto.html, etc.)
│ └── ...
├── sql/
│ ├── schema.sql # Tabellen-Definitionen
│ ├── triggers.sql # Datenbank-Trigger (für reale Nutzung)
│ └── views.sql # Analyse-Views
├── .env # Verbindungsdaten (DB_HOST, DB_USER, DB_PASSWORD)
├── app.py # Flask-Startpunkt
└── README.md
```

---

## 🚀 **Installation & Start**

### 1️⃣ Voraussetzungen
- Raspberry Pi 4 oder 5 mit **Raspberry Pi OS**
- **Python 3.11+**
- **MySQL 8.x**
- Virtuelle Umgebung `.venv` (optional)

### 2️⃣ Setup der Umgebung

```bash
git clone https://github.com/KaterynaSavelieva/newshopdb.git
cd newshopdb
python -m venv .venv
source .venv/bin/activate   # oder: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3️⃣ MySQL-Datenbank vorbereiten

```
mysql -u root -p
CREATE DATABASE newshopdb;
USE newshopdb;
SOURCE sql/schema.sql;
SOURCE sql/views.sql;
-- Trigger nur im Produktionsmodus aktivieren:
-- SOURCE sql/triggers.sql;
```

### 4️⃣ Generierung historischer Daten

> ⚠️ Trigger sollten dabei deaktiviert sein, da der Python-Code Lagerbestand und Durchschnittskosten selbst aktualisiert.

```python -m python.generators.generate_history```


Erzeugt:

- Einkäufe (01.01.–03.01.2024)
- Verkäufe (04.01.2024–30.10.2025)
- Automatische Nachbestellungen bei Bedarf

### 5️⃣ Web-Dashboard starten
```flask --app python.dashboard.routes run --host=0.0.0.0 --port=5000```

Dann im Browser öffnen:
👉 ```http://<Raspberry-IP>:5000```

### 📈 Analyse-Berichte im Dashboard

| Bericht | Beschreibung |
|-------------|---------------|
| Dashboard | Übersicht aller Verkäufe |
| Umsatz pro Tag | Tagesumsätze als Diagramm|
| Umsatz pro Kunde | Artikel	Ranking der besten Kunden und Artikel |
| Pareto 80/20| Umsatzverteilung (80 % Umsatz durch 20 % Kunden/Artikel) |
| Lagerwarnung | Artikel mit niedrigem Bestand |
| Umschlag 90 Tage | Lagerumschlag in den letzten 90 Tagenr | 	

    
### 🧠 Lernziele / Fokus
   - Praxisorientierte Anwendung von SQL, Python, Flask, Bootstrap, Chart.js
   - Datenbank-Design und Trigger-Logik
   - Datenanalyse und Visualisierung auf Raspberry Pi
   - Automatisierung von Verkaufs-/Einkaufsprozessen
   - Projektarbeit im Rahmen einer Weiterbildung zur Data Analystin

### 👩‍💻 Autorin

Kateryna Savelieva

📍 Zeltweg, Österreich

🎓 Teilnehmerin am SZF (Murau / Murtal)

💡 Ziel: Berufseinstieg als Data Analystin


### 📅 Zeitraum
Projektzeitraum: September-Oktober 2025

Letzte Aktualisierung: Oktober 2025


