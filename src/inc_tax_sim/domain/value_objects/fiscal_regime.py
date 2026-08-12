from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from inc_tax_sim.domain.value_objects.tax import Imposta, Scaglione


class DetrazioneLavoroDipendenteFn(Protocol):
    def __call__(
        self,
        reddito: Decimal,
        giorni_lavorati: int = 365,
        tempo_determinato: bool = False,
    ) -> Decimal: ...


class AddizionaleComunaleFn(Protocol):
    def __call__(
        self,
        imponibile: Decimal,
        soglia_esenzione: Decimal = ...,
        aliquota: Decimal = ...,
    ) -> Decimal: ...


class TrattamentoIntegrativoFn(Protocol):
    def __call__(
        self,
        reddito: Decimal,
        irpef_lorda: Decimal,
        detrazione_lavoro_dipendente: Decimal,
        giorni_lavorati: int = 365,
    ) -> Decimal: ...


class SommaIntegrativaCuneoFn(Protocol):
    def __call__(
        self,
        reddito: Decimal,
        giorni_lavorati: int = 365,
    ) -> Decimal: ...


class UlterioreDetrazioneCuneoFn(Protocol):
    def __call__(
        self,
        reddito: Decimal,
        giorni_lavorati: int = 365,
    ) -> Decimal: ...


@dataclass(frozen=True)
class RegimeFiscale:
    anno: int
    comune: str
    regione: str

    inps: Imposta
    irpef: Imposta

    addizionale_regionale: Imposta

    addizionale_comunale: AddizionaleComunaleFn
    detrazione_lavoro_dipendente: DetrazioneLavoroDipendenteFn
    trattamento_integrativo: TrattamentoIntegrativoFn

    # Taglio del cuneo fiscale (art. 1 commi 4 e 6, legge 207/2024,
    # confermato strutturale per il 2026 — v. funzioni sotto). Due
    # meccanismi distinti dal trattamento_integrativo (DL 3/2020) sopra,
    # pur convivendo con esso sulla stessa fascia di reddito bassa.
    somma_integrativa_cuneo: SommaIntegrativaCuneoFn
    ulteriore_detrazione_cuneo: UlterioreDetrazioneCuneoFn


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
        # BUGFIX: era 0.0143 (1,43%) — un'aliquota che DECRESCE
        # sull'ultimo scaglione contraddice la progressività dichiarata
        # nel commento del blocco IRPEF qui sopra ed è incoerente con
        # ogni altro scaglione di questa stessa Imposta. Confermato
        # 1,73% da fonte primaria (art. 72 l.r. 10/2003, Regione
        # Lombardia): https://www.regione.lombardia.it/bollo-auto-e-tributi-regionali/red-addizionale-regionale-irpef
        Scaglione(Decimal(50000), None, Decimal("0.0173")),
    ),
    fonte="https://www1.finanze.gov.it/finanze2/dipartimentopolitichefiscali/fiscalitalocale/addregirpef/addregirpef.php?reg=10",
)
ADDIZIONALE_COMUNALE_MILANO_2026 = Decimal(
    "0.008"
)  # fonte="https://www1.finanze.gov.it/finanze2/dipartimentopolitichefiscali/fiscalitalocale/nuova_addcomirpef/risultato.htm?anno=9999&pr=MI&cc=F205&r=1",

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


def calcola_trattamento_integrativo_2026(
    reddito: Decimal,
    irpef_lorda: Decimal,
    detrazione_lavoro_dipendente: Decimal,
    giorni_lavorati: int = 365,
) -> Decimal:
    """
    Trattamento integrativo (ex bonus Renzi), art. 1 DL 3/2020.

    Per reddito <= 15.000: spetta per intero (1.200€/anno, rapportato ai
    giorni lavorati), a condizione di "capienza" — l'IRPEF lorda deve
    essere pari o superiore alla detrazione lavoro dipendente spettante.
    Vicino al limite della no-tax-area questa condizione può non essere
    soddisfatta, e in quel caso il trattamento non spetta.

    SEMPLIFICAZIONE DICHIARATA: per la fascia 15.001-28.000€ la norma
    richiede una verifica sulle detrazioni complessive che va oltre lo
    scope di questo prototipo (le fonti concordano che "non è automatico"
    ma nessuna dà una formula chiusa affidabile per questa fascia).
    Ritorno 0, sottostimando leggermente il netto — punto da discutere
    in interview.
    """
    if reddito > Decimal("15000"):
        return Decimal(0)

    capiente = irpef_lorda >= detrazione_lavoro_dipendente
    if not capiente:
        return Decimal(0)

    return Decimal("1200") * giorni_lavorati / Decimal("365")


# --- Taglio del cuneo fiscale (art. 1 commi 4 e 6, legge 207/2024)
#
# Introdotto dalla legge di bilancio 2025, confermato strutturale per il
# 2026 (invariato nelle soglie e negli importi: cambia solo il contesto
# IRPEF intorno, v. commento sul secondo scaglione più sopra). Due
# meccanismi distinti che coprono fasce di reddito complementari:
#   - somma integrativa (comma 4): reddito <= 20.000€, somma esente non
#     imponibile, NESSUN requisito di capienza IRPEF (a differenza del
#     trattamento_integrativo qui sopra, con cui è comunque cumulabile
#     nella fascia fino a 15.000€)
#   - ulteriore detrazione (comma 6): reddito 20.000-40.000€, vera
#     detrazione dall'imposta lorda (va quindi trattata come le altre
#     detrazioni, non come una somma a parte)
# Fonte: https://www.lavoro.gov.it/notizie/pagine/legge-di-bilancio-2025-le-misure-lavoratori-imprese-e-famiglie

