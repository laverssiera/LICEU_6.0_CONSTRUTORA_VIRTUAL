# Strategic Classifier
# Classifica eventos para filas estratégicas

class StrategicClassifier:
    def classify(self, event):
        """
        Recebe um dicionário de evento e retorna o nome da fila estratégica.
        """
        event_type = event.get('type', '')
        if event_type.startswith('audit'):
            return 'audit_queue'
        if event_type.startswith('finance'):
            return 'finance_queue'
        if event_type.startswith('legal'):
            return 'legal_queue'
        if event_type.startswith('governance'):
            return 'governance_queue'
        if event_type.startswith('learning'):
            return 'learning_queue'
        if event_type.startswith('analytics'):
            return 'analytics_queue'
        if event_type.startswith('async'):
            return 'async_queue'
        return 'operational_queue'

# Exemplo de uso
if __name__ == "__main__":
    classifier = StrategicClassifier()
    example_event = {'type': 'finance.payment.created'}
    print(classifier.classify(example_event))  # Saída: finance_queue
