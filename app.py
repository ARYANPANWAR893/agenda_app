from flask import Flask, render_template, request, redirect, jsonify, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import request
from apscheduler.schedulers.background import BackgroundScheduler
from flask import flash, redirect, url_for, session
from flask import send_file

import sqlite3
from datetime import datetime, date, timedelta
import os
import pandas as pd
def insert_default_users():
    conn = get_db_connection()
    c = conn.cursor()
users_to_create = [
        ("Dir", "dir@example.com", "Direction"),
        ("Compta1", "compta1@example.com", "Pôle Compta"),
        ("Compta2", "compta2@example.com", "Pôle Compta"),
        ("Compta3", "compta3@example.com", "Pôle Compta"),
        ("Compta4", "compta4@example.com", "Pôle Compta"),
        ("GDP1", "gdp1@example.com", "Pôle Social"),
        ("GDP2", "gdp2@example.com", "Pôle Social"),
        ("ASUDEC", "asudec@example.com", "Pôle juridique"),
        ("Comm", "comm@example.com", "Pôle Communication"),
        ("ASDC1", "asdc1@example.com", "Assistance Compta"),
        ("ASDC2", "asdc2@example.com", "Assistance Compta"),
        ("ASDC3", "asdc3@example.com", "Assistance Compta"),
        ("ASDC4", "asdc4@example.com", "Assistance Compta"),
        ("ASDC5", "asdc5@example.com", "Assistance Compta"),
        ("ASDC6", "asdc6@example.com", "Assistance Compta"),
        ("ASDC7", "asdc7@example.com", "Assistance Compta"),
        ("ASDC8", "asdc8@example.com", "Assistance Compta"),
        ("ASDP1", "asdp1@example.com", "Assistance Paie"),
        ("ASDP2", "asdp2@example.com", "Assistance Paie"),
        ("ASDP3", "asdp3@example.com", "Assistance Paie"),
        ("ASDP4", "asdp4@example.com", "Assistance Paie"),
        ("ASDJ", "asdj@example.com", "Assistance juridique"),
        ("ASDCOM", "asdcom@example.com", "Assistance Communication"),
        ("ASDDEV", "asddev@example.com", "Assistance Communication"),
    ]



DATABASE = 'agenda_db.sqlite'  # adapte selon ton projet

current_date = date.today().isoformat()


UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'bmp'}

app = Flask(__name__)
app.secret_key = 'clé_secrète'

# Configuration Flask (à faire après avoir créé "app")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20 Mo max

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
def insert_default_users():
    conn = get_db_connection()
    c = conn.cursor()

    users_to_create = [
        ("Dir", "dir@example.com", "Direction"),
        ("Compta1", "compta1@example.com", "Pôle Compta"),
        # ... autres utilisateurs
    ]

    for username, email, role in users_to_create:
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        if c.fetchone():
            print(f"Utilisateur {username} existe déjà, passage.")
            continue
        hashed_pw = generate_password_hash("MotDePasse123")  # mot de passe par défaut
        c.execute("INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)",
                  (username, hashed_pw, email, role))
        print(f"Utilisateur {username} créé avec rôle {role}.")
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
def reporter_evenements_non_valides():
    conn = get_db_connection()
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    
    # On ne reporte que les tâches dont la date est passée (avant aujourd’hui) et qui ne sont pas validées
    events = conn.execute("""
        SELECT id, start, statut
        FROM events
        WHERE date(start) <= ? AND (statut IS NULL OR statut != 'validé')
    """, (today.strftime("%Y-%m-%d"),)).fetchall()
    
    for event in events:
        try:
            # On reporte d’un jour la date de start
            old_start = datetime.strptime(event['start'], "%Y-%m-%d %H:%M")
            new_start = old_start + timedelta(days=1)
            new_start_str = new_start.strftime("%Y-%m-%d %H:%M")
            conn.execute("UPDATE events SET start = ? WHERE id = ?", (new_start_str, event['id']))
        except Exception as e:
            print("Erreur report event:", e)
    conn.commit()
    conn.close()
def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=reporter_evenements_non_valides, trigger="interval", days=1, hour=23, minute=59)  # Exécution chaque jour à 23h59
    scheduler.start()
def get_db_connection():
    conn = sqlite3.connect('agenda_db.sqlite')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()

    # Création de la table 'users'
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Création de la table 'events'
    c.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            start TEXT NOT NULL,
            classe TEXT NOT NULL,
            user_id INTEGER,
            statut TEXT DEFAULT 'à faire',
            projet TEXT,
            priorite TEXT DEFAULT 'Moyenne'
        )
    """)

    # Création de la table 'event_logs'
    c.execute("""
        CREATE TABLE IF NOT EXISTS event_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER,
            action TEXT NOT NULL,
            user_id INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            details TEXT
        )
    """)

    # Création de la table 'event_assignees'
    c.execute("""
        CREATE TABLE IF NOT EXISTS event_assignees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER,
            user_id INTEGER,
            FOREIGN KEY (event_id) REFERENCES events(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Vérification et création de l'utilisateur 'Dir'
    c.execute("SELECT * FROM users WHERE username = ?", ('Dir',))
    if not c.fetchone():
        password = generate_password_hash("Directeur123")
        c.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)", ('Dir', password, 'Dir@example.com'))
        print("✅ Utilisateur Dir créé.")
    else:
        print("⚠️ Utilisateur Dir existe déjà.")

    conn.commit()
    conn.close()

init_db()

def generate_monthly_recurrences(base_date_str, time_str, title, description, classe, repeat_months=12):
    base_date = datetime.strptime(base_date_str, "%Y-%m-%d")
    target_day = base_date.day
    hour, minute = map(int, time_str.split(":"))
    events = []
    for i in range(repeat_months):
        year = base_date.year + ((base_date.month - 1 + i) // 12)
        month = (base_date.month - 1 + i) % 12 + 1
        if month == 12:
            last_day = 31
        else:
            last_day = (datetime(year, month + 1, 1) - timedelta(days=1)).day
        day = min(target_day, last_day)
        event_date = datetime(year, month, day, hour, minute)
        while event_date.weekday() == 6:
            event_date += timedelta(days=1)
            if event_date.month != month:
                break
        if event_date.month == month:
            start_str = event_date.strftime("%Y-%m-%dT%H:%M:%S")
            events.append({
                'title': title,
                'description': description,
                'start': start_str,
                'classe': classe,
            })
    return events
@app.context_processor
def inject_request():
    return dict(request=request)

@app.route('/importer_evenements', methods=['GET', 'POST'])
def importer_evenements():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (session['user'],)).fetchone()
    if user['username'] != 'Dir':
        conn.close()
        flash("Accès réservé à l'administrateur.", "danger")
        return redirect(url_for('evenements'))
    if request.method == 'POST':
        file = request.files.get('fichier_excel')
        if not file:
            flash("Aucun fichier fourni.", "danger")
            return render_template('importer_evenements.html')
        try:
            df = pd.read_excel(file)
            # Colonnes attendues
            colonnes_attendues = ['Titre', 'Description', 'DateHeureDébut', 'DateHeureFin']
            for col in ['Titre', 'DateHeureDébut']:
                if col not in df.columns:
                    flash(f"Colonne manquante dans le fichier : {col}", "danger")
                    return render_template('importer_evenements.html')
            # Insertion en base
            for _, row in df.iterrows():
                title = str(row['Titre'])
                description = str(row.get('Description', '') or '')
                start = str(row['DateHeureDébut'])
                end = str(row.get('DateHeureFin', '') or None)
                conn.execute("""
                     INSERT INTO events (title, description, start, end, user_id)
                     VALUES (?, ?, ?, ?, ?)
                             """, (title, description, start, end, user['id']))

            conn.commit()
            conn.close()
            flash("✅ Importation réussie ! Les tâches ont été ajoutées.", "success")
            return redirect(url_for('evenements'))
        except Exception as e:
            print("Erreur import Excel :", e)
            flash("Erreur lors de l'importation : " + str(e), "danger")
            return render_template('importer_evenements.html')
    conn.close()
    return render_template('importer_evenements.html')
