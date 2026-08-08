from decimal import Decimal
import pytest
from inc_tax_sim.domain.value_objects.fiscal import Imposta, Scaglione


class TestCalculateTax:
    @pytest.mark.parametrize("imponibile, expected", [
        (Decimal(50), Decimal("5.00")),      # dentro il primo scaglione
        (Decimal(100), Decimal("10.00")),    # esattamente sul boundary
        (Decimal(150), Decimal("20.00")),    # a cavallo di due scaglioni: 10 + 50*0.20
        (Decimal(300), Decimal("60.00")),    # dentro l'ultimo scaglione aperto
        (Decimal(0), Decimal("0.00")),       # imponibile zero
    ])
    def test_calcolo_su_scaglioni_ordinati(self, imposta_progressiva, imponibile, expected):
        assert imposta_progressiva.calculate_tax(imponibile) == expected

    def test_ordine_input_non_conta(self, scaglioni_tre_fasce):
        """Costruendo l'imposta con scaglioni fuori ordine, il risultato deve essere identico."""
        mescolati = tuple(reversed(scaglioni_tre_fasce))
        imposta = Imposta(nome="mescolata", scaglioni=mescolati)
        assert imposta.calculate_tax(Decimal(150)) == Decimal("20.00")

    def test_caso_degenere_flat_come_inps(self, imposta_flat):
        assert imposta_flat.calculate_tax(Decimal(1000)) == Decimal("91.90")

    def test_imponibile_negativo_solleva_errore(self, imposta_progressiva):
        with pytest.raises(ValueError, match="cannot be negative"):
            imposta_progressiva.calculate_tax(Decimal(-1))


class TestValidazioneScaglioni:
    def test_due_scaglioni_illimitati_solleva_errore(self):
        with pytest.raises(ValueError, match="più di uno scaglione illimitato"):
            Imposta(nome="x", scaglioni=(
                Scaglione(Decimal(0), None, Decimal("0.1")),
                Scaglione(Decimal(50), None, Decimal("0.2")),
            ))

    def test_gap_tra_scaglioni_solleva_errore(self):
        with pytest.raises(ValueError, match="non contigui"):
            Imposta(nome="x", scaglioni=(
                Scaglione(Decimal(0), Decimal(100), Decimal("0.1")),
                Scaglione(Decimal(150), None, Decimal("0.2")),  # gap 100-150
            ))

    def test_overlap_tra_scaglioni_solleva_errore(self):
        with pytest.raises(ValueError, match="non contigui"):
            Imposta(nome="x", scaglioni=(
                Scaglione(Decimal(0), Decimal(150), Decimal("0.1")),
                Scaglione(Decimal(100), None, Decimal("0.2")),  # overlap 100-150
            ))

    def test_soglia_min_duplicata_solleva_errore(self):
        with pytest.raises(ValueError, match="stessa soglia_min"):
            Imposta(nome="x", scaglioni=(
                Scaglione(Decimal(0), Decimal(100), Decimal("0.1")),
                Scaglione(Decimal(0), None, Decimal("0.2")),
            ))