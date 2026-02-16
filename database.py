import sqlite3

def setup_database(db_name='nutrizione.db'):
    """Crea le tabelle se non esistono e ritorna la connessione."""
    conn = sqlite3.connect(db_name)
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