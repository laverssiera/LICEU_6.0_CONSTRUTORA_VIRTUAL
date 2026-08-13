def gerar_qr_campanha(id_campanha, destino_url):
    """
    Gera um QR Code dinâmico que rastreia a localização de quem escaneou.
    Leva o usuário para a Escola (Educação) ou Plataforma (Venda).
    """
    qr_data = {
        "url_final": f"{destino_url}?utm_source=qrcode&utm_campaign={id_campanha}",
        "track_id": f"LICEU-MKT-{id_campanha}",
        "analytics": "Sincronizado com Dashboard Diretor"
    }
    return qr_data # O Frontend Vue.js gera o gráfico do QR com isso
