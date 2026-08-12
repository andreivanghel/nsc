from decimal import Decimal

from inc_tax_sim.domain.services.net_salary_calculator import CalcolaNettoService


class TestPipelineStandard:
    """RAL=2000 con regime_test: inps=200, imponibile=1800,
    irpef_lorda=520 (200 primo scaglione + 320 secondo).

    Detrazioni (riducono irpef_lorda, floor a zero):
    detrazione_lav_dip=100, ulteriore_detrazione_cuneo=30 -> irpef_netta
    = max(520-100-30, 0) = 390.

    Benefici (si sommano al netto, non toccano irpef_netta):
    trattamento=50 (capiente: 520>=100), somma_integrativa_cuneo=20.

    add_reg=1800*0.05=90, add_com=1800*0.02=36.
    netto_annuo = 2000 - (200+390+90+36) + (50+20) = 1354.
    """

    def test_netto_annuo(self, regime_test):
        service = CalcolaNettoService(regime_test)
        risultato = service.calcola(Decimal(2000), mensilita=13)
        assert risultato.netto_annuo == Decimal("1354")

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
        assert importi["IRPEF netta"] == Decimal("390")
        assert importi["Addizionale regionale"] == Decimal("90.0")
        assert importi["Addizionale comunale"] == Decimal("36.0")

    def test_benefici_nomi_e_importi(self, regime_test):
        service = CalcolaNettoService(regime_test)
        risultato = service.calcola(Decimal(2000), mensilita=13)
        importi = {v.nome: v.importo for v in risultato.benefici}
        assert importi == {
            "Trattamento integrativo": Decimal("50"),
            "Somma integrativa cuneo fiscale": Decimal("20"),
        }

    def test_detrazioni_applicate_esposte_e_non_doppio_contate(self, regime_test):
        """Le detrazioni sono già dentro 'IRPEF netta': qui sono solo
        informative, sommarle di nuovo al netto sarebbe un doppio conteggio."""
        service = CalcolaNettoService(regime_test)
        risultato = service.calcola(Decimal(2000), mensilita=13)
        importi = {v.nome: v.importo for v in risultato.detrazioni_applicate}
        assert importi == {
            "Detrazione lavoro dipendente": Decimal("100"),
            "Ulteriore detrazione cuneo fiscale": Decimal("30"),
        }


class TestTrattamentoIntegrativoNonPersoOltreLIrpef:
    """Regressione mirata sul bug corretto: quando (irpef_lorda -
    detrazioni) è INFERIORE al trattamento integrativo spettante, la
    parte eccedente va comunque accreditata per intero, non persa in un
    unico floor a zero insieme alle detrazioni."""

    def test_trattamento_pieno_anche_se_supera_irpef_residua(self, regime_test):
        # RAL=1050 -> inps=105, imponibile=945 (< 1000, un solo scaglione IRPEF)
        # irpef_lorda = 945*0.20 = 189.0
        # detrazione=100, ulteriore_detrazione_cuneo=30 -> irpef_netta = max(189-100-30,0) = 59.0
        # capiente: irpef_lorda(189) >= detrazione(100) -> trattamento pieno = 50
        # (59.0 > 50, quindi qui la differenza col vecchio comportamento
        # non si vede sul totale ma la si vede sulla riga IRPEF netta
        # esposta: 59.0, non 9.0 come sarebbe stato sottraendo anche il
        # trattamento da irpef_lorda)
        service = CalcolaNettoService(regime_test)
        risultato = service.calcola(Decimal(1050), mensilita=13)
        importi_trattenute = {v.nome: v.importo for v in risultato.trattenute}
        importi_benefici = {v.nome: v.importo for v in risultato.benefici}
        assert importi_trattenute["IRPEF netta"] == Decimal("59.0")
        assert importi_benefici["Trattamento integrativo"] == Decimal("50")


class TestNoTaxArea:
    """RAL=300 (imponibile 270, sotto il primo scaglione IRPEF test):
    irpef_lorda=54, detrazione=100, ulteriore_detrazione_cuneo=30 ->
    irpef_netta=max(54-100-30,0)=0 -> guard: addizionale regionale deve
    azzerarsi anch'essa. Addizionale comunale già zero per soglia propria.
    Non capiente (irpef_lorda 54 < detrazione 100) -> trattamento=0, ma
    somma_integrativa_cuneo=20 comunque (nessun requisito di capienza).
    netto_annuo = 300 - (30 inps + 0 + 0 + 0) + (0 + 20) = 290."""

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

    def test_somma_integrativa_non_richiede_capienza(self, regime_test):
        # a differenza del trattamento integrativo, spetta anche se
        # irpef_lorda < detrazione
        service = CalcolaNettoService(regime_test)
        risultato = service.calcola(Decimal(300))
        importi = {v.nome: v.importo for v in risultato.benefici}
        assert importi["Trattamento integrativo"] == Decimal(0)
        assert importi["Somma integrativa cuneo fiscale"] == Decimal("20")

    def test_netto_annuo_no_tax_area(self, regime_test):
        service = CalcolaNettoService(regime_test)
        risultato = service.calcola(Decimal(300))
        assert risultato.netto_annuo == Decimal("290")


class TestRALZero:
    def test_ral_zero_non_esplode(self, regime_test):
        service = CalcolaNettoService(regime_test)
        risultato = service.calcola(Decimal(0))
        assert risultato.netto_annuo == Decimal(0)
        assert all(v.importo == Decimal(0) for v in risultato.trattenute)
        assert all(v.importo == Decimal(0) for v in risultato.benefici)