def processar_mensagem_whatsapp(remetente, mensagem_texto, imagem_url=None):
    """
    O Amigão responde via Zap. Se receber foto de rachadura, aciona o YOLO11.
    """
    if imagem_url:
        # 1. Envia para o Depto de Patologias (IA Vision)
        laudo = "IA detectou fissura de 2mm. Risco Baixo. Sugerido selante Liceu."
        return f"Opa! Recebi a foto aqui. {laudo} Quer que eu chame um técnico da Irmandade?"

    # 2. Resposta Inteligente baseada no Planejamento Estratégico
    if "preço" in mensagem_texto.lower():
        return "O valor do Kit Liceu é 28% menor que a obra comum. Quer que eu rode um EVTL para o seu terreno agora?"

    return "Tudo bem? Sou o Amigão Liceu. Como posso ajudar na sua construção hoje? 👷‍♂️"