@app.route('/events')
def events_json():
    if 'user' not in session:
        return jsonify([])

    conn = get_db_connection()
    try:
        user = conn.execute("SELECT * FROM users WHERE username = ?", (session['user'],)).fetchone()
        current_year = datetime.now().year

        if user['username'] == 'Dir':
            events = conn.execute(
                """SELECT events.*, users.username 
                   FROM events 
                   LEFT JOIN event_assignees ON event_assignees.event_id = events.id
                   LEFT JOIN users ON event_assignees.user_id = users.id
                   WHERE events.start LIKE ?""",
                (f"{current_year}-%",)
            ).fetchall()
        else:
            user_id = user['id']
            events = conn.execute(
                """SELECT events.*, users.username 
                   FROM events 
                   LEFT JOIN event_assignees ON event_assignees.event_id = events.id
                   LEFT JOIN users ON event_assignees.user_id = users.id
                   WHERE event_assignees.user_id = ? AND events.start LIKE ?
                   ORDER BY events.start ASC""",
                (user_id, f"{current_year}-%")
            ).fetchall()

        event_list = []
        for e in events:
            event_dict = {
                'id': e['id'],
                'title': e['title'],
                'start': e['start'],
                'description': e['description'],
                'classe': e['classe'],
                'statut': e['statut'] if 'statut' in e.keys() else 'à faire',
                'projet': e['projet'] if 'projet' in e.keys() else '',
                'priorite': e['priorite'] if 'priorite' in e.keys() else 'Moyenne',
            }

            # Récupérer les utilisateurs associés à cet événement
            event_users = conn.execute(
                """SELECT users.username 
                   FROM event_assignees 
                   JOIN users ON event_assignees.user_id = users.id
                   WHERE event_assignees.event_id = ?""", 
                (e['id'],)
            ).fetchall()

            event_dict['users'] = [user['username'] for user in event_users]

            event_list.append(event_dict)

        return jsonify(event_list)
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la récupération des événements: {str(e)}"}), 500
    finally:
        conn.close()
@app.route('/calendar_personnel')
def calendar_personnel():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (session['user'],)).fetchone()

    if user['username'] != 'Dir':  # Si l'utilisateur n'est pas l'administrateur, le rediriger ailleurs
        flash("Accès réservé à l'administrateur.", "danger")
        return redirect(url_for('calendar_view'))  # Rediriger vers le calendrier de l'utilisateur normal

    # Récupérer uniquement les événements créés par l'administrateur (Dir)
    events = conn.execute("""
        SELECT events.*, users.username
        FROM events
        LEFT JOIN users ON events.user_id = users.id
        WHERE events.user_id = ?  -- Filtrer pour Dir uniquement
    """, (user['id'],)).fetchall()

    # Convertir chaque ligne de la requête en dictionnaire
    events = [dict(event) for event in events]

    conn.close()

    return render_template('calendar_personnel.html', events=events)

@app.route('/supprimer_utilisateur/<int:user_id>', methods=['POST'])
def supprimer_utilisateur(user_id):
    if 'user' not in session or session['user'] != 'Dir':
        flash("Accès refusé.", "danger")
        return redirect(url_for('login'))

    conn = get_db_connection()
    # Vérifier si l'utilisateur existe
    user_to_delete = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    
    if not user_to_delete:
        flash("Utilisateur introuvable.", "danger")
        conn.close()
        return redirect(url_for('liste_utilisateurs'))

    try:
        # Exécution de la suppression
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        flash("Utilisateur supprimé.", "success")
    except Exception as e:
        flash(f"Erreur lors de la suppression de l'utilisateur : {str(e)}", "danger")
    
    conn.close()
    return redirect(url_for('liste_utilisateurs'))
@app.route('/event/<int:event_id>/supprimer', methods=['POST'])
def supprimer_event(event_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (session['user'],)).fetchone()
    event = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()

    # Vérification des autorisations
    if user['username'] != 'Dir' and (event['user_id'] != user['id']):
        conn.close()
        flash("Suppression interdite !", "danger")
        return redirect(url_for('evenements'))

    try:
        # Suppression de l'événement
        conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
        conn.commit()
        flash("Événement supprimé avec succès.", "success")
    except Exception as e:
        flash(f"Erreur lors de la suppression de l'événement : {e}", "danger")

    conn.close()
    return redirect(url_for('evenements'))
