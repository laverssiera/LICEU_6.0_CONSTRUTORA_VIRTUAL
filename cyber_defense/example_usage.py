"""
Exemplo de uso do LICEU SHIELD (Cyber Defense)
"""
from shield_core import CyberDefenseCore

def main():
    shield = CyberDefenseCore()
    # Log de evento normal
    shield.log_event({"id": 1, "tags": ["info"], "desc": "Login bem-sucedido"})
    # Evento suspeito
    event = {"id": 2, "tags": ["malware"], "desc": "Arquivo suspeito detectado"}
    detected = shield.detect_threat(event)
    shield.log_event(event)
    print("Ameaça detectada?", detected)
    print("Status do Shield:", shield.get_status())

if __name__ == "__main__":
    main()
