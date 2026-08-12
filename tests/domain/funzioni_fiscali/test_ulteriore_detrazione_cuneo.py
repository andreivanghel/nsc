from decimal import Decimal

from inc_tax_sim.domain.value_objects.fiscal_regime import (
    _calcola_ulteriore_detrazione_cuneo_2026 as calcola_ulteriore_detrazione,
)


class TestFasce:
    """Boundary test sulle fasce (nessuna detrazione / flat / decrescente
    / nessuna detrazione), anno intero lavorato (365gg)."""

    def test_a_20000_ancora_zero(self):
        # esattamente 20.000: non ancora eleggibile (branch è > 20000)
        assert calcola_ulteriore_detrazione(Decimal(20000)) == Decimal(0)

    def test_appena_sopra_20000_flat_1000(self):
        assert calcola_ulteriore_detrazione(Decimal(20001)) == Decimal("1000")

    def test_a_32000_ancora_flat_1000(self):
        assert calcola_ulteriore_detrazione(Decimal(32000)) == Decimal("1000")

    def test_appena_sopra_32000_inizia_a_decrescere(self):
        # 1.000 * (40.000-32.001)/8.000 = 1.000 * 7.999/8.000 = 999.875
        assert calcola_ulteriore_detrazione(Decimal(32001)) == Decimal("999.875")

    def test_midpoint_decrescita(self):
        # 36.000 è il midpoint esatto (32.000-40.000): frazione 0.5 -> 500
        assert calcola_ulteriore_detrazione(Decimal(36000)) == Decimal("500.0")

    def test_a_40000_azzerata(self):
        assert calcola_ulteriore_detrazione(Decimal(40000)) == Decimal("0.0")

    def test_sopra_40000_zero(self):
        assert calcola_ulteriore_detrazione(Decimal(45000)) == Decimal(0)

    def test_reddito_zero(self):
        assert calcola_ulteriore_detrazione(Decimal(0)) == Decimal(0)


class TestRapportoGiorniLavorati:
    def test_anno_intero_nessun_effetto(self):
        assert calcola_ulteriore_detrazione(Decimal(25000), giorni_lavorati=365) == Decimal("1000")

    def test_proration_giorni_parziali(self):
        # 219/365 = 0.6 esatto -> 1.000 * 0.6 = 600
        assert calcola_ulteriore_detrazione(Decimal(25000), giorni_lavorati=219) == Decimal("600.0")