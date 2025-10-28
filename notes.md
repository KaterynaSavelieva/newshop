# Git Work Routine (Laptop + Raspberry)
1. git pull origin main
2. work...
3. git add .
4. git commit -m "..."
5. git push origin main

   
**Datenbankzugriff (MariaDB)**

    sudo mariadb -u root myshopdb 


**Python-Umgebung**

_Virtuelle Umgebung aktivieren_
  
    .\.venv\Scripts\Activate.ps1
    python .\python\test_insert_select.py

_Test-Skript ausführen_

      python .\python\test_insert_select.py

**Backup-Befehle**

_Ordner für Backups_
        
        mkdir -p ~/myshop/backups

_Backup erstellen_

        sudo mysqldump -u root myshopdb > ~/myshop/backups/myshopdb_$(date +%Y%m%d_%H%M).sql


**Status-Check**

_Prüfen, ob MariaDB läuft_

        sudo systemctl status mariadb

_Tabellen anzeigen_
        
        sudo mariadb -u root myshopdb -e "SHOW TABLES;"
