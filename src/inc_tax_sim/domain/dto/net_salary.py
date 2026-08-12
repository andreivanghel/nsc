from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class VoceTrattenuta:
    """Importo che riduce il netto (contributi, imposte, addizionali)."""

    nome: str
    importo: Decimal


@dataclass(frozen=True)
class VoceBeneficio:
    """Importo erogato per intero (se spettante) e sommato al netto —
    trattamento integrativo, somma integrativa cuneo fiscale. Non è
    un'ulteriore riduzione dell'IRPEF già azzerata dalle detrazioni."""

    nome: str
    importo: Decimal


@dataclass(frozen=True)
class VoceDetrazione:
    """Detrazione già applicata nel calcolo di 'IRPEF netta', esposta
    qui solo per trasparenza — NON va sommata o sottratta di nuovo dal
    netto, altrimenti la si conta due volte."""

    nome: str
    importo: Decimal


@dataclass(frozen=True)
class RisultatoNetto:
    ral: Decimal
    netto_annuo: Decimal
    netto_mensile: Decimal
    trattenute: tuple[VoceTrattenuta, ...]
    benefici: tuple[VoceBeneficio, ...]
    detrazioni_applicate: tuple[VoceDetrazione, ...]
