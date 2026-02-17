from typing import List

from pydantic import BaseModel, field_validator


class UtenteCreate(BaseModel):
    nome: str
    email: str
    password: str
    sesso: str

    @field_validator("sesso")
    @classmethod
    def validate_sesso(cls, value: str) -> str:
        normalized = (value or "").strip().upper()
        if normalized not in {"M", "F"}:
            raise ValueError("sesso deve essere 'M' o 'F'")
        return normalized


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


class AlimentoBulkCreate(BaseModel):
    codice_alimento: str
    grammi: int


class AlimentoMicroRequest(BaseModel):
    codice_alimento: str
    grammi: float


class PastoBulkCreate(BaseModel):
    nome_pasto: str
    giorno_settimana: int
    ordine: int
    alimenti: List[AlimentoBulkCreate]


class DietaCompletaCreate(BaseModel):
    nome: str
    pasti: List[PastoBulkCreate]


class CalcoloMicroRequest(BaseModel):
    alimenti: List[AlimentoMicroRequest]