@app.route('/event/<int:event_id>/reporter', methods=['POST'])
def reporter_event(event_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    event = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()

    # Vérifier si l'événement existe
    if not event:
        flash("Événement non trouvé.", "danger")
        conn.close()
        return redirect(url_for('evenements'))

    # Reporter la date de l'événement au lendemain
    try:
        # Assurez-vous que l'espace dans la date est remplacé par un 'T'
        event_start = event['start'].replace(' ', 'T')  # Remplace l'espace par un 'T' pour correspondre au format attendu "%Y-%m-%dT%H:%M"
        
        # Utiliser strptime pour analyser la date au format correct
        start_datetime = datetime.strptime(event_start, "%Y-%m-%dT%H:%M")  # Assurez-vous que la date est bien au format "%Y-%m-%dT%H:%M"
        
        # Ajouter un jour à la date actuelle
        new_start_datetime = start_datetime + timedelta(days=1)  # Ajouter un jour
        
        # Formater la nouvelle date
        new_start_str = new_start_datetime.strftime("%Y-%m-%dT%H:%M")  # Utilisez le format "%Y-%m-%dT%H:%M" pour la base de données

        # Mettre à jour la date de l'événement dans la base de données
        conn.execute("UPDATE events SET start = ? WHERE id = ?", (new_start_str, event_id))
        conn.commit()

        flash("Tâche reportée.", "success")
    except Exception as e:
        flash(f"Erreur lors du report de la tâche : {str(e)}", "danger")

    conn.close()
    return redirect(url_for('tache_detail', event_id=event_id))
@app.route('/vider_historique', methods=['POST'])
def vider_historique():
    if 'user' not in session or session['user'] != 'Dir':
        flash("Accès refusé. Vous devez être le directeur pour effectuer cette action.", "danger")
        return redirect(url_for('historique_taches'))

    conn = get_db_connection()
    
    try:
        # Suppression des logs d'événements
        conn.execute("DELETE FROM event_logs")
        conn.commit()
        flash("L'historique des tâches a été vidé avec succès.", "success")
    except Exception as e:
        flash(f"Erreur lors de la suppression de l'historique : {e}", "danger")
    
    conn.close()
    return redirect(url_for('historique_taches'))
@app.route('/tache/<int:event_id>')
def tache_detail(event_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    # Récupérer l'événement spécifique par ID
    event = conn.execute(
        """SELECT events.*, users.username 
           FROM events 
           LEFT JOIN users ON events.user_id = users.id
           WHERE events.id = ?""", 
        (event_id,)
    ).fetchone()

    # Vérifier si l'événement existe
    if event is None:
        flash("Tâche non trouvée.", "danger")
        return redirect(url_for('evenements'))

    # Récupérer les utilisateurs affectés à cette tâche
    event_users = conn.execute(
        """SELECT users.username 
           FROM event_assignees 
           JOIN users ON event_assignees.user_id = users.id
           WHERE event_assignees.event_id = ?""", 
        (event_id,)
    ).fetchall()

    conn.close()

    # Afficher la page avec les détails de la tâche
    return render_template(
        'tache_detail.html',  # Crée ce template pour afficher les détails
        event=event,
        users=[user['username'] for user in event_users]
    )
@app.route('/vider_taches_affectees', methods=['POST'])
def vider_taches_affectees():
    if 'user' not in session or session['user'] != 'Dir':
        flash("Accès refusé. Vous devez être le directeur pour effectuer cette action.", "danger")
        return redirect(url_for('evenements'))

    conn = get_db_connection()

    try:
        # Supprimer uniquement les tâches affectées à des utilisateurs
        conn.execute("""
            DELETE FROM events 
            WHERE id IN (SELECT event_id FROM event_assignees)
        """)
        conn.commit()
        flash("Toutes les tâches affectées ont été supprimées avec succès.", "success")
    except Exception as e:
        flash(f"Erreur lors de la suppression des tâches affectées : {str(e)}", "danger")
    
    conn.close()
    return redirect(url_for('evenements'))

@app.route('/vider_taches', methods=['POST'])
def vider_taches():
    if 'user' not in session or session['user'] != 'Dir':
        flash("Accès refusé. Vous devez être le directeur pour effectuer cette action.", "danger")
        return redirect(url_for('evenements'))

    conn = get_db_connection()

    try:
        # Suppression des tâches qui ne sont pas affectées à des utilisateurs
        conn.execute("""
            DELETE FROM events 
            WHERE id NOT IN (SELECT event_id FROM event_assignees)
        """)
        conn.commit()
        flash("Toutes les tâches non affectées ont été supprimées avec succès.", "success")
    except Exception as e:
        flash(f"Erreur lors de la suppression des tâches : {str(e)}", "danger")
    
    conn.close()
    return redirect(url_for('evenements'))

@app.route('/vider_evenements', methods=['POST'])
def vider_evenements():
    if 'user' not in session:
        return jsonify({'error': 'Non autorisé'}), 403

    try:
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (session['user'],)).fetchone()

        if user['username'] == 'Dir':
            # Supprimer toutes les tâches affectées à des utilisateurs
            conn.execute("""
                DELETE FROM events 
                WHERE id IN (SELECT event_id FROM event_assignees)
            """)
        else:
            # Supprimer uniquement les tâches affectées à cet utilisateur
            user_id = user['id']
            conn.execute("""
                DELETE FROM events 
                WHERE id IN (SELECT event_id FROM event_assignees WHERE user_id = ?)
            """, (user_id,))

        conn.commit()
        conn.close()
        return jsonify({'success': True})

    except Exception as e:
        conn.close()
        print(f"Erreur lors de la suppression : {repr(e)}")
        return jsonify({'error': f"Erreur lors de la suppression : {repr(e)}"}), 500
@app.route('/liste_utilisateurs')
def liste_utilisateurs():
    if 'user' not in session or session['user'] != 'Dir':
        flash("Accès refusé.", "danger")
        return redirect(url_for('login'))

    conn = get_db_connection()
    utilisateurs = conn.execute('SELECT * FROM users').fetchall()
    conn.close()

    # Vérifier si les utilisateurs sont correctement récupérés
    print(utilisateurs)  # Cela permet de vérifier la structure des données récupérées

    return render_template('liste_utilisateurs.html', utilisateurs=utilisateurs)



@app.route('/')
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('evenements'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        
        try:
            user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        except Exception as e:
            flash(f"Erreur de connexion à la base de données : {str(e)}", "danger")
            conn.close()
            return render_template('login.html')

        conn.close()
        
        if user:
            # Vérifier si la clé 'is_blocked' existe avant d'y accéder
            if 'is_blocked' in user and user['is_blocked'] == 1:
                flash("Votre compte est bloqué. Contactez un administrateur.", "danger")
                return render_template('login.html')

            # Vérification du mot de passe
            if check_password_hash(user['password'], password):
                session['user'] = user['username']
                next_page = request.args.get('next', '/evenements')
                return redirect(next_page)
            else:
                flash("Nom d'utilisateur ou mot de passe incorrect", "danger")
        else:
            flash("Nom d'utilisateur ou mot de passe incorrect", "danger")
    
    return render_template('login.html')



@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

from datetime import datetime, timedelta

@app.route('/ajouter', methods=['GET', 'POST'])
def ajouter_evenement():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    users = conn.execute("SELECT id, username, role FROM users").fetchall()

    if request.method == 'POST':
        # Récupérer les données du formulaire
        title = request.form.get('event', '').strip()
        description = request.form.get('description', '').strip() or None
        date = request.form.get('date', '').strip()
        time = request.form.get('time', '').strip()

        statut = request.form.get('statut') or 'à faire'
        projet = request.form.get('projet', '').strip() or None
        priorite = request.form.get('priorite') or 'Moyenne'
        recurrence_annee = request.form.get('recurrence_annee')

        # Vérification minimale obligatoire
        if not title or not date or not time:
            flash("Le titre, la date et l'heure sont obligatoires.", "danger")
            return render_template('ajouter_evenement.html', users=users)

        # Gestion de l'attachement
        file = request.files.get('attachment')
        filename = None
        if file and file.filename:
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
            else:
                flash("Format de fichier non autorisé.", "danger")
                return render_template('ajouter_evenement.html', users=users)

        # Récupérer l'utilisateur connecté
        user = conn.execute("SELECT * FROM users WHERE username = ?", (session['user'],)).fetchone()
        if not user:
            flash("Erreur : utilisateur non trouvé ou session expirée. Veuillez vous reconnecter.", "danger")
            conn.close()
            return redirect(url_for('login'))

        # Assigner la classe (pôle) par défaut en fonction de l'utilisateur
        if user['username'] == 'Dir':
            classe = 'Direction'  # L'admin est affecté au pôle Direction
        elif user['role'] == 'Pôle Compta':
            classe = 'Pôle Compta'
        elif user['role'] == 'Pôle Social':
            classe = 'Pôle Social'
        elif user['role'] == 'Pôle juridique':
            classe = 'Pôle juridique'
        elif user['role'] == 'Pôle Communication':
            classe = 'Pôle Communication'
        else:
            classe = 'Assistance'  # Par défaut, tous les autres sont affectés à Assistance

        # Si c'est une tâche récurrente, on crée des événements pour toute l'année
        try:
            if session['user'] == 'Dir' and recurrence_annee:
                date_start = datetime.strptime(date, "%Y-%m-%d")
                year = date_start.year
                day = date_start.day
                for month in range(date_start.month, 13):
                    try:
                        date_evt = date_start.replace(year=year, month=month, day=day)
                    except ValueError:
                        continue
                    if date_evt.weekday() == 6:  # Si c'est un dimanche, on déplace au lundi
                        date_evt += timedelta(days=1)
                    start_datetime = f"{date_evt.date()} {time}"
                    cur = conn.execute(
                        "INSERT INTO events (title, description, start, classe, user_id, statut, projet, priorite, attachment) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (title, description, start_datetime, classe, user['id'], statut, projet, priorite, filename)
                    )
                    event_id = cur.lastrowid
                    conn.execute(
                        "INSERT INTO event_logs (event_id, action, user_id, details) VALUES (?, ?, ?, ?)",
                        (event_id, "création", user['id'], f"Tâche récurrente créée: {title}")
                    )
                conn.commit()
                flash("✅ Les tâches récurrentes ont été ajoutées pour toute l'année.", "success")
            else:
                start_datetime = f"{date} {time}"
                cur = conn.execute(
                    "INSERT INTO events (title, description, start, classe, user_id, statut, projet, priorite, attachment) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (title, description, start_datetime, classe, user['id'], statut, projet, priorite, filename)
                )
                event_id = cur.lastrowid
                conn.execute(
                    "INSERT INTO event_logs (event_id, action, user_id, details) VALUES (?, ?, ?, ?)",
                    (event_id, "création", user['id'], f"Tâche créée: {title}")
                )
                conn.commit()
                flash('✅ La tâche a été ajoutée avec succès.', 'success')
        except Exception as e:
            flash(f"Erreur lors de l’ajout : {e}", "danger")
            conn.close()
            return render_template('ajouter_evenement.html', users=users)

        conn.close()
        return redirect(url_for('ajouter_evenement'))

    return render_template('ajouter_evenement.html', users=users)
    

@app.route('/affecter_tache', methods=['GET', 'POST'])
def affecter_tache():
    if 'user' not in session or session['user'] != 'Dir':
        flash("Accès réservé à l'administrateur.", "danger")
        return redirect(url_for('login'))

    conn = get_db_connection()

    if request.method == 'POST':
        task_title = request.form['task_title']
        task_description = request.form['task_description']
        task_pole = request.form['task_pole']
        user_ids = request.form.getlist('user_ids')  # Liste des utilisateurs sélectionnés
        
        task_date = request.form['task_date']  # Récupérer la date
        task_time = request.form['task_time']  # Récupérer l'heure
        
        # Combiner la date et l'heure pour créer une valeur pour la colonne 'start'
        start_datetime = f"{task_date} {task_time}"
        
        # Vérifier si la tâche doit être répétée
        repeat_task = 'repeatTask' in request.form

        if repeat_task:
            try:
                # Convertir la date en datetime
                base_date = datetime.strptime(task_date, "%Y-%m-%d")
                # Extraire l'heure et les minutes
                hour, minute = map(int, task_time.split(":"))
                
                year = base_date.year

                for month in range(base_date.month, 13):  # De la date actuelle jusqu'à décembre
                    # Calculer la date de début pour chaque mois
                    day = base_date.day
                    try:
                        event_date = base_date.replace(year=year, month=month, day=day)
                    except ValueError:  # Si le jour dépasse le nombre de jours du mois, on le met au dernier jour
                        event_date = datetime(year, month, 1) + timedelta(days=32)  # Prendre le 1er jour du mois suivant et reculer d'un jour
                        event_date = event_date.replace(day=1) - timedelta(days=1)

                    # Si la tâche tombe un samedi ou dimanche, déplacer au lundi
                    if event_date.weekday() == 5:  # Samedi
                        event_date += timedelta(days=2)  # Ajouter 2 jours pour lundi
                    elif event_date.weekday() == 6:  # Dimanche
                        event_date += timedelta(days=1)  # Ajouter 1 jour pour lundi

                    # Conserver l'heure de la tâche et créer l'événement pour ce mois
                    event_date = event_date.replace(hour=hour, minute=minute)  # Appliquer l'heure à l'événement
                    start_str = event_date.strftime("%Y-%m-%dT%H:%M:%S")

                    # Insérer l'événement dans la base de données et assigner la tâche à chaque utilisateur
                    cursor = conn.execute("""
                        INSERT INTO events (title, description, classe, start) 
                        VALUES (?, ?, ?, ?)
                    """, (task_title, task_description, task_pole, start_str))
                    
                    event_id = cursor.lastrowid  # Récupérer l'ID de l'événement créé

                    for user_id in user_ids:
                        conn.execute("""
                            INSERT INTO event_assignees (event_id, user_id) 
                            VALUES (?, ?)
                        """, (event_id, user_id))

                conn.commit()
                flash("✅ La tâche a été affectée à plusieurs utilisateurs et sera répétée tous les mois.", "success")
            except Exception as e:
                flash(f"Erreur lors de l'affectation des tâches récurrentes : {str(e)}", "danger")
                conn.close()
                return redirect(url_for('affecter_tache'))

        else:
            # Si la tâche n'est pas récurrente, créer un seul événement
            cursor = conn.execute("""
                INSERT INTO events (title, description, classe, start) 
                VALUES (?, ?, ?, ?)
            """, (task_title, task_description, task_pole, start_datetime))
            
            event_id = cursor.lastrowid  # Récupérer l'ID de l'événement créé

            for user_id in user_ids:
                conn.execute("""
                    INSERT INTO event_assignees (event_id, user_id) 
                    VALUES (?, ?)
                """, (event_id, user_id))

            conn.commit()
            flash("✅ La tâche a été affectée avec succès.", "success")

        conn.close()
        return redirect(url_for('evenements'))  # Rediriger vers la liste des événements

    # Récupérer la liste des utilisateurs et des pôles
    users = conn.execute("SELECT * FROM users WHERE role != 'Dir'").fetchall()  # Récupère tous les utilisateurs sauf 'Dir'
    poles = ['Pôle Compta', 'Pôle Social', 'Pôle juridique', 'Pôle Communication', 'Assistance Compta', 'Assistance Paie', 'Assistance Communication','']  # Liste des pôles
    conn.close()

    return render_template('affecter_tache.html', users=users, poles=poles)

@app.route('/get_users_by_pole/<pole>', methods=['GET'])
def get_users_by_pole(pole):
    conn = get_db_connection()
    users = conn.execute("SELECT * FROM users WHERE role = ?", (pole,)).fetchall()
    conn.close()
    
    users_list = [{'id': user['id'], 'username': user['username']} for user in users]
    return jsonify(users_list)

@app.route('/evenements', methods=['GET'])
def evenements():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (session['user'],)).fetchone()

    current_year = datetime.now().year
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    # Récupération des filtres
    filter_date = request.args.get('date', '')
    filter_time = request.args.get('time', '')
    filter_priorite = request.args.get('priorite', '')

    # Si l'utilisateur est un administrateur (Dir), on ne récupère que ses propres tâches ou celles auxquelles il est affecté
    if user['username'] == 'Dir':
        # Administrateur peut voir ses propres événements et ceux auxquels il est assigné
        query = """SELECT events.*, users.username
                   FROM events
                   LEFT JOIN event_assignees ON event_assignees.event_id = events.id
                   LEFT JOIN users ON events.user_id = users.id
                   WHERE (events.user_id = ? OR event_assignees.user_id = ?)
                   AND events.start LIKE ?"""
        params = [user['id'], user['id'], f"{current_year}-%"]
    else:
        # Utilisateur normal : il voit ses propres événements et ceux auxquels il est assigné
        user_id = user['id']
        query = """SELECT events.*, users.username
                   FROM events
                   LEFT JOIN event_assignees ON event_assignees.event_id = events.id
                   LEFT JOIN users ON events.user_id = users.id
                   WHERE (events.user_id = ? OR event_assignees.user_id = ?)
                   AND events.start LIKE ?"""
        params = [user_id, user_id, f"{current_year}-%"]

    # Application des filtres
    if filter_date:
        query += " AND date(events.start) = ?"
        params.append(filter_date)

    if filter_time:
        query += " AND strftime('%H:%M', events.start) = ?"
        params.append(filter_time)

    if filter_priorite:
        query += " AND events.priorite = ?"
        params.append(filter_priorite)

    # Exécution de la requête filtrée
    events = conn.execute(query, tuple(params)).fetchall()

    # Pagination
    total = len(events)
    total_pages = (total + per_page - 1) // per_page
    events = events[offset:offset + per_page]

    event_list = []
    for e in events:
        event_dict = {
            'id': e['id'],
            'title': e['title'],
            'start': e['start'],
            'classe': e['classe'],
            'users': []  # Liste des utilisateurs associés
        }

        # Récupérer les utilisateurs associés à cet événement
        event_users = conn.execute(
            """SELECT users.username 
               FROM event_assignees 
               JOIN users ON event_assignees.user_id = users.id
               WHERE event_assignees.event_id = ?""", 
            (e['id'],)
        ).fetchall()

        event_dict['users'] = [user['username'] for user in event_users]
        
        event_list.append(event_dict)

    conn.close()

    current_date = date.today().isoformat()

    return render_template(
        'evenements_liste.html',
        events=event_list,
        is_Dir=(user['username'] == 'Dir'),
        page=page,
        total_pages=total_pages,
        current_date=current_date,
        filter_date=filter_date,
        filter_time=filter_time,
        filter_priorite=filter_priorite
    )

@app.route('/taches_affectees', methods=['GET'])
def taches_affectees():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (session['user'],)).fetchone()

    current_year = datetime.now().year
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    # Récupérer les filtres
    filter_date = request.args.get('date', '')
    filter_time = request.args.get('time', '')
    filter_pole = request.args.get('pole', '')
    filter_priorite = request.args.get('priorite', '')

    # Si l'utilisateur est 'Dir', récupérer toutes les tâches affectées
    if user['username'] == 'Dir':
        query = """
            SELECT events.*, users.username 
            FROM events 
            LEFT JOIN event_assignees ON event_assignees.event_id = events.id
            LEFT JOIN users ON event_assignees.user_id = users.id
            WHERE event_assignees.user_id IS NOT NULL AND events.start LIKE ?
        """
        params = [f"{current_year}-%"]

    else:
        # Si l'utilisateur n'est pas 'Dir', récupérer uniquement les tâches affectées à cet utilisateur
        user_id = user['id']
        query = """
            SELECT events.*, users.username 
            FROM events 
            LEFT JOIN event_assignees ON event_assignees.event_id = events.id
            LEFT JOIN users ON event_assignees.user_id = users.id
            WHERE event_assignees.user_id = ? AND events.start LIKE ?
        """
        params = [user_id, f"{current_year}-%"]

    # Appliquer les filtres
    if filter_date:
        query += " AND date(events.start) = ?"
        params.append(filter_date)

    if filter_time:
        query += " AND strftime('%H:%M', events.start) = ?"
        params.append(filter_time)

    if filter_pole:
        query += " AND events.classe = ?"
        params.append(filter_pole)

    if filter_priorite:
        query += " AND events.priorite = ?"
        params.append(filter_priorite)

    # Exécution de la requête filtrée
    events = conn.execute(query, tuple(params)).fetchall()

    # Pagination
    total = len(events)
    total_pages = (total + per_page - 1) // per_page
    events = events[offset:offset + per_page]

    event_list = []
    for e in events:
        event_dict = {
            'id': e['id'],
            'title': e['title'],
            'start': e['start'],
            'classe': e['classe'],
            'users': []  # Liste des utilisateurs associés
        }

        # Récupérer les utilisateurs associés à cet événement
        event_users = conn.execute(
            """SELECT users.username 
               FROM event_assignees 
               JOIN users ON event_assignees.user_id = users.id
               WHERE event_assignees.event_id = ?""", 
            (e['id'],)
        ).fetchall()

        # Ajouter les utilisateurs associés à cet événement
        event_dict['users'] = [user['username'] for user in event_users]
        
        event_list.append(event_dict)

    conn.close()  # Fermer la connexion après avoir terminé toutes les requêtes

    current_date = date.today().isoformat()

    return render_template(
        'taches_affectees_liste.html',  # Assurez-vous que ce template existe
        events=event_list,
        is_Dir=(user['username'] == 'Dir'),
        page=page,
        total_pages=total_pages,
        current_date=current_date,
        filter_date=filter_date,
        filter_time=filter_time,
        filter_pole=filter_pole,
        filter_priorite=filter_priorite
    )

