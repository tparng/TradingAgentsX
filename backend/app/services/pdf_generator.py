# -*- coding: utf-8 -*-
"""
PDF Generation Service for Analyst Reports
Uses fpdf2 for reliable cross-platform CJK (Chinese/Japanese/Korean) font rendering.

ReportLab's TTFont subsetting produces corrupted zlib streams on Linux (Railway Docker),
causing garbled Chinese characters. fpdf2 uses direct Unicode-to-glyph mapping without
the subsetting compression issue, ensuring correct rendering on all platforms.
"""
import io
import re
import warnings
from typing import Optional, List, Dict
from datetime import datetime

# Suppress matplotlib font warnings globally
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')
import logging
logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)

# Matplotlib for chart generation
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for server
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import numpy as np

# Configure matplotlib to use available system fonts
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Liberation Sans', 'FreeSans', 'Helvetica', 'Arial', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# fpdf2 for PDF generation — reliable cross-platform Unicode/CJK support
from fpdf import FPDF

# ============================================
# PDF LABELS FOR INTERNATIONALIZATION
# ============================================
PDF_LABELS = {
    'en': {
        'cover_title': 'TradingAgentsX Analysis Report',
        'cover_subtitle': 'AI-Powered Multi-Perspective Investment Analysis',
        'toc_title': 'Table of Contents',
        'report_content': 'Report Content',
        'price_chart': 'Price Chart & Volume',
        'price_stats': 'Price Statistics',
        'item': 'Item',
        'value': 'Value',
        'total_return': 'Total Return',
        'analysis_period': 'Analysis Period',
        'days': 'days',
        'start_date': 'Start Date',
        'end_date': 'End Date',
        'start_price': 'Start Price',
        'end_price': 'End Price',
        'chart_failed': 'Chart generation failed',
        'analysts_team': 'Analysts Team',
        'research_team': 'Research Team',
        'trading_risk_team': 'Trading & Risk Team',
        'members': 'members',
        'market_analyst': 'Market Analyst',
        'fundamentals_analyst': 'Fundamentals Analyst',
        'social_analyst': 'Social Media Analyst',
        'news_analyst': 'News Analyst',
        'bull_researcher': 'Bull Researcher',
        'bear_researcher': 'Bear Researcher',
        'research_manager': 'Research Manager',
        'aggressive_analyst': 'Aggressive Analyst',
        'conservative_analyst': 'Conservative Analyst',
        'neutral_analyst': 'Neutral Analyst',
        'risk_manager': 'Risk Manager',
        'trader': 'Trader',
    },
    'zh-TW': {
        'cover_title': 'TradingAgentsX 分析報告',
        'cover_subtitle': 'AI 驅動多角度投資分析',
        'toc_title': '目錄',
        'report_content': '報告內容',
        'price_chart': '價格走勢 & 成交量',
        'price_stats': '價格統計',
        'item': '項目',
        'value': '數值',
        'total_return': '總報酬',
        'analysis_period': '分析期間',
        'days': '天',
        'start_date': '開始日期',
        'end_date': '結束日期',
        'start_price': '起始價格',
        'end_price': '結束價格',
        'chart_failed': '圖表生成失敗',
        'analysts_team': '分析師團隊',
        'research_team': '研究團隊',
        'trading_risk_team': '交易與風險團隊',
        'members': '位成員',
        'market_analyst': '市場分析師',
        'fundamentals_analyst': '基本面分析師',
        'social_analyst': '社群媒體分析師',
        'news_analyst': '新聞分析師',
        'bull_researcher': '看漲研究員',
        'bear_researcher': '看跌研究員',
        'research_manager': '研究經理',
        'aggressive_analyst': '激進分析師',
        'conservative_analyst': '保守分析師',
        'neutral_analyst': '中立分析師',
        'risk_manager': '風險經理',
        'trader': '交易員',
    },
}


def get_pdf_label(key: str, language: str = 'zh-TW') -> str:
    """Get a localized PDF label"""
    lang_labels = PDF_LABELS.get(language, PDF_LABELS['zh-TW'])
    return lang_labels.get(key, PDF_LABELS['zh-TW'].get(key, key))


