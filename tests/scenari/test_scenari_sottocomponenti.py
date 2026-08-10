import pytest

from inc_tax_sim.domain.value_objects.fiscal_regime import REGIME_2026_MILANO

from .casi_sottocomponenti import (
    CASI_ADDIZIONALE_COMUNALE,
    CASI_ADDIZIONALE_REGIONALE,
    CASI_DETRAZIONE,
    CASI_INPS,
    CASI_IRPEF_LORDA,
    CASI_TRATTAMENTO_INTEGRATIVO,
)


@pytest.mark.parametrize("caso", CASI_INPS, ids=[c.descrizione for c in CASI_INPS] or None)
def test_inps(caso):
    assert REGIME_2026_MILANO.inps.calculate_tax(caso.ral) == caso.atteso


@pytest.mark.parametrize("caso", CASI_IRPEF_LORDA, ids=[c.descrizione for c in CASI_IRPEF_LORDA] or None)
def test_irpef_lorda(caso):
    assert REGIME_2026_MILANO.irpef.calculate_tax(caso.imponibile) == caso.atteso


@pytest.mark.parametrize(
    "caso", CASI_ADDIZIONALE_REGIONALE, ids=[c.descrizione for c in CASI_ADDIZIONALE_REGIONALE] or None
)
def test_addizionale_regionale(caso):
    assert REGIME_2026_MILANO.addizionale_regionale.calculate_tax(caso.imponibile) == caso.atteso


@pytest.mark.parametrize(
    "caso", CASI_ADDIZIONALE_COMUNALE, ids=[c.descrizione for c in CASI_ADDIZIONALE_COMUNALE] or None
)
def test_addizionale_comunale(caso):
    assert REGIME_2026_MILANO.addizionale_comunale(caso.imponibile) == caso.atteso


@pytest.mark.parametrize("caso", CASI_DETRAZIONE, ids=[c.descrizione for c in CASI_DETRAZIONE] or None)
def test_detrazione_lavoro_dipendente(caso):
    risultato = REGIME_2026_MILANO.detrazione_lavoro_dipendente(
        caso.imponibile, caso.giorni_lavorati, caso.tempo_determinato
    )
    assert risultato == caso.atteso


@pytest.mark.parametrize(
    "caso", CASI_TRATTAMENTO_INTEGRATIVO, ids=[c.descrizione for c in CASI_TRATTAMENTO_INTEGRATIVO] or None
)
def test_trattamento_integrativo(caso):
    risultato = REGIME_2026_MILANO.trattamento_integrativo(
        caso.imponibile, caso.irpef_lorda, caso.detrazione, caso.giorni_lavorati
    )
    assert risultato == caso.atteso