@app.route('/export_evenements_excel')
def export_evenements_excel():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (session['user'],)).fetchone()
    current_year = datetime.now().year
    if user['username'] == 'Dir':
        events = conn.execute(
            """SELECT events.*, users.username 
               FROM events 
               LEFT JOIN users ON events.user_id = users.id
               WHERE start LIKE ?""",
            (f"{current_year}-%",)
        ).fetchall()
    else:
        user_id = user['id']
        events = conn.execute(
            "SELECT * FROM events WHERE user_id = ? AND start LIKE ?",
            (user_id, f"{current_year}-%")
        ).fetchall()
    conn.close()
    # Format DataFrame pour export
    if not events:
        return "Aucun événement à exporter", 404
    df = pd.DataFrame(events)
    df.columns = [col[0] for col in events[0].keys()]  # Correction noms de colonnes
    output = pd.ExcelWriter('evenements_export.xlsx', engine='xlsxwriter')
    df.to_excel(output, index=False)
    output.close()
    with open('evenements_export.xlsx', 'rb') as f:
        data = f.read()
    os.remove('evenements_export.xlsx')  # Nettoyage fichier temporaire
    from flask import send_file
    import io
    return send_file(io.BytesIO(data), mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     download_name='evenements.xlsx', as_attachment=True)

