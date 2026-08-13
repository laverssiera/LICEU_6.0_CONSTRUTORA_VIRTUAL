def financial_curve(tasks):
    timeline = {}
    for t in tasks:
        if t.duration_days == 0:
            continue
        daily_cost = t.cost / t.duration_days
        day = int(t.start_day)
        while day < int(t.end_day):
            timeline.setdefault(day, 0)
            timeline[day] += daily_cost
            day += 1
    return timeline

def cumulative_curve(timeline):
    total = 0
    curve = {}
    for day in sorted(timeline.keys()):
        total += timeline[day]
        curve[day] = total
    return curve
