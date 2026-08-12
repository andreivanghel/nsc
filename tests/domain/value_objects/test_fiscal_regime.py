from decimal import Decimal

from inc_tax_sim.domain.value_objects.fiscal_regime import REGIME_2026_MILANO


class TestCostruzioneRegime:
    """Il fatto stesso che questo modulo si importi senza errori copre il
    bug di naming risolto (kwarg mismatch in RegimeFiscale). Questi test
    verificano che il wiring interno sia sensato, non le aliquote in sé
    (quelle sono coperte da tests/domain/funzioni_fiscali/ e da
    tests/scenari/)."""

    def test_anno_comune_regione(self):
        assert REGIME_2026_MILANO.anno == 2026
        assert REGIME_2026_MILANO.comune == "Milano"
        assert REGIME_2026_MILANO.regione == "Lombardia"

    def test_inps_flat(self):
        assert REGIME_2026_MILANO.inps.calculate_tax(Decimal(10000)) == Decimal("919.0")

    def test_irpef_primo_scaglione(self):
        assert REGIME_2026_MILANO.irpef.calculate_tax(Decimal(20000)) == Decimal("4600.00")

    def test_addizionale_regionale_e_marginale_a_scaglioni(self):
        # confermato: la regionale Lombardia è progressiva come IRPEF,
        # NON a soglia secca come la comunale — 10.000 ricade tutto nel
        # primo scaglione (0-15.000 @ 1.23%)
        assert REGIME_2026_MILANO.addizionale_regionale.calculate_tax(Decimal(10000)) == Decimal("123.0")

    def test_addizionale_regionale_a_cavallo_di_due_scaglioni(self):
        # 20.000: 15.000*1.23% + 5.000*1.58% = 184.5 + 79.0 = 263.5
        atteso = Decimal(15000) * Decimal("0.0123") + Decimal(5000) * Decimal("0.0158")
        assert REGIME_2026_MILANO.addizionale_regionale.calculate_tax(Decimal(20000)) == atteso

    def test_addizionale_regionale_ultimo_scaglione_1_73_non_1_43(self):
        # Regressione: l'ultimo scaglione (50.000+) era erroneamente
        # 1,43% (aliquota che DECRESCE rispetto al 1,72% precedente,
        # contraddicendo la progressività). Confermato 1,73% da fonte
        # primaria (Regione Lombardia, art. 72 l.r. 10/2003).
        # 55.000: 15.000*1,23% + 13.000*1,58% + 22.000*1,72% + 5.000*1,73%
        atteso = (
            Decimal(15000) * Decimal("0.0123")
            + Decimal(13000) * Decimal("0.0158")
            + Decimal(22000) * Decimal("0.0172")
            + Decimal(5000) * Decimal("0.0173")
        )
        assert REGIME_2026_MILANO.addizionale_regionale.calculate_tax(Decimal(55000)) == atteso

    def test_addizionale_comunale_e_callable_a_soglia_secca(self):
        assert REGIME_2026_MILANO.addizionale_comunale(Decimal(23000)) == Decimal(0)
        assert REGIME_2026_MILANO.addizionale_comunale(Decimal(23001)) == Decimal("184.008")

    def test_detrazione_lavoro_dipendente_callable(self):
        assert REGIME_2026_MILANO.detrazione_lavoro_dipendente(Decimal(10000)) == Decimal("1955")

    def test_trattamento_integrativo_callable(self):
        irpef_lorda = REGIME_2026_MILANO.irpef.calculate_tax(Decimal(10000))
        detrazione = REGIME_2026_MILANO.detrazione_lavoro_dipendente(Decimal(10000))
        assert REGIME_2026_MILANO.trattamento_integrativo(Decimal(10000), irpef_lorda, detrazione) == Decimal("1200")

    def test_somma_integrativa_cuneo_callable(self):
        # 10.000 -> fascia media (8.500-15.000) -> 5,3%
        assert REGIME_2026_MILANO.somma_integrativa_cuneo(Decimal(10000)) == Decimal(10000) * Decimal("0.053")

    def test_ulteriore_detrazione_cuneo_callable(self):
        # 25.000 -> fascia flat (20.000-32.000) -> 1.000 fissi
        assert REGIME_2026_MILANO.ulteriore_detrazione_cuneo(Decimal(25000)) == Decimal("1000")
