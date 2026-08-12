from decimal import Decimal

from inc_tax_sim.domain.value_objects.fiscal_regime import (
    _calcola_detrazione_lavoro_dipendente_2026 as calcola_detrazione,
)


class TestQuattroFasce:
    """Boundary test sulle 4 fasce di reddito, anno intero lavorato (365gg)."""

    def test_fascia_bassa_flat(self):
        # reddito <= 15.000: valore fisso 1.955, indipendente dal reddito esatto
        assert calcola_detrazione(Decimal(0)) == Decimal("1955")
        assert calcola_detrazione(Decimal(10000)) == Decimal("1955")

    def test_boundary_esatto_15000_ancora_fascia_bassa(self):
        # a 15.000 esatti si è ANCORA nella fascia flat (branch è > 15000, non >=)
        assert calcola_detrazione(Decimal(15000)) == Decimal("1955")

    def test_appena_sopra_15000_salto_reale_non_bug(self):
        # NOTA: questo è un salto vero della normativa (confermato su fonte
        # primaria), non un bug — la detrazione teorica qui supera 1.955,
        # ma in pratica non può mai superare l'IRPEF lorda dovuta.
        # 1.910 + 1.190*(28000-15001)/13000
        #
        # Confronto arrotondato al centesimo: la funzione fa un round-trip
        # *giorni_lavorati/365 anche con giorni_lavorati=365 (default), e su
        # un decimale periodico questo introduce rumore oltre la 25a cifra
        # decimale — irrilevante in euro, ma rompe un confronto == esatto.
        # Vedi il commento in fondo al file: vale la pena decidere una
        # policy di arrotondamento esplicita nel codice di produzione.
        atteso = Decimal("1910") + Decimal("1190") * (Decimal(28000) - Decimal(15001)) / Decimal(13000)
        risultato = calcola_detrazione(Decimal(15001))
        assert risultato.quantize(Decimal("0.01")) == atteso.quantize(Decimal("0.01"))
        assert risultato > Decimal("1955")  # il salto, documentato

    def test_fascia_media_midpoint(self):
        # reddito=21.500 è il midpoint esatto (15.000-28.000): frazione = 0.5
        # 1.910 + 1.190*0.5 = 2.505
        assert calcola_detrazione(Decimal(21500)) == Decimal("2505.0")

    def test_boundary_28000_continuita_tra_fascia_media_e_alta(self):
        # a 28.000 esatti entrambe le formule (fascia media e fascia alta)
        # devono dare lo stesso valore: 1.910 — continuità qui, a differenza del boundary 15.000
        assert calcola_detrazione(Decimal(28000)) == Decimal("1910")

    def test_fascia_alta_midpoint(self):
        # reddito=39.000 è il midpoint esatto (28.000-50.000): frazione = 0.5
        # 1.910*0.5 = 955
        assert calcola_detrazione(Decimal(39000)) == Decimal("955.0")

    def test_boundary_50000_azzeramento(self):
        assert calcola_detrazione(Decimal(50000)) == Decimal("0")

    def test_sopra_50000_zero(self):
        assert calcola_detrazione(Decimal(60000)) == Decimal(0)


class TestRapportoGiorniLavorati:
    """Proration ai giorni lavorati nell'anno, solo fascia bassa (<=15.000)."""

    def test_anno_intero_nessun_effetto(self):
        assert calcola_detrazione(Decimal(10000), giorni_lavorati=365) == Decimal("1955")

    def test_proration_sopra_il_minimo_garantito(self):
        # 219/365 = 0.6 esatto -> 1955*0.6 = 1173, sopra il floor di 690
        assert calcola_detrazione(Decimal(10000), giorni_lavorati=219) == Decimal("1173.0")

    def test_proration_sotto_il_minimo_scatta_il_floor_indeterminato(self):
        # 73/365 = 0.2 esatto -> 1955*0.2 = 391, sotto il floor di 690 -> vince il floor
        assert calcola_detrazione(Decimal(10000), giorni_lavorati=73) == Decimal("690")

    def test_proration_sotto_il_minimo_scatta_il_floor_determinato(self):
        # stesso caso, ma tempo determinato -> floor 1380 invece di 690
        assert calcola_detrazione(Decimal(10000), giorni_lavorati=73, tempo_determinato=True) == Decimal("1380")

    def test_floor_non_si_applica_fuori_dalla_fascia_bassa(self):
        # ATTENZIONE: comportamento attuale del codice, da verificare — il
        # floor (690/1380) è applicato SOLO se reddito<=15000. Con reddito
        # sopra 15.000 e pochi giorni lavorati, il codice attuale NON
        # applica alcun floor. Verifica se è corretto rispetto alla norma
        # reale prima di considerare questo test come "assodato".
        risultato = calcola_detrazione(Decimal(20000), giorni_lavorati=10)
        assert risultato < Decimal("690")  # documenta il comportamento attuale
