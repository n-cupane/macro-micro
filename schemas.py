from pydantic import BaseModel


class UtenteCreate(BaseModel):
    nome: str
    email: str
    password: str


class DietaCreate(BaseModel):
    nome_dieta: str


class PastoCreate(BaseModel):
    dieta_id: int
    giorno_settimana: int
    nome_pasto: str
    ordine: int


class AlimentoPastoCreate(BaseModel):
    codice_alimento: str
    quantita_grammi: int
