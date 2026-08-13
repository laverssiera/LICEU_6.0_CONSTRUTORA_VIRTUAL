class GestaoJuridicaSPE(Base):
    __tablename__ = "gestao_spe"
    
    id = Column(Integer, primary_key=True)
    spe_cnpj = Column(String, unique=True)
    imovel_matricula = Column(String)
    tem_patrimonio_afetacao = Column(Boolean, default=True)
    
    # Auditoria Preventiva (Score de 0 a 100)
    score_compliance = Column(Integer) 
    alertas_pendentes = Column(JSON) # Ex: ["Certidão Vencida", "Processo Trabalhista Fornecedor X"]
    
    ultima_auditoria = Column(DateTime, server_default=func.now())
