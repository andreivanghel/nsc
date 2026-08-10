"""
Casi verificati a mano per OGNI SINGOLA funzione della catena fiscale,
eseguiti contro i dati REALI di REGIME_2026_MILANO (non i numeri
astratti dei test unitari in tests/domain/). Usati per fissare punti
di riferimento.
"""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class CasoINPS:
    descrizione: str
    ral: Decimal
    atteso: Decimal


@dataclass(frozen=True)
class CasoIRPEFLorda:
    descrizione: str
    imponibile: Decimal
    atteso: Decimal


@dataclass(frozen=True)
class CasoAddizionaleRegionale:
    descrizione: str
    imponibile: Decimal
    atteso: Decimal


@dataclass(frozen=True)
class CasoAddizionaleComunale:
    descrizione: str
    imponibile: Decimal
    atteso: Decimal


@dataclass(frozen=True)
class CasoDetrazione:
    descrizione: str
    imponibile: Decimal
    giorni_lavorati: int
    tempo_determinato: bool
    atteso: Decimal


@dataclass(frozen=True)
class CasoTrattamentoIntegrativo:
    descrizione: str
    imponibile: Decimal
    irpef_lorda: Decimal
    detrazione: Decimal
    giorni_lavorati: int
    atteso: Decimal


# Esempio
#
# CASI_INPS = [
#     CasoINPS(descrizione="RAL 30.000", ral=Decimal("30000"), atteso=Decimal("2757.00")),
# ]

CASI_INPS: list[CasoINPS] = []
CASI_IRPEF_LORDA: list[CasoIRPEFLorda] = []
CASI_ADDIZIONALE_REGIONALE: list[CasoAddizionaleRegionale] = []
CASI_ADDIZIONALE_COMUNALE: list[CasoAddizionaleComunale] = []
CASI_DETRAZIONE: list[CasoDetrazione] = []
CASI_TRATTAMENTO_INTEGRATIVO: list[CasoTrattamentoIntegrativo] = []
