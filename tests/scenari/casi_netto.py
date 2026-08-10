"""
Casi RAL -> netto, calcolati e verificati a mano
Ogni caso viene eseguito end-to-end contro REGIME_2026_MILANO reale — non i dati
astratti dei test unitari.

Un caso = una riga.
"""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class CasoNetto:
    descrizione: str
    ral: Decimal
    mensilita: int
    netto_annuo_atteso: Decimal


CASI_NETTO: list[CasoNetto] = [
    # Esempio:
    # CasoNetto(
    #     descrizione="RAL 30.000, standard, 13 mensilita",
    #     ral=Decimal("30000"),
    #     mensilita=13,
    #     netto_annuo_atteso=Decimal("23456.78"),
    # ),
]
