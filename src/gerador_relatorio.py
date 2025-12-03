"""
Gerador de relatórios PDF profissionais
Utiliza matplotlib para gráficos e WeasyPrint para PDF
"""

import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional
import matplotlib
matplotlib.use('Agg')  # Backend sem GUI
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import numpy as np

from weasyprint import HTML, CSS
from jinja2 import Template

from .utils import (
    formatar_moeda,
    formatar_numero,
    formatar_percentual,
    formatar_data_br
)

logger = logging.getLogger(__name__)


class GeradorRelatorio:
    """Gera relatórios PDF profissionais"""
    
    def __init__(self, config: Dict[str, Any], template_path: str = "templates/relatorio_template.html"):
        """
        Inicializa o gerador
        
        Args:
            config: Configurações do relatório (logo, empresa, cores, etc)
            template_path: Caminho para o template HTML
        """
        self.config = config
        self.template_path = template_path
        
        # Configuração de cores
        self.cor_primaria = config.get('relatorio', {}).get('cor_primaria', '#FF6B00')
        self.cor_secundaria = config.get('relatorio', {}).get('cor_secundaria', '#2C3E50')
        self.cor_sucesso = '#27AE60'
        self.cor_aviso = '#F39C12'
        self.cor_erro = '#E74C3C'
        
        # Estilo dos gráficos
        plt.style.use('seaborn-v0_8-darkgrid')
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.labelsize'] = 10
        plt.rcParams['axes.titlesize'] = 12
        plt.rcParams['xtick.labelsize'] = 9
        plt.rcParams['ytick.labelsize'] = 9
        plt.rcParams['legend.fontsize'] = 9
        plt.rcParams['figure.titlesize'] = 14
    
    def gerar_relatorio(self, dados: Dict[str, Any], caminho_saida: str) -> str:
        """
        Gera relatório PDF completo
        
        Args:
            dados: Dados processados do ExtratorDados
            caminho_saida: Caminho para salvar o PDF
        
        Returns:
            Caminho do arquivo gerado
        """
        logger.info(f"Gerando relatório para {dados['estacao']['nome']}...")
        
        # Cria diretório de saída se não existir
        os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)
        
        # Diretório temporário para gráficos
        temp_dir = os.path.join(os.path.dirname(caminho_saida), '.temp_graficos')
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            # Gera gráficos
            graficos = self._gerar_graficos(dados, temp_dir)
            
            # Renderiza HTML
            html_content = self._renderizar_html(dados, graficos)
            
            # Gera PDF
            HTML(string=html_content).write_pdf(
                caminho_saida,
                stylesheets=[CSS(string=self._get_css_customizado())]
            )
            
            logger.info(f"Relatório gerado com sucesso: {caminho_saida}")
            
            return caminho_saida
            
        finally:
            # Limpa arquivos temporários
            self._limpar_temp(temp_dir)
    
    def _gerar_graficos(self, dados: Dict, output_dir: str) -> Dict[str, str]:
        """Gera todos os gráficos necessários"""
        graficos = {}
        
        # Gráfico 1: Geração diária
        graficos['geracao_diaria'] = self._grafico_geracao_diaria(
            dados['geracao']['geracao_diaria'],
            dados['periodo']['mes'],
            dados['periodo']['ano'],
            os.path.join(output_dir, 'geracao_diaria.png')
        )
        
        # Gráfico 2: Resumo mensal (pizza ou barras)
        graficos['resumo_mensal'] = self._grafico_resumo_mensal(
            dados,
            os.path.join(output_dir, 'resumo_mensal.png')
        )
        
        # Gráfico 3: Performance (velocímetro/gauge)
        graficos['performance'] = self._grafico_performance(
            dados['performance']['pr'],
            os.path.join(output_dir, 'performance.png')
        )
        
        # Gráfico 4: Comparativo (se houver)
        if dados.get('comparativo'):
            graficos['comparativo'] = self._grafico_comparativo(
                dados,
                os.path.join(output_dir, 'comparativo.png')
            )
        
        return graficos
    
    def _grafico_geracao_diaria(self, geracao_diaria: list, mes: int, ano: int, 
                               output_path: str) -> str:
        """Gráfico de barras com geração diária"""
        fig, ax = plt.subplots(figsize=(12, 5))
        
        dias = [d['dia'] for d in geracao_diaria]
        kwhs = [d['kwh'] for d in geracao_diaria]
        
        cores = [self.cor_primaria if kwh > 0 else '#CCCCCC' for kwh in kwhs]
        
        bars = ax.bar(dias, kwhs, color=cores, alpha=0.8, edgecolor='white', linewidth=0.5)
        
        # Destaca maior valor
        max_idx = kwhs.index(max(kwhs)) if kwhs else 0
        if kwhs and max_idx < len(bars):
            bars[max_idx].set_color(self.cor_sucesso)
            bars[max_idx].set_alpha(1.0)
        
        ax.set_xlabel('Dia do Mês', fontweight='bold')
        ax.set_ylabel('Geração (kWh)', fontweight='bold')
        ax.set_title(f'Geração Diária - {mes:02d}/{ano}', fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_axisbelow(True)
        
        # Formata eixo Y
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return output_path
    
    def _grafico_resumo_mensal(self, dados: Dict, output_path: str) -> str:
        """Gráfico de indicadores principais"""
        fig, axes = plt.subplots(2, 2, figsize=(10, 8))
        fig.suptitle('Resumo Mensal', fontweight='bold', fontsize=14)
        
        # 1. Total gerado
        ax1 = axes[0, 0]
        total_kwh = dados['geracao']['total_kwh']
        ax1.bar(['Total Gerado'], [total_kwh], color=self.cor_primaria, alpha=0.8, width=0.5)
        ax1.set_ylabel('kWh', fontweight='bold')
        ax1.set_title('Energia Total', fontweight='bold')
        ax1.text(0, total_kwh * 0.5, f"{formatar_numero(total_kwh, 0)} kWh", 
                ha='center', va='center', fontsize=16, fontweight='bold', color='white')
        ax1.set_ylim(0, total_kwh * 1.2)
        ax1.grid(True, alpha=0.3, axis='y')
        
        # 2. Economia financeira
        ax2 = axes[0, 1]
        economia = dados['economia']['economia_mensal']
        ax2.bar(['Economia'], [economia], color=self.cor_sucesso, alpha=0.8, width=0.5)
        ax2.set_ylabel('R$', fontweight='bold')
        ax2.set_title('Economia Financeira', fontweight='bold')
        ax2.text(0, economia * 0.5, formatar_moeda(economia), 
                ha='center', va='center', fontsize=14, fontweight='bold', color='white')
        ax2.set_ylim(0, economia * 1.2)
        ax2.grid(True, alpha=0.3, axis='y')
        
        # 3. CO2 evitado
        ax3 = axes[1, 0]
        co2 = dados['impacto_ambiental']['co2_evitado_kg']
        ax3.bar(['CO₂ Evitado'], [co2], color='#27AE60', alpha=0.8, width=0.5)
        ax3.set_ylabel('kg', fontweight='bold')
        ax3.set_title('Impacto Ambiental', fontweight='bold')
        ax3.text(0, co2 * 0.5, f"{formatar_numero(co2, 0)} kg", 
                ha='center', va='center', fontsize=14, fontweight='bold', color='white')
        ax3.set_ylim(0, co2 * 1.2)
        ax3.grid(True, alpha=0.3, axis='y')
        
        # 4. Performance Ratio
        ax4 = axes[1, 1]
        pr = dados['performance']['pr']
        cores_pr = [self.cor_sucesso if pr >= 75 else self.cor_aviso if pr >= 60 else self.cor_erro]
        ax4.bar(['PR'], [pr], color=cores_pr, alpha=0.8, width=0.5)
        ax4.set_ylabel('%', fontweight='bold')
        ax4.set_title('Performance Ratio', fontweight='bold')
        ax4.text(0, pr * 0.5, f"{pr:.1f}%", 
                ha='center', va='center', fontsize=16, fontweight='bold', color='white')
        ax4.set_ylim(0, 100)
        ax4.axhline(y=75, color='gray', linestyle='--', alpha=0.5, label='Meta: 75%')
        ax4.grid(True, alpha=0.3, axis='y')
        ax4.legend()
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return output_path
    
    def _grafico_performance(self, pr: float, output_path: str) -> str:
        """Gráfico estilo velocímetro para Performance Ratio"""
        fig, ax = plt.subplots(figsize=(8, 5), subplot_kw={'projection': 'polar'})
        
        # Configuração do semicírculo
        theta = np.linspace(0, np.pi, 100)
        
        # Faixas de performance
        faixas = [
            (0, 60, self.cor_erro, 'Baixo'),
            (60, 75, self.cor_aviso, 'Médio'),
            (75, 100, self.cor_sucesso, 'Ótimo')
        ]
        
        for inicio, fim, cor, label in faixas:
            theta_faixa = np.linspace(np.pi * inicio / 100, np.pi * fim / 100, 50)
            ax.fill_between(theta_faixa, 0, 1, color=cor, alpha=0.3)
        
        # Ponteiro
        angulo_pr = np.pi * (1 - pr / 100)
        ax.plot([angulo_pr, angulo_pr], [0, 0.9], color='black', linewidth=3)
        ax.plot(angulo_pr, 0.9, 'o', color='black', markersize=10)
        
        # Texto central
        ax.text(np.pi/2, -0.3, f'{pr:.1f}%', ha='center', va='center', 
               fontsize=24, fontweight='bold')
        ax.text(np.pi/2, -0.5, 'Performance Ratio', ha='center', va='center', 
               fontsize=12, style='italic')
        
        ax.set_ylim(0, 1)
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines['polar'].set_visible(False)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white', transparent=False)
        plt.close()
        
        return output_path
    
    def _grafico_comparativo(self, dados: Dict, output_path: str) -> str:
        """Gráfico comparativo com mês anterior"""
        if not dados.get('comparativo'):
            return None
        
        fig, ax = plt.subplots(figsize=(8, 5))
        
        mes_atual = dados['periodo']['mes_ano_texto']
        mes_anterior = dados['comparativo']['mes_anterior']
        
        kwh_atual = dados['geracao']['total_kwh']
        kwh_anterior = dados['comparativo']['kwh_mes_anterior']
        
        meses = [mes_anterior, mes_atual]
        valores = [kwh_anterior, kwh_atual]
        
        cores = [self.cor_secundaria, self.cor_primaria]
        bars = ax.bar(meses, valores, color=cores, alpha=0.8, width=0.5)
        
        # Valores nas barras
        for bar, valor in zip(bars, valores):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height * 0.5,
                   f'{formatar_numero(valor, 0)}\nkWh',
                   ha='center', va='center', fontsize=12, fontweight='bold', color='white')
        
        # Seta de variação
        variacao = dados['comparativo']['variacao_percentual']
        cor_variacao = self.cor_sucesso if variacao >= 0 else self.cor_erro
        sinal = '+' if variacao >= 0 else ''
        
        ax.text(0.5, max(valores) * 1.1, f'{sinal}{variacao:.1f}%',
               ha='center', va='center', fontsize=16, fontweight='bold',
               color=cor_variacao, transform=ax.transData)
        
        ax.set_ylabel('Geração (kWh)', fontweight='bold')
        ax.set_title('Comparativo Mensal', fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_axisbelow(True)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return output_path
    
    def _renderizar_html(self, dados: Dict, graficos: Dict) -> str:
        """Renderiza template HTML com os dados"""
        
        # Carrega template
        if os.path.exists(self.template_path):
            with open(self.template_path, 'r', encoding='utf-8') as f:
                template_str = f.read()
        else:
            template_str = self._get_template_padrao()
        
        template = Template(template_str)
        
        # Prepara dados para o template
        context = {
            'dados': dados,
            'config': self.config,
            'graficos': graficos,
            'data_geracao': formatar_data_br(datetime.now()),
            'formatar_moeda': formatar_moeda,
            'formatar_numero': formatar_numero,
            'formatar_percentual': formatar_percentual
        }
        
        return template.render(**context)
    
    def _get_template_padrao(self) -> str:
        """Template HTML padrão (será substituído pelo arquivo)"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Relatório Solar</title>
        </head>
        <body>
            <h1>Relatório Mensal - {{ dados.estacao.nome }}</h1>
            <p>Período: {{ dados.periodo.mes_ano_texto }}</p>
            <p>Geração Total: {{ formatar_numero(dados.geracao.total_kwh) }} kWh</p>
        </body>
        </html>
        """
    
    def _get_css_customizado(self) -> str:
        """CSS customizado para o PDF"""
        return f"""
        @page {{
            size: A4;
            margin: 1.5cm;
        }}
        
        body {{
            font-family: 'Arial', sans-serif;
            color: #333;
            line-height: 1.6;
        }}
        
        .header {{
            background-color: {self.cor_primaria};
            color: white;
            padding: 20px;
            margin-bottom: 30px;
        }}
        
        .metric-box {{
            border-left: 4px solid {self.cor_primaria};
            padding: 15px;
            margin: 10px 0;
            background-color: #f9f9f9;
        }}
        
        .grafico {{
            width: 100%;
            max-width: 800px;
            margin: 20px auto;
        }}
        """
    
    def _limpar_temp(self, temp_dir: str):
        """Remove arquivos temporários"""
        try:
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except Exception as e:
            logger.warning(f"Erro ao limpar arquivos temporários: {e}")
