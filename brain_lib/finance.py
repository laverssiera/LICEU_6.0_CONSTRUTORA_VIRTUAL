from dataclasses import dataclass

@dataclass(frozen=True)
class FinanceInput:
    price: float
    rent: float

def cap_rate(fin: FinanceInput) -> float:
    return 0 if fin.price == 0 else (fin.rent * 12) / fin.price * 100

def risk_band(cap_rate: float) -> str:
    if cap_rate > 8:
        return "HIGH_YIELD"
    if cap_rate > 5:
        return "STABLE"
    return "SPECULATIVE"