# ============================================
# CUSTOM FPDF CLASS WITH AUTO PAGE NUMBERING
# ============================================
class _ReportPDF(FPDF):
    """Custom FPDF with page number footer (skips cover + TOC pages)"""

    def __init__(self, font_name: str, cover_toc_pages: int = 2, **kwargs):
        super().__init__(orientation='P', unit='mm', format='A4', **kwargs)
        self._fn = font_name
        self._cover_toc_pages = cover_toc_pages

    def footer(self):
        content_page = self.page - self._cover_toc_pages
        if content_page > 0:
            self.set_y(-15)
            self.set_font(self._fn, size=9)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, f'- {content_page} -', align='C')
            self.set_text_color(0, 0, 0)


# ============================================
# PDF GENERATOR CLASS
# ============================================
class PDFGenerator:
    """Generate PDF reports from markdown content using fpdf2"""

    # Emoji → ASCII replacement map
    EMOJI_TO_UNICODE = {
        '✅': '[OK]', '❌': '[X]', '⚠️': '[!]', '⚡': '*', '🔔': 'o',
        '☒': '[X]', '☑': '[V]', '☐': '[ ]', '✓': 'V', '✔': 'V',
        '✗': 'X', '✘': 'X', '※': '*', '△': '^', '▽': 'v',
        '▲': '^', '▼': 'v', '◆': '*', '◇': '*', '○': 'o',
        '●': '*', '□': '[ ]', '■': '[*]', '⭐': '*', '🌟': '*',
        '💎': '+', '🏆': '#', '📊': '', '📈': '^', '📉': 'v',
        '📋': '-', '📌': '*', '💰': '$', '💵': '$', '💴': 'Y',
        '💶': 'E', '💷': 'P', '💸': '$', '💹': '^', '🚀': '^^',
        '⬆️': '^', '⬇️': 'v', '➡️': '>', '⬅️': '<', '🔼': '^',
        '🔽': 'v', '🎯': 'o', '🔥': '*', '💡': '*', '⚙️': '*',
        '🔧': '>', '🔨': '>', '🤖': '', '💻': '', '📱': '',
        '🖥️': '', '👤': '', '👥': '', '🔬': '', '📚': '',
        '⏰': 'o', '📅': '-', '⏱️': 'o', '✨': '*', '🎨': '',
        '📝': '-', '📄': '-', '🗂️': '=', '🌐': 'o', '🔗': '~',
        '💼': '', '🎪': '', '🎭': '', '🌍': 'o', '🌎': 'o',
        '🌏': 'o', '🏦': '$', '🏢': '', '🏭': '', '🔑': '>',
        '🔒': '[L]', '🔓': '[U]', '📢': '>', '📣': '>', '🔊': '>',
        '🔈': 'o', '⚖️': '=', '⚔️': 'X', '🛡️': '[ ]', '🎖️': '*',
        '🏅': '*', '🥇': '#1', '🥈': '#2', '🥉': '#3',
    }

    def __init__(self):
        """Initialize with NotoSerifTC font paths"""
        import os
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))))
        font_dir = os.path.join(
            base_dir, 'Cactus_Classical_Serif,Noto_Serif_TC',
            'Noto_Serif_TC', 'static')

        font_regular = os.path.join(font_dir, 'NotoSerifTC-Regular.ttf')
        font_bold = os.path.join(font_dir, 'NotoSerifTC-Bold.ttf')

        if os.path.exists(font_regular):
            self._font_regular = font_regular
            self._font_bold = font_bold if os.path.exists(font_bold) else font_regular
            self._font_name = 'NotoSerifTC'
            print('✅ NotoSerifTC found — fpdf2 CJK rendering enabled')
        else:
            self._font_regular = None
            self._font_bold = None
            self._font_name = 'Helvetica'
            print('⚠️ NotoSerifTC not found, falling back to Helvetica')

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _new_pdf(self) -> _ReportPDF:
        """Create a fresh PDF instance with fonts registered"""
        pdf = _ReportPDF(font_name=self._font_name)
        pdf.set_margins(15, 15, 15)
        if self._font_regular and self._font_name != 'Helvetica':
            pdf.add_font(self._font_name, '', self._font_regular)
            pdf.add_font(self._font_name, 'B', self._font_bold)
        return pdf

    def _fn(self) -> str:
        return self._font_name

    @staticmethod
    def _hex_to_rgb(hex_color: str):
        h = hex_color.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    def _set_color(self, pdf: FPDF, hex_color: str, is_text: bool = True):
        r, g, b = self._hex_to_rgb(hex_color)
        if is_text:
            pdf.set_text_color(r, g, b)
        else:
            pdf.set_fill_color(r, g, b)

    def _replace_emojis(self, text: str) -> str:
        if not text:
            return text
        for emoji, replacement in self.EMOJI_TO_UNICODE.items():
            text = text.replace(emoji, replacement)
        return text

    def _clean_markdown(self, text: str) -> str:
        """Remove markdown formatting, return plain text"""
        import unicodedata
        text = unicodedata.normalize('NFKC', text)
        # Remove links but keep text
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        # Remove bold markers
        for _ in range(3):
            text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
            text = re.sub(r'__([^_]+)__', r'\1', text)
        text = re.sub(r'\*\*', '', text)
        text = re.sub(r'__', '', text)
        # Remove italic markers
        text = re.sub(r'(?<![*])\*([^*]+?)\*(?![*])', r'\1', text)
        text = re.sub(r'(?<![_])_([^_]+?)_(?![_])', r'\1', text)
        # Remove code
        text = re.sub(r'```[^`]*?```', '', text, flags=re.DOTALL)
        text = re.sub(r'`([^`]+?)`', r'\1', text)
        # Normalize bullet points
        text = re.sub(r'^\s*[\*\-\+]\s+', '- ', text, flags=re.MULTILINE)
        # Remove horizontal rules
        text = re.sub(r'^[\-\*_]{3,}\s*$', '', text, flags=re.MULTILINE)
        # Remove heading markers
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        # Clean up spaces
        text = re.sub(r' {2,}', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def _parse_markdown_table(self, lines: list, start_idx: int) -> tuple:
        """Parse markdown table. Returns (table_data, end_idx)."""
        table_rows = []
        i = start_idx
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('|') and line.endswith('|'):
                cells = [c.strip() for c in line.split('|')[1:-1]]
                is_sep = all(c.replace('-', '').replace(':', '').strip() == '' for c in cells)
                if not is_sep:
                    table_rows.append(cells)
                i += 1
            elif '|' in line and not line.startswith('#'):
                cells = [c.strip() for c in line.split('|')]
                is_sep = all(c.replace('-', '').replace(':', '').strip() == '' for c in cells)
                if not is_sep and cells:
                    table_rows.append(cells)
                i += 1
            else:
                break
        return table_rows, i

    def _add_table(self, pdf: FPDF, table_data: list):
        """Render a parsed markdown table using fpdf2 cells"""
        if not table_data or len(table_data) < 1:
            return

        # Filter out empty rows
        table_data = [row for row in table_data if any(c.strip() for c in row)]
        if not table_data:
            return

        fn = self._fn()
        num_cols = max(len(row) for row in table_data)
        if num_cols == 0:
            return

        col_w = pdf.epw / num_cols
        row_h = 7

        for row_idx, row in enumerate(table_data):
            # Pad row to num_cols
            row = (list(row) + [''] * num_cols)[:num_cols]

            if row_idx == 0:
                # Header row
                pdf.set_font(fn, 'B', size=9)
                self._set_color(pdf, '#2c3e50', is_text=False)
                pdf.set_text_color(255, 255, 255)
                fill = True
            else:
                # Alternate row shading
                pdf.set_font(fn, size=9)
                pdf.set_text_color(51, 51, 51)
                if row_idx % 2 == 0:
                    self._set_color(pdf, '#f3f4f6', is_text=False)
                    fill = True
                else:
                    pdf.set_fill_color(255, 255, 255)
                    fill = True

            for cell_idx, cell in enumerate(row):
                text = self._clean_markdown(str(cell))
                text = self._replace_emojis(text)
                # Truncate long cell content to fit
                max_chars = max(8, int(col_w * 1.5))
                if len(text) > max_chars:
                    text = text[:max_chars - 2] + '..'
                border = 'B' if row_idx == 0 else 1
                pdf.cell(col_w, row_h, text, border=border, fill=fill, align='L')

            pdf.ln()

        pdf.set_text_color(0, 0, 0)
        pdf.set_fill_color(255, 255, 255)
        pdf.ln(3)

    def _add_section_line(self, pdf: FPDF, line: str):
        """Render a single line of markdown text with appropriate formatting"""
        fn = self._fn()
        line_stripped = line.strip()

        if not line_stripped:
            pdf.ln(3)
            return

        # Always reset to left margin before rendering
        pdf.set_x(pdf.l_margin)
        w = pdf.epw  # safe explicit width

        text = self._replace_emojis(line_stripped)

        # Heading levels
        if text.startswith('### '):
            content = self._clean_markdown(text[4:])
            pdf.set_font(fn, 'B', size=11)
            self._set_color(pdf, '#374151')
            pdf.multi_cell(w, 6, content, align='L')
            pdf.ln(1)
            self._set_color(pdf, '#333333')
        elif text.startswith('## '):
            content = self._clean_markdown(text[3:])
            pdf.set_font(fn, 'B', size=13)
            self._set_color(pdf, '#1e3a5f')
            pdf.multi_cell(w, 7, content, align='L')
            pdf.ln(2)
            self._set_color(pdf, '#333333')
        elif text.startswith('# '):
            content = self._clean_markdown(text[2:])
            pdf.set_font(fn, 'B', size=15)
            self._set_color(pdf, '#1e3a5f')
            pdf.multi_cell(w, 8, content, align='L')
            pdf.ln(3)
            self._set_color(pdf, '#333333')
        elif text.startswith('- ') or text.startswith('* '):
            content = self._clean_markdown(text[2:])
            pdf.set_font(fn, size=10)
            # Indent using leading spaces (multi_cell handles wrapping)
            pdf.multi_cell(w, 5.5, '    \u2022 ' + content, align='L')
        else:
            content = self._clean_markdown(text)
            # Detect short "report title" lines
            is_section_title = (
                len(content) < 40 and
                any(kw in content for kw in ['報告', 'Report', 'Analysis', '分析', '摘要', 'Summary'])
                and ',' not in content and '，' not in content
                and not content.endswith('。')
            )
            if is_section_title:
                pdf.set_font(fn, 'B', size=12)
                self._set_color(pdf, '#2c3e50')
                pdf.multi_cell(w, 6, content, align='L')
                pdf.ln(1)
                self._set_color(pdf, '#333333')
            else:
                pdf.set_font(fn, size=10)
                pdf.multi_cell(w, 5.5, content, align='L')

    # ------------------------------------------------------------------
    # Price chart (unchanged from original)
    # ------------------------------------------------------------------

    def _calculate_heikin_ashi(self, price_data: List[Dict]) -> List[Dict]:
        """Calculate Heikin Ashi values from regular OHLC data"""
        if not price_data:
            return []
        ha_data = []
        for i, candle in enumerate(price_data):
            open_price = candle.get('Open', 0)
            high_price = candle.get('High', 0)
            low_price = candle.get('Low', 0)
            close_price = candle.get('Adj Close', candle.get('Close', 0))
            volume = candle.get('Volume', 0)
            ha_close = (open_price + high_price + low_price + close_price) / 4
            if i == 0:
                ha_open = (open_price + close_price) / 2
            else:
                ha_open = (ha_data[i-1]['HA_Open'] + ha_data[i-1]['HA_Close']) / 2
            ha_high = max(high_price, ha_open, ha_close)
            ha_low = min(low_price, ha_open, ha_close)
            ha_data.append({
                'Date': candle.get('Date', ''),
                'HA_Open': ha_open, 'HA_High': ha_high,
                'HA_Low': ha_low, 'HA_Close': ha_close,
                'Volume': volume,
            })
        return ha_data

    def _generate_price_chart(self, price_data: List[Dict], ticker: str) -> bytes:
        """Generate Heikin Ashi candlestick + volume chart as PNG bytes"""
        if not price_data or len(price_data) < 2:
            return None
        ha_data = self._calculate_heikin_ashi(price_data)
        dates = list(range(len(ha_data)))
        ha_opens = [d['HA_Open'] for d in ha_data]
        ha_highs = [d['HA_High'] for d in ha_data]
        ha_lows = [d['HA_Low'] for d in ha_data]
        ha_closes = [d['HA_Close'] for d in ha_data]
        volumes = [d['Volume'] for d in ha_data]

        fig, (ax1, ax2) = plt.subplots(
            2, 1, figsize=(10, 6),
            gridspec_kw={'height_ratios': [3, 1]}, sharex=True)
        fig.patch.set_facecolor('white')

        width = 0.8
        for i in range(len(dates)):
            color = '#22c55e' if ha_closes[i] >= ha_opens[i] else '#ef4444'
            ax1.plot([dates[i], dates[i]], [ha_lows[i], ha_highs[i]],
                     color=color, linewidth=1)
            body_bottom = min(ha_opens[i], ha_closes[i])
            body_height = abs(ha_closes[i] - ha_opens[i])
            rect = Rectangle((dates[i] - width/2, body_bottom), width, body_height,
                              facecolor=color, edgecolor=color, linewidth=0.5)
            ax1.add_patch(rect)

        ax1.set_ylabel('Price ($)', fontsize=10)
        ax1.set_title(f'{ticker} Heikin Ashi Chart', fontsize=12, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.set_facecolor('#fafafa')

        vol_colors = ['#22c55e' if ha_closes[i] >= ha_opens[i] else '#ef4444'
                      for i in range(len(dates))]
        ax2.bar(dates, volumes, width=width, color=vol_colors, alpha=0.7)
        ax2.set_ylabel('Volume', fontsize=10)
        ax2.set_xlabel('Trading Days', fontsize=10)
        ax2.grid(True, alpha=0.3)
        ax2.set_facecolor('#fafafa')
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(
            lambda x, p: f'{x/1e6:.1f}M' if x >= 1e6 else f'{x/1e3:.0f}K' if x >= 1e3 else f'{x:.0f}'))

        if ha_data:
            label_indices = [0, len(ha_data)//2, len(ha_data)-1]
            labels, positions = [], []
            for idx in label_indices:
                if idx < len(ha_data):
                    date_str = ha_data[idx].get('Date', '')
                    if date_str and len(date_str) >= 10:
                        labels.append(date_str[5:10])
                        positions.append(idx)
            if positions and labels:
                ax2.set_xticks(positions)
                ax2.set_xticklabels(labels)

        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                    facecolor='white', edgecolor='none')
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()

    # ------------------------------------------------------------------
    # Page builders
    # ------------------------------------------------------------------

    def _build_cover_page(self, pdf: FPDF, ticker: str, analysis_date: str, language: str):
        """Cover page: large ticker, date, TradingAgentsX branding"""
        fn = self._fn()
        pdf.add_page()

        # Vertical center — push down ~80mm
        pdf.ln(60)

        # Ticker — large, letter-spaced
        spaced_ticker = '  '.join(ticker)
        pdf.set_font(fn, 'B', size=48)
        self._set_color(pdf, '#1a1a1a')
        pdf.cell(0, 20, spaced_ticker, align='C', new_x='LMARGIN', new_y='NEXT')

        # Date
        pdf.set_font(fn, size=16)
        self._set_color(pdf, '#555555')
        pdf.cell(0, 10, analysis_date, align='C', new_x='LMARGIN', new_y='NEXT')

        pdf.ln(20)

        # Brand lines
        pdf.set_font(fn, size=13)
        self._set_color(pdf, '#888888')
        pdf.cell(0, 8, get_pdf_label('cover_title', language), align='C', new_x='LMARGIN', new_y='NEXT')
        pdf.cell(0, 8, get_pdf_label('cover_subtitle', language), align='C', new_x='LMARGIN', new_y='NEXT')

        pdf.set_text_color(0, 0, 0)

    def _build_toc_page(self, pdf: FPDF, reports: list, has_chart: bool,
                        teams: list, language: str):
        """Table of contents page"""
        fn = self._fn()
        pdf.add_page()

        # TOC title
        pdf.set_font(fn, 'B', size=22)
        self._set_color(pdf, '#1e3a5f')
        pdf.cell(0, 12, get_pdf_label('toc_title', language), align='L', new_x='LMARGIN', new_y='NEXT')

        # Horizontal rule
        pdf.set_draw_color(44, 62, 80)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + pdf.epw, pdf.get_y())
        pdf.ln(6)

        report_analyst_names = [r.get('analyst_name', '') for r in reports]

        # Report Content header
        pdf.set_font(fn, 'B', size=12)
        self._set_color(pdf, '#2c3e50')
        pdf.cell(0, 8, get_pdf_label('report_content', language), new_x='LMARGIN', new_y='NEXT')

        # Chart entry
        if has_chart:
            pdf.set_font(fn, size=11)
            self._set_color(pdf, '#555555')
            pdf.cell(8, 7, '')  # indent
            pdf.cell(0, 7, get_pdf_label('price_chart', language),
                     new_x='LMARGIN', new_y='NEXT')

        if teams:
            for team in teams:
                team_count = sum(1 for m in team['members'] if m in report_analyst_names)
                if team_count == 0:
                    continue

                pdf.ln(3)
                pdf.set_font(fn, 'B', size=12)
                self._set_color(pdf, '#2c3e50')
                members_label = get_pdf_label('members', language)
                pdf.cell(0, 8, f"{team['name']}  ({team_count} {members_label})",
                         new_x='LMARGIN', new_y='NEXT')

                pdf.set_font(fn, size=11)
                self._set_color(pdf, '#555555')
                for member in team['members']:
                    if member in report_analyst_names:
                        pdf.cell(12, 7, '')  # indent
                        pdf.cell(0, 7, f'- {member}', new_x='LMARGIN', new_y='NEXT')

        pdf.set_text_color(0, 0, 0)

    def _build_chart_page(self, pdf: FPDF, ticker: str, price_data: list,
                          price_stats: dict, language: str):
        """Price chart + statistics page"""
        fn = self._fn()
        pdf.add_page()

        # Section title
        pdf.set_font(fn, 'B', size=18)
        self._set_color(pdf, '#1e3a5f')
        pdf.cell(0, 10, get_pdf_label('price_chart', language),
                 new_x='LMARGIN', new_y='NEXT')
        pdf.set_draw_color(44, 62, 80)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + pdf.epw, pdf.get_y())
        pdf.ln(4)

        # Chart image
        if price_data and len(price_data) >= 5:
            try:
                chart_bytes = self._generate_price_chart(price_data, ticker)
                if chart_bytes:
                    chart_buf = io.BytesIO(chart_bytes)
                    pdf.image(chart_buf, w=pdf.epw, h=pdf.epw * 0.6)
                    pdf.ln(5)
            except Exception as e:
                print(f'Chart generation failed: {e}')
                pdf.set_font(fn, size=10)
                pdf.cell(0, 6, get_pdf_label('chart_failed', language),
                         new_x='LMARGIN', new_y='NEXT')

        # Price statistics table
        if price_stats:
            pdf.set_font(fn, 'B', size=13)
            self._set_color(pdf, '#2c3e50')
            pdf.cell(0, 8, get_pdf_label('price_stats', language),
                     new_x='LMARGIN', new_y='NEXT')
            pdf.ln(2)

            growth_rate = price_stats.get('growth_rate', 0)
            growth_text = f'+{growth_rate:.2f}%' if growth_rate >= 0 else f'{growth_rate:.2f}%'
            duration = price_stats.get('duration_days', 0)

            stats_rows = [
                [get_pdf_label('item', language), get_pdf_label('value', language)],
                [get_pdf_label('total_return', language), growth_text],
                [get_pdf_label('analysis_period', language),
                 f"{duration} {get_pdf_label('days', language)}"],
                [get_pdf_label('start_date', language), price_stats.get('start_date', '')],
                [get_pdf_label('end_date', language), price_stats.get('end_date', '')],
                [get_pdf_label('start_price', language), f"${price_stats.get('start_price', 0):.2f}"],
                [get_pdf_label('end_price', language), f"${price_stats.get('end_price', 0):.2f}"],
            ]
            self._add_table(pdf, stats_rows)

        pdf.set_text_color(0, 0, 0)

    def _build_team_separator_page(self, pdf: FPDF, team_name: str,
                                   member_count: int, language: str):
        """Team separator page — large centred team name"""
        fn = self._fn()
        pdf.add_page()
        pdf.ln(80)

        # Team name — spaced letters for Chinese
        if language == 'zh-TW':
            spaced_name = ' '.join(team_name)
        else:
            spaced_name = team_name

        pdf.set_font(fn, 'B', size=36)
        self._set_color(pdf, '#2c3e50')
        pdf.cell(0, 18, spaced_name, align='C', new_x='LMARGIN', new_y='NEXT')

        # Member count
        members_label = get_pdf_label('members', language)
        pdf.set_font(fn, size=18)
        self._set_color(pdf, '#7f8c8d')
        pdf.cell(0, 12, f'({member_count} {members_label})',
                 align='C', new_x='LMARGIN', new_y='NEXT')

        pdf.set_text_color(0, 0, 0)

    def _build_analyst_section(self, pdf: FPDF, analyst_name: str,
                                ticker: str, analysis_date: str,
                                report_content: str):
        """Analyst report page"""
        fn = self._fn()
        pdf.add_page()

        # Section title
        pdf.set_font(fn, 'B', size=18)
        self._set_color(pdf, '#1e3a5f')
        pdf.cell(0, 10, analyst_name, new_x='LMARGIN', new_y='NEXT')

        # Subtitle
        pdf.set_font(fn, size=11)
        self._set_color(pdf, '#666666')
        pdf.cell(0, 7, f'{ticker}  |  {analysis_date}',
                 new_x='LMARGIN', new_y='NEXT')

        # Divider
        pdf.set_draw_color(44, 62, 80)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + pdf.epw, pdf.get_y())
        pdf.ln(4)

        pdf.set_text_color(51, 51, 51)

        # Process content
        content = self._replace_emojis(report_content)
        lines = content.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i]
            line_stripped = line.strip()

            if not line_stripped:
                pdf.ln(2)
                i += 1
                continue

            # Detect markdown table
            if '|' in line_stripped and not line_stripped.startswith('#'):
                table_data, end_idx = self._parse_markdown_table(lines, i)
                if table_data and len(table_data) > 1:
                    pdf.ln(2)
                    self._add_table(pdf, table_data)
                    i = end_idx
                    continue

            self._add_section_line(pdf, line)
            i += 1

        pdf.set_text_color(0, 0, 0)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_combined_report_pdf(
        self,
        ticker: str,
        analysis_date: str,
        reports: list,
        price_data: list = None,
        price_stats: dict = None,
        language: str = 'zh-TW',
    ) -> bytes:
        """
        Generate a combined PDF containing all analyst reports.

        Args:
            ticker: Stock ticker symbol
            analysis_date: Date of analysis
            reports: List of dicts with 'analyst_name' and 'report_content'
            price_data: Optional list of OHLC price data dicts
            price_stats: Optional dict with growth_rate, duration_days, etc.
            language: 'en' or 'zh-TW'

        Returns:
            PDF file content as bytes
        """
        if language == 'en':
            TEAMS = [
                {
                    'name': 'Analysts Team',
                    'members': ['Market Analyst', 'Social Media Analyst',
                                'News Analyst', 'Fundamentals Analyst'],
                },
                {
                    'name': 'Research Team',
                    'members': ['Bull Researcher', 'Bear Researcher', 'Research Manager'],
                },
                {
                    'name': 'Trading & Risk Team',
                    'members': ['Trader', 'Aggressive Analyst', 'Conservative Analyst',
                                'Neutral Analyst', 'Risk Manager'],
                },
            ]
        else:
            TEAMS = [
                {
                    'name': '分析師團隊',
                    'members': ['市場分析師', '社群媒體分析師', '新聞分析師', '基本面分析師'],
                },
                {
                    'name': '研究團隊',
                    'members': ['看漲研究員', '看跌研究員', '研究經理'],
                },
                {
                    'name': '交易與風險團隊',
                    'members': ['交易員', '激進分析師', '保守分析師', '中立分析師', '風險經理'],
                },
            ]

        report_map = {r.get('analyst_name', ''): r.get('report_content', '')
                      for r in reports}
        has_chart = bool(price_data and len(price_data) >= 5)

        pdf = self._new_pdf()

        # 1. Cover page (page 1 — no footer)
        self._build_cover_page(pdf, ticker, analysis_date, language)

        # 2. TOC page (page 2 — no footer)
        self._build_toc_page(pdf, reports, has_chart, TEAMS, language)

        # 3. Content pages start here (footer shows page numbers)
        # Chart page
        if has_chart:
            self._build_chart_page(pdf, ticker, price_data, price_stats, language)

        # Team separator + analyst sections
        for team in TEAMS:
            team_reports = []
            for member_name in team['members']:
                if member_name in report_map and report_map[member_name]:
                    team_reports.append({
                        'analyst_name': member_name,
                        'report_content': report_map[member_name],
                    })

            if not team_reports:
                continue

            self._build_team_separator_page(
                pdf, team['name'], len(team_reports), language)

            for report in team_reports:
                self._build_analyst_section(
                    pdf=pdf,
                    analyst_name=report['analyst_name'],
                    ticker=ticker,
                    analysis_date=analysis_date,
                    report_content=report['report_content'],
                )

        return bytes(pdf.output())

    def generate_analyst_report_pdf(
        self,
        analyst_name: str,
        ticker: str,
        analysis_date: str,
        report_content: str,
        price_data: list = None,
        price_stats: dict = None,
    ) -> bytes:
        """
        Generate a single-analyst PDF report.

        Args:
            analyst_name: Name of the analyst
            ticker: Stock ticker symbol
            analysis_date: Date of analysis
            report_content: Markdown formatted report content
            price_data: Optional OHLC price data
            price_stats: Optional price statistics dict

        Returns:
            PDF file content as bytes
        """
        pdf = self._new_pdf()
        pdf._cover_toc_pages = 0  # All pages get page numbers

        fn = self._fn()

        # Cover
        pdf.add_page()
        pdf.ln(50)
        pdf.set_font(fn, 'B', size=36)
        self._set_color(pdf, '#1a1a1a')
        pdf.cell(0, 16, '  '.join(ticker), align='C', new_x='LMARGIN', new_y='NEXT')
        pdf.set_font(fn, size=14)
        self._set_color(pdf, '#555555')
        pdf.cell(0, 8, analysis_date, align='C', new_x='LMARGIN', new_y='NEXT')
        pdf.ln(10)
        pdf.set_font(fn, 'B', size=16)
        self._set_color(pdf, '#2c3e50')
        pdf.cell(0, 10, analyst_name, align='C', new_x='LMARGIN', new_y='NEXT')
        pdf.set_text_color(0, 0, 0)

        # Chart + stats page
        if price_data and price_stats and len(price_data) >= 5:
            self._build_chart_page(pdf, ticker, price_data, price_stats, language='zh-TW')

        # Report content
        self._build_analyst_section(
            pdf=pdf,
            analyst_name=analyst_name,
            ticker=ticker,
            analysis_date=analysis_date,
            report_content=report_content,
        )

        return bytes(pdf.output())
