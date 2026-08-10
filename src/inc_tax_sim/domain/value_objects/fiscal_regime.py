from dataclasses import dataclass
from decimal import Decimal
from typing import Callable

from inc_tax_sim.domain.value_objects.tax import Imposta, Scaglione


@dataclass(frozen=True)
class RegimeFiscale:
    anno: int
    comune: str
    regione: str

    inps: Imposta
    irpef: Imposta

    addizionale_regionale: Imposta

    addizionale_comunale: Callable[[Decimal], Decimal]
    detrazione_lavoro_dipendente: Callable[[Decimal, int, bool], Decimal]
    trattamento_integrativo: Callable[[Decimal, Decimal, Decimal, int], Decimal]


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
ADDIZIONALE_COMUNALE_MILANO_2026 = Decimal("0.008") # fonte="https://www1.finanze.gov.it/finanze2/dipartimentopolitichefiscali/fiscalitalocale/nuova_addcomirpef/risultato.htm?anno=9999&pr=MI&cc=F205&r=1",

SOGLIA_ESENZIONE_ADD_COMUNALE_MILANO = Decimal("23000")

def _calcola_detrazione_lavoro_dipendente_2026(
    reddito: Decimal,
    giorni_lavorati: int = 365,
    tempo_determinato: bool = False,
) -> Decimal:
    if reddito > Decimal("50000"):
        return Decimal(0)
    elif reddito > Decimal("28000"):
        teorica = Decimal("1910") * (Decimal("50000") - reddito) / Decimal("22000")
    elif reddito > Decimal("15000"):
        teorica = Decimal("1910") + Decimal("1190") * (Decimal("28000") - reddito) / Decimal("13000")
    else:
        teorica = Decimal("1955")

    rapportata = teorica * giorni_lavorati / Decimal("365")
    minimo = Decimal("1380") if tempo_determinato else Decimal("690")
    return max(rapportata, minimo) if reddito <= Decimal("15000") else rapportata

def calcola_trattamento_integrativo_2026( # TODO: verificare con fonte normativa
    reddito: Decimal,
    irpef_lorda: Decimal,
    detrazione_lavoro_dipendente: Decimal,
    giorni_lavorati: int = 365,
) -> Decimal:
    """
    Trattamento integrativo (ex bonus Renzi), art. 1 DL 3/2020.
    Spetta fino a 28.000€ di reddito, solo se c'è "capienza": l'IRPEF
    lorda deve essere almeno pari alla detrazione lavoro dipendente
    (altrimenti la detrazione da sola avrebbe già assorbito tutto,
    e non spetta cash aggiuntivo — è l'anti-abuso del meccanismo).
    Importo = quanto la detrazione "avanza" oltre l'IRPEF lorda,
    fino a un massimo di 1.200€/anno, rapportato ai giorni lavorati.
    """
    if reddito > Decimal("28000"):
        return Decimal(0)

    capienza = detrazione_lavoro_dipendente - irpef_lorda
    if capienza <= Decimal(0):
        return Decimal(0)

    massimo = Decimal("1200") * giorni_lavorati / Decimal("365")
    return min(capienza, massimo)

def _calcola_addizionale_comunale(
    imponibile: Decimal,
    soglia_esenzione: Decimal,
    aliquota: Decimal,
) -> Decimal:
    """
    A soglia secca (confermato per Milano da MEF): sotto la soglia,
    zero; sopra, l'aliquota si applica all'INTERO imponibile, non solo
    alla parte eccedente — a differenza di IRPEF e addizionale regionale.
    """
    if imponibile <= soglia_esenzione:
        return Decimal(0)
    return imponibile * aliquota

REGIME_2026_MILANO = RegimeFiscale(
    anno=2026,
    comune="Milano",
    regione="Lombardia",
    inps=INPS_2026,
    irpef=IRPEF_2026,
    addizionale_regionale=ADDIZIONALE_REGIONALE_LOMBARDIA_2026,
    addizionale_comunale=lambda imponibile: _calcola_addizionale_comunale(imponibile, SOGLIA_ESENZIONE_ADD_COMUNALE_MILANO, ADDIZIONALE_COMUNALE_MILANO_2026),
    detrazione_lavoro_dipendente=lambda imponibile, giorni_lavorati=365, tempo_determinato=False: _calcola_detrazione_lavoro_dipendente_2026(imponibile, giorni_lavorati, tempo_determinato),
    trattamento_integrativo=lambda imponibile, irpef_lorda, detrazione_lavoro_dipendente, giorni_lavorati=365: calcola_trattamento_integrativo_2026(imponibile, irpef_lorda, detrazione_lavoro_dipendente, giorni_lavorati),
)