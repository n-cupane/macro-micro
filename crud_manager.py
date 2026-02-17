import sqlite3

from schemas import DietaCompletaCreate


def _to_float_value(value: object) -> float:
    """Converte un valore nutrizionale testuale in float gestendo null e 'tr'."""
    if value is None:
        return 0.0
    raw = str(value).strip().lower().replace(",", ".")
    if not raw or raw == "tr":
        return 0.0
    try:
        return float(raw)
    except ValueError:
        return 0.0


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


def crea_dieta_completa(
    conn: sqlite3.Connection,
    utente_id: int,
    dati_dieta: DietaCompletaCreate,
) -> int:
    """Crea dieta, pasti e alimenti in transazione singola."""
    cursor = conn.cursor()
    cursor.execute("BEGIN")
    try:
        cursor.execute(
            """
            INSERT INTO diete (utente_id, nome_dieta)
            VALUES (?, ?)
            """,
            (utente_id, dati_dieta.nome),
        )
        dieta_id = cursor.lastrowid

        for index, pasto in enumerate(dati_dieta.pasti, start=1):
            ordine = int(pasto.ordine or 0) if pasto.ordine is not None else 0
            if ordine <= 0:
                ordine = index
            cursor.execute(
                """
                INSERT INTO pasti (dieta_id, giorno_settimana, nome_pasto, ordine)
                VALUES (?, ?, ?, ?)
                """,
                (dieta_id, pasto.giorno_settimana, pasto.nome_pasto, ordine),
            )
            pasto_id = cursor.lastrowid

            for alimento in pasto.alimenti:
                cursor.execute(
                    """
                    INSERT INTO dettaglio_pasti (pasto_id, codice_alimento, quantita_grammi)
                    VALUES (?, ?, ?)
                    """,
                    (pasto_id, alimento.codice_alimento, alimento.grammi),
                )

        conn.commit()
        return dieta_id
    except Exception:
        conn.rollback()
        raise


def aggiorna_dieta_completa(
    conn: sqlite3.Connection,
    dieta_id: int,
    utente_id: int,
    dati_dieta: DietaCompletaCreate,
) -> bool:
    """Aggiorna una dieta esistente con approccio wipe-and-replace."""
    cursor = conn.cursor()
    cursor.execute("BEGIN")
    try:
        cursor.execute(
            """
            SELECT id
            FROM diete
            WHERE id = ? AND utente_id = ?
            """,
            (dieta_id, utente_id),
        )
        if not cursor.fetchone():
            conn.rollback()
            return False

        cursor.execute(
            """
            UPDATE diete
            SET nome_dieta = ?
            WHERE id = ? AND utente_id = ?
            """,
            (dati_dieta.nome, dieta_id, utente_id),
        )

        cursor.execute(
            """
            DELETE FROM dettaglio_pasti
            WHERE pasto_id IN (
                SELECT p.id
                FROM pasti p
                WHERE p.dieta_id IN (
                    SELECT d.id FROM diete d WHERE d.id = ? AND d.utente_id = ?
                )
            )
            """,
            (dieta_id, utente_id),
        )
        cursor.execute(
            """
            DELETE FROM pasti
            WHERE dieta_id IN (
                SELECT d.id FROM diete d WHERE d.id = ? AND d.utente_id = ?
            )
            """,
            (dieta_id, utente_id),
        )

        for index, pasto in enumerate(dati_dieta.pasti, start=1):
            ordine = int(pasto.ordine or 0) if pasto.ordine is not None else 0
            if ordine <= 0:
                ordine = index
            cursor.execute(
                """
                INSERT INTO pasti (dieta_id, giorno_settimana, nome_pasto, ordine)
                VALUES (?, ?, ?, ?)
                """,
                (dieta_id, pasto.giorno_settimana, pasto.nome_pasto, ordine),
            )
            pasto_id = cursor.lastrowid

            for alimento in pasto.alimenti:
                cursor.execute(
                    """
                    INSERT INTO dettaglio_pasti (pasto_id, codice_alimento, quantita_grammi)
                    VALUES (?, ?, ?)
                    """,
                    (pasto_id, alimento.codice_alimento, alimento.grammi),
                )

        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise


def elimina_dieta(conn: sqlite3.Connection, dieta_id: int, utente_id: int) -> bool:
    """Elimina una dieta (solo se appartiene all'utente) con cleanup dei figli."""
    cursor = conn.cursor()
    cursor.execute("BEGIN")
    try:
        cursor.execute(
            """
            DELETE FROM dettaglio_pasti
            WHERE pasto_id IN (
                SELECT p.id
                FROM pasti p
                WHERE p.dieta_id IN (
                    SELECT d.id FROM diete d WHERE d.id = ? AND d.utente_id = ?
                )
            )
            """,
            (dieta_id, utente_id),
        )
        cursor.execute(
            """
            DELETE FROM pasti
            WHERE dieta_id IN (
                SELECT d.id FROM diete d WHERE d.id = ? AND d.utente_id = ?
            )
            """,
            (dieta_id, utente_id),
        )
        cursor.execute(
            """
            DELETE FROM diete
            WHERE id = ? AND utente_id = ?
            """,
            (dieta_id, utente_id),
        )
        deleted = cursor.rowcount > 0
        conn.commit()
        return deleted
    except Exception:
        conn.rollback()
        raise


