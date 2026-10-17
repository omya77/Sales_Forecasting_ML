"""
SalesForecast AI PRO — Executive Demand Intelligence PDF Generator
Generates publication-quality, multi-page PDF reports using ReportLab & Matplotlib.
Guarantees 100% data visibility, crisp vector formatting, and fail-safe direct downloads.
"""

import io
import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    KeepTogether,
    HRFlowable
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to compute dynamic total page count ('Page X of Y')
    and print an executive confidential header/footer stamp on every page.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Footer divider line
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.75)
        self.line(36, 32, A4[0] - 36, 32)

        # Footer Left: Confidentiality Stamp
        self.drawString(
            36, 20,
            "SalesForecast AI PRO — Confidential Executive Report • Multi-Step Recursive Forecast Ledger"
        )

        # Footer Right: Page X of Y
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(A4[0] - 36, 20, page_str)

        self.restoreState()


def render_forecast_chart_image(dates_str, preds, lower, upper):
    """
    Renders a high-resolution forecast trajectory chart with 95% Confidence Interval
    and returns an in-memory BytesIO image stream.
    """
    # Parse dates if strings
    parsed_dates = []
    for d in dates_str:
        if isinstance(d, str):
            try:
                parsed_dates.append(datetime.datetime.strptime(d, "%Y-%m-%d"))
            except ValueError:
                parsed_dates.append(d)
        else:
            parsed_dates.append(d)

    fig, ax = plt.subplots(figsize=(8.2, 2.7), dpi=180)
    fig.patch.set_facecolor('#ffffff')
    ax.set_facecolor('#fafafa')

    # Confidence interval band
    ax.fill_between(
        range(len(parsed_dates)),
        lower,
        upper,
        color='#06b6d4',
        alpha=0.15,
        label='95% Confidence Interval'
    )
    ax.plot(
        range(len(parsed_dates)),
        upper,
        color='#94a3b8',
        linestyle='--',
        linewidth=1.0,
        alpha=0.8
    )
    ax.plot(
        range(len(parsed_dates)),
        lower,
        color='#94a3b8',
        linestyle='--',
        linewidth=1.0,
        alpha=0.8
    )

    # Predicted sales line
    ax.plot(
        range(len(parsed_dates)),
        preds,
        color='#0284c7',
        linewidth=2.2,
        marker='o',
        markersize=3.5 if len(parsed_dates) <= 30 else 1.8,
        label='Projected Sales (Rs.)'
    )

    # X-axis label sampling
    step_sample = max(1, len(parsed_dates) // 10)
    sample_indices = list(range(0, len(parsed_dates), step_sample))
    if (len(parsed_dates) - 1) not in sample_indices:
        sample_indices.append(len(parsed_dates) - 1)

    labels = []
    for idx in sample_indices:
        dt = parsed_dates[idx]
        if isinstance(dt, datetime.datetime):
            labels.append(dt.strftime("%d %b"))
        else:
            labels.append(str(dt))

    ax.set_xticks(sample_indices)
    ax.set_xticklabels(labels, fontsize=7.5, color='#475569', rotation=0)

    # Y-axis formatter in 'Rs. Xk'
    def inr_fmt(x, p):
        if x >= 1000000:
            return f"Rs. {x/100000:.1f}L"
        elif x >= 1000:
            return f"Rs. {x/1000:.0f}k"
        return f"Rs. {x:.0f}"

    ax.yaxis.set_major_formatter(plt.FuncFormatter(inr_fmt))
    ax.tick_params(axis='y', labelsize=7.5, colors='#475569')

    # Grid styling
    ax.grid(True, linestyle=':', alpha=0.6, color='#cbd5e1')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#cbd5e1')
    ax.spines['bottom'].set_color('#cbd5e1')

    # Legend
    ax.legend(
        loc='upper right',
        frameon=True,
        facecolor='#ffffff',
        edgecolor='#e2e8f0',
        fontsize=7.5
    )

    plt.title(
        "Simulated Sales Trajectory & 95% Confidence Interval Bounds",
        fontsize=9,
        fontweight='bold',
        color='#0f172a',
        pad=6
    )

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=180)
    plt.close(fig)
    buf.seek(0)
    return buf


