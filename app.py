from flask import Flask, render_template_string, request, send_file, url_for
import io
import math
import pandas as pd
import matplotlib
matplotlib.use('AGG')
import matplotlib.pyplot as plt
import base64
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import tempfile

app = Flask(__name__)
excel_data = None
last_results = None
last_annual_table = None

# ========= HTML Templates =========

index_html = '''
<!DOCTYPE html>
<html>
<head>
    <title>Real Estate Investment Analysis</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        small { color: #6c757d; }
        .section { background: #fff; border-radius: 12px; box-shadow: 0 2px 12px #eef3ff; padding: 24px; margin-bottom: 28px; }
        body { background: linear-gradient(90deg, #f7faff 0%, #e3f6fc 100%); }
        h1 { color: #1769aa; font-weight: 800; }
    </style>
</head>
<body>
<div class="container py-5">
    <h1 class="mb-4 text-center">🏠 Real Estate Investment Analysis</h1>
    <div class="alert alert-warning"><strong>Note:</strong> This calculator is a simplified analysis and does not constitute tax, legal, or investment advice. For rental properties, it estimates U.S. depreciation and capital gains tax. Consult your accountant for actual filings!</div>
    <form action="{{ url_for('analyze') }}" method="post">
        <div class="section">
            <h2 class="mb-3">Initial Loan Information</h2>
            <div class="mb-3">
                <label class="form-label">Home Cost</label>
                <input type="number" class="form-control" name="home_cost" required>
                <small>Purchase price of the property (e.g., 350000).</small>
            </div>
            <div class="mb-3">
                <label class="form-label">Closing Cost</label>
                <input type="number" class="form-control" name="closing_cost" required>
                <small>Initial closing cost in dollars (e.g., 5000).</small>
            </div>
            <div class="mb-3">
                <label class="form-label">Select Loan Type</label>
                <select class="form-select" name="loan_type_choice">
                    <option value="1">Conventional 30-year</option>
                    <option value="2">15-year</option>
                    <option value="3">Custom</option>
                </select>
                <small>Choose the term of your mortgage.</small>
            </div>
            <div class="mb-3">
                <label class="form-label">Custom Loan Term</label>
                <input type="number" class="form-control" name="custom_loan_term">
                <small>Enter number of years if "Custom" was chosen.</small>
            </div>
            <div class="mb-3">
                <label class="form-label">Down Payment Percentage</label>
                <input type="number" class="form-control" name="down_payment_percent" required>
                <small>Enter as a percentage (e.g., 20 for 20%).</small>
            </div>
            <div class="mb-3">
                <label class="form-label">Annual Appreciation Rate (%)</label>
                <input type="number" class="form-control" name="annual_appreciation_percent" required>
                <small>Expected yearly home value increase (e.g., 3).</small>
            </div>
            <div class="mb-3">
                <label class="form-label">Mortgage Interest Rate (%)</label>
                <input type="number" class="form-control" name="mortgage_interest_rate" required>
                <small>Current annual interest rate (e.g., 4).</small>
            </div>
        </div>
        <div class="section">
            <h2 class="mb-3">Rental Income & Expenses</h2>
            <div class="mb-3">
                <label class="form-label">Monthly Rent</label>
                <input type="number" class="form-control" name="monthly_rent" required>
                <small>Expected rent income per month.</small>
            </div>
            <div class="mb-3">
                <label class="form-label">Rental Income Growth Rate (%)</label>
                <input type="number" class="form-control" name="rental_income_growth_percent" required>
                <small>Annual increase in rent income (e.g., 3).</small>
            </div>
            <div class="mb-3">
                <label class="form-label">Vacancy Rate (%)</label>
                <input type="number" class="form-control" name="vacancy_rate" required>
                <small>Expected average vacancy (e.g., 5).</small>
            </div>
            <div class="mb-3">
                <label class="form-label">Management Fee (%)</label>
                <input type="number" class="form-control" name="management_fee_percent" required>
                <small>Typical property management (e.g., 8). Enter 0 if self-managed.</small>
            </div>
            <div class="mb-3">
                <label class="form-label">HOA Fees (Annual, $)</label>
                <input type="number" class="form-control" name="hoa_fee" required>
                <small>Enter $0 if none.</small>
            </div>
        </div>
        <div class="section">
            <h2 class="mb-3">Property Tax & Insurance</h2>
            <div class="mb-3">
                <label class="form-label">Property Tax Input Mode</label>
                <input type="text" class="form-control" name="prop_tax_mode" required>
                <small>Enter 'p' for percentage or 'd' for fixed dollar amount.</small>
            </div>
            <div class="mb-3">
                <label class="form-label">Property Tax Percentage</label>
                <input type="number" class="form-control" name="property_tax_percent">
                <small>If mode is 'p', e.g., 1 for 1%.</small>
            </div>
            <div class="mb-3">
                <label class="form-label">Property Tax Amount</label>
                <input type="number" class="form-control" name="property_tax_amount">
                <small>If mode is 'd', enter dollar amount.</small>
            </div>
            <div class="mb-3">
                <label class="form-label">Property Tax Appraisal Growth (%)</label>
                <input type="number" class="form-control" name="tax_appraisal_growth" required>
                <small>If you want property tax based on a different growth rate than market appreciation (e.g., capped appraisal increase), enter that here (e.g., 2).</small>
            </div>
            <div class="mb-3">
                <label class="form-label">Home Insurance Input Mode</label>
                <input type="text" class="form-control" name="ins_mode" required>
                <small>Enter 'p' for percentage or 'd' for fixed amount.</small>
            </div>
            <div class="mb-3">
                <label class="form-label">Home Insurance Percentage</label>
                <input type="number" class="form-control" name="home_insurance_percent">
                <small>If mode is 'p', e.g., 0.5 for 0.5%.</small>
            </div>
            <div class="mb-3">
                <label class="form-label">Home Insurance Amount</label>
                <input type="number" class="form-control" name="home_insurance_amount">
                <small>If mode is 'd', enter dollar amount.</small>
            </div>
        </div>
        <div class="section">
            <h2 class="mb-3">Property Details & Taxes</h2>
            <div class="mb-3">
                <label class="form-label">House Name</label>
                <input type="text" class="form-control" name="house_name" required>
            </div>
            <div class="mb-3">
                <label class="form-label">Ownership Years</label>
                <input type="number" class="form-control" name="ownership_years" required>
            </div>
            <div class="mb-3">
                <label class="form-label">Selling Closing Cost Percentage</label>
                <input type="number" class="form-control" name="sell_closing_cost_percent" required>
                <small>Closing cost when selling (e.g., 6 for 6%).</small>
            </div>
            <div class="mb-3">
                <label class="form-label">Is This a Rental Property?</label>
                <select class="form-select" name="is_rental" required>
                    <option value="yes">Yes</option>
                    <option value="no">No (Primary Residence)</option>
                </select>
                <small>Impacts depreciation and capital gains tax.</small>
            </div>
            <div class="mb-3">
                <label class="form-label">Structure Value Percentage (%)</label>
                <input type="number" class="form-control" name="structure_percent" value="80">
                <small>For depreciation (typically 75-80% of purchase price for residential).</small>
            </div>
            <div class="mb-3">
                <label class="form-label">Marginal Tax Rate (%)</label>
                <input type="number" class="form-control" name="tax_rate" value="25">
                <small>Federal + State (guess if unsure, for after-tax returns).</small>
            </div>
            <div class="mb-3">
                <label class="form-label">Capital Gains Tax Rate (%)</label>
                <input type="number" class="form-control" name="cap_gains_rate" value="20">
                <small>Typical LTCG is 15-20%. Ignored if primary residence (with IRS exclusion).</small>
            </div>
        </div>
        <div class="d-grid gap-2 col-6 mx-auto">
            <button type="submit" class="btn btn-primary btn-lg my-4 shadow">Analyze Initial Loan</button>
        </div>
    </form>
</div>
</body>
</html>
'''
results_html = '''
<!DOCTYPE html>
<html>
<head>
    <title>Investment Analysis Results</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .section { background: #fff; border-radius: 12px; box-shadow: 0 2px 12px #eef3ff; padding: 24px; margin-bottom: 28px; }
        body { background: linear-gradient(90deg, #f7faff 0%, #e3f6fc 100%); }
        h1 { color: #1769aa; font-weight: 800; }
        .divider { background-color: #90EE90; text-align: center; font-weight: bold; padding: 8px; margin: 16px 0; border-radius: 8px; font-size: 1.1em; }
    </style>
</head>
<body>
<div class="container py-5">
    <h1 class="mb-4 text-center">Results for {{ results.house_name }}</h1>
    <div class="section">
        <h2>Basic Loan Analysis</h2>
        <ul class="list-group list-group-flush">
            <li class="list-group-item"><strong>Initial Cash Outlay:</strong> {{ results.initial_cash_outlay }}</li>
            <li class="list-group-item"><strong>Loan Amount:</strong> {{ results.loan_amount }}</li>
            <li class="list-group-item"><strong>Monthly Mortgage Payment:</strong> {{ results.monthly_payment }}</li>
            <li class="list-group-item"><strong>Annualized Return:</strong> {{ results.annualized_return }}</li>
            <li class="list-group-item"><strong>Cumulative Return:</strong> {{ results.cumulative_return }}</li>
            <li class="list-group-item"><strong>Capital Gains Tax (if Rental):</strong> {{ results.capital_gains_tax }}</li>
            <li class="list-group-item"><strong>Final Value After Tax:</strong> {{ results.final_total_value }}</li>
        </ul>
    </div>
    <div class="section">
        <h2>Annual Summary</h2>
        {{ annual_table|safe }}
    </div>
    <div class="section">
        <h2>Wealth Accumulation Over Time</h2>
        <img class="img-fluid rounded shadow" src="data:image/png;base64,{{ plot_url }}" alt="Wealth Accumulation Chart">
    </div>
    <div class="section">
        <h2>Optional: Refinance Simulation</h2>
        <form action="{{ url_for('simulate_refinance') }}" method="post">
            {% for key, value in original_data.items() %}
                <input type="hidden" name="{{ key }}" value="{{ value }}">
            {% endfor %}
            <div class="mb-3">
                <label class="form-label">Refinance Type</label>
                <select class="form-select" name="refinance_type" required>
                    <option value="cashout">Cash-Out Refinance</option>
                    <option value="newrate">New Rate & Timeline (No Cash-Out)</option>
                </select>
            </div>
            <div class="mb-3">
                <label class="form-label">Refinance Year</label>
                <input type="number" class="form-control" name="refinance_year" required>
            </div>
            <div class="mb-3">
                <label class="form-label">Cost to Refinance ($)</label>
                <input type="number" class="form-control" name="refinance_cost" required>
            </div>
            <div class="mb-3">
                <label class="form-label">New Interest Rate (%)</label>
                <input type="number" class="form-control" name="refinance_interest_rate" required>
            </div>
            <div class="mb-3">
                <label class="form-label">New Loan Term (years)</label>
                <input type="number" class="form-control" name="custom_ref_loan_term" required>
            </div>
            <div class="d-grid gap-2 col-6 mx-auto">
                <button type="submit" class="btn btn-success btn-lg my-3 shadow">Simulate Refinance</button>
            </div>
        </form>
    </div>
    <div class="section text-center">
        <a class="btn btn-outline-primary btn-lg" href="{{ url_for('download_excel') }}">⬇️ Download Excel File of Analysis</a>
        <a class="btn btn-outline-danger btn-lg" href="{{ url_for('download_pdf') }}">⬇️ Download PDF Summary</a>
    </div>
    <div class="text-center my-4">
        <a href="{{ url_for('index') }}" class="btn btn-link">⬅️ Back to Input Form</a>
    </div>
</div>
</body>
</html>
'''

