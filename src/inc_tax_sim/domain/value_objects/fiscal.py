from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Scaglione:
    soglia_min: Decimal
    soglia_max: Decimal | None  # None = ultimo scaglione, aperto
    aliquota: Decimal

    def __post_init__(self):
        if self.soglia_min < Decimal(0):
            raise ValueError("Soglia min cannot be negative")
        if self.soglia_max is not None and self.soglia_max <= self.soglia_min:
            raise ValueError("Soglia max must be greater than soglia min")
        if not (Decimal(0) <= self.aliquota <= Decimal(1)):
            raise ValueError("Aliquota must be between 0 and 1")

@dataclass(frozen=True)
class Imposta:
    nome: str
    scaglioni: tuple[Scaglione, ...]

    # Validazione di coerenza degli scaglioni
    def __post_init__(self):
        if not self.scaglioni:
            raise ValueError("Almeno uno scaglione richiesto")
        scaglioni_ordinati = sorted(self.scaglioni, key=lambda s: s.soglia_min)
        if list(scaglioni_ordinati) != list(self.scaglioni):
            raise ValueError("Scaglioni devono essere ordinati per soglia_min")
        for i, s in enumerate(self.scaglioni[:-1]):
            if s.soglia_max != self.scaglioni[i + 1].soglia_min:
                raise ValueError("Scaglioni devono essere contigui")
        if self.scaglioni[-1].soglia_max is not None:
            raise ValueError("Solo l'ultimo scaglione può essere aperto (soglia_max=None)")

    # Ci possiamo servire di un unico metodo per calcolare il valore di una generica imposta su un generico importo.
    # TODO: Edge cases? Quando potrebbe non valere questa generalizzazione?
    def calculate_tax(self, imponibile: Decimal) -> Decimal:
        """
        Calcola l'imposta dovuta in base all'imponibile e agli scaglioni definiti.
        """
        if imponibile < Decimal(0):
            raise ValueError("Imponibile cannot be negative") # TODO: Magari ampliare la logica e gestire anche questo caso

        tax = Decimal(0)
        for scaglione in self.scaglioni:
            if scaglione.soglia_max is None or imponibile <= scaglione.soglia_max:
                taxable_income = max(Decimal(0), min(imponibile, scaglione.soglia_max or imponibile) - scaglione.soglia_min)
                tax += taxable_income * scaglione.aliquota
                break
            else:
                taxable_income = scaglione.soglia_max - scaglione.soglia_min
                tax += taxable_income * scaglione.aliquota

        return tax
