import uvicorn
import sqlite3
from typing import Generator

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

from calcolatore import calcola_macro_pasto
from crud_manager import (
    aggiungi_alimento_a_pasto,
    aggiungi_pasto,
    aggiorna_dieta_completa,
    calcola_micronutrienti_lista,
    cerca_alimenti,
    copia_giorno_dieta,
    crea_dieta,
    crea_dieta_completa,
    crea_utente,
    elimina_dieta,
    ottieni_dieta_completa,
    ottieni_diete_utente,
)
from database import setup_database
from nutritional_targets import load_larn_data
from security import ALGORITHM, SECRET_KEY, crea_access_token, hash_password, verify_password
from schemas import (
    AlimentoPastoCreate,
    CalcoloMicroRequest,
    DietaCompletaCreate,
    DietaCreate,
    PastoCreate,
    UtenteCreate,
)

app = FastAPI(title="Macro Micro API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")


class CopiaGiornoRequest(BaseModel):
    giorno_origine: int
    giorno_destinazione: int


@app.on_event("startup")
def startup_load_targets() -> None:
    load_larn_data()


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Apre e chiude automaticamente la connessione DB per richiesta."""
    conn = setup_database()
    try:
        yield conn
    finally:
        conn.close()


def get_utente_corrente(
    token: str = Depends(oauth2_scheme),
    conn: sqlite3.Connection = Depends(get_db),
) -> dict:
    """Valida il token JWT e ritorna l'utente corrente."""
    credenziali_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token non valido",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise credenziali_exception
    except jwt.InvalidTokenError:
        raise credenziali_exception

    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, nome, email, ruolo, sesso
        FROM utenti
        WHERE id = ?
        """,
        (user_id,),
    )
    user = cursor.fetchone()
    if not user:
        raise credenziali_exception

    return {
        "id": user[0],
        "nome": user[1],
        "email": user[2],
        "ruolo": user[3],
        "sesso": user[4],
    }


def get_utente_admin(utente_corrente: dict = Depends(get_utente_corrente)) -> dict:
    """Permette accesso solo ad utenti admin."""
    if utente_corrente.get("ruolo") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Privilegi insufficienti",
        )
    return utente_corrente


@app.post("/api/utenti", status_code=201)
def crea_utente_endpoint(
    payload: UtenteCreate,
    conn: sqlite3.Connection = Depends(get_db),
    admin_user: dict = Depends(get_utente_admin),
) -> dict:
    password_hash = hash_password(payload.password)
    utente_id = crea_utente(conn, payload.nome, payload.email, password_hash, payload.sesso)
    return {"id": utente_id}


@app.post("/api/diete", status_code=201)
def crea_dieta_endpoint(
    payload: DietaCreate,
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_utente_corrente),
) -> dict:
    dieta_id = crea_dieta(conn, current_user["id"], payload.nome_dieta)
    return {"id": dieta_id}


@app.post("/api/diete/completa", status_code=201)
def crea_dieta_completa_endpoint(
    payload: DietaCompletaCreate,
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_utente_corrente),
) -> dict:
    dieta_id = crea_dieta_completa(conn, current_user["id"], payload)
    return {"status": "ok", "id": dieta_id, "message": "Dieta salvata con successo"}


@app.put("/api/diete/{dieta_id}/completa")
def aggiorna_dieta_completa_endpoint(
    dieta_id: int,
    payload: DietaCompletaCreate,
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_utente_corrente),
) -> dict:
    updated = aggiorna_dieta_completa(conn, dieta_id, current_user["id"], payload)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dieta non trovata")
    return {"status": "ok", "id": dieta_id, "message": "Dieta aggiornata con successo"}


@app.get("/api/utenti/me/diete")
def ottieni_diete_utente_endpoint(
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_utente_corrente),
) -> list[dict]:
    return ottieni_diete_utente(conn, current_user["id"])


@app.get("/api/diete")
def ottieni_mie_diete_endpoint(
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_utente_corrente),
) -> list[dict]:
    return ottieni_diete_utente(conn, current_user["id"])


@app.get("/api/diete/{dieta_id}/completa")
def ottieni_dieta_completa_endpoint(
    dieta_id: int,
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_utente_corrente),
) -> dict:
    dieta = ottieni_dieta_completa(conn, dieta_id, current_user["id"])
    if not dieta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dieta non trovata")
    return dieta


@app.delete("/api/diete/{dieta_id}")
def elimina_dieta_endpoint(
    dieta_id: int,
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_utente_corrente),
) -> dict:
    deleted = elimina_dieta(conn, dieta_id, current_user["id"])
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dieta non trovata")
    return {"status": "ok"}


@app.post("/api/pasti", status_code=201)
def aggiungi_pasto_endpoint(
    payload: PastoCreate,
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_utente_corrente),
) -> dict:
    pasto_id = aggiungi_pasto(
        conn,
        payload.dieta_id,
        payload.giorno_settimana,
        payload.nome_pasto,
        payload.ordine,
    )
    return {"id": pasto_id}


@app.post("/api/pasti/{pasto_id}/alimenti", status_code=201)
def aggiungi_alimento_a_pasto_endpoint(
    pasto_id: int,
    payload: AlimentoPastoCreate,
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_utente_corrente),
) -> dict:
    aggiungi_alimento_a_pasto(conn, pasto_id, payload.codice_alimento, payload.quantita_grammi)
    return {"status": "ok"}


@app.post("/api/diete/{dieta_id}/copia-giorno", status_code=201)
def copia_giorno_dieta_endpoint(
    dieta_id: int,
    payload: CopiaGiornoRequest,
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_utente_corrente),
) -> dict:
    copia_giorno_dieta(conn, dieta_id, payload.giorno_origine, payload.giorno_destinazione)
    return {"status": "ok"}


@app.get("/api/alimenti/search")
def cerca_alimenti_endpoint(
    q: str,
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_utente_corrente),
) -> list[dict]:
    return cerca_alimenti(conn, q)


@app.get("/api/pasti/{pasto_id}/nutrizione")
def nutrizione_pasto_endpoint(
    pasto_id: int,
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_utente_corrente),
) -> dict:
    totali = calcola_macro_pasto(conn, pasto_id)
    return {
        "pasto_id": pasto_id,
        "kcal": totali["energia_kcal"],
        "proteine": totali["proteine_g"],
        "grassi": totali["lipidi_g"],
        "carboidrati": totali["carboidrati_g"],
    }


@app.post("/api/nutrizione/giornaliera/micro")
def nutrizione_giornaliera_micro_endpoint(
    payload: CalcoloMicroRequest,
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_utente_corrente),
) -> dict[str, dict[str, float]]:
    return calcola_micronutrienti_lista(conn, payload.alimenti, current_user["sesso"])


@app.post("/api/token")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    conn: sqlite3.Connection = Depends(get_db),
) -> dict:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, email, password_hash, ruolo, sesso
        FROM utenti
        WHERE email = ?
        """,
        (form_data.username,),
    )
    user = cursor.fetchone()

    if not user or not verify_password(form_data.password, user[2]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenziali non valide",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = crea_access_token(
        data={"sub": str(user[0]), "email": user[1], "ruolo": user[3], "sesso": user[4]}
    )
    return {"access_token": access_token, "token_type": "bearer"}

if __name__ == "__main__":
    uvicorn.run("main_api:app", host="127.0.0.1", port=8000, reload=True)
