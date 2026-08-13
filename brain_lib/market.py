def viability_score(demand, supply, risk):
    return (demand * 0.5) - (supply * 0.3) - (risk * 0.2)

def decision(score):
    if score > 70:
        return "APPROVED"
    if score > 40:
        return "REVIEW"
    return "REJECTED"
