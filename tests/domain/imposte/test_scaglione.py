from decimal import Decimal

import pytest

from inc_tax_sim.domain.value_objects.tax import Imposta, Scaglione


class TestValidazioneScaglioneSingolo:
    """Copertura mancante: le invarianti di Scaglione stesso, non ancora
    testate in test_imposta.py (quello copre Imposta come aggregato)."""

    def test_soglia_min_negativa_solleva_errore(self):
        with pytest.raises(ValueError, match="non può essere negativo"):
            Scaglione(Decimal(-1), None, Decimal("0.1"))

    def test_soglia_max_minore_uguale_soglia_min_solleva_errore(self):
        with pytest.raises(ValueError, match="maggiore di soglia_min"):
            Scaglione(Decimal(100), Decimal(100), Decimal("0.1"))

    def test_aliquota_negativa_solleva_errore(self):
        with pytest.raises(ValueError, match="compreso tra 0 e 1"):
            Scaglione(Decimal(0), None, Decimal("-0.1"))

    def test_aliquota_sopra_uno_solleva_errore(self):
        with pytest.raises(ValueError, match="compreso tra 0 e 1"):
            Scaglione(Decimal(0), None, Decimal("1.1"))

    def test_aliquota_zero_e_uno_sono_valide_ai_bordi(self):
        Scaglione(Decimal(0), Decimal(100), Decimal("0"))
        Scaglione(Decimal(100), None, Decimal("1"))


class TestValidazioneImpostaAggregato:
    def test_imposta_senza_scaglioni_solleva_errore(self):
        with pytest.raises(ValueError, match="Almeno uno scaglione richiesto"):
            Imposta(nome="x", scaglioni=())

    def test_scaglione_illimitato_non_ultimo_solleva_errore(self):
        # un solo scaglione aperto, ma con soglia_min piu' bassa di un
        # altro scaglione chiuso -> deve fallire sul controllo "deve
        # essere il piu' alto", non su gap/overlap
        with pytest.raises(ValueError, match="deve essere quello con soglia_min più alta"):
            Imposta(
                nome="x",
                scaglioni=(
                    Scaglione(Decimal(0), None, Decimal("0.1")),
                    Scaglione(Decimal(50), Decimal(100), Decimal("0.2")),
                ),
            )