@app.route('/delete_event/<int:event_id>', methods=['POST'])
def delete_event(event_id):
    if 'user' not in session:
        return jsonify({"error": "Non autorisé"}), 403

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (session['user'],)).fetchone()
    event = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()

    # Vérification des autorisations
    if user['username'] != 'Dir':
        if not event or event['user_id'] != user['id']:
            conn.close()
            return jsonify({"error": "Suppression interdite"}), 403

    try:
        conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True}), 200
    except Exception as e:
        conn.close()
        return jsonify({"error": f"Erreur lors de la suppression: {e}"}), 500




@app.route('/historique_taches', methods=['GET'])
def historique_taches():
    if 'user' not in session or session['user'] != 'Dir':
        flash("Accès refusé.", "danger")
        return redirect(url_for('login'))

    # Récupérer les paramètres de filtre
    filter_pole = request.args.get('pole', '')
    filter_priorite = request.args.get('priorite', '')
    filter_date = request.args.get('date', '')
    filter_heure = request.args.get('heure', '')

    # Requête de base pour récupérer les logs des événements
    query = """
        SELECT event_logs.*, users.username as action_user, events.classe, events.priorite, events.start
        FROM event_logs
        LEFT JOIN users ON event_logs.user_id = users.id
        LEFT JOIN events ON event_logs.event_id = events.id
        WHERE 1=1
    """
    params = []

    # Appliquer les filtres à la requête
    if filter_pole:
        query += " AND events.classe = ?"
        params.append(filter_pole)
    
    if filter_priorite:
        query += " AND events.priorite = ?"
        params.append(filter_priorite)
    
    if filter_date:
        query += " AND date(events.start) = ?"
        params.append(filter_date)
    
    if filter_heure:
        query += " AND strftime('%H:%M', events.start) = ?"
        params.append(filter_heure)

    # Exécution de la requête filtrée
    conn = get_db_connection()
    logs = conn.execute(query, tuple(params)).fetchall()
    conn.close()

    # Retourner la page avec les logs filtrés et les valeurs des filtres
    return render_template('historique_taches.html', logs=logs, filter_pole=filter_pole, filter_priorite=filter_priorite, filter_date=filter_date, filter_heure=filter_heure)

