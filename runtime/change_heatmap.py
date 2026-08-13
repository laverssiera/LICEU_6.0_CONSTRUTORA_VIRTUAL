"""
Change Heatmap Engine
- Analisa logs de mudanças, falhas e aprovações para gerar um heatmap de sensibilidade e atividade do sistema.
- Mostra onde o sistema mais muda, onde quebra mais e onde é mais sensível.
"""
from collections import defaultdict
from datetime import datetime, timedelta

class ChangeHeatmap:
    def __init__(self):
        # Estrutura: {modulo: {dia: {'changes': int, 'failures': int, 'sensitivity': float}}}
        self.heatmap = defaultdict(lambda: defaultdict(lambda: {'changes': 0, 'failures': 0, 'sensitivity': 0.0}))

    def ingest_change(self, module, timestamp=None):
        day = (timestamp or datetime.utcnow()).date().isoformat()
        self.heatmap[module][day]['changes'] += 1

    def ingest_failure(self, module, timestamp=None):
        day = (timestamp or datetime.utcnow()).date().isoformat()
        self.heatmap[module][day]['failures'] += 1

    def set_sensitivity(self, module, value, timestamp=None):
        day = (timestamp or datetime.utcnow()).date().isoformat()
        self.heatmap[module][day]['sensitivity'] = value

    def get_heatmap(self, days=30):
        cutoff = (datetime.utcnow() - timedelta(days=days)).date().isoformat()
        result = {}
        for module, days_dict in self.heatmap.items():
            result[module] = []
            for day, stats in days_dict.items():
                if day >= cutoff:
                    result[module].append({'day': day, **stats})
        return result

    def top_changing_modules(self, n=5, days=30):
        heatmap = self.get_heatmap(days)
        ranking = []
        for module, stats in heatmap.items():
            total_changes = sum(s['changes'] for s in stats)
            total_failures = sum(s['failures'] for s in stats)
            avg_sens = sum(s['sensitivity'] for s in stats) / (len(stats) or 1)
            ranking.append((module, total_changes, total_failures, avg_sens))
        ranking.sort(key=lambda x: (x[1], x[2], -x[3]), reverse=True)
        return ranking[:n]
