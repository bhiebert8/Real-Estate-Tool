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
        .remodel-section { background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; padding: 16px; margin-bottom: 16px; }
    </style>
    <script>
        function toggleRemodeling() {
            const isRemodeling = document.getElementById('is_remodeling').value === 'yes';
            document.getElementById('remodeling_details').style.display = isRemodeling ? 'block' : 'none';
        }

        function updateRemodelSections() {
            const numRemodels = parseInt(document.getElementById('num_remodels').value);
            for (let i = 1; i <= 3; i++) {
                document.getElementById('remodel_' + i).style.display = i <= numRemodels ? 'block' : 'none';
            }
        }

        window.onload = function() {
            toggleRemodeling();
            updateRemodelSections();
        }
    </script>
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
                <input type="number" class="form-control" name="down_payment_percent" required step="any">
                <small>Enter as a percentage (e.g., 20 for 20%).</small>
            </div>
            <div class="mb-3">
                <label class="form-label">Annual Appreciation Rate (%)</label>
                <input type="number" class="form-control" name="annual_appreciation_percent" required step="any">
                <small>Expected yearly home value increase (e.g., 3).</small>
            </div>
            <div class="mb-3">
                <label class="form-label">Mortgage Interest Rate (%)</label>
                <input type="number" class="form-control" name="mortgage_interest_rate" required step="any">
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
                <input type="number" class="form-control" name="rental_income_growth_percent" required step="any">
                <small>Annual increase in rent income (e.g., 3).</small>
            </div>
            <div class="mb-3">
                <label class="form-label">Vacancy Rate (%)</label>
                <input type="number" class="form-control" name="vacancy_rate" required step="any">
                <small>Expected average vacancy (e.g., 5).</small>
            </div>
            <div class="mb-3">
                <label class="form-label">Management Fee (%)</label>
                <input type="number" class="form-control" name="management_fee_percent" step="any">
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
                <input type="number" class="form-control" name="property_tax_percent" step="any">
                <small>If mode is 'p', e.g., 1 for 1%.</small>
            </div>
            <div class="mb-3">
                <label class="form-label">Property Tax Amount</label>
                <input type="number" class="form-control" name="property_tax_amount">
                <small>If mode is 'd', enter dollar amount.</small>
            </div>
            <div class="mb-3">
                <label class="form-label">Property Tax Appraisal Growth (%)</label>
                <input type="number" class="form-control" name="tax_appraisal_growth" required step="any">
                <small>If you want property tax based on a different growth rate than market appreciation (e.g., capped appraisal increase), enter that here (e.g., 2).</small>
            </div>
            <div class="mb-3">
                <label class="form-label">Home Insurance Input Mode</label>
                <input type="text" class="form-control" name="ins_mode" required>
                <small>Enter 'p' for percentage or 'd' for fixed amount.</small>
            </div>
            <div class="mb-3">
                <label class="form-label">Home Insurance Percentage</label>
                <input type="number" class="form-control" name="home_insurance_percent" step="any">
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
                <input type="number" class="form-control" name="sell_closing_cost_percent" required step="any">
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
        <div class="section">
            <h2 class="mb-3">Remodeling Plans</h2>
            <div class="mb-3">
                <label class="form-label">Are You Planning to Remodel?</label>
                <select class="form-select" name="is_remodeling" id="is_remodeling" onchange="toggleRemodeling()">
                    <option value="no">No</option>
                    <option value="yes">Yes</option>
                </select>
            </div>
            <div id="remodeling_details" style="display: none;">
                <div class="mb-3">
                    <label class="form-label">Number of Remodels</label>
                    <select class="form-select" name="num_remodels" id="num_remodels" onchange="updateRemodelSections()">
                        <option value="1">1</option>
                        <option value="2">2</option>
                        <option value="3">3</option>
                    </select>
                </div>

                <!-- Remodel 1 -->
                <div id="remodel_1" class="remodel-section">
                    <h4>Remodel 1</h4>
                    <div class="mb-3">
                        <label class="form-label">Cost of Remodel ($)</label>
                        <input type="number" class="form-control" name="remodel_cost_1" value="0">
                        <small>Total cost of this remodel project.</small>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Value Added ($)</label>
                        <input type="number" class="form-control" name="remodel_value_1" value="0">
                        <small>Expected increase in property value from this remodel.</small>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Remodel Year</label>
                        <input type="number" class="form-control" name="remodel_year_1" value="1">
                        <small>Year when remodel will occur (applied at beginning of year).</small>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Months Without Rent</label>
                        <input type="number" class="form-control" name="remodel_months_1" value="0">
                        <small>Number of months property will be vacant during remodel.</small>
                    </div>
                </div>

                <!-- Remodel 2 -->
                <div id="remodel_2" class="remodel-section" style="display: none;">
                    <h4>Remodel 2</h4>
                    <div class="mb-3">
                        <label class="form-label">Cost of Remodel ($)</label>
                        <input type="number" class="form-control" name="remodel_cost_2" value="0">
                        <small>Total cost of this remodel project.</small>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Value Added ($)</label>
                        <input type="number" class="form-control" name="remodel_value_2" value="0">
                        <small>Expected increase in property value from this remodel.</small>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Remodel Year</label>
                        <input type="number" class="form-control" name="remodel_year_2" value="2">
                        <small>Year when remodel will occur (applied at beginning of year).</small>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Months Without Rent</label>
                        <input type="number" class="form-control" name="remodel_months_2" value="0">
                        <small>Number of months property will be vacant during remodel.</small>
                    </div>
                </div>

                <!-- Remodel 3 -->
                <div id="remodel_3" class="remodel-section" style="display: none;">
                    <h4>Remodel 3</h4>
                    <div class="mb-3">
                        <label class="form-label">Cost of Remodel ($)</label>
                        <input type="number" class="form-control" name="remodel_cost_3" value="0">
                        <small>Total cost of this remodel project.</small>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Value Added ($)</label>
                        <input type="number" class="form-control" name="remodel_value_3" value="0">
                        <small>Expected increase in property value from this remodel.</small>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Remodel Year</label>
                        <input type="number" class="form-control" name="remodel_year_3" value="3">
                        <small>Year when remodel will occur (applied at beginning of year).</small>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Months Without Rent</label>
                        <input type="number" class="form-control" name="remodel_months_3" value="0">
                        <small>Number of months property will be vacant during remodel.</small>
                    </div>
                </div>
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
        .remodel-info { background-color: #e3f2fd; padding: 12px; border-radius: 8px; margin-top: 8px; }
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
        {% if results.remodel_summary %}
        <div class="remodel-info">
            <h5>Remodeling Summary</h5>
            {{ results.remodel_summary|safe }}
        </div>
        {% endif %}
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
        .remodel-info { background-color: #e3f2fd; padding: 12px; border-radius: 8px; margin-top: 8px; }
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
        {% if results.remodel_summary %}
        <div class="remodel-info">
            <h5>Remodeling Summary</h5>
            {{ results.remodel_summary|safe }}
        </div>
        {% endif %}
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


# ---- Professional PDF Report Generator ----
def generate_pdf_report(results, annual_table_html, refinance_details=None, pre_table=None, post_table=None,
                        plot_url=None):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import inch, cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (Paragraph, Frame, Image, Spacer, Table, TableStyle,
                                    SimpleDocTemplate, PageBreak, KeepTogether, Flowable,
                                    HRFlowable, PageTemplate, BaseDocTemplate)
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY
    from reportlab.platypus.tableofcontents import TableOfContents
    import tempfile
    import base64
    from datetime import datetime
    import pandas as pd

    # Custom color scheme
    PRIMARY_COLOR = colors.HexColor("#1769aa")
    SECONDARY_COLOR = colors.HexColor("#ffc800")
    ACCENT_COLOR = colors.HexColor("#2196F3")
    DARK_COLOR = colors.HexColor("#212529")
    LIGHT_BLUE = colors.HexColor("#E3F2FD")
    LIGHT_GRAY = colors.HexColor("#F5F5F5")
    SUCCESS_COLOR = colors.HexColor("#4CAF50")
    WARNING_COLOR = colors.HexColor("#FF9800")

    # Create document
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')

    # Custom page template with header/footer
    def add_header_footer(canvas, doc):
        canvas.saveState()
        # Header
        canvas.setFillColor(PRIMARY_COLOR)
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawString(1 * inch, 10.5 * inch, results.get("house_name", "Property Analysis"))
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(7.5 * inch, 10.5 * inch, f"Generated: {datetime.now().strftime('%B %d, %Y')}")

        # Header line
        canvas.setStrokeColor(PRIMARY_COLOR)
        canvas.setLineWidth(2)
        canvas.line(1 * inch, 10.3 * inch, 7.5 * inch, 10.3 * inch)

        # Footer
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.gray)
        canvas.drawCentredString(4.25 * inch, 0.5 * inch, f"Page {doc.page}")
        canvas.drawString(1 * inch, 0.5 * inch, "Confidential Investment Analysis")
        canvas.drawRightString(7.5 * inch, 0.5 * inch, "Real Estate Investment Tool")
        canvas.restoreState()

    # Create document with custom page template
    doc = SimpleDocTemplate(
        tmp.name,
        pagesize=letter,
        topMargin=1.2 * inch,
        bottomMargin=1 * inch,
        leftMargin=1 * inch,
        rightMargin=1 * inch
    )

    # Build story
    story = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=32,
        textColor=PRIMARY_COLOR,
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=24,
        textColor=SECONDARY_COLOR,
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    section_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=PRIMARY_COLOR,
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold',
        borderWidth=0,
        borderPadding=0,
        borderColor=PRIMARY_COLOR,
        borderRadius=5
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        leading=16,
        alignment=TA_JUSTIFY,
        spaceAfter=12
    )

    # ========== COVER PAGE ==========
    story.append(Spacer(1, 2 * inch))
    story.append(Paragraph("INVESTMENT ANALYSIS REPORT", title_style))
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph(results.get("house_name", ""), subtitle_style))
    story.append(Spacer(1, 0.3 * inch))

    # Executive metrics on cover
    cover_data = [
        ["Initial Investment", results.get("initial_cash_outlay", "")],
        ["Projected Return", results.get("annualized_return", "")],
        ["Total Value at Exit", results.get("final_total_value", "")]
    ]
    cover_table = Table(cover_data, colWidths=[2.5 * inch, 2.5 * inch])
    cover_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 14),
        ('TEXTCOLOR', (0, 0), (0, -1), PRIMARY_COLOR),
        ('TEXTCOLOR', (1, 0), (1, -1), SUCCESS_COLOR),
        ('LINEBELOW', (0, 0), (-1, -2), 1, colors.lightgrey),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
    ]))
    story.append(cover_table)

    story.append(Spacer(1, 1 * inch))
    story.append(Paragraph(f"Prepared on {datetime.now().strftime('%B %d, %Y')}",
                           ParagraphStyle('DateStyle', parent=body_style, alignment=TA_CENTER, fontSize=12)))
    story.append(PageBreak())

    # ========== EXECUTIVE SUMMARY ==========
    story.append(Paragraph("EXECUTIVE SUMMARY", section_style))
    story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY_COLOR, spaceAfter=12))

    # Key metrics summary box
    exec_summary_data = []

    # Parse values for calculations
    try:
        initial_cash = float(results.get("initial_cash_outlay", "0").replace("$", "").replace(",", ""))
        final_value = float(results.get("final_total_value", "0").replace("$", "").replace(",", ""))
        profit = final_value - initial_cash

        exec_summary_data = [
            ["METRIC", "VALUE", "ANALYSIS"],
            ["Initial Cash Required", results.get("initial_cash_outlay", ""), "Total upfront investment"],
            ["Loan Amount", results.get("loan_amount", ""), "Mortgage principal"],
            ["Monthly Payment", results.get("monthly_payment", ""), "P&I payment"],
            ["Annualized Return", results.get("annualized_return", ""),
             "Excellent" if float(results.get("annualized_return", "0%").replace("%", "")) > 10 else "Good"],
            ["Total Return", results.get("cumulative_return", ""), f"Profit: ${profit:,.2f}"],
            ["Final Portfolio Value", results.get("final_total_value", ""), "After all costs & taxes"]
        ]
    except:
        exec_summary_data = [
            ["METRIC", "VALUE", "NOTES"],
            ["Initial Cash Required", results.get("initial_cash_outlay", ""), ""],
            ["Loan Amount", results.get("loan_amount", ""), ""],
            ["Monthly Payment", results.get("monthly_payment", ""), ""],
            ["Annualized Return", results.get("annualized_return", ""), ""],
            ["Total Return", results.get("cumulative_return", ""), ""],
            ["Final Portfolio Value", results.get("final_total_value", ""), ""]
        ]

    exec_table = Table(exec_summary_data, colWidths=[2.2 * inch, 1.8 * inch, 2.5 * inch])
    exec_table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        # Data rows
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ('TEXTCOLOR', (1, 1), (1, -1), SUCCESS_COLOR),
        ('FONTNAME', (1, 1), (1, -1), 'Helvetica-Bold'),
        # Styling
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(exec_table)

    # Investment thesis
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Investment Thesis", ParagraphStyle('SubSection', parent=section_style, fontSize=14)))

    try:
        ann_return = float(results.get('annualized_return', '0%').replace('%', ''))
        if ann_return >= 15:
            thesis = "This investment presents an <b>exceptional opportunity</b> with projected returns significantly exceeding market averages. The combination of leverage, cash flow, and appreciation creates a compelling wealth-building vehicle."
        elif ann_return >= 10:
            thesis = "This property offers <b>strong returns</b> that outperform typical market investments. The risk-adjusted returns justify the capital commitment and management requirements."
        elif ann_return >= 5:
            thesis = "This investment provides <b>steady, reliable returns</b> suitable for conservative investors seeking stable cash flow and gradual wealth accumulation."
        else:
            thesis = "This property offers <b>modest returns</b> that may be suitable for risk-averse investors or those prioritizing stability over growth."
    except:
        thesis = "This real estate investment combines rental income, tax benefits, and appreciation potential to create long-term wealth."

    story.append(Paragraph(thesis, body_style))

    # Remodeling summary if applicable
    if results.get("remodel_summary"):
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph("Remodeling Strategy", ParagraphStyle('SubSection', parent=section_style, fontSize=14)))
        # Parse the HTML-style remodel summary
        remodel_text = results.get("remodel_summary", "").replace("<b>", "").replace("</b>", "").replace("<br>", "\n")
        story.append(Paragraph(remodel_text.replace("\n", "<br/>"), body_style))

    story.append(PageBreak())

    # ========== REFINANCING OPPORTUNITIES ==========
    story.append(Paragraph("STRATEGIC REFINANCING OPPORTUNITIES", section_style))
    story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY_COLOR, spaceAfter=12))

    story.append(
        Paragraph("Cash-Out Refinance Strategy", ParagraphStyle('SubSection', parent=section_style, fontSize=14)))

    refinance_text = """
    As your property appreciates and the mortgage balance decreases, significant equity will accumulate, 
    creating opportunities for strategic cash-out refinancing. This powerful wealth-building tool allows 
    investors to access their equity without selling the property.
    """
    story.append(Paragraph(refinance_text, body_style))

    story.append(Spacer(1, 0.2 * inch))

    # Refinance options box
    refi_options_data = [
        ["INVESTOR OPTIONS AT REFINANCE", ""],
        ["Option 1: Cash Return", "Receive your initial investment back tax-free while maintaining property ownership"],
        ["Option 2: Portfolio Expansion", "Reinvest proceeds into additional properties to compound returns"],
        ["Option 3: Hybrid Approach", "Take partial cash distribution and reinvest remainder"]
    ]

    refi_table = Table(refi_options_data, colWidths=[2 * inch, 4.5 * inch])
    refi_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), SECONDARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), DARK_COLOR),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('SPAN', (0, 0), (1, 0)),
        # Options
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TEXTCOLOR', (0, 1), (0, -1), PRIMARY_COLOR),
        # Styling
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [LIGHT_BLUE, colors.white, LIGHT_BLUE]),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(refi_table)

    story.append(Spacer(1, 0.3 * inch))
    story.append(
        Paragraph("Our Deal Sourcing Advantage", ParagraphStyle('SubSection', parent=section_style, fontSize=14)))

    sourcing_text = """
    <b>We specialize in sourcing the very best real estate investment opportunities.</b> Our team leverages:

    • Extensive market relationships with brokers, wholesalers, and property owners
    • Advanced analytics to identify undervalued properties with strong appreciation potential
    • Rigorous due diligence process to minimize risk and maximize returns
    • Off-market deal flow providing exclusive access to premium opportunities
    • Strategic market timing to capitalize on optimal entry and exit points

    When you're ready to expand your portfolio through refinancing proceeds, we'll present carefully 
    vetted opportunities that meet our strict investment criteria, ensuring your capital is deployed 
    into properties with the highest potential for success.
    """
    story.append(Paragraph(sourcing_text, body_style))

    # Wealth accumulation chart (if available)
    if plot_url:
        story.append(PageBreak())
        story.append(Paragraph("PROJECTED WEALTH ACCUMULATION", section_style))
        story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY_COLOR, spaceAfter=12))
        try:
            imgdata = base64.b64decode(plot_url)
            tmpimg = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            tmpimg.write(imgdata)
            tmpimg.flush()
            img = Image(tmpimg.name, width=6 * inch, height=3.5 * inch)
            story.append(KeepTogether([img]))
            story.append(Paragraph("<i>Chart shows total wealth accumulation including equity and cash flow</i>",
                                   ParagraphStyle('Caption', parent=body_style, fontSize=9, textColor=colors.gray,
                                                  alignment=TA_CENTER)))
        except:
            story.append(Paragraph("Chart unavailable", body_style))

    story.append(PageBreak())

    # ========== INVESTMENT METRICS & RATIOS ==========
    story.append(Paragraph("KEY INVESTMENT METRICS", section_style))
    story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY_COLOR, spaceAfter=12))

    # Calculate additional metrics if possible
    try:
        loan_amount = float(results.get("loan_amount", "0").replace("$", "").replace(",", ""))
        initial_cash = float(results.get("initial_cash_outlay", "0").replace("$", "").replace(",", ""))
        monthly_payment = float(results.get("monthly_payment", "0").replace("$", "").replace(",", ""))

        # Try to get first year rent from annual table
        annual_df = pd.read_html(annual_table_html)[0]
        first_year_rent = annual_df.iloc[0]["Annual Rent Income"]
        first_year_rent_val = float(first_year_rent.replace("$", "").replace(",", ""))

        # Calculate metrics
        total_investment = loan_amount + initial_cash
        leverage_ratio = loan_amount / total_investment
        debt_service = monthly_payment * 12
        dscr = first_year_rent_val / debt_service if debt_service > 0 else 0

        metrics_data = [
            ["FINANCIAL METRICS", "VALUE", "BENCHMARK", "STATUS"],
            ["Leverage Ratio", f"{leverage_ratio * 100:.1f}%", "60-80%", "✓" if 0.6 <= leverage_ratio <= 0.8 else "!"],
            ["Debt Service Coverage", f"{dscr:.2f}x", ">1.25x", "✓" if dscr > 1.25 else "!"],
            ["Cash-on-Cash Return", "Calculated", ">8%", "—"],
            ["Cap Rate", "Market-based", "4-10%", "—"]
        ]
    except:
        metrics_data = [
            ["FINANCIAL METRICS", "VALUE", "BENCHMARK", "STATUS"],
            ["Leverage Ratio", "—", "60-80%", "—"],
            ["Debt Service Coverage", "—", ">1.25x", "—"],
            ["Cash-on-Cash Return", "—", ">8%", "—"],
            ["Cap Rate", "—", "4-10%", "—"]
        ]

    metrics_table = Table(metrics_data, colWidths=[2.5 * inch, 1.5 * inch, 1.5 * inch, 1 * inch])
    metrics_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), ACCENT_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        # Data
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BLUE]),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(metrics_table)

    # ========== RISK ANALYSIS ==========
    story.append(Spacer(1, 0.4 * inch))
    story.append(Paragraph("RISK ASSESSMENT", section_style))
    story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY_COLOR, spaceAfter=12))

    risk_data = [
        ["RISK FACTOR", "IMPACT", "MITIGATION STRATEGY"],
        ["Market Downturn", "Medium", "Conservative appreciation assumptions, strong cash flow buffer"],
        ["Vacancy Risk", "Low-Med", "Competitive pricing, property maintenance, tenant screening"],
        ["Interest Rate Risk", "Medium", "Fixed-rate mortgage, refinancing options available"],
        ["Maintenance Surprises", "Low", "Annual reserves, regular inspections, warranty coverage"],
        ["Regulatory Changes", "Low", "Stay informed on local regulations, professional management"]
    ]

    risk_table = Table(risk_data, colWidths=[2.2 * inch, 1.3 * inch, 3 * inch])
    risk_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), WARNING_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        # Risk factors column
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        # Impact column colors
        ('TEXTCOLOR', (1, 1), (1, 1), WARNING_COLOR),  # Medium
        ('TEXTCOLOR', (1, 2), (1, 2), SECONDARY_COLOR),  # Low-Med
        ('TEXTCOLOR', (1, 3), (1, 3), WARNING_COLOR),  # Medium
        ('TEXTCOLOR', (1, 4), (1, 4), SUCCESS_COLOR),  # Low
        ('TEXTCOLOR', (1, 5), (1, 5), SUCCESS_COLOR),  # Low
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),
        ('FONTNAME', (1, 1), (1, -1), 'Helvetica-Bold'),
        # Grid and styling
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(risk_table)

    story.append(PageBreak())

    # ========== EXIT STRATEGY ==========
    story.append(Paragraph("EXIT STRATEGY & RETURNS", section_style))
    story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY_COLOR, spaceAfter=12))

    story.append(Paragraph("Disposition Analysis", ParagraphStyle('SubSection', parent=section_style, fontSize=14)))

    exit_text = f"""
    This analysis assumes a {results.get('ownership_years', 'N/A')}-year holding period with the following exit assumptions:

    • Property appreciation continues at the modeled rate
    • Selling costs of approximately 6-7% of sale price
    • Capital gains tax treatment for investment properties
    • All deferred maintenance addressed prior to sale
    """
    story.append(Paragraph(exit_text, body_style))

    # Capital gains summary if rental
    if results.get("capital_gains_tax", "N/A") != "N/A":
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph("Tax Implications", ParagraphStyle('SubSection', parent=section_style, fontSize=14)))
        cap_gains_text = f"""
        As a rental property, this investment will be subject to capital gains tax upon sale. 
        The estimated tax liability is {results.get('capital_gains_tax', 'N/A')}, which has been 
        factored into the final return calculations. Consider 1031 exchange options to defer taxes.
        """
        story.append(Paragraph(cap_gains_text, body_style))

    # ========== APPENDIX (if refinance) ==========
    if refinance_details:
        story.append(PageBreak())
        story.append(Paragraph("REFINANCE ANALYSIS", section_style))
        story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY_COLOR, spaceAfter=12))
        story.append(Paragraph(refinance_details.replace("<br>", "<br/>"), body_style))

    # ========== DISCLAIMER ==========
    story.append(PageBreak())
    story.append(Paragraph("IMPORTANT DISCLAIMERS", section_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.red, spaceAfter=12))

    disclaimer_text = """
    <b>Investment Risk:</b> Real estate investments carry inherent risks including but not limited to market volatility, 
    economic downturns, natural disasters, and regulatory changes. Past performance does not guarantee future results.

    <b>Tax Advice:</b> This analysis provides estimates only. Consult with a qualified tax professional for advice 
    specific to your situation. Tax laws and regulations are subject to change.

    <b>Financial Projections:</b> All projections are based on assumptions that may not materialize. Actual results 
    may vary significantly from these projections.

    <b>Professional Advice:</b> This tool is for educational purposes only and does not constitute financial, legal, 
    or tax advice. Always consult with qualified professionals before making investment decisions.
    """

    story.append(
        Paragraph(disclaimer_text, ParagraphStyle('Disclaimer', parent=body_style, fontSize=9, textColor=colors.gray)))

    # Build PDF
    doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
    tmp.seek(0)
    return tmp.read()
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
        .remodel-section { background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; padding: 16px; margin-bottom: 16px; }
    </style>
    <script>
        function toggleRemodeling() {
            const isRemodeling = document.getElementById('is_remodeling').value === 'yes';
            document.getElementById('remodeling_details').style.display = isRemodeling ? 'block' : 'none';
        }

        function updateRemodelSections() {
            const numRemodels = parseInt(document.getElementById('num_remodels').value);
            for (let i = 1; i <= 3; i++) {
                document.getElementById('remodel_' + i).style.display = i <= numRemodels ? 'block' : 'none';
            }
        }

        window.onload = function() {
            toggleRemodeling();
            updateRemodelSections();
        }
    </script>
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
                <input type="number" class="form-control" name="down_payment_percent" required step="any">
                <small>Enter as a percentage (e.g., 20 for 20%).</small>
            </div>
            <div class="mb-3">
                <label class="form-label">Annual Appreciation Rate (%)</label>
                <input type="number" class="form-control" name="annual_appreciation_percent" required step="any">
                <small>Expected yearly home value increase (e.g., 3).</small>
            </div>
            <div class="mb-3">
                <label class="form-label">Mortgage Interest Rate (%)</label>
                <input type="number" class="form-control" name="mortgage_interest_rate" required step="any">
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
                <input type="number" class="form-control" name="rental_income_growth_percent" required step="any">
                <small>Annual increase in rent income (e.g., 3).</small>
            </div>
            <div class="mb-3">
                <label class="form-label">Vacancy Rate (%)</label>
                <input type="number" class="form-control" name="vacancy_rate" required step="any">
                <small>Expected average vacancy (e.g., 5).</small>
            </div>
            <div class="mb-3">
                <label class="form-label">Management Fee (%)</label>
                <input type="number" class="form-control" name="management_fee_percent" step="any">
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
                <input type="number" class="form-control" name="property_tax_percent" step="any">
                <small>If mode is 'p', e.g., 1 for 1%.</small>
            </div>
            <div class="mb-3">
                <label class="form-label">Property Tax Amount</label>
                <input type="number" class="form-control" name="property_tax_amount">
                <small>If mode is 'd', enter dollar amount.</small>
            </div>
            <div class="mb-3">
                <label class="form-label">Property Tax Appraisal Growth (%)</label>
                <input type="number" class="form-control" name="tax_appraisal_growth" required step="any">
                <small>If you want property tax based on a different growth rate than market appreciation (e.g., capped appraisal increase), enter that here (e.g., 2).</small>
            </div>
            <div class="mb-3">
                <label class="form-label">Home Insurance Input Mode</label>
                <input type="text" class="form-control" name="ins_mode" required>
                <small>Enter 'p' for percentage or 'd' for fixed amount.</small>
            </div>
            <div class="mb-3">
                <label class="form-label">Home Insurance Percentage</label>
                <input type="number" class="form-control" name="home_insurance_percent" step="any">
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
                <input type="number" class="form-control" name="sell_closing_cost_percent" required step="any">
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
        <div class="section">
            <h2 class="mb-3">Remodeling Plans</h2>
            <div class="mb-3">
                <label class="form-label">Are You Planning to Remodel?</label>
                <select class="form-select" name="is_remodeling" id="is_remodeling" onchange="toggleRemodeling()">
                    <option value="no">No</option>
                    <option value="yes">Yes</option>
                </select>
            </div>
            <div id="remodeling_details" style="display: none;">
                <div class="mb-3">
                    <label class="form-label">Number of Remodels</label>
                    <select class="form-select" name="num_remodels" id="num_remodels" onchange="updateRemodelSections()">
                        <option value="1">1</option>
                        <option value="2">2</option>
                        <option value="3">3</option>
                    </select>
                </div>

                <!-- Remodel 1 -->
                <div id="remodel_1" class="remodel-section">
                    <h4>Remodel 1</h4>
                    <div class="mb-3">
                        <label class="form-label">Cost of Remodel ($)</label>
                        <input type="number" class="form-control" name="remodel_cost_1" value="0">
                        <small>Total cost of this remodel project.</small>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Value Added ($)</label>
                        <input type="number" class="form-control" name="remodel_value_1" value="0">
                        <small>Expected increase in property value from this remodel.</small>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Remodel Year</label>
                        <input type="number" class="form-control" name="remodel_year_1" value="1">
                        <small>Year when remodel will occur (applied at beginning of year).</small>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Months Without Rent</label>
                        <input type="number" class="form-control" name="remodel_months_1" value="0">
                        <small>Number of months property will be vacant during remodel.</small>
                    </div>
                </div>

                <!-- Remodel 2 -->
                <div id="remodel_2" class="remodel-section" style="display: none;">
                    <h4>Remodel 2</h4>
                    <div class="mb-3">
                        <label class="form-label">Cost of Remodel ($)</label>
                        <input type="number" class="form-control" name="remodel_cost_2" value="0">
                        <small>Total cost of this remodel project.</small>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Value Added ($)</label>
                        <input type="number" class="form-control" name="remodel_value_2" value="0">
                        <small>Expected increase in property value from this remodel.</small>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Remodel Year</label>
                        <input type="number" class="form-control" name="remodel_year_2" value="2">
                        <small>Year when remodel will occur (applied at beginning of year).</small>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Months Without Rent</label>
                        <input type="number" class="form-control" name="remodel_months_2" value="0">
                        <small>Number of months property will be vacant during remodel.</small>
                    </div>
                </div>

                <!-- Remodel 3 -->
                <div id="remodel_3" class="remodel-section" style="display: none;">
                    <h4>Remodel 3</h4>
                    <div class="mb-3">
                        <label class="form-label">Cost of Remodel ($)</label>
                        <input type="number" class="form-control" name="remodel_cost_3" value="0">
                        <small>Total cost of this remodel project.</small>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Value Added ($)</label>
                        <input type="number" class="form-control" name="remodel_value_3" value="0">
                        <small>Expected increase in property value from this remodel.</small>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Remodel Year</label>
                        <input type="number" class="form-control" name="remodel_year_3" value="3">
                        <small>Year when remodel will occur (applied at beginning of year).</small>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Months Without Rent</label>
                        <input type="number" class="form-control" name="remodel_months_3" value="0">
                        <small>Number of months property will be vacant during remodel.</small>
                    </div>
                </div>
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
        .remodel-info { background-color: #e3f2fd; padding: 12px; border-radius: 8px; margin-top: 8px; }
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
        {% if results.remodel_summary %}
        <div class="remodel-info">
            <h5>Remodeling Summary</h5>
            {{ results.remodel_summary|safe }}
        </div>
        {% endif %}
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
        .remodel-info { background-color: #e3f2fd; padding: 12px; border-radius: 8px; margin-top: 8px; }
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
        {% if results.remodel_summary %}
        <div class="remodel-info">
            <h5>Remodeling Summary</h5>
            {{ results.remodel_summary|safe }}
        </div>
        {% endif %}
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


# ---- Professional PDF Report Generator ----
def generate_pdf_report(results, annual_table_html, refinance_details=None, pre_table=None, post_table=None,
                        plot_url=None):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import inch, cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (Paragraph, Frame, Image, Spacer, Table, TableStyle,
                                    SimpleDocTemplate, PageBreak, KeepTogether, Flowable,
                                    HRFlowable, PageTemplate, BaseDocTemplate)
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY
    from reportlab.platypus.tableofcontents import TableOfContents
    import tempfile
    import base64
    from datetime import datetime
    import pandas as pd

    # Custom color scheme
    PRIMARY_COLOR = colors.HexColor("#1769aa")
    SECONDARY_COLOR = colors.HexColor("#ffc800")
    ACCENT_COLOR = colors.HexColor("#2196F3")
    DARK_COLOR = colors.HexColor("#212529")
    LIGHT_BLUE = colors.HexColor("#E3F2FD")
    LIGHT_GRAY = colors.HexColor("#F5F5F5")
    SUCCESS_COLOR = colors.HexColor("#4CAF50")
    WARNING_COLOR = colors.HexColor("#FF9800")

    # Create document
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')

    # Custom page template with header/footer
    def add_header_footer(canvas, doc):
        canvas.saveState()
        # Header
        canvas.setFillColor(PRIMARY_COLOR)
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawString(1 * inch, 10.5 * inch, results.get("house_name", "Property Analysis"))
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(7.5 * inch, 10.5 * inch, f"Generated: {datetime.now().strftime('%B %d, %Y')}")

        # Header line
        canvas.setStrokeColor(PRIMARY_COLOR)
        canvas.setLineWidth(2)
        canvas.line(1 * inch, 10.3 * inch, 7.5 * inch, 10.3 * inch)

        # Footer
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.gray)
        canvas.drawCentredString(4.25 * inch, 0.5 * inch, f"Page {doc.page}")
        canvas.drawString(1 * inch, 0.5 * inch, "Confidential Investment Analysis")
        canvas.drawRightString(7.5 * inch, 0.5 * inch, "Real Estate Investment Tool")
        canvas.restoreState()

    # Create document with custom page template
    doc = SimpleDocTemplate(
        tmp.name,
        pagesize=letter,
        topMargin=1.2 * inch,
        bottomMargin=1 * inch,
        leftMargin=1 * inch,
        rightMargin=1 * inch
    )

    # Build story
    story = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=32,
        textColor=PRIMARY_COLOR,
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=24,
        textColor=SECONDARY_COLOR,
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    section_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=PRIMARY_COLOR,
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold',
        borderWidth=0,
        borderPadding=0,
        borderColor=PRIMARY_COLOR,
        borderRadius=5
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        leading=16,
        alignment=TA_JUSTIFY,
        spaceAfter=12
    )

    # ========== COVER PAGE ==========
    story.append(Spacer(1, 2 * inch))
    story.append(Paragraph("INVESTMENT ANALYSIS REPORT", title_style))
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph(results.get("house_name", ""), subtitle_style))
    story.append(Spacer(1, 0.3 * inch))

    # Executive metrics on cover
    cover_data = [
        ["Initial Investment", results.get("initial_cash_outlay", "")],
        ["Projected Return", results.get("annualized_return", "")],
        ["Total Value at Exit", results.get("final_total_value", "")]
    ]
    cover_table = Table(cover_data, colWidths=[2.5 * inch, 2.5 * inch])
    cover_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 14),
        ('TEXTCOLOR', (0, 0), (0, -1), PRIMARY_COLOR),
        ('TEXTCOLOR', (1, 0), (1, -1), SUCCESS_COLOR),
        ('LINEBELOW', (0, 0), (-1, -2), 1, colors.lightgrey),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
    ]))
    story.append(cover_table)

    story.append(Spacer(1, 1 * inch))
    story.append(Paragraph(f"Prepared on {datetime.now().strftime('%B %d, %Y')}",
                           ParagraphStyle('DateStyle', parent=body_style, alignment=TA_CENTER, fontSize=12)))
    story.append(PageBreak())

    # ========== EXECUTIVE SUMMARY ==========
    story.append(Paragraph("EXECUTIVE SUMMARY", section_style))
    story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY_COLOR, spaceAfter=12))

    # Key metrics summary box
    exec_summary_data = []

    # Parse values for calculations
    try:
        initial_cash = float(results.get("initial_cash_outlay", "0").replace("$", "").replace(",", ""))
        final_value = float(results.get("final_total_value", "0").replace("$", "").replace(",", ""))
        profit = final_value - initial_cash

        exec_summary_data = [
            ["METRIC", "VALUE", "ANALYSIS"],
            ["Initial Cash Required", results.get("initial_cash_outlay", ""), "Total upfront investment"],
            ["Loan Amount", results.get("loan_amount", ""), "Mortgage principal"],
            ["Monthly Payment", results.get("monthly_payment", ""), "P&I payment"],
            ["Annualized Return", results.get("annualized_return", ""),
             "Excellent" if float(results.get("annualized_return", "0%").replace("%", "")) > 10 else "Good"],
            ["Total Return", results.get("cumulative_return", ""), f"Profit: ${profit:,.2f}"],
            ["Final Portfolio Value", results.get("final_total_value", ""), "After all costs & taxes"]
        ]
    except:
        exec_summary_data = [
            ["METRIC", "VALUE", "NOTES"],
            ["Initial Cash Required", results.get("initial_cash_outlay", ""), ""],
            ["Loan Amount", results.get("loan_amount", ""), ""],
            ["Monthly Payment", results.get("monthly_payment", ""), ""],
            ["Annualized Return", results.get("annualized_return", ""), ""],
            ["Total Return", results.get("cumulative_return", ""), ""],
            ["Final Portfolio Value", results.get("final_total_value", ""), ""]
        ]

    exec_table = Table(exec_summary_data, colWidths=[2.2 * inch, 1.8 * inch, 2.5 * inch])
    exec_table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        # Data rows
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ('TEXTCOLOR', (1, 1), (1, -1), SUCCESS_COLOR),
        ('FONTNAME', (1, 1), (1, -1), 'Helvetica-Bold'),
        # Styling
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(exec_table)

    # Investment thesis
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Investment Thesis", ParagraphStyle('SubSection', parent=section_style, fontSize=14)))

    try:
        ann_return = float(results.get('annualized_return', '0%').replace('%', ''))
        if ann_return >= 15:
            thesis = "This investment presents an <b>exceptional opportunity</b> with projected returns significantly exceeding market averages. The combination of leverage, cash flow, and appreciation creates a compelling wealth-building vehicle."
        elif ann_return >= 10:
            thesis = "This property offers <b>strong returns</b> that outperform typical market investments. The risk-adjusted returns justify the capital commitment and management requirements."
        elif ann_return >= 5:
            thesis = "This investment provides <b>steady, reliable returns</b> suitable for conservative investors seeking stable cash flow and gradual wealth accumulation."
        else:
            thesis = "This property offers <b>modest returns</b> that may be suitable for risk-averse investors or those prioritizing stability over growth."
    except:
        thesis = "This real estate investment combines rental income, tax benefits, and appreciation potential to create long-term wealth."

    story.append(Paragraph(thesis, body_style))

    # Remodeling summary if applicable
    if results.get("remodel_summary"):
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph("Remodeling Strategy", ParagraphStyle('SubSection', parent=section_style, fontSize=14)))
        # Parse the HTML-style remodel summary
        remodel_text = results.get("remodel_summary", "").replace("<b>", "").replace("</b>", "").replace("<br>", "\n")
        story.append(Paragraph(remodel_text.replace("\n", "<br/>"), body_style))

    story.append(PageBreak())

    # ========== REFINANCING OPPORTUNITIES ==========
    story.append(Paragraph("STRATEGIC REFINANCING OPPORTUNITIES", section_style))
    story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY_COLOR, spaceAfter=12))

    story.append(
        Paragraph("Cash-Out Refinance Strategy", ParagraphStyle('SubSection', parent=section_style, fontSize=14)))

    refinance_text = """
    As your property appreciates and the mortgage balance decreases, significant equity will accumulate, 
    creating opportunities for strategic cash-out refinancing. This powerful wealth-building tool allows 
    investors to access their equity without selling the property.
    """
    story.append(Paragraph(refinance_text, body_style))

    story.append(Spacer(1, 0.2 * inch))

    # Refinance options box
    refi_options_data = [
        ["INVESTOR OPTIONS AT REFINANCE", ""],
        ["Option 1: Cash Return", "Receive your initial investment back tax-free while maintaining property ownership"],
        ["Option 2: Portfolio Expansion", "Reinvest proceeds into additional properties to compound returns"],
        ["Option 3: Hybrid Approach", "Take partial cash distribution and reinvest remainder"]
    ]

    refi_table = Table(refi_options_data, colWidths=[2 * inch, 4.5 * inch])
    refi_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), SECONDARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), DARK_COLOR),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('SPAN', (0, 0), (1, 0)),
        # Options
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TEXTCOLOR', (0, 1), (0, -1), PRIMARY_COLOR),
        # Styling
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [LIGHT_BLUE, colors.white, LIGHT_BLUE]),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(refi_table)

    story.append(Spacer(1, 0.3 * inch))
    story.append(
        Paragraph("Our Deal Sourcing Advantage", ParagraphStyle('SubSection', parent=section_style, fontSize=14)))

    sourcing_text = """
    <b>We specialize in sourcing the very best real estate investment opportunities.</b> Our team leverages:

    • Extensive market relationships with brokers, wholesalers, and property owners
    • Advanced analytics to identify undervalued properties with strong appreciation potential
    • Rigorous due diligence process to minimize risk and maximize returns
    • Off-market deal flow providing exclusive access to premium opportunities
    • Strategic market timing to capitalize on optimal entry and exit points

    When you're ready to expand your portfolio through refinancing proceeds, we'll present carefully 
    vetted opportunities that meet our strict investment criteria, ensuring your capital is deployed 
    into properties with the highest potential for success.
    """
    story.append(Paragraph(sourcing_text, body_style))

    # Wealth accumulation chart (if available)
    if plot_url:
        story.append(PageBreak())
        story.append(Paragraph("PROJECTED WEALTH ACCUMULATION", section_style))
        story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY_COLOR, spaceAfter=12))
        try:
            imgdata = base64.b64decode(plot_url)
            tmpimg = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            tmpimg.write(imgdata)
            tmpimg.flush()
            img = Image(tmpimg.name, width=6 * inch, height=3.5 * inch)
            story.append(KeepTogether([img]))
            story.append(Paragraph("<i>Chart shows total wealth accumulation including equity and cash flow</i>",
                                   ParagraphStyle('Caption', parent=body_style, fontSize=9, textColor=colors.gray,
                                                  alignment=TA_CENTER)))
        except:
            story.append(Paragraph("Chart unavailable", body_style))

    story.append(PageBreak())

    # ========== INVESTMENT METRICS & RATIOS ==========
    story.append(Paragraph("KEY INVESTMENT METRICS", section_style))
    story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY_COLOR, spaceAfter=12))

    # Calculate additional metrics if possible
    try:
        loan_amount = float(results.get("loan_amount", "0").replace("$", "").replace(",", ""))
        initial_cash = float(results.get("initial_cash_outlay", "0").replace("$", "").replace(",", ""))
        monthly_payment = float(results.get("monthly_payment", "0").replace("$", "").replace(",", ""))

        # Try to get first year rent from annual table
        annual_df = pd.read_html(annual_table_html)[0]
        first_year_rent = annual_df.iloc[0]["Annual Rent Income"]
        first_year_rent_val = float(first_year_rent.replace("$", "").replace(",", ""))

        # Calculate metrics
        total_investment = loan_amount + initial_cash
        leverage_ratio = loan_amount / total_investment
        debt_service = monthly_payment * 12
        dscr = first_year_rent_val / debt_service if debt_service > 0 else 0

        metrics_data = [
            ["FINANCIAL METRICS", "VALUE", "BENCHMARK", "STATUS"],
            ["Leverage Ratio", f"{leverage_ratio * 100:.1f}%", "60-80%", "✓" if 0.6 <= leverage_ratio <= 0.8 else "!"],
            ["Debt Service Coverage", f"{dscr:.2f}x", ">1.25x", "✓" if dscr > 1.25 else "!"],
            ["Cash-on-Cash Return", "Calculated", ">8%", "—"],
            ["Cap Rate", "Market-based", "4-10%", "—"]
        ]
    except:
        metrics_data = [
            ["FINANCIAL METRICS", "VALUE", "BENCHMARK", "STATUS"],
            ["Leverage Ratio", "—", "60-80%", "—"],
            ["Debt Service Coverage", "—", ">1.25x", "—"],
            ["Cash-on-Cash Return", "—", ">8%", "—"],
            ["Cap Rate", "—", "4-10%", "—"]
        ]

    metrics_table = Table(metrics_data, colWidths=[2.5 * inch, 1.5 * inch, 1.5 * inch, 1 * inch])
    metrics_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), ACCENT_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        # Data
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BLUE]),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(metrics_table)

    # ========== RISK ANALYSIS ==========
    story.append(Spacer(1, 0.4 * inch))
    story.append(Paragraph("RISK ASSESSMENT", section_style))
    story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY_COLOR, spaceAfter=12))

    risk_data = [
        ["RISK FACTOR", "IMPACT", "MITIGATION STRATEGY"],
        ["Market Downturn", "Medium", "Conservative appreciation assumptions, strong cash flow buffer"],
        ["Vacancy Risk", "Low-Med", "Competitive pricing, property maintenance, tenant screening"],
        ["Interest Rate Risk", "Medium", "Fixed-rate mortgage, refinancing options available"],
        ["Maintenance Surprises", "Low", "Annual reserves, regular inspections, warranty coverage"],
        ["Regulatory Changes", "Low", "Stay informed on local regulations, professional management"]
    ]

    risk_table = Table(risk_data, colWidths=[2.2 * inch, 1.3 * inch, 3 * inch])
    risk_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), WARNING_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        # Risk factors column
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        # Impact column colors
        ('TEXTCOLOR', (1, 1), (1, 1), WARNING_COLOR),  # Medium
        ('TEXTCOLOR', (1, 2), (1, 2), SECONDARY_COLOR),  # Low-Med
        ('TEXTCOLOR', (1, 3), (1, 3), WARNING_COLOR),  # Medium
        ('TEXTCOLOR', (1, 4), (1, 4), SUCCESS_COLOR),  # Low
        ('TEXTCOLOR', (1, 5), (1, 5), SUCCESS_COLOR),  # Low
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),
        ('FONTNAME', (1, 1), (1, -1), 'Helvetica-Bold'),
        # Grid and styling
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(risk_table)

    story.append(PageBreak())

    # ========== EXIT STRATEGY ==========
    story.append(Paragraph("EXIT STRATEGY & RETURNS", section_style))
    story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY_COLOR, spaceAfter=12))

    story.append(Paragraph("Disposition Analysis", ParagraphStyle('SubSection', parent=section_style, fontSize=14)))

    exit_text = f"""
    This analysis assumes a {results.get('ownership_years', 'N/A')}-year holding period with the following exit assumptions:

    • Property appreciation continues at the modeled rate
    • Selling costs of approximately 6-7% of sale price
    • Capital gains tax treatment for investment properties
    • All deferred maintenance addressed prior to sale
    """
    story.append(Paragraph(exit_text, body_style))

    # Capital gains summary if rental
    if results.get("capital_gains_tax", "N/A") != "N/A":
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph("Tax Implications", ParagraphStyle('SubSection', parent=section_style, fontSize=14)))
        cap_gains_text = f"""
        As a rental property, this investment will be subject to capital gains tax upon sale. 
        The estimated tax liability is {results.get('capital_gains_tax', 'N/A')}, which has been 
        factored into the final return calculations. Consider 1031 exchange options to defer taxes.
        """
        story.append(Paragraph(cap_gains_text, body_style))

    # ========== APPENDIX (if refinance) ==========
    if refinance_details:
        story.append(PageBreak())
        story.append(Paragraph("REFINANCE ANALYSIS", section_style))
        story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY_COLOR, spaceAfter=12))
        story.append(Paragraph(refinance_details.replace("<br>", "<br/>"), body_style))

    # ========== DISCLAIMER ==========
    story.append(PageBreak())
    story.append(Paragraph("IMPORTANT DISCLAIMERS", section_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.red, spaceAfter=12))

    disclaimer_text = """
    <b>Investment Risk:</b> Real estate investments carry inherent risks including but not limited to market volatility, 
    economic downturns, natural disasters, and regulatory changes. Past performance does not guarantee future results.

    <b>Tax Advice:</b> This analysis provides estimates only. Consult with a qualified tax professional for advice 
    specific to your situation. Tax laws and regulations are subject to change.

    <b>Financial Projections:</b> All projections are based on assumptions that may not materialize. Actual results 
    may vary significantly from these projections.

    <b>Professional Advice:</b> This tool is for educational purposes only and does not constitute financial, legal, 
    or tax advice. Always consult with qualified professionals before making investment decisions.
    """

    story.append(
        Paragraph(disclaimer_text, ParagraphStyle('Disclaimer', parent=body_style, fontSize=9, textColor=colors.gray)))

    # Build PDF
    doc

