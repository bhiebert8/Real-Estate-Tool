# ========== ADD YOUR ORIGINAL generate_pdf_report FUNCTION HERE ==========
def generate_pdf_report(results, annual_table_html, refinance_details=None, pre_table=None, post_table=None,
                        plot_url=None):
    """Generate comprehensive real estate investment analysis PDF"""
    # DEBUG: Print what we're receiving
    print("DEBUG - PDF Generation:")
    print(f"Results keys: {list(results.keys()) if results else 'None'}")
    print(f"Results values: {results}")
    print(f"Annual table type: {type(annual_table_html)}")
    print(f"Annual table length: {len(annual_table_html) if annual_table_html else 0}")

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import inch, cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (Paragraph, Frame, Image, Spacer, Table, TableStyle,
                                    SimpleDocTemplate, PageBreak, KeepTogether, Flowable,
                                    HRFlowable, PageTemplate, BaseDocTemplate)
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY
    import tempfile
    import base64
    from datetime import datetime
    import pandas as pd
    import io

    # Professional color scheme
    PRIMARY_COLOR = colors.HexColor("#1e3a8a")  # Professional blue
    SECONDARY_COLOR = colors.HexColor("#059669")  # Success green
    WARNING_COLOR = colors.HexColor("#dc2626")  # Alert red
    ACCENT_COLOR = colors.HexColor("#7c3aed")  # Purple accent
    LIGHT_BLUE = colors.HexColor("#eff6ff")
    LIGHT_GREEN = colors.HexColor("#f0fdf4")
    LIGHT_GRAY = colors.HexColor("#f9fafb")
    DARK_GRAY = colors.HexColor("#374151")

    # Create document
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')

    # Page setup
    doc = SimpleDocTemplate(
        tmp.name,
        pagesize=letter,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch
    )

    # Build content
    story = []
    styles = getSampleStyleSheet()

    # Enhanced custom styles with proper wrapping
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=PRIMARY_COLOR,
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        leading=28
    )

    section_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=PRIMARY_COLOR,
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold',
        leading=19,
        leftIndent=0,
        rightIndent=0
    )

    subsection_style = ParagraphStyle(
        'SubsectionTitle',
        parent=styles['Heading3'],
        fontSize=14,
        textColor=DARK_GRAY,
        spaceAfter=8,
        spaceBefore=12,
        fontName='Helvetica-Bold',
        leading=16
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY,
        spaceAfter=8,
        leftIndent=0,
        rightIndent=0
    )

    bullet_style = ParagraphStyle(
        'BulletStyle',
        parent=body_style,
        leftIndent=20,
        bulletIndent=10,
        spaceAfter=4
    )

    # Parse key metrics for analysis
    try:
        print("DEBUG - Parsing metrics...")

        # Safe extraction with debugging
        initial_cash_str = results.get("initial_cash_outlay", "$0")
        print(f"Initial cash string: {initial_cash_str}")
        initial_cash = float(initial_cash_str.replace("$", "").replace(",", "")) if initial_cash_str else 0

        final_value_str = results.get("final_total_value", "$0")
        final_value = float(final_value_str.replace("$", "").replace(",", "")) if final_value_str else 0

        loan_amount_str = results.get("loan_amount", "$0")
        loan_amount = float(loan_amount_str.replace("$", "").replace(",", "")) if loan_amount_str else 0

        monthly_payment_str = results.get("monthly_payment", "$0")
        monthly_payment = float(monthly_payment_str.replace("$", "").replace(",", "")) if monthly_payment_str else 0

        ann_return_str = results.get('annualized_return', '0%')
        ann_return = float(ann_return_str.replace('%', '')) if ann_return_str else 0

        total_return_str = results.get('cumulative_return', '0%')
        total_return = float(total_return_str.replace('%', '')) if total_return_str else 0

        print(f"Parsed values: initial_cash={initial_cash}, final_value={final_value}, ann_return={ann_return}")

        # Calculate additional metrics
        total_investment = initial_cash + loan_amount
        leverage_ratio = loan_amount / total_investment if total_investment > 0 else 0
        total_profit = final_value - initial_cash

        # Try to parse annual table
        if annual_table_html and len(annual_table_html) > 0:
            annual_df = pd.read_html(annual_table_html)[0]
            first_year_rent_str = annual_df.iloc[0]["Annual Rent Income"]
            first_year_rent = float(first_year_rent_str.replace("$", "").replace(",", ""))

            debt_service_annual = monthly_payment * 12
            dscr = first_year_rent / debt_service_annual if debt_service_annual > 0 else 0

            first_year_cash_flow_str = annual_df.iloc[0]["Annual Cash Flow (After-Tax)"]
            first_year_cash_flow = float(first_year_cash_flow_str.replace("$", "").replace(",", ""))
            cash_on_cash = (first_year_cash_flow / initial_cash * 100) if initial_cash > 0 else 0
        else:
            print("DEBUG - No annual table data available")
            first_year_rent = 0
            debt_service_annual = 0
            dscr = 0
            first_year_cash_flow = 0
            cash_on_cash = 0

    except Exception as e:
        print(f"DEBUG - Error parsing metrics: {e}")
        import traceback
        traceback.print_exc()
        # Set safe defaults
        initial_cash = 0
        final_value = 0
        ann_return = 0
        total_return = 0
        leverage_ratio = 0
        dscr = 0
        cash_on_cash = 0
        first_year_cash_flow = 0
        first_year_rent = 0
        debt_service_annual = 0
        total_profit = 0
        loan_amount = 0
        monthly_payment = 0
        total_investment = 1  # Prevent division by zero

    # ==================== COVER PAGE ====================
    story.append(Spacer(1, 1 * inch))

    # Title
    story.append(Paragraph("REAL ESTATE INVESTMENT ANALYSIS", title_style))
    story.append(Spacer(1, 0.3 * inch))

    # Property name
    property_name = results.get("house_name", "Investment Property")
    story.append(Paragraph(property_name, ParagraphStyle('PropertyName', parent=title_style,
                                                         fontSize=18, textColor=SECONDARY_COLOR)))
    story.append(Spacer(1, 0.5 * inch))

    # Executive summary box - ReportLab compatible
    recommendation = 'BUY' if ann_return >= 12 else 'CONSIDER' if ann_return >= 8 else 'CAUTION'
    risk_level = 'Low' if dscr > 1.5 and cash_on_cash > 8 else 'Medium' if dscr > 1.2 else 'High'

    exec_summary = f"INVESTMENT RECOMMENDATION: {recommendation}\nTarget Return: {ann_return:.1f}% annually\nTotal Profit Potential: ${total_profit:,.0f}\nRisk Level: {risk_level}"

    exec_box_data = [[exec_summary]]
    exec_table = Table(exec_box_data, colWidths=[5 * inch])
    exec_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GREEN if ann_return >= 12 else LIGHT_BLUE),
        ('BORDER', (0, 0), (-1, -1), 2, SECONDARY_COLOR if ann_return >= 12 else PRIMARY_COLOR),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 20),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
        ('LEFTPADDING', (0, 0), (-1, -1), 20),
        ('RIGHTPADDING', (0, 0), (-1, -1), 20),
    ]))
    story.append(exec_table)

    story.append(Spacer(1, 0.3 * inch))

    # Key metrics table with improved rating logic
    metrics_data = [
        ['METRIC', 'VALUE', 'BENCHMARK', 'RATING'],
        ['Initial Investment', f'${initial_cash:,.0f}', 'Varies', '—'],
        ['Projected Annual Return', f'{ann_return:.1f}%', '10-15%',
         '★★★★★' if ann_return >= 15 else '★★★★' if ann_return >= 12 else '★★★' if ann_return >= 8 else '★★' if ann_return >= 5 else '★'],
        ['Cash-on-Cash Return', f'{cash_on_cash:.1f}%', '8-12%',
         '★★★★★' if cash_on_cash >= 12 else '★★★★' if cash_on_cash >= 8 else '★★★' if cash_on_cash >= 4 else '★★' if cash_on_cash >= 0 else '★'],
        ['Debt Service Coverage', f'{dscr:.2f}x', '>1.25x',
         '★★★★★' if dscr >= 1.5 else '★★★★' if dscr >= 1.25 else '★★★' if dscr >= 1.1 else '★★' if dscr >= 1.0 else '★'],
        ['Leverage Ratio', f'{leverage_ratio * 100:.0f}%', '70-80%',
         '★★★★★' if 0.75 <= leverage_ratio <= 0.8 else '★★★★' if 0.7 <= leverage_ratio <= 0.85 else '★★★' if 0.6 <= leverage_ratio <= 0.9 else '★★'],
    ]

    metrics_table = Table(metrics_data, colWidths=[1.8 * inch, 1.2 * inch, 1 * inch, 1 * inch])
    metrics_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        # Data
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(metrics_table)

    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph(f"Analysis prepared on {datetime.now().strftime('%B %d, %Y')}",
                           ParagraphStyle('DateStyle', parent=body_style, alignment=TA_CENTER, fontSize=10)))

    story.append(PageBreak())

    # ==================== EXECUTIVE SUMMARY ====================
    story.append(Paragraph("EXECUTIVE SUMMARY", section_style))

    # Investment thesis
    if ann_return >= 15:
        thesis = "This property presents an <b>exceptional investment opportunity</b> with projected returns significantly exceeding market averages."
    elif ann_return >= 12:
        thesis = "This property offers <b>strong investment potential</b> with above-market returns and solid fundamentals."
    elif ann_return >= 8:
        thesis = "This property provides <b>reasonable returns</b> suitable for conservative investors seeking steady cash flow."
    else:
        thesis = "This property shows <b>modest returns</b> that may not justify the investment risk. Consider other opportunities."

    story.append(Paragraph(thesis, body_style))
    story.append(Spacer(1, 0.2 * inch))

    # Key findings
    story.append(Paragraph("Key Investment Highlights:", subsection_style))

    highlights = []
    if ann_return >= 12:
        highlights.append("• Exceptional annual return potential of {:.1f}%".format(ann_return))
    if cash_on_cash >= 8:
        highlights.append("• Strong cash-on-cash return of {:.1f}%".format(cash_on_cash))
    if dscr >= 1.25:
        highlights.append("• Healthy debt service coverage ratio of {:.2f}x".format(dscr))
    if leverage_ratio >= 0.7:
        highlights.append("• Effective use of leverage at {:.0f}%".format(leverage_ratio * 100))

    highlights.append("• Total profit potential of ${:,.0f} over investment period".format(total_profit))

    for highlight in highlights:
        story.append(Paragraph(highlight, bullet_style))

    story.append(Spacer(1, 0.2 * inch))

    # Risk factors
    story.append(Paragraph("Key Risk Considerations:", subsection_style))

    risks = []
    if dscr < 1.25:
        risks.append("• Low debt service coverage ratio increases financial risk")
    if cash_on_cash < 6:
        risks.append("• Below-market cash-on-cash returns")
    if ann_return < 8:
        risks.append("• Returns below typical real estate investment benchmarks")

    risks.extend([
        "• Market volatility could impact property values and rental rates",
        "• Interest rate changes may affect refinancing opportunities",
        "• Vacancy periods could reduce cash flow projections"
    ])

    for risk in risks:
        story.append(Paragraph(risk, bullet_style))

    # Investment recommendation
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("Investment Recommendation:", subsection_style))

    if ann_return >= 12 and dscr >= 1.25:
        recommendation = "STRONG BUY - This property meets or exceeds key investment criteria and should generate excellent returns."
    elif ann_return >= 10 and dscr >= 1.2:
        recommendation = "BUY - Solid investment opportunity with good fundamentals and market-beating returns."
    elif ann_return >= 8:
        recommendation = "CONDITIONAL BUY - Reasonable investment if purchased at asking price or below. Consider negotiating."
    else:
        recommendation = "PASS - Returns do not justify the investment risk. Look for better opportunities."

    story.append(Paragraph(f"<b>{recommendation}</b>", body_style))

    story.append(PageBreak())

    # ==================== DETAILED FINANCIAL ANALYSIS ====================
    story.append(Paragraph("DETAILED FINANCIAL ANALYSIS", section_style))

    # Investment structure
    story.append(Paragraph("Investment Structure", subsection_style))

    # Prevent division by zero
    if total_investment > 0:
        down_payment_pct = f'{(initial_cash / total_investment * 100):.1f}%'
        mortgage_pct = f'{(loan_amount / total_investment * 100):.1f}%'
    else:
        down_payment_pct = 'N/A'
        mortgage_pct = 'N/A'

    structure_data = [
        ['Component', 'Amount', '% of Total'],
        ['Property Purchase Price', f'${total_investment:,.0f}', '100.0%'],
        ['Down Payment (Your Cash)', f'${initial_cash:,.0f}', down_payment_pct],
        ['Mortgage Financing', f'${loan_amount:,.0f}', mortgage_pct],
        ['Monthly Debt Service', f'${monthly_payment:,.0f}', f'${monthly_payment * 12:,.0f}/year'],
    ]

    structure_table = Table(structure_data, colWidths=[2.5 * inch, 1.5 * inch, 1.2 * inch])
    structure_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(structure_table)

    story.append(Spacer(1, 0.2 * inch))

    # Return analysis
    story.append(Paragraph("Return Analysis", subsection_style))

    return_data = [
        ['Metric', 'Value', 'Benchmark', 'Assessment'],
        ['Annualized Return (IRR)', f'{ann_return:.1f}%', '10-15%',
         'Excellent' if ann_return >= 15 else 'Good' if ann_return >= 10 else 'Fair'],
        ['Total Return', f'{total_return:.1f}%', 'Varies', f'${total_profit:,.0f} profit'],
        ['Cash-on-Cash (Year 1)', f'{cash_on_cash:.1f}%', '8-12%',
         'Strong' if cash_on_cash >= 10 else 'Adequate' if cash_on_cash >= 6 else 'Weak'],
        ['Payback Period',
         f'{initial_cash / abs(first_year_cash_flow):.1f} years' if first_year_cash_flow != 0 else 'N/A',
         '8-12 years', 'Good' if first_year_cash_flow > 0 else 'Poor'],
    ]

    return_table = Table(return_data, colWidths=[2 * inch, 1.2 * inch, 1 * inch, 1 * inch])
    return_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SECONDARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(return_table)

    story.append(PageBreak())

    # ==================== CASH FLOW ANALYSIS ====================
    story.append(Paragraph("CASH FLOW ANALYSIS", section_style))

    # Convert annual table to better format
    story.append(
        Paragraph("The following table shows projected annual performance over the investment period:", body_style))
    story.append(Spacer(1, 0.1 * inch))

    # Parse and reformat annual data for better presentation
    try:
        # Create a more readable version of the annual table
        annual_simple_data = [['Year', 'Rent Income', 'Cash Flow', 'Property Value', 'Total Wealth']]

        for i, row in annual_df.iterrows():
            annual_simple_data.append([
                str(row['Year']),
                row['Annual Rent Income'],
                row['Annual Cash Flow (After-Tax)'],
                row['Home Value'],
                row['Total Wealth']
            ])

        annual_simple_table = Table(annual_simple_data,
                                    colWidths=[0.8 * inch, 1.2 * inch, 1.2 * inch, 1.2 * inch, 1.2 * inch])
        annual_simple_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(annual_simple_table)

    except:
        # Fallback if table parsing fails
        story.append(Paragraph("Detailed annual projections available in source data.", body_style))

    story.append(Spacer(1, 0.2 * inch))

    # Cash flow insights
    story.append(Paragraph("Cash Flow Insights:", subsection_style))
    insights = [
        f"• First year projected cash flow: ${first_year_cash_flow:,.0f}",
        f"• Monthly cash flow (Year 1): ${first_year_cash_flow / 12:,.0f}",
        f"• Debt service coverage: {dscr:.2f}x (${first_year_rent:,.0f} rent vs ${debt_service_annual:,.0f} debt service)",
        f"• Cash-on-cash return: {cash_on_cash:.1f}% on ${initial_cash:,.0f} invested"
    ]

    for insight in insights:
        story.append(Paragraph(insight, bullet_style))

    story.append(PageBreak())

    # ==================== SENSITIVITY ANALYSIS ====================
    story.append(Paragraph("SENSITIVITY ANALYSIS", section_style))

    story.append(
        Paragraph("The following analysis shows how changes in key variables affect your returns:", body_style))
    story.append(Spacer(1, 0.1 * inch))

    # Create sensitivity scenarios
    base_return = ann_return
    scenarios = [
        ['Scenario', 'Rent Change', 'Value Change', 'Projected Return', 'Impact'],
        ['Base Case', '0%', '0%', f'{base_return:.1f}%', 'Baseline'],
        ['Optimistic', '+10%', '+20%', f'{base_return * 1.3:.1f}%', 'Strong upside'],
        ['Conservative', '-5%', '-10%', f'{base_return * 0.7:.1f}%', 'Moderate downside'],
        ['Pessimistic', '-15%', '-20%', f'{base_return * 0.4:.1f}%', 'Significant risk'],
        ['Market Crash', '-25%', '-30%', f'{base_return * 0.1:.1f}%', 'Severe impact'],
    ]

    sensitivity_table = Table(scenarios, colWidths=[1.5 * inch, 1 * inch, 1 * inch, 1.2 * inch, 1.3 * inch])
    sensitivity_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), WARNING_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(sensitivity_table)

    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("Key Takeaways:", subsection_style))
    takeaways = [
        "• Your investment is most sensitive to rental income changes",
        "• Property value fluctuations significantly impact total returns",
        "• Maintain 6-month expense reserves for vacancy protection",
        "• Consider rent growth potential in your target market",
        "• Monitor local market conditions for early warning signs"
    ]

    for takeaway in takeaways:
        story.append(Paragraph(takeaway, bullet_style))

    story.append(PageBreak())

    # ==================== MARKET ANALYSIS ====================
    story.append(Paragraph("MARKET ANALYSIS", section_style))

    story.append(Paragraph("Understanding the local market is crucial for investment success:", body_style))
    story.append(Spacer(1, 0.1 * inch))

    # Market factors to consider
    story.append(Paragraph("Key Market Factors to Research:", subsection_style))
    market_factors = [
        "• Local employment growth and major employers",
        "• Population growth trends and demographics",
        "• New construction and housing supply",
        "• School district quality and ratings",
        "• Crime rates and neighborhood safety",
        "• Transportation and infrastructure development",
        "• Local government policies affecting rentals",
        "• Comparable property sales and rental rates"
    ]

    for factor in market_factors:
        story.append(Paragraph(factor, bullet_style))

    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("Due Diligence Checklist:", subsection_style))
    due_diligence = [
        "□ Property inspection by qualified professional",
        "□ Title search and insurance verification",
        "□ Review of property tax history and assessments",
        "□ Analysis of comparable rental properties",
        "□ Verification of current rent rolls (if applicable)",
        "□ Review of local zoning and rental regulations",
        "□ Insurance quotes and coverage verification",
        "□ Property management cost estimates",
        "□ Reserve fund requirements analysis",
        "□ Exit strategy and resale market evaluation"
    ]

    for item in due_diligence:
        story.append(Paragraph(item, bullet_style))

    story.append(PageBreak())

    # ==================== RISK ASSESSMENT MATRIX ====================
    story.append(Paragraph("COMPREHENSIVE RISK ASSESSMENT", section_style))

    # Risk assessment table
    risk_data = [
        ['Risk Factor', 'Probability', 'Impact', 'Mitigation Strategy', 'Priority'],
        ['Market Downturn', 'Medium', 'High', 'Conservative assumptions, reserves', 'High'],
        ['Extended Vacancy', 'Low-Med', 'Medium', 'Competitive pricing, good location', 'Medium'],
        ['Major Repairs', 'Medium', 'Medium', 'Professional inspection, reserves', 'Medium'],
        ['Interest Rate Rise', 'Medium', 'Low', 'Fixed-rate mortgage', 'Low'],
        ['Rent Control', 'Low', 'High', 'Research local politics', 'Medium'],
        ['Economic Recession', 'Low', 'High', 'Diversified tenant base', 'High'],
    ]

    risk_table = Table(risk_data, colWidths=[1.8 * inch, 0.8 * inch, 0.8 * inch, 1.8 * inch, 0.8 * inch])
    risk_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), WARNING_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (3, 0), (3, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(risk_table)

    story.append(Spacer(1, 0.2 * inch))

    # Risk management recommendations
    story.append(Paragraph("Risk Management Recommendations:", subsection_style))
    risk_mgmt = [
        "• Maintain 6-12 months of expenses in reserve fund",
        "• Secure comprehensive landlord insurance policy",
        "• Screen tenants thoroughly with credit and background checks",
        "• Consider property management if not local to property",
        "• Build relationships with reliable contractors and vendors",
        "• Stay informed about local rental market conditions",
        "• Have legal counsel familiar with landlord-tenant law",
        "• Plan exit strategy before purchase"
    ]

    for item in risk_mgmt:
        story.append(Paragraph(item, bullet_style))

    # Add remodeling summary if applicable
    if results.get("remodel_summary"):
        story.append(PageBreak())
        story.append(Paragraph("RENOVATION ANALYSIS", section_style))

        # Clean up the HTML formatting in remodel summary
        remodel_text = results.get("remodel_summary", "").replace("<b>", "").replace("</b>", "").replace("<br>", "\n")
        story.append(Paragraph("Planned Renovations:", subsection_style))

        # Split by lines and format each
        for line in remodel_text.split('\n'):
            if line.strip():
                story.append(Paragraph(f"• {line.strip()}", bullet_style))

        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph("Renovation Considerations:", subsection_style))
        reno_considerations = [
            "• Obtain multiple contractor bids before proceeding",
            "• Factor in permit costs and approval timelines",
            "• Consider seasonal timing for optimal rental market entry",
            "• Budget 10-20% contingency for unexpected issues",
            "• Verify renovations align with neighborhood standards",
            "• Document all improvements for tax depreciation benefits"
        ]

        for consideration in reno_considerations:
            story.append(Paragraph(consideration, bullet_style))

    # Wealth chart if available
    if plot_url:
        story.append(PageBreak())
        story.append(Paragraph("WEALTH ACCUMULATION PROJECTION", section_style))

        try:
            imgdata = base64.b64decode(plot_url)
            tmpimg = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            tmpimg.write(imgdata)
            tmpimg.flush()

            # Add chart with proper sizing
            img = Image(tmpimg.name, width=6 * inch, height=3.5 * inch)
            story.append(img)

            story.append(Spacer(1, 0.1 * inch))
            story.append(Paragraph(
                "This chart illustrates the projected growth of your total wealth (equity + cash flow) over the investment period.",
                ParagraphStyle('Caption', parent=body_style, fontSize=9, textColor=colors.gray, alignment=TA_CENTER)))

        except Exception as e:
            story.append(Paragraph("Wealth accumulation chart unavailable.", body_style))

    story.append(PageBreak())

    # ==================== FINAL RECOMMENDATIONS ====================
    story.append(Paragraph("FINAL INVESTMENT DECISION", section_style))

    # Decision matrix
    story.append(Paragraph("Investment Decision Matrix:", subsection_style))

    decision_score = 0
    if ann_return >= 12:
        decision_score += 3
    elif ann_return >= 8:
        decision_score += 2
    elif ann_return >= 5:
        decision_score += 1

    if cash_on_cash >= 10:
        decision_score += 2
    elif cash_on_cash >= 6:
        decision_score += 1

    if dscr >= 1.5:
        decision_score += 2
    elif dscr >= 1.25:
        decision_score += 1

    # Final recommendation based on score
    if decision_score >= 6:
        final_rec = "STRONG BUY - Excellent investment opportunity"
        rec_color = SECONDARY_COLOR
    elif decision_score >= 4:
        final_rec = "BUY - Good investment with solid fundamentals"
        rec_color = PRIMARY_COLOR
    elif decision_score >= 2:
        final_rec = "CONDITIONAL - Proceed with caution"
        rec_color = WARNING_COLOR
    else:
        final_rec = "PASS - Look for better opportunities"
        rec_color = WARNING_COLOR

    # Final recommendation box
    final_rec_data = [[f"RECOMMENDATION: {final_rec}"]]
    final_rec_table = Table(final_rec_data, colWidths=[6 * inch])
    final_rec_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), rec_color),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 14),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
    ]))
    story.append(final_rec_table)

    story.append(Spacer(1, 0.3 * inch))

    # Next steps
    story.append(Paragraph("Recommended Next Steps:", subsection_style))

    if decision_score >= 4:
        next_steps = [
            "1. Submit competitive offer with appropriate contingencies",
            "2. Schedule professional property inspection",
            "3. Secure financing pre-approval",
            "4. Conduct final due diligence on neighborhood",
            "5. Prepare property management strategy",
            "6. Set up reserve funds and insurance"
        ]
    else:
        next_steps = [
            "1. Continue searching for better investment opportunities",
            "2. Reassess investment criteria and requirements",
            "3. Consider different markets or property types",
            "4. Improve financing terms to enhance returns",
            "5. Wait for better market conditions"
        ]

    for step in next_steps:
        story.append(Paragraph(step, bullet_style))

    # Disclaimer
    story.append(PageBreak())
    story.append(Paragraph("IMPORTANT DISCLAIMERS", section_style))

    disclaimer_text = """
    <b>Investment Risk:</b> Real estate investments involve significant risks including market volatility, 
    economic downturns, property damage, and regulatory changes. All projections are estimates based on 
    current assumptions and may not reflect actual results.<br/><br/>

    <b>Professional Advice:</b> This analysis is for educational purposes only and does not constitute 
    professional financial, legal, or tax advice. Consult qualified professionals before making investment decisions.<br/><br/>

    <b>Market Conditions:</b> Real estate markets can change rapidly. Verify all assumptions and 
    market data before proceeding with any investment.<br/><br/>

    <b>Due Diligence:</b> Conduct thorough due diligence including professional inspections, 
    title searches, and market analysis before purchasing any property.
    """

    story.append(Paragraph(disclaimer_text, ParagraphStyle('Disclaimer', parent=body_style, fontSize=9,
                                                           textColor=colors.gray, alignment=TA_JUSTIFY)))

    # Build the PDF
    doc.build(story)
    tmp.seek(0)
    return tmp.read()
