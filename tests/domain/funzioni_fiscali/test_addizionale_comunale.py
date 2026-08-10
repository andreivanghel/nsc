from decimal import Decimal

from inc_tax_sim.domain.value_objects.fiscal_regime import (
    _calcola_addizionale_comunale as calcola_add_comunale,
)


class TestSogliaSecca:
    """A differenza di IRPEF e addizionale regionale, l'addizionale
    comunale è a soglia secca: sopra soglia, l'aliquota si applica
    all'INTERO imponibile, non solo alla parte eccedente."""

    def test_sotto_soglia_esente(self):
        assert calcola_add_comunale(Decimal(1000), Decimal(2000), Decimal("0.1")) == Decimal(0)

    def test_esattamente_alla_soglia_ancora_esente(self):
        # boundary inclusivo: <= soglia -> zero
        assert calcola_add_comunale(Decimal(2000), Decimal(2000), Decimal("0.1")) == Decimal(0)

    def test_appena_sopra_soglia_tassa_intero_imponibile(self):
        # non solo l'eccedenza (1) ma l'intero imponibile (2001)
        assert calcola_add_comunale(Decimal(2001), Decimal(2000), Decimal("0.1")) == Decimal("200.1")

    def test_ben_sopra_soglia(self):
        assert calcola_add_comunale(Decimal(5000), Decimal(2000), Decimal("0.1")) == Decimal("500.0")


class TestWiringRegimeMilano2026:
    """Cross-check contro i dati reali del regime, non solo la logica astratta."""

    def test_soglia_esenzione_milano_23000(self):
        from inc_tax_sim.domain.value_objects.fiscal_regime import REGIME_2026_MILANO
        assert REGIME_2026_MILANO.addizionale_comunale(Decimal(23000)) == Decimal(0)

    def test_appena_sopra_soglia_milano(self):
        from inc_tax_sim.domain.value_objects.fiscal_regime import REGIME_2026_MILANO
        # 23001 * 0.008 = 184.008
        assert REGIME_2026_MILANO.addizionale_comunale(Decimal(23001)) == Decimal("184.008")
