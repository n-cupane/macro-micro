import re
import sqlite3


NUTRIENTI_TARGET = {
    "Proteine (g)": "proteine_g",
    "Lipidi (g)": "lipidi_g",
    "Carboidrati disponibili (g)": "carboidrati_g",
    "Energia (kcal)": "energia_kcal",
}


def _parse_valore_100g(raw_value: str | None) -> float:
    """Converte il valore testuale in float, trattando 'tr' e null come 0.0."""
    if raw_value is None:
        return 0.0

    value = str(raw_value).strip().lower()
    if not value or value == "tr":
        return 0.0

    value = value.replace(",", ".")
    try:
        return float(value)
    except ValueError:
        # Fallback: estrae la prima porzione numerica (es. "12.3 g").
        match = re.search(r"-?\d+(?:\.\d+)?", value)
        return float(match.group(0)) if match else 0.0


def calcola_macro_pasto(conn: sqlite3.Connection, pasto_id: int) -> dict:
    """
    Calcola i totali del pasto per proteine, lipidi, carboidrati disponibili ed energia.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT codice_alimento, quantita_grammi
        FROM dettaglio_pasti
        WHERE pasto_id = ?
        """,
        (pasto_id,),
    )
    alimenti_pasto = cursor.fetchall()

    totali = {
        "pasto_id": pasto_id,
        "proteine_g": 0.0,
        "lipidi_g": 0.0,
        "carboidrati_g": 0.0,
        "energia_kcal": 0.0,
    }

    if not alimenti_pasto:
        return totali

    for codice_alimento, quantita_grammi in alimenti_pasto:
        quantita = float(quantita_grammi or 0)
        cursor.execute(
            """
            SELECT nutriente, valore_100g
            FROM valori_nutrizionali
            WHERE codice_alimento = ?
              AND nutriente IN (?, ?, ?, ?)
            """,
            (codice_alimento, *NUTRIENTI_TARGET.keys()),
        )
        nutrienti = cursor.fetchall()

        for nutriente, valore_100g in nutrienti:
            chiave_totale = NUTRIENTI_TARGET.get(nutriente)
            if not chiave_totale:
                continue
            valore = _parse_valore_100g(valore_100g)
            totali[chiave_totale] += (valore / 100.0) * quantita

    return totali