def ottieni_dieta_completa(conn: sqlite3.Connection, dieta_id: int, utente_id: int) -> dict | None:
    """
    Ritorna la dieta completa (nome + struttura giorni/pasti/alimenti) se appartiene all'utente.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, nome_dieta
        FROM diete
        WHERE id = ? AND utente_id = ?
        """,
        (dieta_id, utente_id),
    )
    dieta_row = cursor.fetchone()
    if not dieta_row:
        return None

    week_plan = [{"meals": []} for _ in range(7)]

    cursor.execute(
        """
        SELECT id, giorno_settimana, nome_pasto, ordine
        FROM pasti
        WHERE dieta_id = ?
        ORDER BY giorno_settimana ASC, ordine ASC, id ASC
        """,
        (dieta_id,),
    )
    pasti_rows = cursor.fetchall()

    for pasto_id, giorno_settimana, nome_pasto, _ordine in pasti_rows:
        cursor.execute(
            """
            SELECT dp.id, dp.codice_alimento, a.nome, dp.quantita_grammi,
                   MAX(CASE WHEN v.nutriente = 'Energia (kcal)' THEN v.valore_100g END) AS kcal,
                   MAX(CASE WHEN v.nutriente = 'Proteine (g)' THEN v.valore_100g END) AS proteine,
                   MAX(CASE WHEN v.nutriente = 'Carboidrati disponibili (g)' THEN v.valore_100g END) AS carboidrati,
                   MAX(CASE WHEN v.nutriente = 'Lipidi (g)' THEN v.valore_100g END) AS grassi
            FROM dettaglio_pasti dp
            LEFT JOIN alimenti a ON a.codice_alimento = dp.codice_alimento
            LEFT JOIN valori_nutrizionali v ON v.codice_alimento = dp.codice_alimento
            WHERE dp.pasto_id = ?
            GROUP BY dp.id, dp.codice_alimento, a.nome, dp.quantita_grammi
            ORDER BY dp.id ASC
            """,
            (pasto_id,),
        )
        alimenti_rows = cursor.fetchall()

        foods = []
        for alimento_row in alimenti_rows:
            dettaglio_id = alimento_row[0]
            codice_alimento = alimento_row[1]
            nome_alimento = alimento_row[2] or codice_alimento
            grammi = int(alimento_row[3] or 0)
            ratio = grammi / 100.0
            kcal = _to_float_value(alimento_row[4]) * ratio
            pro = _to_float_value(alimento_row[5]) * ratio
            carb = _to_float_value(alimento_row[6]) * ratio
            fat = _to_float_value(alimento_row[7]) * ratio

            foods.append(
                {
                    "id": dettaglio_id,
                    "codice_alimento": codice_alimento,
                    "name": nome_alimento,
                    "grams": grammi,
                    "kcal": kcal,
                    "pro": pro,
                    "carb": carb,
                    "fat": fat,
                }
            )

        day_index = int(giorno_settimana) - 1
        if 0 <= day_index < 7:
            week_plan[day_index]["meals"].append(
                {
                    "id": pasto_id,
                    "name": nome_pasto,
                    "ordine": _ordine,
                    "open": True,
                    "foods": foods,
                }
            )

    return {
        "id": dieta_row[0],
        "nome": dieta_row[1],
        "week_plan": week_plan,
    }


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
        SELECT a.codice_alimento, a.nome, a.categoria,
               MAX(CASE WHEN v.nutriente = 'Energia (kcal)' THEN v.valore_100g END) AS kcal,
               MAX(CASE WHEN v.nutriente = 'Proteine (g)' THEN v.valore_100g END) AS proteine,
               MAX(CASE WHEN v.nutriente = 'Carboidrati disponibili (g)' THEN v.valore_100g END) AS carboidrati,
               MAX(CASE WHEN v.nutriente = 'Lipidi (g)' THEN v.valore_100g END) AS grassi
        FROM alimenti a
        LEFT JOIN valori_nutrizionali v ON a.codice_alimento = v.codice_alimento
        WHERE a.nome LIKE ? OR a.categoria LIKE ?
        GROUP BY a.codice_alimento, a.nome, a.categoria
        ORDER BY a.nome ASC
        LIMIT 20
        """,
        (pattern, pattern),
    )
    rows = cursor.fetchall()

    results = []
    for row in rows:
        results.append(
            {
                "codice_alimento": row[0],
                "nome": row[1],
                "categoria": row[2],
                "kcal": _to_float_value(row[3]),
                "proteine": _to_float_value(row[4]),
                "carboidrati": _to_float_value(row[5]),
                "grassi": _to_float_value(row[6]),
            }
        )

    return results


def calcola_micronutrienti_lista(conn: sqlite3.Connection, alimenti_richiesti: list) -> dict[str, float]:
    """
    Calcola i micronutrienti totali per una lista di alimenti/grammature
    senza persistere la dieta.
    """
    cursor = conn.cursor()
    totali: dict[str, float] = {}

    for alimento in alimenti_richiesti:
        if isinstance(alimento, dict):
            codice_alimento = alimento.get("codice_alimento")
            grammi = alimento.get("grammi", 0)
        else:
            codice_alimento = getattr(alimento, "codice_alimento", None)
            grammi = getattr(alimento, "grammi", 0)

        if not codice_alimento:
            continue

        try:
            grammi_float = float(grammi or 0)
        except (TypeError, ValueError):
            grammi_float = 0.0
        if grammi_float <= 0:
            continue

        ratio = grammi_float / 100.0
        cursor.execute(
            """
            SELECT nutriente, valore_100g
            FROM valori_nutrizionali
            WHERE codice_alimento = ?
              AND nutriente NOT LIKE 'Energia%'
              AND nutriente NOT LIKE 'Proteine%'
              AND nutriente NOT LIKE 'Lipidi%'
              AND nutriente NOT LIKE 'Carboidrati%'
            """,
            (codice_alimento,),
        )
        rows = cursor.fetchall()

        for nutriente, valore_100g in rows:
            valore = _to_float_value(valore_100g) * ratio
            totali[nutriente] = totali.get(nutriente, 0.0) + valore

    return {k: totali[k] for k in sorted(totali)}
