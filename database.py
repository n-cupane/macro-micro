import sqlite3
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def setup_database(db_name='nutrizione.db'):
    """Crea le tabelle se non esistono e ritorna la connessione."""
    conn = sqlite3.connect(db_name)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alimenti (
            codice_alimento TEXT PRIMARY KEY,
            nome TEXT,
            categoria TEXT,
            nome_scientifico TEXT,
            english_name TEXT,
            parte_edibile TEXT,
            porzione TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS valori_nutrizionali (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codice_alimento TEXT,
            macrocategoria TEXT,
            nutriente TEXT,
            unita_misura TEXT,
            valore_100g TEXT,
            valore_porzione TEXT,
            FOREIGN KEY (codice_alimento) REFERENCES alimenti (codice_alimento)
        )
        ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS utenti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            email TEXT UNIQUE,
            password_hash TEXT,
            sesso TEXT NOT NULL DEFAULT 'M',
            ruolo TEXT DEFAULT 'user'
        )
    ''')

    # Migrazione semplice per DB gia esistenti: aggiunge la colonna ruolo se manca.
    cursor.execute("PRAGMA table_info(utenti)")
    utenti_columns = {row[1] for row in cursor.fetchall()}
    if "ruolo" not in utenti_columns:
        cursor.execute("ALTER TABLE utenti ADD COLUMN ruolo TEXT DEFAULT 'user'")
    if "sesso" not in utenti_columns:
        cursor.execute("ALTER TABLE utenti ADD COLUMN sesso TEXT NOT NULL DEFAULT 'M'")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS diete (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            utente_id INTEGER,
            nome_dieta TEXT,
            data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (utente_id) REFERENCES utenti (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pasti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dieta_id INTEGER,
            giorno_settimana INTEGER CHECK(giorno_settimana BETWEEN 1 AND 7),
            nome_pasto TEXT,
            ordine INTEGER,
            FOREIGN KEY (dieta_id) REFERENCES diete (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dettaglio_pasti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pasto_id INTEGER,
            codice_alimento TEXT,
            quantita_grammi INTEGER,
            FOREIGN KEY (pasto_id) REFERENCES pasti (id),
            FOREIGN KEY (codice_alimento) REFERENCES alimenti (codice_alimento)
        )
    ''')

    # Se non esistono utenti, crea l'admin di default per il primo accesso.
    cursor.execute("SELECT COUNT(*) FROM utenti")
    utenti_count = cursor.fetchone()[0]
    if utenti_count == 0:
        admin_password_hash = pwd_context.hash("admin123")
        cursor.execute(
            """
            INSERT INTO utenti (nome, email, password_hash, ruolo)
            VALUES (?, ?, ?, ?)
            """,
            ("Admin", "admin@admin.com", admin_password_hash, "admin"),
        )
    conn.commit()
    return conn

def salva_dati(conn, anagrafica, valori):
    """Salva l'anagrafica e i relativi valori nutrizionali nel DB."""
    cursor = conn.cursor()

    # Inserisce l'alimento (sovrascrive se esiste già grazie a REPLACE)
    cursor.execute('''
        INSERT OR REPLACE INTO alimenti 
        (codice_alimento, nome, categoria, nome_scientifico, english_name, parte_edibile, porzione)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        anagrafica['codice_alimento'], anagrafica['nome'], anagrafica['categoria'],
        anagrafica['nome_scientifico'], anagrafica['english_name'],
        anagrafica['parte_edibile'], anagrafica['porzione']
    ))

    # Elimina vecchi valori nutrizionali per questo alimento prima di inserire i nuovi
    # (utile se fai girare lo script più volte per aggiornare i dati)
    cursor.execute('DELETE FROM valori_nutrizionali WHERE codice_alimento = ?', (anagrafica['codice_alimento'],))

    # Inserisce i nuovi valori nutrizionali
    for v in valori:
        cursor.execute('''
            INSERT INTO valori_nutrizionali
            (codice_alimento, macrocategoria, nutriente, unita_misura, valore_100g, valore_porzione)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
        anagrafica['codice_alimento'], v['macrocategoria'], v['nutriente'],
        v['unita_misura'], v['valore_100g'], v['valore_porzione']
        ))

    conn.commit()
