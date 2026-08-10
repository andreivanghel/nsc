from dataclasses import dataclass
from decimal import Decimal

from inc_tax_sim.domain.value_objects.fiscal_regime import RegimeFiscale


@dataclass(frozen=True)
class VoceTrattenuta:
    nome: str
    importo: Decimal

@dataclass(frozen=True)
class RisultatoNetto:
    ral: Decimal
    netto_annuo: Decimal
    netto_mensile: Decimal
    trattenute: tuple[VoceTrattenuta, ...]
