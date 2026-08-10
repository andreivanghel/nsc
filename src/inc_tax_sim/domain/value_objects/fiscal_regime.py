from dataclasses import dataclass
from decimal import Decimal

from inc_tax_sim.domain.value_objects.tax import Imposta, Scaglione


@dataclass(frozen=True)
class RegimeFiscale:
    anno: int
    comune: str
    regione: str

    inps: Imposta
    irpef: Imposta

    addizionale_regionale: Imposta
    addizionale_comunale: Imposta

    soglia_esenzione_addizionale_comunale: Decimal


# --- INPS
INPS_2026 = Imposta(
    nome="inps_ivs_dipendente",
    scaglioni=(Scaglione(Decimal(0), None, Decimal("0.0919")),),
    fonte="https://www.inps.it/it/it/dettaglio-scheda.it.schede-servizio-strumento.schede-servizi.50286.denuncia-e-versamento-dei-contributi-ex-enpals-fondo-pensioni-lavoratori-dello-spettacolo-e-fondo-pensioni-sportivi-professionisti-.html",
)

# --- IRPEF: 3 scaglioni (Legge di Bilancio 2026 ha ridotto il secondo da 35% a 33%)
IRPEF_2026 = Imposta(
    nome="irpef",
    scaglioni=(
        Scaglione(Decimal(0), Decimal(28000), Decimal("0.23")),
        Scaglione(Decimal(28000), Decimal(50000), Decimal("0.33")),
        Scaglione(Decimal(50000), None, Decimal("0.43")),
    ),
    fonte="https://www.agenziaentrate.gov.it/portale/imposta-sul-reddito-delle-persone-fisiche-irpef-/aliquote-e-calcolo-dell-irpef",
)

# Addizionali
ADDIZIONALE_REGIONALE_LOMBARDIA_2026 = Imposta(
    nome="addizionale_regionale_lombardia",
    scaglioni=(
        Scaglione(Decimal(0), Decimal(15000), Decimal("0.0123")),
        Scaglione(Decimal(15000), Decimal(28000), Decimal("0.0158")),
        Scaglione(Decimal(28000), Decimal(50000), Decimal("0.0172")),
        Scaglione(Decimal(50000), None, Decimal("0.0143")),
    ),
    fonte="https://www1.finanze.gov.it/finanze2/dipartimentopolitichefiscali/fiscalitalocale/addregirpef/addregirpef.php?reg=10",
)
ADDIZIONALE_COMUNALE_MILANO_2026 = Imposta(
    nome="addizionale_comunale_milano",
    scaglioni=(Scaglione(Decimal(0), None, Decimal("0.008")),),
    fonte="https://www1.finanze.gov.it/finanze2/dipartimentopolitichefiscali/fiscalitalocale/nuova_addcomirpef/risultato.htm?anno=9999&pr=MI&cc=F205&r=1",
)
SOGLIA_ESENZIONE_ADD_COMUNALE_MILANO = Decimal("23000")

REGIME_2026_MILANO = RegimeFiscale(
    anno=2026,
    comune="Milano",
    regione="Lombardia",
    inps=INPS_2026,
    irpef=IRPEF_2026,
    aliquota_addizionale_regionale=ADDIZIONALE_REGIONALE_LOMBARDIA_2026,
    aliquota_addizionale_comunale=ADDIZIONALE_COMUNALE_MILANO_2026,
    soglia_esenzione_addizionale_comunale=SOGLIA_ESENZIONE_ADD_COMUNALE_MILANO,
)