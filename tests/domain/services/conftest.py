from decimal import Decimal

import pytest

from inc_tax_sim.domain.value_objects.fiscal_regime import RegimeFiscale
from inc_tax_sim.domain.value_objects.tax import Imposta, Scaglione


@pytest.fixture
def regime_test() -> RegimeFiscale:
    """Regime fittizio con numeri tondi, isolato dai dati fiscali reali.
    Serve a testare la CORRETTEZZA DELL'ORCHESTRAZIONE (l'ordine delle
    trattenute, il guard sulla no-tax-area, la struttura del risultato)
    senza dipendere dalla correttezza delle aliquote 2026 reali — quella
    è responsabilità di tests/domain/funzioni_fiscali e tests/scenari."""
    return RegimeFiscale(
        anno=9999,
        comune="Testopoli",
        regione="Testania",
        inps=Imposta(
            nome="inps_test",
            scaglioni=(Scaglione(Decimal(0), None, Decimal("0.10")),),
        ),
        irpef=Imposta(
            nome="irpef_test",
            scaglioni=(
                Scaglione(Decimal(0), Decimal(1000), Decimal("0.20")),
                Scaglione(Decimal(1000), None, Decimal("0.40")),
            ),
        ),
        addizionale_regionale=Imposta(
            nome="add_reg_test",
            scaglioni=(Scaglione(Decimal(0), None, Decimal("0.05")),),
        ),
        addizionale_comunale=lambda imponibile: Decimal(0) if imponibile <= Decimal(500) else imponibile * Decimal("0.02"),  # type: ignore[arg-type]
        detrazione_lavoro_dipendente=lambda imponibile, giorni_lavorati=365, tempo_determinato=False: Decimal("100"),
        trattamento_integrativo=lambda imponibile, irpef_lorda, detrazione, giorni_lavorati=365: (
            Decimal("50") if irpef_lorda >= detrazione else Decimal(0)
        ),
        # Numeri tondi, condizionati a imponibile > 0 (a differenza di
        # detrazione_lavoro_dipendente sopra) perché sono benefici che
        # si SOMMANO al netto senza floor protettivo: se fossero
        # incondizionati, RAL=0 produrrebbe un netto positivo e
        # romperebbe l'invariante testata in TestRALZero.
        somma_integrativa_cuneo=lambda imponibile, giorni_lavorati=365: Decimal("20") if imponibile > Decimal(0) else Decimal(0),
        ulteriore_detrazione_cuneo=lambda imponibile, giorni_lavorati=365: Decimal("30") if imponibile > Decimal(0) else Decimal(0),
    )
