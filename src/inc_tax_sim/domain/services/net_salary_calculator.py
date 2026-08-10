from decimal import Decimal

from inc_tax_sim.domain.dto.net_salary import RisultatoNetto, VoceTrattenuta
from inc_tax_sim.domain.value_objects.fiscal_regime import RegimeFiscale


class CalcolaNettoService:
    def __init__(self, regime: RegimeFiscale):
        self._regime = regime

    def calcola(self, ral: Decimal, mensilita: int = 13) -> RisultatoNetto:
        trattenute: list[VoceTrattenuta] = []

        inps = self._regime.inps.calculate_tax(ral)
        trattenute.append(VoceTrattenuta("Contributi INPS", inps))
        imponibile = ral - inps

        irpef_lorda = self._regime.irpef.calculate_tax(imponibile)
        detrazione = self._regime.detrazione_lavoro_dipendente(imponibile)
        trattamento = self._regime.trattamento_integrativo(imponibile, irpef_lorda, detrazione)
        irpef_netta = max(irpef_lorda - detrazione - trattamento, Decimal(0))
        trattenute.append(VoceTrattenuta("IRPEF netta", irpef_netta))

        add_reg = (
            self._regime.addizionale_regionale.calculate_tax(imponibile)
            if irpef_netta > Decimal(0)
            else Decimal(0)
        ) # solo se irpef al netto delle detrazioni è > 0, altrimenti addizionale regionale non si paga
        trattenute.append(VoceTrattenuta("Addizionale regionale", add_reg))

        add_com = self._regime.addizionale_comunale(imponibile)
        trattenute.append(VoceTrattenuta("Addizionale comunale", add_com))

        netto_annuo = ral - sum((v.importo for v in trattenute), Decimal(0))
        return RisultatoNetto(
            ral=ral, netto_annuo=netto_annuo,
            netto_mensile=netto_annuo / mensilita,
            trattenute=tuple(trattenute),
        )


