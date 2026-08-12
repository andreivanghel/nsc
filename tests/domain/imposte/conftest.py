from decimal import Decimal

import pytest

from inc_tax_sim.domain.value_objects.tax import Imposta, Scaglione


@pytest.fixture
def scaglioni_tre_fasce() -> tuple[Scaglione, ...]:
    """0-100 al 10%, 100-200 al 20%, 200+ al 30%. Numeri tondi
    per isolare il test dell'algoritmo dai dati fiscali reali."""
    return (
        Scaglione(Decimal(0), Decimal(100), Decimal("0.10")),
        Scaglione(Decimal(100), Decimal(200), Decimal("0.20")),
        Scaglione(Decimal(200), None, Decimal("0.30")),
    )


@pytest.fixture
def imposta_progressiva(scaglioni_tre_fasce) -> Imposta:  # type: ignore[no-untyped-def]
    return Imposta(nome="test_progressiva", scaglioni=scaglioni_tre_fasce)


@pytest.fixture
def imposta_flat() -> Imposta:
    """Caso degenere: scaglione singolo aperto, come INPS 9,19%."""
    return Imposta(
        nome="test_flat",
        scaglioni=(Scaglione(Decimal(0), None, Decimal("0.0919")),),
    )