@app.route('/dashboard_admin', methods=['GET'])
def dashboard_admin():
    conn = get_db_connection()

    # Récupérer les paramètres de filtre
    filter_date = request.args.get('date', '')
    filter_time = request.args.get('time', '')
    filter_pole = request.args.get('pole', '')

    # Requête de base pour récupérer les événements
    query = """SELECT events.*, users.username 
               FROM events 
               LEFT JOIN users ON events.user_id = users.id
               WHERE 1=1"""
    
    params = []

    # Appliquer les filtres
    if filter_date:
        query += " AND date(events.start) = ?"
        params.append(filter_date)
    
    if filter_time:
        query += " AND strftime('%H:%M', events.start) = ?"
        params.append(filter_time)
    
    if filter_pole:
        query += " AND events.classe = ?"
        params.append(filter_pole)

    # Exécuter la requête avec les filtres appliqués
    events = conn.execute(query, tuple(params)).fetchall()

    # Récupérer des statistiques
    users_by_pole = conn.execute("""
        SELECT users.role, users.username, COUNT(events.id) AS task_count
        FROM users
        LEFT JOIN events ON events.user_id = users.id
        GROUP BY users.role, users.username
    """).fetchall()

    statuts_stats = conn.execute("""
        SELECT statut, COUNT(*) as nb
        FROM events
        GROUP BY statut
    """).fetchall()

    conn.close()
    return render_template(
        'dashboard_admin.html',
        users_by_pole=users_by_pole,
        events=events,
        statuts_stats=statuts_stats
    )

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    sort_by = request.args.get('sort_by', 'start')
    order = request.args.get('order', 'desc')
    allowed_sort = {
        "start": "events.start",
        "username": "users.username",
        "projet": "events.projet",
        "priorite": "events.priorite"
    }
    sort_sql = allowed_sort.get(sort_by, "events.start")
    order_sql = "DESC" if order == "desc" else "ASC"

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (session['user'],)).fetchone()

    if user['username'] == 'Dir':
        # Utilisateurs par pôle avec le nombre de tâches créées
        users_by_pole = conn.execute("""
            SELECT users.role, users.username, COUNT(events.id) AS task_count
            FROM users
            LEFT JOIN events ON events.user_id = users.id
            GROUP BY users.role, users.username
        """).fetchall()

        # Statistiques des tâches par statut
        statuts_stats = conn.execute("""
            SELECT statut, COUNT(*) as nb
            FROM events
            GROUP BY statut
        """).fetchall()

        # Récupérer tous les événements avec les informations des utilisateurs
        events = conn.execute(f"""
            SELECT events.*, users.username
            FROM events
            LEFT JOIN users ON events.user_id = users.id
            ORDER BY {sort_sql} {order_sql}
        """).fetchall()

        conn.close()
        return render_template('dashboard_admin.html',
                               users_by_pole=users_by_pole,  # Passer la variable users_by_pole
                               events=events,
                               statuts_stats=statuts_stats)
    else:
        user_id = user['id']
        events = conn.execute("SELECT * FROM events WHERE user_id = ?", (user_id,)).fetchall()
        conn.close()
        return render_template('dashboard.html', events=events)


