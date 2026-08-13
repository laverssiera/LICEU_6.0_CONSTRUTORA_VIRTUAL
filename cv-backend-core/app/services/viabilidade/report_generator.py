from fpdf import FPDF
import datetime

class EVTLReport(FPDF):
    def header(self):
        # Logo e Título
        self.set_font("helvetica", "B", 14)
        self.cell(0, 10, "LICEU 6.0 - RELATÓRIO TÉCNICO DE VIABILIDADE (EVTL)", ln=True, align="C")
        self.set_font("helvetica", "I", 8)
        self.cell(0, 5, f"Gerado em: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align="C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Página {self.page_no()} - Propriedade Intelectual Liceu 6.0", align="C")

    def chapter_title(self, label, color=(240, 240, 240)):
        self.set_font("helvetica", "B", 11)
        self.set_fill_color(*color)
        self.cell(0, 10, f" {label}", ln=True, fill=True)
        self.ln(2)

    def create_report(self, dados_financeiros, pontos_criticos, filename):
        self.add_page()
        
        # 1. RESUMO EXECUTIVO
        self.chapter_title("1. INDICADORES FINANCEIROS")
        self.set_font("helvetica", "", 10)
        for chave, valor in dados_financeiros.items():
            self.cell(60, 8, f"{chave.replace('_', ' ').upper()}:", border="B")
            self.cell(0, 8, f"{valor}", border="B", ln=True)
        self.ln(5)

        # 2. PONTOS CRÍTICOS (O DNA DO RISCO)
        # Usamos uma cor de fundo amarela clara para destacar o alerta
        self.chapter_title("2. MATRIZ DE RISCO / PONTOS CRÍTICOS", color=(255, 255, 200))
        
        if not pontos_criticos:
            self.set_font("helvetica", "I", 10)
            self.cell(0, 10, "Nenhum ponto crítico impeditivo detectado nesta análise.", ln=True)
        else:
            for risco in pontos_criticos:
                self.set_font("helvetica", "B", 10)
                self.set_text_color(180, 0, 0) # Texto em Vermelho
                self.cell(0, 8, f"• [{risco['tipo']}] {risco['fator']}", ln=True)
                
                self.set_text_color(0, 0, 0) # Volta para Preto
                self.set_font("helvetica", "", 9)
                self.multi_cell(0, 6, f"Diagnóstico: {risco['detalhe']}")
                self.ln(2)

        self.output(filename)
        return filename