SOGLIA_SOMMA_INTEGRATIVA = Decimal("20000")
SOGLIA_BASSA_SOMMA_INTEGRATIVA = Decimal("8500")
SOGLIA_MEDIA_SOMMA_INTEGRATIVA = Decimal("15000")
ALIQUOTA_SOMMA_INTEGRATIVA_BASSA = Decimal("0.071")
ALIQUOTA_SOMMA_INTEGRATIVA_MEDIA = Decimal("0.053")
ALIQUOTA_SOMMA_INTEGRATIVA_ALTA = Decimal("0.048")

SOGLIA_ULTERIORE_DETRAZIONE_MIN = Decimal("20000")
SOGLIA_ULTERIORE_DETRAZIONE_FLAT = Decimal("32000")
SOGLIA_ULTERIORE_DETRAZIONE_MAX = Decimal("40000")
IMPORTO_ULTERIORE_DETRAZIONE = Decimal("1000")


def _calcola_somma_integrativa_cuneo_2026(
    reddito: Decimal,
    giorni_lavorati: int = 365,
) -> Decimal:
    """
    Somma integrativa non imponibile, art. 1 c. 4 legge 207/2024.

    Percentuale sul reddito di lavoro dipendente, per reddito <= 20.000€:
      - 7,1% fino a 8.500€
      - 5,3% tra 8.500€ e 15.000€
      - 4,8% tra 15.000€ e 20.000€

    A 20.001€ il beneficio "salta" al meccanismo diverso di
    ulteriore_detrazione_cuneo_2026 (1.000€ fissi): è un salto vero
    della normativa, non un bug — stesso pattern già visto al confine
    dei 15.000€ in detrazione_lavoro_dipendente.

    SEMPLIFICAZIONE DICHIARATA: la circolare AdE 4/2025 richiede di
    annualizzare il reddito per individuare la fascia/percentuale
    corretta e poi applicare quella percentuale al reddito
    EFFETTIVAMENTE percepito nel periodo. Qui, come per
    detrazione_lavoro_dipendente, si assume reddito già annuale e si
    rapporta solo il risultato finale ai giorni lavorati — coerente col
    resto del modulo, ma da rivedere se serve gestire con precisione
    variazioni di reddito infra-annuali.
    """
    if reddito > SOGLIA_SOMMA_INTEGRATIVA:
        return Decimal(0)
    elif reddito > SOGLIA_MEDIA_SOMMA_INTEGRATIVA:
        aliquota = ALIQUOTA_SOMMA_INTEGRATIVA_ALTA
    elif reddito > SOGLIA_BASSA_SOMMA_INTEGRATIVA:
        aliquota = ALIQUOTA_SOMMA_INTEGRATIVA_MEDIA
    else:
        aliquota = ALIQUOTA_SOMMA_INTEGRATIVA_BASSA

    teorica = reddito * aliquota
    return teorica * giorni_lavorati / Decimal("365")


def _calcola_ulteriore_detrazione_cuneo_2026(
    reddito: Decimal,
    giorni_lavorati: int = 365,
) -> Decimal:
    """
    Ulteriore detrazione d'imposta, art. 1 c. 6 legge 207/2024.

    Per reddito > 20.000€ e <= 40.000€:
      - 1.000€ fissi tra 20.000€ e 32.000€
      - decrescente linearmente da 1.000€ a 0€ tra 32.000€ e 40.000€

    A differenza di somma_integrativa_cuneo_2026, questa è una vera
    detrazione dall'imposta lorda: nel service va sommata a
    detrazione_lavoro_dipendente e sottratta da irpef_lorda (con lo
    stesso floor a zero), NON aggiunta come somma a parte.
    """
    if reddito <= SOGLIA_ULTERIORE_DETRAZIONE_MIN:
        teorica = Decimal(0)
    elif reddito <= SOGLIA_ULTERIORE_DETRAZIONE_FLAT:
        teorica = IMPORTO_ULTERIORE_DETRAZIONE
    elif reddito <= SOGLIA_ULTERIORE_DETRAZIONE_MAX:
        teorica = (
            IMPORTO_ULTERIORE_DETRAZIONE
            * (SOGLIA_ULTERIORE_DETRAZIONE_MAX - reddito)
            / (SOGLIA_ULTERIORE_DETRAZIONE_MAX - SOGLIA_ULTERIORE_DETRAZIONE_FLAT)
        )
    else:
        teorica = Decimal(0)

    return teorica * giorni_lavorati / Decimal("365")


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
    addizionale_comunale=lambda imponibile, soglia=SOGLIA_ESENZIONE_ADD_COMUNALE_MILANO, aliquota=ADDIZIONALE_COMUNALE_MILANO_2026: (
        _calcola_addizionale_comunale(imponibile, soglia, aliquota)
    ),
    detrazione_lavoro_dipendente=lambda imponibile, giorni_lavorati=365, tempo_determinato=False: _calcola_detrazione_lavoro_dipendente_2026(
        imponibile, giorni_lavorati, tempo_determinato
    ),
    trattamento_integrativo=lambda imponibile, irpef_lorda, detrazione_lavoro_dipendente, giorni_lavorati=365: calcola_trattamento_integrativo_2026(
        imponibile, irpef_lorda, detrazione_lavoro_dipendente, giorni_lavorati
    ),
    somma_integrativa_cuneo=lambda imponibile, giorni_lavorati=365: _calcola_somma_integrativa_cuneo_2026(imponibile, giorni_lavorati),
    ulteriore_detrazione_cuneo=lambda imponibile, giorni_lavorati=365: _calcola_ulteriore_detrazione_cuneo_2026(imponibile, giorni_lavorati),
)
