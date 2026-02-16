from typing import List

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


class AlimentoBulkCreate(BaseModel):
    codice_alimento: str
    grammi: int


class PastoBulkCreate(BaseModel):
    nome_pasto: str
    giorno_settimana: int
    alimenti: List[AlimentoBulkCreate]


class DietaCompletaCreate(BaseModel):
    nome: str
    pasti: List[PastoBulkCreate]
