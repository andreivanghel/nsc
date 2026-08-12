from decimal import Decimal

from inc_tax_sim.domain.value_objects.fiscal_regime import (
    _calcola_somma_integrativa_cuneo_2026 as calcola_somma_integrativa,
)


class TestTreFasce:
    """Boundary test sulle 3 fasce di percentuale, anno intero (365gg)."""

    def test_fascia_bassa_al_confine(self):
        # esattamente 8.500: ancora fascia bassa (branch è > 8500, non >=)
        assert calcola_somma_integrativa(Decimal(8500)) == Decimal(8500) * Decimal("0.071")

    def test_appena_sopra_fascia_bassa(self):
        assert calcola_somma_integrativa(Decimal(8501)) == Decimal(8501) * Decimal("0.053")

    def test_fascia_media_al_confine(self):
        # esattamente 15.000: ancora fascia media (branch è > 15000, non >=)
        assert calcola_somma_integrativa(Decimal(15000)) == Decimal(15000) * Decimal("0.053")

    def test_appena_sopra_fascia_media(self):
        assert calcola_somma_integrativa(Decimal(15001)) == Decimal(15001) * Decimal("0.048")

    def test_fascia_alta_al_confine_20000(self):
        assert calcola_somma_integrativa(Decimal(20000)) == Decimal(20000) * Decimal("0.048")

    def test_appena_sopra_20000_salto_al_meccanismo_della_detrazione(self):
        # NOTA: salto vero della normativa (a 20.001 subentra
        # ulteriore_detrazione_cuneo_2026, non un proseguimento di
        # questa funzione), non un bug — stesso pattern del confine
        # 15.000 in detrazione_lavoro_dipendente.
        assert calcola_somma_integrativa(Decimal(20001)) == Decimal(0)

    def test_ben_oltre_20000_zero(self):
        assert calcola_somma_integrativa(Decimal(50000)) == Decimal(0)

    def test_reddito_zero(self):
        assert calcola_somma_integrativa(Decimal(0)) == Decimal(0)


class TestRapportoGiorniLavorati:
    def test_anno_intero_nessun_effetto(self):
        atteso = Decimal(10000) * Decimal("0.053")
        assert calcola_somma_integrativa(Decimal(10000), giorni_lavorati=365) == atteso

    def test_proration_giorni_parziali(self):
        # 73/365 = 0.2 esatto -> teorica(530) * 0.2 = 106.0
        assert calcola_somma_integrativa(Decimal(10000), giorni_lavorati=73) == Decimal("106.0")