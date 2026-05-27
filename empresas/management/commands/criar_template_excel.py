"""
Comando para criar arquivo Excel de exemplo para importação de profissionais
"""
from django.core.management.base import BaseCommand
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from pathlib import Path


class Command(BaseCommand):
    help = 'Cria arquivo Excel de exemplo para importação de profissionais'

    def handle(self, *args, **kwargs):
        # Criar workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Profissionais"

        # Estilo do cabeçalho
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=12)
        header_alignment = Alignment(horizontal="center", vertical="center")

        # Cabeçalhos
        headers = ['Nome', 'CPF', 'Email']
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num)
            cell.value = header
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment

        # Dados de exemplo
        exemplos = [
            ['João da Silva', '123.456.789-00', 'joao.silva@empresa.com'],
            ['Maria Santos', '98765432100', 'maria.santos@empresa.com'],
            ['Pedro Oliveira', '111.222.333-44', ''],
            ['Ana Costa', '555.666.777-88', 'ana.costa@empresa.com'],
        ]

        for row_num, dados in enumerate(exemplos, 2):
            for col_num, valor in enumerate(dados, 1):
                cell = ws.cell(row=row_num, column=col_num)
                cell.value = valor
                cell.alignment = Alignment(vertical="center")

        # Ajustar largura das colunas
        ws.column_dimensions['A'].width = 30
        ws.column_dimensions['B'].width = 20
        ws.column_dimensions['C'].width = 35

        # Adicionar instruções em uma planilha separada
        ws_instrucoes = wb.create_sheet("Instruções")
        
        instrucoes = [
            ["IMPORTAÇÃO DE PROFISSIONAIS - INSTRUÇÕES", ""],
            ["", ""],
            ["Formato do Arquivo:", ""],
            ["", "O arquivo deve conter 3 colunas na primeira linha:"],
            ["", "• Nome (obrigatório)"],
            ["", "• CPF (obrigatório, com ou sem pontuação)"],
            ["", "• Email (opcional)"],
            ["", ""],
            ["Regras:", ""],
            ["", "• CPF deve ser único no sistema"],
            ["", "• Se email não fornecido, será gerado automaticamente"],
            ["", "• Senha padrão: últimos 4 dígitos do CPF"],
            ["", ""],
            ["Exemplo:", ""],
            ["", "CPF: 123.456.789-00 → Senha: 7900"],
            ["", ""],
            ["Observações:", ""],
            ["", "• Linhas vazias são ignoradas"],
            ["", "• Cada profissional é importado individualmente"],
            ["", "• Se um CPF já existir, a linha será ignorada com erro"],
            ["", "• Formato suportado: .xlsx (Excel 2007+)"],
        ]

        for row_num, (col1, col2) in enumerate(instrucoes, 1):
            ws_instrucoes.cell(row=row_num, column=1).value = col1
            ws_instrucoes.cell(row=row_num, column=2).value = col2
            
            if row_num == 1:
                ws_instrucoes.cell(row=row_num, column=1).font = Font(bold=True, size=14, color="4472C4")

        ws_instrucoes.column_dimensions['A'].width = 40
        ws_instrucoes.column_dimensions['B'].width = 60

        # Salvar arquivo
        static_path = Path('static/templates')
        static_path.mkdir(parents=True, exist_ok=True)
        
        file_path = static_path / 'importacao_profissionais_template.xlsx'
        wb.save(file_path)

        self.stdout.write(
            self.style.SUCCESS(f'Template Excel criado com sucesso: {file_path}')
        )