# ========== Main Loan/Analysis Logic with Remodeling ==========
def parse_remodeling_data(form):
    """Parse remodeling information from form data"""
    remodeling_data = []

    if form.get('is_remodeling') == 'yes':
        num_remodels = int(form.get('num_remodels', 1))

        for i in range(1, num_remodels + 1):
            remodel = {
                'cost': float(form.get(f'remodel_cost_{i}', 0)),
                'value_added': float(form.get(f'remodel_value_{i}', 0)),
                'year': int(form.get(f'remodel_year_{i}', i)),
                'months_no_rent': int(form.get(f'remodel_months_{i}', 0))
            }
            if remodel['cost'] > 0:  # Only add if there's actually a cost
                remodeling_data.append(remodel)

    return remodeling_data


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
    property_tax_percent = float(form.get('property_tax_percent') or 0) / 100.0 if form.get(
        'property_tax_percent') else 0
    property_tax_amount = float(form.get('property_tax_amount') or 0)
    tax_appraisal_growth = float(form.get('tax_appraisal_growth')) / 100.0

    ins_mode = form.get('ins_mode')
    home_insurance_percent = float(form.get('home_insurance_percent') or 0) / 100.0 if form.get(
        'home_insurance_percent') else 0
    home_insurance_amount = float(form.get('home_insurance_amount') or 0)

    house_name = form.get('house_name')
    ownership_years = int(form.get('ownership_years'))
    sell_closing_cost_percent = float(form.get('sell_closing_cost_percent')) / 100.0
    is_rental = form.get('is_rental') == "yes"
    structure_percent = float(form.get('structure_percent') or 80) / 100.0
    tax_rate = float(form.get('tax_rate') or 25) / 100.0
    cap_gains_rate = float(form.get('cap_gains_rate') or 20) / 100.0

    # Parse remodeling data
    remodeling_data = parse_remodeling_data(form)

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

    # ========== Annual Summary with Remodeling ==========
    annual_data = []
    cumulative_cash_flow = 0.0
    cumulative_depreciation = 0.0
    cumulative_remodel_cost = 0.0
    cumulative_value_added = 0.0
    assessed_value = home_cost
    structure_value = home_cost * structure_percent
    annual_depreciation = structure_value / 27.5 if is_rental else 0

    # Create a dict to track remodels by year
    remodels_by_year = {}
    for remodel in remodeling_data:
        year = remodel['year']
        if year not in remodels_by_year:
            remodels_by_year[year] = []
        remodels_by_year[year].append(remodel)

    for year in range(1, ownership_years + 1):
        # Check for remodeling this year
        year_remodels = remodels_by_year.get(year, [])
        year_remodel_cost = sum(r['cost'] for r in year_remodels)
        year_value_added = sum(r['value_added'] for r in year_remodels)
        year_months_no_rent = sum(r['months_no_rent'] for r in year_remodels)

        # Ensure we don't exceed 12 months of no rent
        year_months_no_rent = min(year_months_no_rent, 12)

        cumulative_remodel_cost += year_remodel_cost
        cumulative_value_added += year_value_added

        if year <= loan_term_years:
            start_month = (year - 1) * 12
            end_month = year * 12
            year_schedule = schedule_df.iloc[start_month:end_month]
            total_mortgage_payment = year_schedule["Payment"].sum()
            end_balance = year_schedule.iloc[-1]["Balance"]
        else:
            total_mortgage_payment = 0.0
            end_balance = 0.0

        # Home value includes appreciation plus value added from remodeling
        base_home_value = home_cost * ((1 + annual_appreciation_percent) ** year)
        home_value = base_home_value + cumulative_value_added

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

        # Adjust rent for remodeling vacancy
        adjusted_monthly_rent = monthly_rent * ((1 + rental_income_growth_percent) ** (year - 1))
        gross_annual_rent = adjusted_monthly_rent * 12

        # Reduce rent by the months of remodeling
        if year_months_no_rent > 0:
            effective_months = 12 - year_months_no_rent
            gross_annual_rent = adjusted_monthly_rent * effective_months

        effective_rent = gross_annual_rent * (1 - vacancy_rate)
        management_fee = effective_rent * management_fee_percent
        annual_rent_income = effective_rent - management_fee

        depreciation = annual_depreciation if is_rental else 0
        taxable_income = annual_rent_income - (total_mortgage_payment + operating_expenses + depreciation)
        tax_due = max(0, taxable_income) * tax_rate if is_rental else 0

        # Annual cash flow includes remodeling costs
        annual_cash_flow = annual_rent_income - total_mortgage_payment - operating_expenses - tax_due - year_remodel_cost
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
            "Remodel Cost": f"${year_remodel_cost:,.2f}" if year_remodel_cost > 0 else "$0",
            "Annual Cash Flow (After-Tax)": f"${annual_cash_flow:,.2f}",
            "Cumulative Cash Flow": f"${cumulative_cash_flow:,.2f}",
            "Unrealized Wealth": f"${unrealized_wealth:,.2f}",
            "Total Wealth": f"${total_wealth:,.2f}",
            "Taxable Rental Income": f"${taxable_income:,.2f}" if is_rental else "N/A",
            "Tax Due": f"${tax_due:,.2f}" if is_rental else "N/A",
            "Depreciation": f"${depreciation:,.2f}" if is_rental else "N/A"
        })

    annual_df = pd.DataFrame(annual_data)

    sale_price = home_cost * ((1 + annual_appreciation_percent) ** ownership_years) + cumulative_value_added
    sale_closing_cost = sale_price * sell_closing_cost_percent
    net_sale_price = sale_price - sale_closing_cost
    basis = home_cost + closing_cost + cumulative_remodel_cost - cumulative_depreciation if is_rental else home_cost + closing_cost + cumulative_remodel_cost
    capital_gain = net_sale_price - basis
    capital_gains_tax = cap_gains_rate * capital_gain if (is_rental and capital_gain > 0) else 0
    final_total_value = net_sale_price + cumulative_cash_flow - capital_gains_tax

    annualized_return = (final_total_value / initial_cash) ** (1 / ownership_years) - 1
    cumulative_return = (final_total_value / initial_cash - 1) * 100

    # Create remodeling summary
    remodel_summary = ""
    if remodeling_data:
        remodel_summary = f"<b>Total Remodeling Investment:</b> ${cumulative_remodel_cost:,.2f}<br>"
        remodel_summary += f"<b>Total Value Added:</b> ${cumulative_value_added:,.2f}<br>"
        remodel_summary += f"<b>Net Value Gain:</b> ${cumulative_value_added - cumulative_remodel_cost:,.2f}<br>"
        for i, remodel in enumerate(remodeling_data, 1):
            remodel_summary += f"<br><b>Remodel {i}:</b> Year {remodel['year']}, Cost: ${remodel['cost']:,.2f}, "
            remodel_summary += f"Value Added: ${remodel['value_added']:,.2f}, Vacancy: {remodel['months_no_rent']} months"

    results = {
        "house_name": house_name,
        "initial_cash_outlay": f"${initial_cash:,.2f}",
        "loan_amount": f"${loan_amount:,.2f}",
        "monthly_payment": f"${monthly_payment:,.2f}",
        "annualized_return": f"{annualized_return * 100:.2f}%",
        "cumulative_return": f"{cumulative_return:.2f}%",
        "capital_gains_tax": f"${capital_gains_tax:,.2f}" if is_rental else "N/A",
        "final_total_value": f"${final_total_value:,.2f}",
        "remodel_summary": remodel_summary if remodeling_data else None,
        "has_remodeling": len(remodeling_data) > 0
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

    # Excel export with remodeling info
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
            "Total Remodeling Cost": [cumulative_remodel_cost],
            "Total Value Added": [cumulative_value_added]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name="Summary", index=False)

        # Add remodeling details sheet if applicable
        if remodeling_data:
            remodel_df = pd.DataFrame(remodeling_data)
            remodel_df.to_excel(writer, sheet_name="Remodeling Details", index=False)

    excel_buffer.seek(0)
    excel_data = excel_buffer.read()

    global last_results, last_annual_table
    last_results = results
    last_annual_table = annual_table

    original_data = dict(form)
    return results, annual_table, plot_url, original_data