def generate_forecast_pdf(forecast_data, selected_days, selected_model_name):
    """
    Generates a complete, multi-page ReportLab PDF document
    and returns the binary stream.
    """
    buffer = io.BytesIO()
    # A4 dimensions in points: 595.27 x 841.89
    # Margins: 36 pt (0.5 inch)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=42
    )

    styles = getSampleStyleSheet()

    # Custom Typography Styles
    style_brand = ParagraphStyle(
        'DocBrand',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=colors.HexColor('#0f172a')
    )
    style_brand_sub = ParagraphStyle(
        'DocBrandSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#64748b')
    )
    style_meta_label = ParagraphStyle(
        'DocMetaLabel',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        alignment=2, # Right aligned
        textColor=colors.HexColor('#475569')
    )
    style_meta_val = ParagraphStyle(
        'DocMetaVal',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        alignment=2,
        textColor=colors.HexColor('#1e1b4b')
    )
    style_section_title = ParagraphStyle(
        'DocSecTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#0f172a')
    )
    style_kpi_label = ParagraphStyle(
        'DocKPILabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor('#475569')
    )
    style_kpi_val = ParagraphStyle(
        'DocKPIVal',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#1e1b4b')
    )
    style_kpi_sub = ParagraphStyle(
        'DocKPISub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        leading=9,
        textColor=colors.HexColor('#64748b')
    )
    style_th = ParagraphStyle(
        'DocTH',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9,
        textColor=colors.white,
        alignment=1 # Center
    )
    style_td = ParagraphStyle(
        'DocTD',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor('#0f172a')
    )
    style_td_bold = ParagraphStyle(
        'DocTDBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor('#0f172a')
    )
    style_td_num = ParagraphStyle(
        'DocTDNum',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9,
        alignment=2, # Right
        textColor=colors.HexColor('#0284c7')
    )
    style_td_ci = ParagraphStyle(
        'DocTDCI',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        leading=9,
        alignment=2, # Right
        textColor=colors.HexColor('#64748b')
    )
    style_td_badge_wknd = ParagraphStyle(
        'DocTDBadgeWknd',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=6.5,
        leading=8,
        alignment=1, # Center
        textColor=colors.HexColor('#b45309')
    )
    style_td_badge_wkd = ParagraphStyle(
        'DocTDBadgeWkd',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=6.5,
        leading=8,
        alignment=1, # Center
        textColor=colors.HexColor('#0284c7')
    )

    story = []

    # ---------------------------------------------------------
    # 1. Executive Header Block
    # ---------------------------------------------------------
    report_gen_time = datetime.datetime.now().strftime("%d %b %Y, %I:%M %p")
    header_left = [
        Paragraph("SalesForecast AI — Demand Intelligence Report", style_brand),
        Spacer(1, 2),
        Paragraph("Empirical Machine Learning Production Engine • Time-Series Forecast Ledger", style_brand_sub),
    ]

    header_right = [
        Paragraph(f"<b>Forecast Horizon:</b> {selected_days} Days Forward", style_meta_val),
        Paragraph(f"<b>Model:</b> {selected_model_name}", style_meta_label),
        Paragraph(f"<b>Generated:</b> {report_gen_time}", style_meta_label),
    ]

    header_table = Table(
        [[header_left, header_right]],
        colWidths=[340, 183]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)

    story.append(HRFlowable(
        width="100%",
        thickness=2,
        color=colors.HexColor('#4f46e5'),
        spaceBefore=4,
        spaceAfter=12
    ))

    # ---------------------------------------------------------
    # 2. Key Performance Indicators (3-Bento Grid)
    # ---------------------------------------------------------
    total_rev = forecast_data.get('total_forecasted_sales', 0.0)
    daily_avg = forecast_data.get('avg_daily_forecast', 0.0)
    start_date = forecast_data.get('start_forecast_date', '')
    end_date = forecast_data.get('end_forecast_date', '')

    kpi1_content = [
        Paragraph("PROJECTED REVENUE", style_kpi_label),
        Spacer(1, 2),
        Paragraph(f"Rs. {total_rev:,.2f}", style_kpi_val),
        Spacer(1, 2),
        Paragraph(f"{selected_days} Days Horizon ({start_date} → {end_date})", style_kpi_sub)
    ]

    kpi2_content = [
        Paragraph("DAILY RUN-RATE", style_kpi_label),
        Spacer(1, 2),
        Paragraph(f"Rs. {daily_avg:,.2f}", style_kpi_val),
        Spacer(1, 2),
        Paragraph("Projected Mean Run-Rate per Day", style_kpi_sub)
    ]

    kpi3_content = [
        Paragraph("PRODUCTION ALGORITHM", style_kpi_label),
        Spacer(1, 2),
        Paragraph(f"{selected_model_name}", style_kpi_val),
        Spacer(1, 2),
        Paragraph("Scikit-Learn Production Pipeline", style_kpi_sub)
    ]

    kpi_table = Table(
        [[kpi1_content, kpi2_content, kpi3_content]],
        colWidths=[174, 174, 175]
    )
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 12))

    # ---------------------------------------------------------
    # 3. High-Resolution Forecast Trajectory Chart
    # ---------------------------------------------------------
    breakdown = forecast_data.get('daily_breakdown', [])
    dates = [row['date'] for row in breakdown]
    preds = [row['predicted_sales'] for row in breakdown]
    lower = [row['lower_bound'] for row in breakdown]
    upper = [row['upper_bound'] for row in breakdown]

    if dates and preds:
        chart_stream = render_forecast_chart_image(dates, preds, lower, upper)
        chart_flowable = Image(chart_stream, width=523, height=172)
        chart_box = Table([[chart_flowable]], colWidths=[523])
        chart_box.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        story.append(chart_box)
        story.append(Spacer(1, 14))

    # ---------------------------------------------------------
    # 4. Chronological Forecast Schedule Table
    # ---------------------------------------------------------
    table_heading = [
        Paragraph(f"<b>Chronological Forecast Ledger ({len(breakdown)} Days Schedule)</b>", style_section_title),
        Paragraph("Day-by-day simulated receipts with recursive 95% Confidence Interval bounds", style_brand_sub)
    ]
    story.append(KeepTogether(table_heading))
    story.append(Spacer(1, 6))

    # Table Header Row
    table_data = [[
        Paragraph("Day #", style_th),
        Paragraph("Date", style_th),
        Paragraph("Day", style_th),
        Paragraph("Projected Sales", style_th),
        Paragraph("Lower 95% CI", style_th),
        Paragraph("Upper 95% CI", style_th),
        Paragraph("Signal", style_th)
    ]]

    # Table Body Rows
    row_styles = []
    current_row_idx = 1

    for row in breakdown:
        is_weekend = row.get('is_weekend', False)
        step_val = row.get('step', current_row_idx)
        date_str = row.get('date', '')
        day_name = row.get('day_name', '')
        pred_val = row.get('predicted_sales', 0.0)
        low_val = row.get('lower_bound', 0.0)
        up_val = row.get('upper_bound', 0.0)

        badge_p = Paragraph("Weekend Peak" if is_weekend else "Weekday", 
                            style_td_badge_wknd if is_weekend else style_td_badge_wkd)

        table_data.append([
            Paragraph(f"Day {step_val}", style_td),
            Paragraph(date_str, style_td_bold),
            Paragraph(day_name, style_td),
            Paragraph(f"Rs. {pred_val:,.2f}", style_td_num),
            Paragraph(f"Rs. {low_val:,.2f}", style_td_ci),
            Paragraph(f"Rs. {up_val:,.2f}", style_td_ci),
            badge_p
        ])

        if is_weekend:
            # Highlight weekend rows with a subtle amber/golden background
            row_styles.append(('BACKGROUND', (0, current_row_idx), (-1, current_row_idx), colors.HexColor('#fef3c7')))
        elif current_row_idx % 2 == 0:
            # Subtle zebra striping
            row_styles.append(('BACKGROUND', (0, current_row_idx), (-1, current_row_idx), colors.HexColor('#f8fafc')))

        current_row_idx += 1

    # Col Widths sum = 523 (matches printable width 595.27 - 72)
    # [45, 75, 60, 95, 84, 84, 80] = 523
    col_widths = [45, 75, 60, 95, 84, 84, 80]
    schedule_table = Table(table_data, colWidths=col_widths, repeatRows=1)

    base_table_styles = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]
    base_table_styles.extend(row_styles)

    schedule_table.setStyle(TableStyle(base_table_styles))
    story.append(schedule_table)

    # Build the document with two-pass NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer
