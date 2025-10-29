import sqlite3
from datetime import datetime, timedelta

def report_non_validated_events():
    conn = sqlite3.connect('agenda_db.sqlite')
    conn.row_factory = sqlite3.Row
    today = datetime.now().strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Prend les événements du jour non validés
    events = conn.execute("""
        SELECT * FROM events
        WHERE DATE(start) = ? AND (statut != 'validé' OR statut IS NULL)
    """, (today,)).fetchall()
    
    for event in events:
        # Décale la date de 1 jour
        start_dt = datetime.strptime(event['start'], "%Y-%m-%d %H:%M:%S")
        new_start = (start_dt + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("UPDATE events SET start = ? WHERE id = ?", (new_start, event['id']))
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    report_non_validated_events()