# =================== Refinance Simulation Logic with Remodeling =====================

def run_refinance_simulation(form):
    # Unpack original data
    orig = {k: form.get(k) for k in [
        'home_cost', 'closing_cost', 'loan_type_choice', 'custom_loan_term', 'down_payment_percent',
        'annual_appreciation_percent', 'mortgage_interest_rate', 'monthly_rent', 'rental_income_growth_percent',
        'vacancy_rate', 'management_fee_percent', 'hoa_fee', 'prop_tax_mode', 'property_tax_percent',
        'property_tax_amount', 'tax_appraisal_growth', 'ins_mode', 'home_insurance_percent', 'home_insurance_amount',
        'house_name', 'ownership_years', 'sell_closing_cost_percent', 'is_rental', 'structure_percent', 'tax_rate',
        'cap_gains_rate',
        'is_remodeling', 'num_remodels', 'remodel_cost_1', 'remodel_value_1', 'remodel_year_1', 'remodel_months_1',
        'remodel_cost_2', 'remodel_value_2', 'remodel_year_2', 'remodel_months_2',
        'remodel_cost_3', 'remodel_value_3', 'remodel_year_3', 'remodel_months_3'
    ]}
    ownership_years = int(orig['ownership_years'])
    refinance_type = form.get('refinance_type')
    refinance_year = int(form.get('refinance_year'))
    refinance_cost = float(form.get('refinance_cost'))
    refinance_interest_rate = float(form.get('refinance_interest_rate')) / 100.0
    ref_loan_term_years = int(form.get('custom_ref_loan_term'))
    ref_loan_term_months = ref_loan_term_years * 12

    # Parse remodeling data
    remodeling_data = parse_remodeling_data(orig)

    # Run the initial analysis to get full data
    res, annual_table, plot_url, _ = run_initial_analysis(orig)

    # Extract key values
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

    # Build amortization schedule
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

    # Get other parameters
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

    # Calculate cumulative value added from remodeling up to refinance year
    cumulative_value_added_at_refi = sum(r['value_added'] for r in remodeling_data if r['year'] < refinance_year)

    refinance_home_value = home_cost * (
                (1 + annual_appreciation_percent) ** refinance_year) + cumulative_value_added_at_refi

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
    new_monthly_payment = new_loan_amount * (
                new_monthly_interest_rate * (1 + new_monthly_interest_rate) ** ref_loan_term_months) / \
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

    # Create a dict to track remodels by year
    remodels_by_year = {}
    for remodel in remodeling_data:
        year = remodel['year']
        if year not in remodels_by_year:
            remodels_by_year[year] = []
        remodels_by_year[year].append(remodel)

    # Pre-refinance annuals
    pre_data = []
    cumulative_cash_flow_pre = 0.0
    cumulative_depreciation = 0.0
    cumulative_remodel_cost = 0.0
    cumulative_value_added = 0.0
    assessed_value = home_cost
    structure_value = home_cost * structure_percent
    annual_depreciation = structure_value / 27.5 if is_rental else 0
    initial_cash = home_cost * down_payment_percent + closing_cost

    for year in range(1, refinance_year):
        # Check for remodeling this year
        year_remodels = remodels_by_year.get(year, [])
        year_remodel_cost = sum(r['cost'] for r in year_remodels)
        year_value_added = sum(r['value_added'] for r in year_remodels)
        year_months_no_rent = min(sum(r['months_no_rent'] for r in year_remodels), 12)

        cumulative_remodel_cost += year_remodel_cost
        cumulative_value_added += year_value_added

        if year <= loan_term_years:
            start_month = (year - 1) * 12
            end_month = year * 12
            year_schedule = schedule_df.iloc[start_month:end_month]
            total_mortgage_payment = year_schedule["Payment"].sum()
            end_balance = year_schedule.iloc[-1]["Balance"]
        else:
            total_mortgage_payment = 0.0
            end_balance = 0.0

        base_home_value = home_cost * ((1 + annual_appreciation_percent) ** year)
        home_value = base_home_value + cumulative_value_added

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

        # Adjust for remodeling vacancy
        if year_months_no_rent > 0:
            effective_months = 12 - year_months_no_rent
            gross_annual_rent = adjusted_monthly_rent * effective_months
        else:
            gross_annual_rent = adjusted_monthly_rent * 12

        effective_rent = gross_annual_rent * (1 - vacancy_rate)
        management_fee = effective_rent * management_fee_percent
        annual_rent_income = effective_rent - management_fee

        depreciation = annual_depreciation if is_rental else 0
        taxable_income = annual_rent_income - (total_mortgage_payment + operating_expenses + depreciation)
        tax_due = max(0, taxable_income) * tax_rate if is_rental else 0
        annual_cash_flow = annual_rent_income - total_mortgage_payment - operating_expenses - tax_due - year_remodel_cost
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
            "Remodel Cost": f"${year_remodel_cost:,.2f}" if year_remodel_cost > 0 else "$0",
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

        # Check for remodeling this year
        year_remodels = remodels_by_year.get(current_year, [])
        year_remodel_cost = sum(r['cost'] for r in year_remodels)
        year_value_added = sum(r['value_added'] for r in year_remodels)
        year_months_no_rent = min(sum(r['months_no_rent'] for r in year_remodels), 12)

        cumulative_remodel_cost += year_remodel_cost
        cumulative_value_added += year_value_added

        start_month = (j - 1) * 12
        end_month = j * 12
        if j * 12 <= ref_loan_term_months:
            new_year_schedule = new_schedule_df.iloc[start_month:end_month]
            new_total_mortgage_payment = new_year_schedule["Payment"].sum()
            new_end_balance = new_year_schedule.iloc[-1]["Balance"]
        else:
            new_total_mortgage_payment = 0.0
            new_end_balance = 0.0

        base_home_value = home_cost * ((1 + annual_appreciation_percent) ** current_year)
        home_value = base_home_value + cumulative_value_added

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

        # Adjust for remodeling vacancy
        if year_months_no_rent > 0:
            effective_months = 12 - year_months_no_rent
            gross_annual_rent = adjusted_monthly_rent * effective_months
        else:
            gross_annual_rent = adjusted_monthly_rent * 12

        effective_rent = gross_annual_rent * (1 - vacancy_rate)
        management_fee = effective_rent * management_fee_percent
        annual_rent_income = effective_rent - management_fee

        depreciation = annual_depreciation if is_rental else 0
        taxable_income = annual_rent_income - (new_total_mortgage_payment + operating_expenses + depreciation)
        tax_due = max(0, taxable_income) * tax_rate if is_rental else 0
        annual_cash_flow = annual_rent_income - new_total_mortgage_payment - operating_expenses - tax_due - year_remodel_cost
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
            "Remodel Cost": f"${year_remodel_cost:,.2f}" if year_remodel_cost > 0 else "$0",
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
    sale_price = home_cost * ((1 + annual_appreciation_percent) ** ownership_years) + cumulative_value_added
    sale_closing_cost = sale_price * sell_closing_cost_percent
    net_sale_price = sale_price - sale_closing_cost
    basis = home_cost + closing_cost + cumulative_remodel_cost - cumulative_depreciation_post if is_rental else home_cost + closing_cost + cumulative_remodel_cost
    capital_gain = net_sale_price - basis
    capital_gains_tax = cap_gains_rate * capital_gain if (is_rental and capital_gain > 0) else 0
    final_total_value = net_sale_price + cumulative_cash_flow_ref - capital_gains_tax
    annualized_return = (final_total_value / initial_cash) ** (1 / ownership_years) - 1
    cumulative_return = (final_total_value / initial_cash - 1) * 100

    # Create remodeling summary
    remodel_summary = ""
    if remodeling_data:
        remodel_summary = f"<b>Total Remodeling Investment:</b> ${cumulative_remodel_cost:,.2f}<br>"
        remodel_summary += f"<b>Total Value Added:</b> ${cumulative_value_added:,.2f}<br>"
        remodel_summary += f"<b>Net Value Gain:</b> ${cumulative_value_added - cumulative_remodel_cost:,.2f}<br>"
        for i, remodel in enumerate(remodeling_data, 1):
            remodel_summary += f"<br><b>Remodel {i}:</b> Year {remodel['year']}, Cost: ${remodel['cost']:,.2f}, "
            remodel_summary += f"Value Added: ${remodel['value_added']:,.2f}, Vacancy: {remodel['months_no_rent']} months"

    results = {
        "house_name": house_name,
        "initial_cash_outlay": f"${initial_cash:,.2f}",
        "loan_amount": f"${loan_amount:,.2f}",
        "monthly_payment": f"${monthly_payment:,.2f}",
        "annualized_return": f"{annualized_return * 100:.2f}%",
        "cumulative_return": f"{cumulative_return:.2f}%",
        "capital_gains_tax": f"${capital_gains_tax:,.2f}" if is_rental else "N/A",
        "final_total_value": f"${final_total_value:,.2f}",
        "remodel_summary": remodel_summary if remodeling_data else None,
        "has_remodeling": len(remodeling_data) > 0
    }

    refinance_details = f"{ref_details}<br>Refinance Year: {refinance_year}<br>Cost: ${refinance_cost:,.2f}<br>New Rate: {refinance_interest_rate * 100:.2f}%<br>New Loan Term: {ref_loan_term_years} years"
    annual_table = post_df_html

    return results, annual_table, plot_url, refinance_details, pre_df_html, post_df_html


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
    results, annual_table, plot_url, refinance_details, pre_table, post_table = run_refinance_simulation(
        request.form.to_dict())
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
