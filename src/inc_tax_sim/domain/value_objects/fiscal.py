from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Scaglione:
    soglia_min: Decimal
    soglia_max: Decimal | None  # None = ultimo scaglione, aperto
    aliquota: Decimal

    def __post_init__(self):
        if self.soglia_min < Decimal(0):
            raise ValueError("soglia_min non può essere negativo")
        if self.soglia_max is not None and self.soglia_max <= self.soglia_min:
            raise ValueError("soglia_max deve essere maggiore di soglia_min")
        if not (Decimal(0) <= self.aliquota <= Decimal(1)):
            raise ValueError("aliquota deve essere compreso tra 0 e 1")

@dataclass(frozen=True)
class Imposta:
    nome: str
    scaglioni: tuple[Scaglione, ...]

    # Validazione di coerenza degli scaglioni
    def __post_init__(self):
        if not self.scaglioni:
            raise ValueError("Almeno uno scaglione richiesto")

        # Il chiamante può passarli in qualsiasi ordine: normalizziamo qui,
        # una volta sola, così l'invariante interna è garantita da questo
        # punto in poi e calculate_tax non deve più preoccuparsene.
        scaglioni_ordinati = tuple(sorted(self.scaglioni, key=lambda s: s.soglia_min))
        object.__setattr__(self, "scaglioni", scaglioni_ordinati)

        soglie_min = [s.soglia_min for s in scaglioni_ordinati]
        if len(set(soglie_min)) != len(soglie_min):
            raise ValueError("Due scaglioni non possono avere la stessa soglia_min")

        aperti = [s for s in scaglioni_ordinati if s.soglia_max is None]
        if len(aperti) > 1:
            raise ValueError("Non può esserci più di uno scaglione illimitato (soglia_max=None)")
        if aperti and aperti[0] is not scaglioni_ordinati[-1]: # TODO: assicurarsi di come funziona il confronto aperti[0] is not scaglioni_ordinati[-1]
            raise ValueError("Lo scaglione illimitato deve essere quello con soglia_min più alta")

        for corrente, successivo in zip(scaglioni_ordinati, scaglioni_ordinati[1:]):
            if corrente.soglia_max != successivo.soglia_min:
                raise ValueError(
                    f"Scaglioni non contigui: {corrente.soglia_max} != {successivo.soglia_min}"
                )

    def calculate_tax(self, imponibile: Decimal) -> Decimal:
        """
        Somma il contributo di ogni scaglione sulla porzione di imponibile
        che vi rientra. Ogni scaglione clippa la propria fetta a zero se
        l'imponibile non la raggiunge — indipendente dall'ordine di iterazione.
        """
        if imponibile < Decimal(0):
            raise ValueError("Imponibile cannot be negative")

        tax = Decimal(0)
        for scaglione in self.scaglioni:
            tetto = scaglione.soglia_max if scaglione.soglia_max is not None else imponibile
            fetta_tassabile = max(Decimal(0), min(imponibile, tetto) - scaglione.soglia_min)
            tax += fetta_tassabile * scaglione.aliquota
        return tax
