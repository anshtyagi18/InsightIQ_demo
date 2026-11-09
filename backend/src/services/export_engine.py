"""
Multi-Format Export Engine for Insightia / InsightIQ.
Generates:
1. Cleaned CSV (.csv)
2. Formatted Excel with professional styles & metadata tab (.xlsx)
3. Clean JSON schema (.json)
4. Executive PDF Summary Report with KPI summary & charts (.pdf)
"""

import io
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .data_engine import DataEngine, sanitize_value


class ExportEngine:
    """Enterprise multi-format export generator."""

    @staticmethod
    def export_csv(df: pd.DataFrame) -> bytes:
        """Export cleaned dataframe as UTF-8 CSV bytes."""
        buffer = io.StringIO()
        df.to_csv(buffer, index=False, encoding='utf-8')
        return buffer.getvalue().encode('utf-8')

    @staticmethod
    def export_json(df: pd.DataFrame, profile: Optional[Dict[str, Any]] = None) -> bytes:
        """Export cleaned dataset and schema metadata as formatted JSON bytes."""
        export_payload = {
            "metadata": {
                "exported_at": datetime.utcnow().isoformat(),
                "row_count": len(df),
                "col_count": len(df.columns),
                "health_score": profile.get("health_score", 100) if profile else 100,
            },
            "columns": list(df.columns),
            "records": df.to_dict(orient="records"),
        }
        sanitized = sanitize_value(export_payload)
        return json.dumps(sanitized, indent=2).encode('utf-8')

    @staticmethod
    def export_excel(df: pd.DataFrame, dataset_name: str = "Dataset", profile: Optional[Dict[str, Any]] = None) -> bytes:
        """
        Export styled Excel workbook with:
        - Sheet 1: Cleaned Data with dark header, borders, alternating rows, auto column widths
        - Sheet 2: Executive Summary & Health Report
        """
        wb = Workbook()
        
        # Sheet 1: Data
        ws_data = wb.active
        ws_data.title = "Cleaned Data"

        # Styles
        header_fill = PatternFill(start_color="18181B", end_color="18181B", fill_type="solid")  # Zinc-900
        header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
        row_alt_fill = PatternFill(start_color="F4F4F5", end_color="F4F4F5", fill_type="solid")
        thin_border = Border(
            left=Side(style='thin', color='E4E4E7'),
            right=Side(style='thin', color='E4E4E7'),
            top=Side(style='thin', color='E4E4E7'),
            bottom=Side(style='thin', color='E4E4E7')
        )
        data_font = Font(name="Segoe UI", size=10)

        # Write Headers
        headers = list(df.columns)
        for col_idx, header in enumerate(headers, 1):
            cell = ws_data.cell(row=1, column=col_idx, value=str(header))
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = thin_border
        ws_data.row_dimensions[1].height = 28

        # Write Data Rows
        for row_idx, row in enumerate(df.itertuples(index=False), 2):
            is_alt = (row_idx % 2 == 0)
            ws_data.row_dimensions[row_idx].height = 20
            for col_idx, value in enumerate(row, 1):
                # Clean value for Excel
                if pd.isna(value):
                    val_str = ""
                elif isinstance(value, (pd.Timestamp, datetime)):
                    val_str = value.strftime("%Y-%m-%d %H:%M")
                else:
                    val_str = value

                cell = ws_data.cell(row=row_idx, column=col_idx, value=val_str)
                cell.font = data_font
                cell.border = thin_border
                if is_alt:
                    cell.fill = row_alt_fill
                
                # Number alignment
                if isinstance(value, (int, float, np.number)) and not pd.isna(value):
                    cell.alignment = Alignment(horizontal="right", vertical="center")
                else:
                    cell.alignment = Alignment(horizontal="left", vertical="center")

        # Auto-adjust column widths
        for col_idx, col in enumerate(df.columns, 1):
            col_letter = get_column_letter(col_idx)
            max_len = len(str(col))
            # Sample up to 100 rows for speed
            for cell_val in df[col].dropna().head(100):
                max_len = max(max_len, len(str(cell_val)))
            ws_data.column_dimensions[col_letter].width = min(max(max_len + 4, 12), 40)

        # Sheet 2: Executive Summary
        ws_summary = wb.create_sheet(title="Executive Summary")
        ws_summary.views.sheetView[0].showGridLines = True

        title_font = Font(name="Segoe UI", size=16, bold=True, color="18181B")
        subtitle_font = Font(name="Segoe UI", size=11, color="71717A")
        section_font = Font(name="Segoe UI", size=12, bold=True, color="09090B")
        badge_font = Font(name="Segoe UI", size=14, bold=True, color="FFFFFF")

        ws_summary.cell(row=2, column=2, value="Insightia Executive Summary").font = title_font
        ws_summary.cell(row=3, column=2, value=f"Dataset: {dataset_name} | Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}").font = subtitle_font

        # Health Score card
        score = profile.get("health_score", 100) if profile else 100
        health_color = "10B981" if score >= 85 else "F59E0B" if score >= 65 else "EF4444"
        score_cell = ws_summary.cell(row=5, column=2, value=f"Data Health Score: {score}%")
        score_cell.font = badge_font
        score_cell.fill = PatternFill(start_color=health_color, end_color=health_color, fill_type="solid")
        score_cell.alignment = Alignment(horizontal="center", vertical="center")
        ws_summary.row_dimensions[5].height = 26

        # Key Metrics Table
        ws_summary.cell(row=7, column=2, value="Dataset Metrics").font = section_font
        metrics = [
            ("Total Rows", len(df)),
            ("Total Columns", len(df.columns)),
            ("Missing Values", int(df.isna().sum().sum())),
            ("Duplicate Rows", int(df.duplicated().sum())),
            ("Memory Usage", f"{df.memory_usage(deep=True).sum() / (1024 * 1024):.2f} MB")
        ]
        for m_idx, (m_label, m_val) in enumerate(metrics, 8):
            c1 = ws_summary.cell(row=m_idx, column=2, value=m_label)
            c2 = ws_summary.cell(row=m_idx, column=3, value=m_val)
            c1.font = data_font
            c2.font = Font(name="Segoe UI", size=10, bold=True)
            c1.border = thin_border
            c2.border = thin_border
            c2.alignment = Alignment(horizontal="right")

        ws_summary.column_dimensions["B"].width = 28
        ws_summary.column_dimensions["C"].width = 24

        output = io.BytesIO()
        wb.save(output)
        return output.getvalue()

    @staticmethod
    def export_pdf(df: pd.DataFrame, dataset_name: str = "Dataset", profile: Optional[Dict[str, Any]] = None) -> bytes:
        """
        Generate executive PDF Summary Report with:
        - Modern dark/indigo corporate banner
        - Health score gauge badge
        - Executive KPI summary grid
        - Column schema & statistics summary table
        - Automated strategic insights
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        # Custom typography styles
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=22,
            leading=26,
            textColor=colors.HexColor('#09090b')
        )
        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#71717a')
        )
        h2_style = ParagraphStyle(
            'SectionH2',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=18,
            textColor=colors.HexColor('#18181b'),
            spaceBefore=14,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            'BodyTextCustom',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#27272a')
        )
        badge_style = ParagraphStyle(
            'BadgeStyle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=14,
            textColor=colors.white,
            alignment=1  # Centered
        )

        elements = []

        # 1. Header Banner
        header_table = Table(
            [
                [
                    Paragraph("<b>INSIGHTIA</b> <font color='#6366f1'>AI Data Platform</font>", title_style),
                    Paragraph(f"<b>Generated:</b> {datetime.utcnow().strftime('%b %d, %Y %H:%M UTC')}<br/><font color='#71717a'>Executive Data Intelligence Report</font>", subtitle_style)
                ]
            ],
            colWidths=[4.2 * inch, 3.0 * inch]
        )
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(header_table)
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#e4e4e7'), spaceBefore=4, spaceAfter=14))

        # 2. Executive Health & KPI Overview
        health_score = profile.get("health_score", 100) if profile else 100
        health_bg = colors.HexColor('#10b981') if health_score >= 85 else colors.HexColor('#f59e0b') if health_score >= 65 else colors.HexColor('#ef4444')
        health_text = "EXCELLENT" if health_score >= 85 else "MODERATE" if health_score >= 65 else "CRITICAL"

        score_p = Paragraph(f"DATA HEALTH SCORE<br/><font size=20><b>{health_score}%</b></font><br/>{health_text}", badge_style)
        
        kpi_rows = len(df)
        kpi_cols = len(df.columns)
        kpi_nulls = int(df.isna().sum().sum())
        kpi_dups = int(df.duplicated().sum())

        kpi_table_data = [
            [
                score_p,
                Paragraph(f"<b>Total Rows</b><br/><font size=14 color='#09090b'><b>{kpi_rows:,}</b></font><br/><font size=7 color='#71717a'>Complete records</font>", body_style),
                Paragraph(f"<b>Features</b><br/><font size=14 color='#09090b'><b>{kpi_cols}</b></font><br/><font size=7 color='#71717a'>Dataset columns</font>", body_style),
                Paragraph(f"<b>Missing Cells</b><br/><font size=14 color='#{('10b981' if kpi_nulls == 0 else 'ef4444')}'><b>{kpi_nulls}</b></font><br/><font size=7 color='#71717a'>{(kpi_nulls / max(1, kpi_rows * kpi_cols) * 100):.1f}% null rate</font>", body_style),
                Paragraph(f"<b>Duplicates</b><br/><font size=14 color='#{('10b981' if kpi_dups == 0 else 'f59e0b')}'><b>{kpi_dups}</b></font><br/><font size=7 color='#71717a'>Redundant rows</font>", body_style),
            ]
        ]
        kpi_table = Table(kpi_table_data, colWidths=[1.8 * inch, 1.35 * inch, 1.35 * inch, 1.35 * inch, 1.35 * inch])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), health_bg),
            ('BACKGROUND', (1, 0), (-1, 0), colors.HexColor('#f8fafc')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('INNERGRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(kpi_table)
        elements.append(Spacer(1, 14))

        # 3. Key Automated Findings & Strategic Insights
        elements.append(Paragraph("<b>Strategic Insights & Statistical Findings</b>", h2_style))
        insights = profile.get("insights", []) if profile else []
        if not insights:
            insights = [
                {"title": "Data Ingestion Validated", "description": f"Dataset '{dataset_name}' successfully processed with {kpi_rows} rows and {kpi_cols} dimensions."}
            ]

        for ins in insights[:4]:  # Top 4 insights
            ins_title = ins.get("title", "Insight")
            ins_desc = ins.get("description", "")
            ins_p = Paragraph(f"• <b>{ins_title}</b>: <font color='#4b5563'>{ins_desc}</font>", body_style)
            elements.append(ins_p)
            elements.append(Spacer(1, 4))

        elements.append(Spacer(1, 10))

        # 4. Column Schema & Data Distribution Table
        elements.append(Paragraph("<b>Schema Specification & Quality Breakdown</b>", h2_style))

        schema_headers = ["Column Name", "Type", "Missing", "Unique", "Distribution / Range"]
        schema_rows = [schema_headers]

        cols_info = profile.get("columns", []) if profile else []
        for col_data in cols_info[:15]:  # Top 15 columns for PDF report layout
            c_name = col_data.get("name", "")
            c_type = col_data.get("type", "text").upper()
            c_null = f"{col_data.get('missing_count', 0)} ({col_data.get('missing_pct', 0)}%)"
            c_uniq = str(col_data.get("unique_count", "-"))
            
            stats = col_data.get("stats", {})
            if c_type == "NUMERIC" and stats:
                c_dist = f"[{stats.get('min', 0)} → {stats.get('max', 0)}], μ={stats.get('mean', 0)}"
            else:
                top_v = col_data.get("top_values", [])
                c_dist = ", ".join([v["name"] for v in top_v[:3]]) if top_v else "-"

            schema_rows.append([
                Paragraph(f"<b>{c_name}</b>", body_style),
                Paragraph(f"<font color='#6366f1'>{c_type}</font>", body_style),
                Paragraph(c_null, body_style),
                Paragraph(c_uniq, body_style),
                Paragraph(c_dist[:40], body_style)
            ])

        schema_table = Table(schema_rows, colWidths=[1.8 * inch, 0.9 * inch, 1.1 * inch, 0.8 * inch, 2.6 * inch])
        schema_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#18181b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(schema_table)

        # Build PDF
        doc.build(elements)
        return buffer.getvalue()