refinance_results_html = '''
<!DOCTYPE html>
<html>
<head>
    <title>Refinance Simulation Results</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .section { background: #fff; border-radius: 12px; box-shadow: 0 2px 12px #eef3ff; padding: 24px; margin-bottom: 28px; }
        body { background: linear-gradient(90deg, #f7faff 0%, #e3f6fc 100%); }
        h1 { color: #1769aa; font-weight: 800; }
        .divider { background-color: #90EE90; text-align: center; font-weight: bold; padding: 8px; margin: 16px 0; border-radius: 8px; font-size: 1.1em; }
    </style>
</head>
<body>
<div class="container py-5">
    <h1 class="mb-4 text-center">Refinance Simulation Results for {{ results.house_name }}</h1>
    <div class="section">
        <h2>Original Loan Analysis</h2>
        <ul class="list-group list-group-flush">
            <li class="list-group-item"><strong>Initial Cash Outlay:</strong> {{ results.initial_cash_outlay }}</li>
            <li class="list-group-item"><strong>Loan Amount:</strong> {{ results.loan_amount }}</li>
            <li class="list-group-item"><strong>Monthly Mortgage Payment:</strong> {{ results.monthly_payment }}</li>
            <li class="list-group-item"><strong>Annualized Return:</strong> {{ results.annualized_return }}</li>
            <li class="list-group-item"><strong>Cumulative Return:</strong> {{ results.cumulative_return }}</li>
            <li class="list-group-item"><strong>Capital Gains Tax (if Rental):</strong> {{ results.capital_gains_tax }}</li>
            <li class="list-group-item"><strong>Final Value After Tax:</strong> {{ results.final_total_value }}</li>
        </ul>
    </div>
    <div class="section">
        <h2>Annual Summary</h2>
        {{ annual_table|safe }}
    </div>
    <div class="section">
        <h2>Wealth Accumulation Over Time</h2>
        <img class="img-fluid rounded shadow" src="data:image/png;base64,{{ plot_url }}" alt="Wealth Accumulation Chart">
    </div>
    <div class="section">
        <h2>Refinance Simulation Details</h2>
        <div class="alert alert-info" role="alert">
            {{ refinance_details|safe }}
        </div>
        <h3>Pre-Refinance Cash Flow</h3>
        {{ pre_table|safe }}
        <div class="divider">--- Refinance Occurs Here ---</div>
        <h3>Post-Refinance Cash Flow</h3>
        {{ post_table|safe }}
    </div>
    <div class="section text-center">
        <a class="btn btn-outline-primary btn-lg" href="{{ url_for('download_excel') }}">⬇️ Download Excel File of Analysis</a>
        <a class="btn btn-outline-danger btn-lg" href="{{ url_for('download_pdf') }}">⬇️ Download PDF Summary</a>
    </div>
    <div class="text-center my-4">
        <a href="{{ url_for('index') }}" class="btn btn-link">⬅️ Back to Input Form</a>
    </div>
</div>
</body>
</html>
'''

# ---- Utility: PDF Report ----
def generate_pdf_report(results, annual_table_html, refinance_details=None, pre_table=None, post_table=None, plot_url=None):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import inch
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import Paragraph, Frame, Image, Spacer, Table, TableStyle, SimpleDocTemplate, PageBreak
    import tempfile
    import base64

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    doc = SimpleDocTemplate(tmp.name, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()

    # --- PITCH DECK COVER SLIDE (OPTION 1) ---
    story.append(PageBreak())
    story.append(Spacer(1, 2.5 * inch))
    story.append(Paragraph(
        '<font size=28 color="#1769aa"><b>🏠 Investment Pitch Deck</b></font>',
        ParagraphStyle(name="CoverTitle", alignment=1, fontSize=28, textColor=colors.HexColor("#1769aa"))
    ))
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph(
        f'<font size=22 color="#ffc800"><b>{results.get("house_name", "")}</b></font>',
        ParagraphStyle(name="CoverSubTitle", alignment=1, fontSize=22, textColor=colors.HexColor("#ffc800"))
    ))
    story.append(Spacer(1, 0.25 * inch))
    story.append(Paragraph(
        '<font size=16 color="#666">Generated Investment Analysis</font>',
        ParagraphStyle(name="CoverText", alignment=1, fontSize=16, textColor=colors.HexColor("#666"))
    ))
    story.append(PageBreak())
    # --- END COVER SLIDE ---

    # ... rest of your story/slide logic here ...


    # ========== DEAL SUMMARY SLIDE ==========
    story.append(Paragraph(
        f'<para align="center"><font size=26 color="#1769aa"><b>Deal Snapshot</b></font></para>',
        styles['Normal']
    ))
    story.append(Spacer(1, 0.3 * inch))

    summary_data = [
        ["Initial Cash Outlay", results.get("initial_cash_outlay", "")],
        ["Loan Amount", results.get("loan_amount", "")],
        ["Monthly Mortgage Payment", results.get("monthly_payment", "")],
        ["Annualized Return", results.get("annualized_return", "")],
        ["Cumulative Return", results.get("cumulative_return", "")],
        ["Capital Gains Tax", results.get("capital_gains_tax", "")],
        ["Final Value After Tax", results.get("final_total_value", "")]
    ]
    table = Table(summary_data, colWidths=[2.8*inch, 3*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.Color(0.8, 0.92, 1)),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 14),
        ('TEXTCOLOR', (0,0), (-1,0), colors.darkblue),
        ('BACKGROUND', (0,1), (-1,-1), colors.whitesmoke),
        ('TEXTCOLOR', (0,1), (0,-1), colors.Color(0.12, 0.35, 0.66)),
        ('TEXTCOLOR', (1,1), (1,-1), colors.darkgreen),
        ('GRID', (0,0), (-1,-1), 1, colors.gray),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(table)
    story.append(PageBreak())

    # ========== WEALTH ACCUMULATION CHART ==========
    story.append(Paragraph(
        f'<para align="center"><font size=22 color="#1769aa"><b>Wealth Over Time</b></font></para>',
        styles['Normal']
    ))
    story.append(Spacer(1, 0.1 * inch))
    if plot_url:
        try:
            # plot_url is a base64 png string
            imgdata = base64.b64decode(plot_url)
            tmpimg = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            tmpimg.write(imgdata)
            tmpimg.flush()
            story.append(Image(tmpimg.name, width=6.5*inch, height=4*inch))
            story.append(Spacer(1, 0.2*inch))
        except Exception as e:
            story.append(Paragraph("Chart not available.", styles["Normal"]))
    story.append(PageBreak())

    # ========== DEAL QUALITY EXPLANATION SLIDE ==========
    # Compose dynamic, AI-style narrative
    try:
        ann_return = float(results['annualized_return'].replace('%',''))
        risk_comment = "The deal exhibits a very strong projected return profile." if ann_return >= 8 else \
                       "The projected returns are solid and in line with market averages." if ann_return >= 4 else \
                       "The projected return is conservative; the deal may be best for risk-averse investors."
    except Exception:
        risk_comment = "The projected return profile is robust for this type of property."

    from reportlab.lib.styles import ParagraphStyle

    # Title (centered, large font)
    story.append(Paragraph("Deal Quality Assessment", ParagraphStyle(
        name="CenterTitle", alignment=1, fontSize=20, textColor=colors.HexColor("#1769aa"), spaceAfter=16,
        spaceBefore=12
    )))

    # Summary
    story.append(Paragraph("<b>Summary:</b><br/>" + risk_comment, ParagraphStyle(
        name="Body", fontSize=12, spaceAfter=8
    )))

    # Strengths
    strengths = [
        "Attractive leverage and wealth growth over time.",
        "Solid cash flow and equity accumulation each year.",
        "Tax benefits through depreciation (if rental)."
    ]
    strengths_text = "<b>Strengths:</b><br/>" + "<br/>".join([f"&bull; {s}" for s in strengths])
    story.append(Paragraph(strengths_text, ParagraphStyle(name="Body", fontSize=12, spaceAfter=8)))

    # Considerations
    consids = [
        "Returns assume consistent rent and appreciation; actual performance may vary.",
        "Be mindful of vacancy risk, unexpected expenses, and tax law changes.",
        "Refinancing can unlock equity and improve returns, but adds complexity."
    ]
    consids_text = "<b>Considerations:</b><br/>" + "<br/>".join([f"&bull; {c}" for c in consids])
    story.append(Paragraph(consids_text, ParagraphStyle(name="Body", fontSize=12, spaceAfter=8)))

    # Bottom line
    story.append(Paragraph(
        "<b>Bottom line:</b> This property provides a compelling opportunity for long-term wealth creation with a favorable risk/return profile.",
        ParagraphStyle(
            name="Body", fontSize=12, spaceAfter=16
        )))
    story.append(PageBreak())

    # ========== OPTIONAL: REFINANCE SLIDE ==========
    if refinance_details:
        story.append(Paragraph(
            f'<para align="center"><font size=22 color="#1769aa"><b>Refinance Simulation</b></font></para>',
            styles['Normal']
        ))
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph(str(refinance_details).replace("<br>", "<br/>"), styles["BodyText"]))
        story.append(PageBreak())

    # ========== ANNUAL TABLE SLIDE ==========
    story.append(Paragraph(
        f'<para align="center"><font size=22 color="#1769aa"><b>Annual Cash Flow & Wealth Table</b></font></para>',
        styles['Normal']
    ))
    story.append(Spacer(1, 0.1 * inch))
    # Show only the first 10 rows of table if table is too big
    import pandas as pd
    try:
        # Try to parse annual_table_html (should be pandas table HTML)
        annual_df = pd.read_html(annual_table_html)[0]
        preview_df = annual_df.head(10)
        tdata = [list(preview_df.columns)] + preview_df.values.tolist()
        t = Table(tdata, colWidths=[1.1*inch]*len(preview_df.columns))
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('TEXTCOLOR', (0,0), (-1,0), colors.darkblue),
            ('GRID', (0,0), (-1,-1), 0.5, colors.gray),
        ]))
        story.append(t)
        if len(annual_df) > 10:
            story.append(Paragraph('<i>...table truncated for preview</i>', styles['Normal']))
    except Exception:
        story.append(Paragraph("Table unavailable.", styles['Normal']))

    doc.build(story)
    tmp.seek(0)
    return tmp.read()