@app.route('/export_taches_affectees', methods=['GET'])
def export_taches_affectees():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (session['user'],)).fetchone()

    current_year = datetime.now().year
    # Récupérer uniquement les tâches affectées à des utilisateurs
    events = conn.execute("""
        SELECT events.*, users.username 
        FROM events
        LEFT JOIN event_assignees ON event_assignees.event_id = events.id
        LEFT JOIN users ON event_assignees.user_id = users.id
        WHERE event_assignees.user_id IS NOT NULL 
        AND events.start LIKE ?
    """, (f"{current_year}-%",)).fetchall()

    conn.close()

    if not events:
        return "Aucune tâche affectée à exporter", 404

    # Format DataFrame pour export
    df = pd.DataFrame(events)
    df.columns = [col[0] for col in events[0].keys()]  # Correction des noms de colonnes
    output = pd.ExcelWriter('taches_affectees_export.xlsx', engine='xlsxwriter')
    df.to_excel(output, index=False)
    output.close()

    with open('taches_affectees_export.xlsx', 'rb') as f:
        data = f.read()

    os.remove('taches_affectees_export.xlsx')  # Nettoyage fichier temporaire

    from flask import send_file
    import io
    return send_file(io.BytesIO(data), mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     download_name='taches_affectees.xlsx', as_attachment=True)

@app.route('/export_taches_personnelles', methods=['GET'])
def export_taches_personnelles():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (session['user'],)).fetchone()

    current_year = datetime.now().year
    # Récupérer les tâches créées ou affectées à l'utilisateur connecté
    events = conn.execute("""
        SELECT events.*, users.username 
        FROM events
        LEFT JOIN event_assignees ON event_assignees.event_id = events.id
        LEFT JOIN users ON event_assignees.user_id = users.id
        WHERE (events.user_id = ? OR event_assignees.user_id = ?) 
        AND events.start LIKE ?
    """, (user['id'], user['id'], f"{current_year}-%")).fetchall()

    conn.close()

    if not events:
        return "Aucune tâche personnelle à exporter", 404

    # Format DataFrame pour export
    df = pd.DataFrame(events)
    df.columns = [col[0] for col in events[0].keys()]  # Correction des noms de colonnes
    output = pd.ExcelWriter('taches_personnelles_export.xlsx', engine='xlsxwriter')
    df.to_excel(output, index=False)
    output.close()

    with open('taches_personnelles_export.xlsx', 'rb') as f:
        data = f.read()

    os.remove('taches_personnelles_export.xlsx')  # Nettoyage fichier temporaire

    from flask import send_file
    import io
    return send_file(io.BytesIO(data), mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     download_name='taches_personnelles.xlsx', as_attachment=True)

