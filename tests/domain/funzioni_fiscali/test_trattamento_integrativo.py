from decimal import Decimal

from inc_tax_sim.domain.value_objects.fiscal_regime import (
    calcola_trattamento_integrativo_2026 as calcola_ti,
)


class TestCapienza:
    """Reddito <= 15.000: spetta per intero (1.200/anno) SOLO se
    irpef_lorda >= detrazione_lavoro_dipendente."""

    def test_capiente_spetta_per_intero(self):
        # irpef_lorda (2300) >= detrazione (1955) -> capiente
        assert calcola_ti(Decimal(10000), Decimal(2300), Decimal(1955)) == Decimal("1200")

    def test_non_capiente_niente_bonus(self):
        # caso limite vicino alla no-tax-area: detrazione teorica supera
        # l'irpef lorda -> non capiente -> zero, anche se reddito è basso
        assert calcola_ti(Decimal(7000), Decimal(1000), Decimal(1955)) == Decimal(0)

    def test_boundary_uguaglianza_conta_come_capiente(self):
        # irpef_lorda == detrazione esattamente: il confronto è >=, quindi capiente
        assert calcola_ti(Decimal(10000), Decimal(1955), Decimal(1955)) == Decimal("1200")

    def test_boundary_di_un_centesimo_sotto_non_capiente(self):
        assert calcola_ti(Decimal(10000), Decimal("1954.99"), Decimal(1955)) == Decimal(0)


class TestSogliaReddito:
    def test_esattamente_15000_ancora_valutato(self):
        # a 15.000 esatti si applica ancora la logica di capienza (branch è > 15000)
        assert calcola_ti(Decimal(15000), Decimal(3450), Decimal(1955)) == Decimal("1200")

    def test_sopra_15000_semplificazione_zero(self):
        # semplificazione dichiarata: 15.001-28.000 non implementato, ritorna 0
        # indipendentemente da irpef_lorda/detrazione
        assert calcola_ti(Decimal(15001), Decimal(999999), Decimal(0)) == Decimal(0)

    def test_ben_oltre_28000_zero(self):
        assert calcola_ti(Decimal(40000), Decimal(5000), Decimal(500)) == Decimal(0)


class TestProrationGiorniLavorati:
    def test_anno_intero_massimo_pieno(self):
        assert calcola_ti(Decimal(10000), Decimal(2300), Decimal(1955), giorni_lavorati=365) == Decimal("1200")

    def test_proration_giorni_parziali(self):
        # 219/365 = 0.6 esatto -> 1200*0.6 = 720
        assert calcola_ti(Decimal(10000), Decimal(2300), Decimal(1955), giorni_lavorati=219) == Decimal("720.0")

    def test_non_capiente_ignora_giorni_lavorati(self):
        # se non c'è capienza, resta zero a prescindere dai giorni
        assert calcola_ti(Decimal(7000), Decimal(1000), Decimal(1955), giorni_lavorati=365) == Decimal(0)
