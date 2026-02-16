import sqlite3


def crea_utente(conn: sqlite3.Connection, nome: str, email: str, password_hash: str) -> int:
    """Inserisce un utente e ritorna l'id creato."""
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO utenti (nome, email, password_hash)
        VALUES (?, ?, ?)
        """,
        (nome, email, password_hash),
    )
    conn.commit()
    return cursor.lastrowid


def crea_dieta(conn: sqlite3.Connection, utente_id: int, nome_dieta: str) -> int:
    """Crea una nuova dieta per un utente e ritorna l'id della dieta."""
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO diete (utente_id, nome_dieta)
        VALUES (?, ?)
        """,
        (utente_id, nome_dieta),
    )
    conn.commit()
    return cursor.lastrowid


def ottieni_diete_utente(conn: sqlite3.Connection, utente_id: int) -> list[dict]:
    """Ritorna tutte le diete associate a un utente come lista di dizionari."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, utente_id, nome_dieta, data_creazione
        FROM diete
        WHERE utente_id = ?
        ORDER BY data_creazione DESC, id DESC
        """,
        (utente_id,),
    )
    rows = cursor.fetchall()

    return [
        {
            "id": row[0],
            "utente_id": row[1],
            "nome_dieta": row[2],
            "data_creazione": row[3],
        }
        for row in rows
    ]


def aggiungi_pasto(
    conn: sqlite3.Connection,
    dieta_id: int,
    giorno_settimana: int,
    nome_pasto: str,
    ordine: int,
) -> int:
    """Inserisce un pasto in un giorno specifico e ritorna il pasto_id."""
    if giorno_settimana < 1 or giorno_settimana > 7:
        raise ValueError("giorno_settimana deve essere compreso tra 1 e 7")

    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO pasti (dieta_id, giorno_settimana, nome_pasto, ordine)
        VALUES (?, ?, ?, ?)
        """,
        (dieta_id, giorno_settimana, nome_pasto, ordine),
    )
    conn.commit()
    return cursor.lastrowid


def aggiungi_alimento_a_pasto(
    conn: sqlite3.Connection,
    pasto_id: int,
    codice_alimento: str,
    quantita_grammi: int,
) -> None:
    """Associa un alimento a un pasto."""
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO dettaglio_pasti (pasto_id, codice_alimento, quantita_grammi)
        VALUES (?, ?, ?)
        """,
        (pasto_id, codice_alimento, quantita_grammi),
    )
    conn.commit()


def copia_giorno_dieta(
    conn: sqlite3.Connection,
    dieta_id: int,
    giorno_origine: int,
    giorno_destinazione: int,
) -> None:
    """
    Duplica i pasti di un giorno di una dieta e i relativi dettaglio_pasti
    assegnandoli al giorno di destinazione.
    """
    if giorno_origine < 1 or giorno_origine > 7:
        raise ValueError("giorno_origine deve essere compreso tra 1 e 7")
    if giorno_destinazione < 1 or giorno_destinazione > 7:
        raise ValueError("giorno_destinazione deve essere compreso tra 1 e 7")

    cursor = conn.cursor()
    cursor.execute("BEGIN")
    try:
        cursor.execute(
            """
            SELECT id, nome_pasto, ordine
            FROM pasti
            WHERE dieta_id = ? AND giorno_settimana = ?
            ORDER BY ordine ASC, id ASC
            """,
            (dieta_id, giorno_origine),
        )
        pasti_origine = cursor.fetchall()

        for pasto_id_origine, nome_pasto, ordine in pasti_origine:
            cursor.execute(
                """
                INSERT INTO pasti (dieta_id, giorno_settimana, nome_pasto, ordine)
                VALUES (?, ?, ?, ?)
                """,
                (dieta_id, giorno_destinazione, nome_pasto, ordine),
            )
            nuovo_pasto_id = cursor.lastrowid

            cursor.execute(
                """
                SELECT codice_alimento, quantita_grammi
                FROM dettaglio_pasti
                WHERE pasto_id = ?
                """,
                (pasto_id_origine,),
            )
            dettagli = cursor.fetchall()

            for codice_alimento, quantita_grammi in dettagli:
                cursor.execute(
                    """
                    INSERT INTO dettaglio_pasti (pasto_id, codice_alimento, quantita_grammi)
                    VALUES (?, ?, ?)
                    """,
                    (nuovo_pasto_id, codice_alimento, quantita_grammi),
                )

        conn.commit()
    except Exception:
        conn.rollback()
        raise


def cerca_alimenti(conn: sqlite3.Connection, keyword: str) -> list[dict]:
    """
    Cerca alimenti per parola chiave su nome o categoria (case-insensitive).
    Ritorna al massimo 20 risultati.
    """
    cursor = conn.cursor()
    pattern = f"%{keyword.strip()}%"
    cursor.execute(
        """
        SELECT codice_alimento, nome, categoria
        FROM alimenti
        WHERE nome LIKE ? COLLATE NOCASE
           OR categoria LIKE ? COLLATE NOCASE
        ORDER BY nome ASC
        LIMIT 20
        """,
        (pattern, pattern),
    )
    rows = cursor.fetchall()

    return [
        {
            "codice_alimento": row[0],
            "nome": row[1],
            "categoria": row[2],
        }
        for row in rows
    ]