@app.route('/calendar_view')
def calendar_view():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('calendar.html')
@app.route('/valider_event/<int:event_id>', methods=['POST'])
def valider_event(event_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    # Vérifier si l'utilisateur est autorisé à valider cette tâche (ex : seulement l'admin ou la personne assignée)
    event = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
    
    if event:
        # Mise à jour du statut de la tâche
        conn.execute("UPDATE events SET statut = 'validé' WHERE id = ?", (event_id,))
        conn.commit()
        flash("Tâche validée avec succès", "success")
    else:
        flash("Erreur : tâche non trouvée", "danger")
    
    conn.close()
    return redirect(url_for('tache_detail', event_id=event_id))  # Rediriger vers les détails de la tâche après validation



@app.route('/modifier_event/<int:event_id>', methods=['GET', 'POST'])
def modifier_event(event_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (session['user'],)).fetchone()
    event = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()

    if user['username'] != 'Dir':
        if not event or event['user_id'] != user['id']:
            conn.close()
            flash("Modification interdite !", "danger")
            return redirect(url_for('evenements'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        start = request.form['start']
        classe = request.form['classe']
        statut = request.form.get('statut', 'à faire')
        projet = request.form.get('projet', '')
        priorite = request.form.get('priorite', 'Moyenne')

        file = request.files.get('attachment')
        filename = event['attachment'] if event and 'attachment' in event.keys() else None
        if file and file.filename:
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
            else:
                flash("Format de fichier non autorisé.", "danger")
                conn.close()
                return render_template('modifier_evenement.html', event=event)

        try:
            # Mettre à jour l'événement
            conn.execute(
                "UPDATE events SET title = ?, description = ?, start = ?, classe = ?, statut = ?, projet = ?, priorite = ?, attachment = ? WHERE id = ?",
                (title, description, start, classe, statut, projet, priorite, filename, event_id)
            )
            # Log modification
            conn.execute(
                "INSERT INTO event_logs (event_id, action, user_id, details) VALUES (?, ?, ?, ?)",
                (event_id, "modification", user['id'], f"Tâche modifiée: {title}")
            )
            conn.commit()
            flash("Événement modifié avec succès.", "success")
        except Exception as e:
            flash(f"Erreur lors de la modification : {e}", "danger")
            conn.close()
            return render_template('modifier_evenement.html', event=event)

        conn.close()
        return redirect(url_for('evenements'))

    conn.close()
    return render_template('modifier_evenement.html', event=event)




# ----------- RECUPERATION DE MOT DE PASSE DIRECTE (SANS LIEN EMAIL) ------------

@app.route('/reset_password/<int:user_id>', methods=['POST'])
def reset_password(user_id):
    if 'user' not in session or session['user'] != 'Dir':
        return jsonify({'success': False, 'error': "Accès refusé"}), 403

    data = request.get_json()
    new_password = data.get('new_password', '').strip()

    # Vérification que le mot de passe est suffisamment long
    if not new_password or len(new_password) < 5:
        return jsonify({'success': False, 'error': "Mot de passe trop court"}), 400

    hashed_pw = generate_password_hash(new_password)
    conn = get_db_connection()

    try:
        # Vérification si l'utilisateur existe
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            return jsonify({'success': False, 'error': "Utilisateur introuvable"}), 404

        # Mise à jour du mot de passe
        conn.execute("UPDATE users SET password = ? WHERE id = ?", (hashed_pw, user_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/new_password', methods=['POST'])
def new_password():
    email = request.form['email']
    password = request.form['password']
    hashed_password = generate_password_hash(password)
    conn = get_db_connection()
    conn.execute('UPDATE users SET password = ? WHERE email = ?', (hashed_password, email))
    conn.commit()
    conn.close()
    flash('Mot de passe modifié avec succès !', 'success')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user' not in session or session['user'] != 'Dir':
        flash("Accès réservé à l'administrateur.", "danger")
        return redirect(url_for('login'))
    
    # Liste des pôles à afficher
    poles = [
        "Pôle Compta", "Pôle Social", "Pôle juridique", 
        "Pôle Communication", "Direction", 
        "Assistance Compta", "Assistance Paie", 
        "Assistance juridique", "Assistance Communication"
    ]
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        role = request.form['role']  # Récupère le pôle sélectionné

        if password != confirm_password:
            flash("Les mots de passe ne correspondent pas", "danger")
            return redirect(url_for('register'))
        
        try:
            conn = get_db_connection()
            
            # Vérification de l'unicité du nom d'utilisateur et de l'email
            user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            if user:
                flash("Le nom d'utilisateur est déjà utilisé", "danger")
                conn.close()
                return redirect(url_for('register'))
            
            email_used = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            if email_used:
                flash("Cet email est déjà utilisé", "danger")
                conn.close()
                return redirect(url_for('register'))
            
            # Hachage du mot de passe
            hashed_password = generate_password_hash(password)
            
            # Création du nouvel utilisateur
            conn.execute("INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)",
                         (username, hashed_password, email, role))
            conn.commit()
            conn.close()
            flash("Compte créé avec succès ! Vous pouvez maintenant vous connecter.", "success")
            return redirect(url_for('login'))
        
        except Exception as e:
            flash(f"Erreur lors de la création du compte : {str(e)}", "danger")
            return redirect(url_for('register'))

    return render_template('register.html', poles=poles)


@app.route('/profil', methods=['GET', 'POST'])
def profil():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (session['user'],)).fetchone()

    if request.method == 'POST':
        # Vérification si 'username' est présent dans la requête
        if 'username' not in request.form:
            flash("Erreur : nom d'utilisateur manquant.", "danger")
            return redirect(url_for('profil'))

        # Récupérer les données envoyées dans le formulaire
        username = request.form['username']  # Cela ne devrait plus lever l'erreur si la clé existe
        email = request.form['email']
        role = request.form['role']

        # Mise à jour de l'utilisateur dans la base de données
        conn.execute("UPDATE users SET email = ?, username = ?, role = ? WHERE id = ?", (email, username, role, user['id']))
        conn.commit()
        flash("Profil mis à jour avec succès.", "success")
        return redirect(url_for('profil'))

    conn.close()
    return render_template('profil.html', user=user)
@app.route('/projets/ajouter', methods=['GET', 'POST'])
def ajouter_projet():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (session['user'],)).fetchone()
    if request.method == 'POST':
        name = request.form['name'].strip()
        description = request.form['description']
        echeance = request.form['echeance']
        is_collaborative = int(request.form.get('is_collaborative', 0))
        file = request.files.get('piece_jointe')
        filename = None

        # ----- Validation du nom -----
        if len(name) < 3:
            flash("Le nom du projet doit comporter au moins 3 caractères.", "danger")
            conn.close()
            return render_template('ajouter_projet.html')

        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
        cur = conn.execute(
            "INSERT INTO projects (name, description, owner_id, is_collaborative, echeance, attachment) VALUES (?, ?, ?, ?, ?, ?)",
            (name, description, user['id'], is_collaborative, echeance, filename)
        )
        project_id = cur.lastrowid
        conn.execute(
            "INSERT INTO project_members (project_id, user_id) VALUES (?, ?)", (project_id, user['id'])
        )
        conn.commit()
        flash("Projet créé avec succès !", "success")
        conn.close()
        return redirect(url_for('liste_projets'))
    conn.close()
    return render_template('ajouter_projet.html')

@app.route('/projets')
def liste_projets():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (session['user'],)).fetchone()
    projets = conn.execute("""
        SELECT p.*
        FROM projects p
        JOIN project_members pm ON pm.project_id = p.id
        WHERE pm.user_id = ?
    """, (user['id'],)).fetchall()

    projets_list = []
    for p in projets:
        # Récupère les membres pour chaque projet collaboratif
        membres = conn.execute("""
            SELECT u.username
            FROM project_members pm
            JOIN users u ON u.id = pm.user_id
            WHERE pm.project_id = ?
        """, (p['id'],)).fetchall()
        p = dict(p)
        p['members'] = membres
        projets_list.append(p)
    conn.close()
    return render_template('liste_projets.html', projets=projets_list)
@app.route('/reporter_evenements', methods=['POST'])
def reporter_evenements():
    if 'user' not in session or session['user'] != 'Dir':
        flash("Action réservée à l'administrateur.", "danger")
        return redirect(url_for('evenements'))

    conn = get_db_connection()

    # Récupérer les IDs des événements envoyés par le frontend
    data = request.get_json()
    event_ids = data.get('event_ids', [])
    
    if not event_ids:
        flash("Aucune tâche sélectionnée pour le report.", "warning")
        return redirect(url_for('evenements'))

    nb = 0
    new_start = None  # Initialisation de la nouvelle date
    for event_id in event_ids:
        event = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
        if event and event['statut'] != 'validé':
            start_str = event['start']
            start_dt = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")  # Format de date
            new_start = (start_dt + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")  # Ajouter 1 jour
            conn.execute(
                "UPDATE events SET start = ? WHERE id = ?",
                (new_start, event['id'])
            )
            nb += 1

    conn.commit()
    conn.close()
    
    # Retourner la nouvelle date pour l'affichage
    return jsonify({"success": True, "new_date": new_start}), 200



@app.route('/projets/supprimer/<int:project_id>', methods=['POST'])
def supprimer_projet(project_id):
    if 'user' not in session:
        return jsonify({"error": "Non autorisé"}), 403
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (session['user'],)).fetchone()
    projet = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    est_membre = conn.execute("SELECT * FROM project_members WHERE project_id = ? AND user_id = ?", (project_id, user['id'])).fetchone()
    if not projet or not est_membre:
        conn.close()
        flash("Suppression interdite !", "danger")
        return redirect(url_for('liste_projets'))
    # Supprime les membres du projet
    conn.execute("DELETE FROM project_members WHERE project_id = ?", (project_id,))
    # Supprime les éventuels événements liés à ce projet (si tu as la colonne project_id dans events)
    # conn.execute("DELETE FROM events WHERE project_id = ?", (project_id,))
    # Supprime le projet
    conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()
    flash("Projet supprimé avec succès.", "success")
    return redirect(url_for('liste_projets'))
def reporter_evenements_non_valides():
    conn = get_db_connection()
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    # On ne reporte que les tâches dont la date est passée (avant aujourd’hui) et qui ne sont pas validées
    events = conn.execute("""
        SELECT id, start, statut
        FROM events
        WHERE date(start) <= ? AND (statut IS NULL OR statut != 'validé')
    """, (today.strftime("%Y-%m-%d"),)).fetchall()
    for event in events:
        try:
            # On reporte d’un jour la date de start
            old_start = datetime.strptime(event['start'], "%Y-%m-%d %H:%M")
            new_start = old_start + timedelta(days=1)
            new_start_str = new_start.strftime("%Y-%m-%d %H:%M")
            conn.execute("UPDATE events SET start = ? WHERE id = ?", (new_start_str, event['id']))
        except Exception as e:
            print("Erreur report event:", e)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    app.run(debug=True, port=5005
    )
