from decimal import Decimal

import pytest

from inc_tax_sim.domain.services.net_salary_calculator import CalcolaNettoService
from inc_tax_sim.domain.value_objects.fiscal_regime import REGIME_2026_MILANO

from .casi_netto import CASI_NETTO


@pytest.fixture
def service() -> CalcolaNettoService:
    return CalcolaNettoService(REGIME_2026_MILANO)


@pytest.mark.parametrize(
    "caso",
    CASI_NETTO,
    ids=[c.descrizione for c in CASI_NETTO] or None,
)
def test_ral_a_netto_annuo(service, caso):
    risultato = service.calcola(caso.ral, mensilita=caso.mensilita)
    assert risultato.netto_annuo == caso.netto_annuo_atteso


def test_avviso_se_nessun_caso_ancora_inserito():
    if not CASI_NETTO:
        pytest.skip(
            "Nessun caso in tests/scenari/casi_netto.py"
        )
