from decimal import Decimal

from inc_tax_sim.domain.dto.net_salary import (
    RisultatoNetto,
    VoceBeneficio,
    VoceDetrazione,
    VoceTrattenuta,
)
from inc_tax_sim.domain.value_objects.fiscal_regime import RegimeFiscale


class CalcolaNettoService:
    def __init__(self, regime: RegimeFiscale):
        self._regime = regime

    def calcola(self, ral: Decimal, mensilita: int = 13) -> RisultatoNetto:
        trattenute: list[VoceTrattenuta] = []
        benefici: list[VoceBeneficio] = []
        detrazioni_applicate: list[VoceDetrazione] = []

        inps = self._regime.inps.calculate_tax(ral)
        trattenute.append(VoceTrattenuta("Contributi INPS", inps))
        imponibile = ral - inps

        irpef_lorda = self._regime.irpef.calculate_tax(imponibile)

        detrazione_lav_dip = self._regime.detrazione_lavoro_dipendente(imponibile)
        ulteriore_detrazione = self._regime.ulteriore_detrazione_cuneo(imponibile)
        detrazioni_applicate.append(VoceDetrazione("Detrazione lavoro dipendente", detrazione_lav_dip))
        detrazioni_applicate.append(
            VoceDetrazione("Ulteriore detrazione cuneo fiscale", ulteriore_detrazione)
        )

        # Le detrazioni riducono l'IRPEF lorda ma non possono renderla
        # negativa: l'eventuale eccedenza non utilizzata è persa, non
        # erogata come somma — a differenza di trattamento integrativo
        # e somma integrativa cuneo fiscale, gestiti sotto come
        # benefici a parte che si SOMMANO al netto per intero (se
        # spettanti), indipendentemente da quanta IRPEF resta da pagare.
        irpef_netta = max(irpef_lorda - detrazione_lav_dip - ulteriore_detrazione, Decimal(0))
        trattenute.append(VoceTrattenuta("IRPEF netta", irpef_netta))

        add_reg = (
            self._regime.addizionale_regionale.calculate_tax(imponibile)
            if irpef_netta > Decimal(0)
            else Decimal(0)
        ) # solo se irpef al netto delle detrazioni è > 0, altrimenti addizionale regionale non si paga
        trattenute.append(VoceTrattenuta("Addizionale regionale", add_reg))

        add_com = self._regime.addizionale_comunale(imponibile)
        trattenute.append(VoceTrattenuta("Addizionale comunale", add_com))

        trattamento = self._regime.trattamento_integrativo(imponibile, irpef_lorda, detrazione_lav_dip)
        somma_integrativa = self._regime.somma_integrativa_cuneo(imponibile)
        benefici.append(VoceBeneficio("Trattamento integrativo", trattamento))
        benefici.append(VoceBeneficio("Somma integrativa cuneo fiscale", somma_integrativa))

        netto_annuo = (
            ral
            - sum((v.importo for v in trattenute), Decimal(0))
            + sum((v.importo for v in benefici), Decimal(0))
        )
        return RisultatoNetto(
            ral=ral,
            netto_annuo=netto_annuo,
            netto_mensile=netto_annuo / mensilita,
            trattenute=tuple(trattenute),
            benefici=tuple(benefici),
            detrazioni_applicate=tuple(detrazioni_applicate),
        )