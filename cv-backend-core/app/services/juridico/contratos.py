from fpdf import FPDF
from datetime import datetime

class GeradorContratoLiceu(FPDF):
    def criar_minuta_spe(self, dados_estudo, investidor_nome, filename):
        self.add_page()
        
        # Cabeçalho Jurídico
        self.set_font("helvetica", "B", 16)
        self.cell(0, 10, "CONTRATO DE INVESTIMENTO EM SPE - LICEU 6.0", ln=True, align="C")
        self.set_font("helvetica", "I", 8)
        self.cell(0, 5, f"Protocolo Digital: {datetime.now().strftime('%Y%m%d%H%M%S')}", ln=True, align="C")
        self.ln(10)

        # 1. OBJETO E AFETAÇÃO
        self.set_font("helvetica", "B", 12)
        self.cell(0, 10, "1. OBJETO E PATRIMÔNIO DE AFETAÇÃO", ln=True)
        self.set_font("helvetica", "", 10)
        texto_objeto = (
            f"O INVESTIDOR {investidor_nome.upper()} aporta capital na SPE vinculada ao imóvel "
            f"de matrícula {dados_estudo['matricula']}, localizado em {dados_estudo['cep']}. "
            f"Este empreendimento adota o REGIME DE PATRIMÔNIO DE AFETAÇÃO, garantindo que os "
            f"recursos e ativos desta obra não se comuniquem com outras obrigações da incorporadora."
        )
        self.multi_cell(0, 6, texto_objeto)
        self.ln(5)

        # 2. DADOS FINANCEIROS (Vindos do EVTL)
        self.set_font("helvetica", "B", 12)
        self.cell(0, 10, "2. PROJEÇÃO FINANCEIRA E VGV", ln=True)
        self.set_font("helvetica", "", 10)
        self.cell(0, 7, f"- VGV Estimado: R$ {dados_estudo['vgv']:,.2f}", ln=True)
        self.cell(0, 7, f"- Investimento Total: R$ {dados_estudo['investimento_total']:,.2f}", ln=True)
        self.ln(5)

        # 3. CLÁUSULA DE ARBITRAGEM (O Ponto Crítico de Prevenção)
        self.set_font("helvetica", "B", 12)
        self.cell(0, 10, "3. RESOLUÇÃO DE CONFLITOS (ARBITRAGEM)", ln=True)
        self.set_font("helvetica", "I", 10)
        texto_arbitragem = (
            "As partes elegem a ARBITRAGEM como meio exclusivo de resolução de conflitos, "
            "renunciando expressamente ao foro comum. O processo seguirá o regulamento da "
            "Câmara de Arbitragem pactuada, com juízes especializados em Engenharia e Direito Imobiliário."
        )
        self.multi_cell(0, 6, texto_arbitragem)
        
        self.output(filename)
        return filename