# ========== Main Loan/Analysis Logic ==========
def run_initial_analysis(form):
    # Parse all inputs
    home_cost = float(form.get('home_cost'))
    closing_cost = float(form.get('closing_cost'))
    loan_type_choice = form.get('loan_type_choice')
    if loan_type_choice == "1":
        loan_term_years = 30
    elif loan_type_choice == "2":
        loan_term_years = 15
    elif loan_type_choice == "3":
        loan_term_years = int(form.get('custom_loan_term') or 30)
    else:
        loan_term_years = 30
    down_payment_percent = float(form.get('down_payment_percent')) / 100.0
    annual_appreciation_percent = float(form.get('annual_appreciation_percent')) / 100.0
    mortgage_interest_rate = float(form.get('mortgage_interest_rate')) / 100.0
    monthly_rent = float(form.get('monthly_rent'))
    rental_income_growth_percent = float(form.get('rental_income_growth_percent')) / 100.0
    vacancy_rate = float(form.get('vacancy_rate')) / 100.0
    management_fee_percent = float(form.get('management_fee_percent')) / 100.0
    hoa_fee = float(form.get('hoa_fee'))

    prop_tax_mode = form.get('prop_tax_mode')
    property_tax_percent = float(form.get('property_tax_percent') or 0) / 100.0 if form.get('property_tax_percent') else 0
    property_tax_amount = float(form.get('property_tax_amount') or 0)
    tax_appraisal_growth = float(form.get('tax_appraisal_growth')) / 100.0

    ins_mode = form.get('ins_mode')
    home_insurance_percent = float(form.get('home_insurance_percent') or 0) / 100.0 if form.get('home_insurance_percent') else 0
    home_insurance_amount = float(form.get('home_insurance_amount') or 0)

    house_name = form.get('house_name')
    ownership_years = int(form.get('ownership_years'))
    sell_closing_cost_percent = float(form.get('sell_closing_cost_percent')) / 100.0
    is_rental = form.get('is_rental') == "yes"
    structure_percent = float(form.get('structure_percent') or 80) / 100.0
    tax_rate = float(form.get('tax_rate') or 25) / 100.0
    cap_gains_rate = float(form.get('cap_gains_rate') or 20) / 100.0

    # ========== Initial Loan ==========
    down_payment = home_cost * down_payment_percent
    initial_cash = down_payment + closing_cost
    loan_amount = home_cost - down_payment
    loan_term_months = loan_term_years * 12
    monthly_interest_rate_val = mortgage_interest_rate / 12.0

    monthly_payment = loan_amount * (monthly_interest_rate_val * (1 + monthly_interest_rate_val) ** loan_term_months) / \
                      ((1 + monthly_interest_rate_val) ** loan_term_months - 1)

    # Amortization Schedule
    schedule = []
    balance = loan_amount
    for m in range(1, loan_term_months + 1):
        interest_payment = balance * monthly_interest_rate_val
        principal_payment = monthly_payment - interest_payment
        balance -= principal_payment
        if balance < 0:
            principal_payment += balance
            balance = 0
        schedule.append((m, monthly_payment, principal_payment, interest_payment, balance))
    schedule_df = pd.DataFrame(schedule, columns=["Month", "Payment", "Principal", "Interest", "Balance"])

    # ========== Annual Summary ==========
    annual_data = []
    cumulative_cash_flow = 0.0
    cumulative_depreciation = 0.0
    assessed_value = home_cost
    structure_value = home_cost * structure_percent
    annual_depreciation = structure_value / 27.5 if is_rental else 0

    for year in range(1, ownership_years + 1):
        if year <= loan_term_years:
            start_month = (year - 1) * 12
            end_month = year * 12
            year_schedule = schedule_df.iloc[start_month:end_month]
            total_mortgage_payment = year_schedule["Payment"].sum()
            end_balance = year_schedule.iloc[-1]["Balance"]
        else:
            total_mortgage_payment = 0.0
            end_balance = 0.0

        home_value = home_cost * ((1 + annual_appreciation_percent) ** year)
        if prop_tax_mode.lower() == 'p':
            if year == 1:
                assessed_value = home_cost
            else:
                assessed_value = assessed_value * (1 + tax_appraisal_growth)
            property_tax = property_tax_percent * assessed_value
        else:
            property_tax = property_tax_amount

        maintenance_cost = 0.01 * home_value
        if ins_mode.lower() == 'p':
            insurance_cost = home_insurance_percent * home_value
        else:
            insurance_cost = home_insurance_amount

        operating_expenses = property_tax + maintenance_cost + insurance_cost + hoa_fee

        adjusted_monthly_rent = monthly_rent * ((1 + rental_income_growth_percent) ** (year - 1))
        gross_annual_rent = adjusted_monthly_rent * 12
        effective_rent = gross_annual_rent * (1 - vacancy_rate)
        management_fee = effective_rent * management_fee_percent
        annual_rent_income = effective_rent - management_fee

        depreciation = annual_depreciation if is_rental else 0
        taxable_income = annual_rent_income - (total_mortgage_payment + operating_expenses + depreciation)
        tax_due = max(0, taxable_income) * tax_rate if is_rental else 0

        annual_cash_flow = annual_rent_income - total_mortgage_payment - operating_expenses - tax_due
        cumulative_cash_flow += annual_cash_flow
        cumulative_depreciation += depreciation
        equity = home_value - end_balance
        unrealized_wealth = equity - initial_cash
        total_wealth = cumulative_cash_flow + unrealized_wealth

        annual_data.append({
            "Year": year,
            "Home Value": f"${home_value:,.2f}",
            "Mortgage Balance": f"${end_balance:,.2f}",
            "Equity": f"${equity:,.2f}",
            "Annual Rent Income": f"${annual_rent_income:,.2f}",
            "Operating Expenses": f"${operating_expenses:,.2f}",
            "Annual Cash Flow (After-Tax)": f"${annual_cash_flow:,.2f}",
            "Cumulative Cash Flow": f"${cumulative_cash_flow:,.2f}",
            "Unrealized Wealth": f"${unrealized_wealth:,.2f}",
            "Total Wealth": f"${total_wealth:,.2f}",
            "Taxable Rental Income": f"${taxable_income:,.2f}" if is_rental else "N/A",
            "Tax Due": f"${tax_due:,.2f}" if is_rental else "N/A",
            "Depreciation": f"${depreciation:,.2f}" if is_rental else "N/A"
        })

    annual_df = pd.DataFrame(annual_data)

    sale_price = home_cost * ((1 + annual_appreciation_percent) ** ownership_years)
    sale_closing_cost = sale_price * sell_closing_cost_percent
    net_sale_price = sale_price - sale_closing_cost
    basis = home_cost + closing_cost - cumulative_depreciation if is_rental else home_cost + closing_cost
    capital_gain = net_sale_price - basis
    capital_gains_tax = cap_gains_rate * capital_gain if (is_rental and capital_gain > 0) else 0
    final_total_value = net_sale_price + cumulative_cash_flow - capital_gains_tax

    annualized_return = (final_total_value / initial_cash) ** (1 / ownership_years) - 1
    cumulative_return = (final_total_value / initial_cash - 1) * 100

    results = {
        "house_name": house_name,
        "initial_cash_outlay": f"${initial_cash:,.2f}",
        "loan_amount": f"${loan_amount:,.2f}",
        "monthly_payment": f"${monthly_payment:,.2f}",
        "annualized_return": f"{annualized_return * 100:.2f}%",
        "cumulative_return": f"{cumulative_return:.2f}%",
        "capital_gains_tax": f"${capital_gains_tax:,.2f}" if is_rental else "N/A",
        "final_total_value": f"${final_total_value:,.2f}"
    }
    annual_table = annual_df.to_html(index=False, classes='table table-striped')

    # Wealth plot data
    plot_data = []
    for row in annual_data:
        plot_data.append((row["Year"], float(str(row["Total Wealth"]).replace("$", "").replace(",", ""))))
    plot_df = pd.DataFrame(plot_data, columns=["Year", "Total Wealth"])

    img = io.BytesIO()
    plt.figure(figsize=(10, 6))
    plt.plot(plot_df["Year"], plot_df["Total Wealth"], marker='o')
    plt.title(f"Wealth Accumulation Over Time for {house_name}")
    plt.xlabel("Year")
    plt.ylabel("Total Wealth [$]")
    plt.grid(True)
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()

    # Excel export
    global excel_data
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
        schedule_df.to_excel(writer, sheet_name="Amortization Schedule", index=False)
        annual_df.to_excel(writer, sheet_name="Annual Summary", index=False)
        summary_data = {
            "Property Name": [house_name],
            "Initial Cash Outlay": [initial_cash],
            "Loan Amount": [loan_amount],
            "Monthly Mortgage Payment": [monthly_payment],
            "Net Sale Price": [net_sale_price],
            "Final Total Value": [final_total_value],
            "Annualized Return (%)": [annualized_return * 100],
            "Cumulative Return (%)": [cumulative_return],
            "Capital Gains Tax (If Rental)": [capital_gains_tax],
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
    excel_buffer.seek(0)
    excel_data = excel_buffer.read()

    global last_results, last_annual_table
    last_results = results
    last_annual_table = annual_table

    original_data = dict(form)
    return results, annual_table, plot_url, original_data

# [HTML templates for results_html and refinance_results_html are the same as in the previous block; you can use those.]

# ... continue to Part 3 (Refinance logic, routes) ...
# =================== Refinance Simulation Logic =====================

def run_refinance_simulation(form):
    # Unpack original data
    orig = {k: form.get(k) for k in [
        'home_cost', 'closing_cost', 'loan_type_choice', 'custom_loan_term', 'down_payment_percent',
        'annual_appreciation_percent', 'mortgage_interest_rate', 'monthly_rent', 'rental_income_growth_percent',
        'vacancy_rate', 'management_fee_percent', 'hoa_fee', 'prop_tax_mode', 'property_tax_percent',
        'property_tax_amount', 'tax_appraisal_growth', 'ins_mode', 'home_insurance_percent', 'home_insurance_amount',
        'house_name', 'ownership_years', 'sell_closing_cost_percent', 'is_rental', 'structure_percent', 'tax_rate', 'cap_gains_rate'
    ]}
    ownership_years = int(orig['ownership_years'])
    refinance_type = form.get('refinance_type')
    refinance_year = int(form.get('refinance_year'))
    refinance_cost = float(form.get('refinance_cost'))
    refinance_interest_rate = float(form.get('refinance_interest_rate')) / 100.0
    ref_loan_term_years = int(form.get('custom_ref_loan_term'))
    ref_loan_term_months = ref_loan_term_years * 12

    # --- Run the "initial analysis" up to (not including) the refi year ---
    annuals = []
    for yr in range(1, refinance_year):
        yform = orig.copy()
        yform['ownership_years'] = str(yr)
        r, _, _, _ = run_initial_analysis(yform)
        annuals.append(r)
    # Now, we get the full amortization schedule and remaining balance at refi time:
    res, annual_table, plot_url, _ = run_initial_analysis(orig)
    home_cost = float(orig['home_cost'])
    down_payment_percent = float(orig['down_payment_percent']) / 100.0
    closing_cost = float(orig['closing_cost'])
    loan_type_choice = orig['loan_type_choice']
    if loan_type_choice == "1":
        loan_term_years = 30
    elif loan_type_choice == "2":
        loan_term_years = 15
    elif loan_type_choice == "3":
        loan_term_years = int(orig['custom_loan_term'] or 30)
    else:
        loan_term_years = 30
    mortgage_interest_rate = float(orig['mortgage_interest_rate']) / 100.0
    loan_amount = home_cost - (home_cost * down_payment_percent)
    loan_term_months = loan_term_years * 12
    monthly_interest_rate_val = mortgage_interest_rate / 12.0
    monthly_payment = loan_amount * (monthly_interest_rate_val * (1 + monthly_interest_rate_val) ** loan_term_months) / \
                      ((1 + monthly_interest_rate_val) ** loan_term_months - 1)
    schedule = []
    balance = loan_amount
    for m in range(1, loan_term_months + 1):
        interest_payment = balance * monthly_interest_rate_val
        principal_payment = monthly_payment - interest_payment
        balance -= principal_payment
        if balance < 0:
            principal_payment += balance
            balance = 0
        schedule.append((m, monthly_payment, principal_payment, interest_payment, balance))
    schedule_df = pd.DataFrame(schedule, columns=["Month", "Payment", "Principal", "Interest", "Balance"])
    # Determine remaining balance at refinance
    refinance_month = (refinance_year - 1) * 12
    remaining_balance = schedule_df.iloc[refinance_month - 1]["Balance"]

    # Now set up the *new* (post-refi) loan:
    annual_appreciation_percent = float(orig['annual_appreciation_percent']) / 100.0
    monthly_rent = float(orig['monthly_rent'])
    rental_income_growth_percent = float(orig['rental_income_growth_percent']) / 100.0
    vacancy_rate = float(orig['vacancy_rate']) / 100.0
    management_fee_percent = float(orig['management_fee_percent']) / 100.0
    hoa_fee = float(orig['hoa_fee'])
    prop_tax_mode = orig['prop_tax_mode']
    property_tax_percent = float(orig['property_tax_percent'] or 0) / 100.0 if orig['property_tax_percent'] else 0
    property_tax_amount = float(orig['property_tax_amount'] or 0)
    tax_appraisal_growth = float(orig['tax_appraisal_growth']) / 100.0
    ins_mode = orig['ins_mode']
    home_insurance_percent = float(orig['home_insurance_percent'] or 0) / 100.0 if orig['home_insurance_percent'] else 0
    home_insurance_amount = float(orig['home_insurance_amount'] or 0)
    house_name = orig['house_name']
    sell_closing_cost_percent = float(orig['sell_closing_cost_percent']) / 100.0
    is_rental = orig['is_rental'] == "yes"
    structure_percent = float(orig['structure_percent'] or 80) / 100.0
    tax_rate = float(orig['tax_rate'] or 25) / 100.0
    cap_gains_rate = float(orig['cap_gains_rate'] or 20) / 100.0

    refinance_home_value = home_cost * ((1 + annual_appreciation_percent) ** refinance_year)
    if refinance_type == "cashout":
        max_new_loan = refinance_home_value * 0.75
        if max_new_loan <= remaining_balance:
            new_loan_amount = remaining_balance
            cash_out_amount = 0
            net_cash_out = -refinance_cost
            ref_details = f"Refinance amount cannot exceed current balance."
        else:
            cash_out_amount = max_new_loan - remaining_balance
            net_cash_out = cash_out_amount - refinance_cost
            new_loan_amount = max_new_loan
            ref_details = f"Cash-Out Refinance: Net cash out after costs: ${net_cash_out:,.2f}"
    else:
        new_loan_amount = remaining_balance
        cash_out_amount = 0
        net_cash_out = -refinance_cost
        ref_details = f"Rate/Term Refinance: No cash out, loan resets at current balance (after costs deducted from cash flow)."
    # Post-refi amortization schedule
    new_monthly_interest_rate = refinance_interest_rate / 12.0
    new_monthly_payment = new_loan_amount * (new_monthly_interest_rate * (1 + new_monthly_interest_rate) ** ref_loan_term_months) / \
                          ((1 + new_monthly_interest_rate) ** ref_loan_term_months - 1)
    new_schedule = []
    new_balance = new_loan_amount
    for m in range(1, ref_loan_term_months + 1):
        interest_payment = new_balance * new_monthly_interest_rate
        principal_payment = new_monthly_payment - interest_payment
        new_balance -= principal_payment
        if new_balance < 0:
            principal_payment += new_balance
            new_balance = 0
        new_schedule.append((m, new_monthly_payment, principal_payment, interest_payment, new_balance))
    new_schedule_df = pd.DataFrame(new_schedule, columns=["Month", "Payment", "Principal", "Interest", "Balance"])

    # Pre-refinance annuals (just the years up to refi)
    pre_data = []
    cumulative_cash_flow_pre = 0.0
    cumulative_depreciation = 0.0
    assessed_value = home_cost
    structure_value = home_cost * structure_percent
    annual_depreciation = structure_value / 27.5 if is_rental else 0
    initial_cash = home_cost * down_payment_percent + closing_cost

    for year in range(1, refinance_year):
        if year <= loan_term_years:
            start_month = (year - 1) * 12
            end_month = year * 12
            year_schedule = schedule_df.iloc[start_month:end_month]
            total_mortgage_payment = year_schedule["Payment"].sum()
            end_balance = year_schedule.iloc[-1]["Balance"]
        else:
            total_mortgage_payment = 0.0
            end_balance = 0.0

        home_value = home_cost * ((1 + annual_appreciation_percent) ** year)
        if prop_tax_mode.lower() == 'p':
            if year == 1:
                assessed_value = home_cost
            else:
                assessed_value = assessed_value * (1 + tax_appraisal_growth)
            property_tax = property_tax_percent * assessed_value
        else:
            property_tax = property_tax_amount

        maintenance_cost = 0.01 * home_value
        if ins_mode.lower() == 'p':
            insurance_cost = home_insurance_percent * home_value
        else:
            insurance_cost = home_insurance_amount

        operating_expenses = property_tax + maintenance_cost + insurance_cost + hoa_fee
        adjusted_monthly_rent = monthly_rent * ((1 + rental_income_growth_percent) ** (year - 1))
        gross_annual_rent = adjusted_monthly_rent * 12
        effective_rent = gross_annual_rent * (1 - vacancy_rate)
        management_fee = effective_rent * management_fee_percent
        annual_rent_income = effective_rent - management_fee

        depreciation = annual_depreciation if is_rental else 0
        taxable_income = annual_rent_income - (total_mortgage_payment + operating_expenses + depreciation)
        tax_due = max(0, taxable_income) * tax_rate if is_rental else 0
        annual_cash_flow = annual_rent_income - total_mortgage_payment - operating_expenses - tax_due
        cumulative_cash_flow_pre += annual_cash_flow
        cumulative_depreciation += depreciation
        equity = home_value - end_balance
        unrealized_wealth = equity - initial_cash
        total_wealth = cumulative_cash_flow_pre + unrealized_wealth

        pre_data.append({
            "Year": year,
            "Home Value": f"${home_value:,.2f}",
            "Mortgage Balance": f"${end_balance:,.2f}",
            "Equity": f"${equity:,.2f}",
            "Annual Rent Income": f"${annual_rent_income:,.2f}",
            "Operating Expenses": f"${operating_expenses:,.2f}",
            "Annual Cash Flow (After-Tax)": f"${annual_cash_flow:,.2f}",
            "Cumulative Cash Flow": f"${cumulative_cash_flow_pre:,.2f}",
            "Unrealized Wealth": f"${unrealized_wealth:,.2f}",
            "Total Wealth": f"${total_wealth:,.2f}",
            "Taxable Rental Income": f"${taxable_income:,.2f}" if is_rental else "N/A",
            "Tax Due": f"${tax_due:,.2f}" if is_rental else "N/A",
            "Depreciation": f"${depreciation:,.2f}" if is_rental else "N/A"
        })

    # At refi: add net cash-out to cumulative cash flow
    cumulative_cash_flow_ref = cumulative_cash_flow_pre + net_cash_out
    cumulative_depreciation_post = cumulative_depreciation
    assessed_value = home_cost * ((1 + annual_appreciation_percent) ** refinance_year)
    post_data = []
    for j in range(1, ownership_years - refinance_year + 1 + 1):
        current_year = refinance_year + j - 1
        start_month = (j - 1) * 12
        end_month = j * 12
        if j * 12 <= ref_loan_term_months:
            new_year_schedule = new_schedule_df.iloc[start_month:end_month]
            new_total_mortgage_payment = new_year_schedule["Payment"].sum()
            new_end_balance = new_year_schedule.iloc[-1]["Balance"]
        else:
            new_total_mortgage_payment = 0.0
            new_end_balance = 0.0
        home_value = home_cost * ((1 + annual_appreciation_percent) ** current_year)
        if prop_tax_mode.lower() == 'p':
            if current_year == refinance_year:
                assessed_value = home_cost * ((1 + tax_appraisal_growth) ** current_year)
            else:
                assessed_value = assessed_value * (1 + tax_appraisal_growth)
            property_tax = property_tax_percent * assessed_value
        else:
            property_tax = property_tax_amount

        maintenance_cost = 0.01 * home_value
        if ins_mode.lower() == 'p':
            insurance_cost = home_insurance_percent * home_value
        else:
            insurance_cost = home_insurance_amount

        operating_expenses = property_tax + maintenance_cost + insurance_cost + hoa_fee
        adjusted_monthly_rent = monthly_rent * ((1 + rental_income_growth_percent) ** (current_year - 1))
        gross_annual_rent = adjusted_monthly_rent * 12
        effective_rent = gross_annual_rent * (1 - vacancy_rate)
        management_fee = effective_rent * management_fee_percent
        annual_rent_income = effective_rent - management_fee

        depreciation = annual_depreciation if is_rental else 0
        taxable_income = annual_rent_income - (new_total_mortgage_payment + operating_expenses + depreciation)
        tax_due = max(0, taxable_income) * tax_rate if is_rental else 0
        annual_cash_flow = annual_rent_income - new_total_mortgage_payment - operating_expenses - tax_due
        cumulative_cash_flow_ref += annual_cash_flow
        cumulative_depreciation_post += depreciation
        equity = home_value - new_end_balance
        unrealized_wealth = equity - initial_cash
        total_wealth = cumulative_cash_flow_ref + unrealized_wealth

        post_data.append({
            "Year": current_year,
            "Home Value": f"${home_value:,.2f}",
            "Mortgage Balance": f"${new_end_balance:,.2f}",
            "Equity": f"${equity:,.2f}",
            "Annual Rent Income": f"${annual_rent_income:,.2f}",
            "Operating Expenses": f"${operating_expenses:,.2f}",
            "Annual Cash Flow (After-Tax)": f"${annual_cash_flow:,.2f}",
            "Cumulative Cash Flow": f"${cumulative_cash_flow_ref:,.2f}",
            "Unrealized Wealth": f"${unrealized_wealth:,.2f}",
            "Total Wealth": f"${total_wealth:,.2f}",
            "Taxable Rental Income": f"${taxable_income:,.2f}" if is_rental else "N/A",
            "Tax Due": f"${tax_due:,.2f}" if is_rental else "N/A",
            "Depreciation": f"${depreciation:,.2f}" if is_rental else "N/A"
        })

    pre_df = pd.DataFrame(pre_data)
    post_df = pd.DataFrame(post_data)
    pre_df_html = pre_df.to_html(index=False, classes='table table-striped')
    post_df_html = post_df.to_html(index=False, classes='table table-striped')

    # Combined plot
    combined_plot_data = []
    for row in pre_data:
        val = float(row["Total Wealth"].replace("$", "").replace(",", ""))
        combined_plot_data.append((row["Year"], val))
    for row in post_data:
        val = float(row["Total Wealth"].replace("$", "").replace(",", ""))
        combined_plot_data.append((row["Year"], val))
    combined_plot_df = pd.DataFrame(combined_plot_data, columns=["Year", "Total Wealth"])
    img = io.BytesIO()
    plt.figure(figsize=(10, 6))
    plt.plot(combined_plot_df["Year"], combined_plot_df["Total Wealth"], marker='o')
    plt.title(f"Wealth Accumulation Over Time for {house_name}")
    plt.xlabel("Year")
    plt.ylabel("Total Wealth [$]")
    plt.grid(True)
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()

    # Sale returns
    sale_price = home_cost * ((1 + annual_appreciation_percent) ** ownership_years)
    sale_closing_cost = sale_price * sell_closing_cost_percent
    net_sale_price = sale_price - sale_closing_cost
    basis = home_cost + closing_cost - cumulative_depreciation_post if is_rental else home_cost + closing_cost
    capital_gain = net_sale_price - basis
    capital_gains_tax = cap_gains_rate * capital_gain if (is_rental and capital_gain > 0) else 0
    final_total_value = net_sale_price + cumulative_cash_flow_ref - capital_gains_tax
    annualized_return = (final_total_value / initial_cash) ** (1 / ownership_years) - 1
    cumulative_return = (final_total_value / initial_cash - 1) * 100

    results = {
        "house_name": house_name,
        "initial_cash_outlay": f"${initial_cash:,.2f}",
        "loan_amount": f"${loan_amount:,.2f}",
        "monthly_payment": f"${monthly_payment:,.2f}",
        "annualized_return": f"{annualized_return * 100:.2f}%",
        "cumulative_return": f"{cumulative_return:.2f}%",
        "capital_gains_tax": f"${capital_gains_tax:,.2f}" if is_rental else "N/A",
        "final_total_value": f"${final_total_value:,.2f}"
    }
    refinance_details = f"{ref_details}<br>Refinance Year: {refinance_year}<br>Cost: ${refinance_cost:,.2f}<br>New Rate: {refinance_interest_rate*100:.2f}%<br>New Loan Term: {ref_loan_term_years} years"
    # For Excel and PDF download, you can choose to export post-refi as well (left as exercise).
    annual_table = post_df_html
    return results, annual_table, plot_url, refinance_details, pre_df_html, post_df_html

# ========== TEMPLATES ARE DEFINED ABOVE ==========
# [use results_html and refinance_results_html as above]

# ========== ROUTES ==========

@app.route('/')
def index():
    return render_template_string(index_html)

@app.route('/analyze', methods=['POST'])
def analyze():
    results, annual_table, plot_url, original_data = run_initial_analysis(request.form.to_dict())
    return render_template_string(results_html, results=results, annual_table=annual_table,
                                  plot_url=plot_url, original_data=original_data)

@app.route('/simulate_refinance', methods=['POST'])
def simulate_refinance():
    results, annual_table, plot_url, refinance_details, pre_table, post_table = run_refinance_simulation(request.form.to_dict())
    return render_template_string(refinance_results_html, results=results, annual_table=annual_table,
                                  plot_url=plot_url, refinance_details=refinance_details,
                                  pre_table=pre_table, post_table=post_table)

@app.route('/download')
def download_excel():
    global excel_data
    if excel_data is None:
        return "No Excel file available. Please run an analysis first."
    return send_file(
        io.BytesIO(excel_data),
        as_attachment=True,
        download_name="investment_analysis.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.route('/download/pdf')
def download_pdf():
    global last_results, last_annual_table
    if last_results is None or last_annual_table is None:
        return "No PDF available. Please run an analysis first."
    pdf_bytes = generate_pdf_report(last_results, last_annual_table)
    return send_file(
        io.BytesIO(pdf_bytes),
        as_attachment=True,
        download_name="investment_analysis.pdf",
        mimetype="application/pdf"
    )

if __name__ == '__main__':
    app.run(debug=True)
