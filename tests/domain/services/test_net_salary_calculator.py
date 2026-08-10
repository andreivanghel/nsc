from decimal import Decimal

from inc_tax_sim.domain.services.net_salary_calculator import CalcolaNettoService


class TestPipelineStandard:
    """RAL=2000 con regime_test: inps=200, imponibile=1800,
    irpef_lorda=520 (200 primo scaglione + 320 secondo), detrazione=100,
    trattamento=50 (capiente: 520>=100), irpef_netta=370,
    add_reg=1800*0.05=90, add_com=1800*0.02=36.
    netto_annuo = 2000 - (200+370+90+36) = 1304."""

    def test_netto_annuo(self, regime_test):
        service = CalcolaNettoService(regime_test)
        risultato = service.calcola(Decimal(2000), mensilita=13)
        assert risultato.netto_annuo == Decimal("1304")

    def test_netto_mensile_coerente_con_annuo(self, regime_test):
        service = CalcolaNettoService(regime_test)
        risultato = service.calcola(Decimal(2000), mensilita=13)
        assert risultato.netto_mensile == risultato.netto_annuo / Decimal(13)

    def test_breakdown_completo_nomi_e_ordine(self, regime_test):
        service = CalcolaNettoService(regime_test)
        risultato = service.calcola(Decimal(2000), mensilita=13)
        nomi = [v.nome for v in risultato.trattenute]
        assert nomi == ["Contributi INPS", "IRPEF netta", "Addizionale regionale", "Addizionale comunale"]

    def test_breakdown_importi(self, regime_test):
        service = CalcolaNettoService(regime_test)
        risultato = service.calcola(Decimal(2000), mensilita=13)
        importi = {v.nome: v.importo for v in risultato.trattenute}
        assert importi["Contributi INPS"] == Decimal("200")
        assert importi["IRPEF netta"] == Decimal("370")
        assert importi["Addizionale regionale"] == Decimal("90.0")
        assert importi["Addizionale comunale"] == Decimal("36.0")


class TestNoTaxArea:
    """RAL=300 (imponibile 270, sotto il primo scaglione IRPEF test):
    irpef_lorda=54, detrazione=100 -> non capiente -> trattamento=0,
    irpef_netta=max(54-100-0,0)=0 -> guard: addizionale regionale
    deve azzerarsi anch'essa. Addizionale comunale già zero per soglia propria."""

    def test_irpef_netta_azzerata(self, regime_test):
        service = CalcolaNettoService(regime_test)
        risultato = service.calcola(Decimal(300))
        importi = {v.nome: v.importo for v in risultato.trattenute}
        assert importi["IRPEF netta"] == Decimal(0)

    def test_addizionale_regionale_azzerata_dal_guard_no_tax_area(self, regime_test):
        # questo è il test che verifica ESPLICITAMENTE il guard
        # "solo se irpef_netta > 0" nel service — senza, questo fallirebbe
        service = CalcolaNettoService(regime_test)
        risultato = service.calcola(Decimal(300))
        importi = {v.nome: v.importo for v in risultato.trattenute}
        assert importi["Addizionale regionale"] == Decimal(0)

    def test_netto_annuo_no_tax_area(self, regime_test):
        service = CalcolaNettoService(regime_test)
        risultato = service.calcola(Decimal(300))
        # netto = 300 - (30 inps + 0 + 0 + 0) = 270
        assert risultato.netto_annuo == Decimal("270")


class TestRALZero:
    def test_ral_zero_non_esplode(self, regime_test):
        service = CalcolaNettoService(regime_test)
        risultato = service.calcola(Decimal(0))
        assert risultato.netto_annuo == Decimal(0)
        assert all(v.importo == Decimal(0) for v in risultato.trattenute)
