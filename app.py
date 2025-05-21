from flask import Flask, render_template_string, request, send_file, url_for
import io
import math
import pandas as pd

import matplotlib
matplotlib.use('AGG')
import matplotlib.pyplot as plt
import base64

app = Flask(__name__)
excel_data = None  # Global variable to hold Excel file data for download

##########################################
# HTML Templates (as inline strings)
##########################################

# Index page – only initial loan info with short descriptions.
index_html = '''
<!DOCTYPE html>
<html>
<head>
    <title>Real Estate Investment Analysis</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <!-- Bootstrap 5 CDN -->
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
            <h2 class="mb-3">Property Details</h2>
            <div class="mb-3">
                <label class="form-label">House Name</label>
                <input type="text" class="form-control" name="house_name" required>
                <small>Nickname or identifier for the property.</small>
            </div>
            <div class="mb-3">
                <label class="form-label">Ownership Years</label>
                <input type="number" class="form-control" name="ownership_years" required>
                <small>How many years you plan to own the property.</small>
            </div>
            <div class="mb-3">
                <label class="form-label">Selling Closing Cost Percentage</label>
                <input type="number" class="form-control" name="sell_closing_cost_percent" required>
                <small>Closing cost when selling (e.g., 6 for 6%).</small>
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

# Results page – shows original analysis and then a section to optionally simulate refinancing.
results_html = '''
<!DOCTYPE html>
<html>
<head>
    <title>Investment Analysis Results</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <!-- Bootstrap 5 CDN -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .section { background: #fff; border-radius: 12px; box-shadow: 0 2px 12px #eef3ff; padding: 24px; margin-bottom: 28px; }
        body { background: linear-gradient(90deg, #f7faff 0%, #e3f6fc 100%); }
        h1 { color: #1769aa; font-weight: 800; }
        .divider { background-color: #90EE90; text-align: center; font-weight: bold; padding: 5px; margin: 10px 0; border-radius: 8px; }
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
        <p class="text-muted">If you wish to simulate refinancing (to extract cash or obtain a better rate/timeline), please fill out the fields below. Your original loan info is passed along automatically.</p>
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
                <small class="form-text text-muted">Choose 'Cash-Out' to extract equity or 'New Rate' for better terms without cash.</small>
            </div>
            <div class="mb-3">
                <label class="form-label">Refinance Year</label>
                <input type="number" class="form-control" name="refinance_year" required>
                <small class="form-text text-muted">Year in which you plan to refinance (must be &gt; 1).</small>
            </div>
            <div class="mb-3">
                <label class="form-label">Cost to Refinance (in dollars)</label>
                <input type="number" class="form-control" name="refinance_cost" required>
                <small class="form-text text-muted">All fees associated with refinancing.</small>
            </div>
            <div class="mb-3">
                <label class="form-label">New Refinancing Annual Interest Rate (%)</label>
                <input type="number" class="form-control" name="refinance_interest_rate" required>
                <small class="form-text text-muted">Enter the new interest rate you expect.</small>
            </div>
            <div class="mb-3">
                <label class="form-label">New Loan Term (years)</label>
                <input type="number" class="form-control" name="custom_ref_loan_term" required>
                <small class="form-text text-muted">Length of the new loan term (e.g., 30 or 15).</small>
            </div>
            <div class="d-grid gap-2 col-6 mx-auto">
                <button type="submit" class="btn btn-success btn-lg my-3 shadow">Simulate Refinance</button>
            </div>
        </form>
    </div>
    <div class="section text-center">
        <a class="btn btn-outline-primary btn-lg" href="{{ url_for('download_excel') }}">⬇️ Download Excel File of Analysis</a>
    </div>
    <div class="text-center my-4">
        <a href="{{ url_for('index') }}" class="btn btn-link">⬅️ Back to Input Form</a>
    </div>
</div>
</body>
</html>
'''

# Results page after refinance simulation – shows both original and refinance details.
refinance_results_html = '''
<!DOCTYPE html>
<html>
<head>
    <title>Refinance Simulation Results</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <!-- Bootstrap 5 CDN -->
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
    </div>
    <div class="text-center my-4">
        <a href="{{ url_for('index') }}" class="btn btn-link">⬅️ Back to Input Form</a>
    </div>
</div>
</body>
</html>
'''


##########################################
# Analysis Functions
##########################################

def run_initial_analysis(form):
    """
    Run the analysis for the initial loan using the inputs.
    Returns a dictionary of results, the annual summary table as HTML,
    the wealth accumulation plot (as a base64 image string), and a dictionary
    of original input data to pass along for refinance simulation.
    """
    # Store original input values to pass along
    original_data = {
        'home_cost': form.get('home_cost'),
        'closing_cost': form.get('closing_cost'),
        'loan_type_choice': form.get('loan_type_choice'),
        'custom_loan_term': form.get('custom_loan_term') or "",
        'down_payment_percent': form.get('down_payment_percent'),
        'annual_appreciation_percent': form.get('annual_appreciation_percent'),
        'mortgage_interest_rate': form.get('mortgage_interest_rate'),
        'monthly_rent': form.get('monthly_rent'),
        'rental_income_growth_percent': form.get('rental_income_growth_percent'),
        'prop_tax_mode': form.get('prop_tax_mode'),
        'property_tax_percent': form.get('property_tax_percent') or "",
        'property_tax_amount': form.get('property_tax_amount') or "",
        'ins_mode': form.get('ins_mode'),
        'home_insurance_percent': form.get('home_insurance_percent') or "",
        'home_insurance_amount': form.get('home_insurance_amount') or "",
        'house_name': form.get('house_name'),
        'ownership_years': form.get('ownership_years'),
        'sell_closing_cost_percent': form.get('sell_closing_cost_percent')
    }
    # Convert numeric inputs
    home_cost = float(original_data['home_cost'])
    closing_cost = float(original_data['closing_cost'])
    loan_type_choice = original_data['loan_type_choice']
    if loan_type_choice == "1":
        loan_term_years = 30
    elif loan_type_choice == "2":
        loan_term_years = 15
    elif loan_type_choice == "3":
        loan_term_years = int(original_data['custom_loan_term'] or 30)
    else:
        loan_term_years = 30
    down_payment_percent = float(original_data['down_payment_percent']) / 100.0
    annual_appreciation_percent = float(original_data['annual_appreciation_percent']) / 100.0
    mortgage_interest_rate = float(original_data['mortgage_interest_rate']) / 100.0
    monthly_rent = float(original_data['monthly_rent'])
    rental_income_growth_percent = float(original_data['rental_income_growth_percent']) / 100.0

    # Property tax
    if original_data['prop_tax_mode'].lower() == 'p':
        property_tax_percent = float(original_data['property_tax_percent']) / 100.0
        property_tax_amount = None
    else:
        property_tax_amount = float(original_data['property_tax_amount'])
        property_tax_percent = None

    # Home insurance
    if original_data['ins_mode'].lower() == 'p':
        home_insurance_percent = float(original_data['home_insurance_percent']) / 100.0
        home_insurance_amount = None
    else:
        home_insurance_amount = float(original_data['home_insurance_amount'])
        home_insurance_percent = None

    house_name = original_data['house_name']
    ownership_years = int(original_data['ownership_years'])
    sell_closing_cost_percent = float(original_data['sell_closing_cost_percent']) / 100.0

    # Initial Loan Calculations
    down_payment = home_cost * down_payment_percent
    initial_cash = down_payment + closing_cost
    loan_amount = home_cost - down_payment
    loan_term_months = loan_term_years * 12
    monthly_interest_rate_val = mortgage_interest_rate / 12.0

    monthly_payment = loan_amount * (monthly_interest_rate_val * (1 + monthly_interest_rate_val) ** loan_term_months) / \
                      ((1 + monthly_interest_rate_val) ** loan_term_months - 1)

    # Build the full amortization schedule
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

    # Annual summary and wealth accumulation (original simulation)
    annual_data = []
    cumulative_cash_flow = 0.0
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
        equity = home_value - end_balance

        if property_tax_percent is not None:
            property_tax = property_tax_percent * home_value
        else:
            property_tax = property_tax_amount
        maintenance_cost = 0.01 * home_value
        if home_insurance_percent is not None:
            insurance_cost = home_insurance_percent * home_value
        else:
            insurance_cost = home_insurance_amount
        operating_expenses = property_tax + maintenance_cost + insurance_cost

        adjusted_monthly_rent = monthly_rent * ((1 + rental_income_growth_percent) ** (year - 1))
        annual_rent_income = adjusted_monthly_rent * 12

        annual_cash_flow = annual_rent_income - total_mortgage_payment - operating_expenses
        cumulative_cash_flow += annual_cash_flow
        unrealized_wealth = equity - initial_cash
        realized_wealth = cumulative_cash_flow
        total_wealth = unrealized_wealth + realized_wealth

        annual_data.append({
            "Year": year,
            "Home Value": f"${home_value:,.2f}",
            "Mortgage Balance": f"${end_balance:,.2f}",
            "Equity": f"${equity:,.2f}",
            "Annual Rent Income": f"${annual_rent_income:,.2f}",
            "Operating Expenses": f"${operating_expenses:,.2f}",
            "Annual Cash Flow": f"${annual_cash_flow:,.2f}",
            "Cumulative Cash Flow": f"${realized_wealth:,.2f}",
            "Unrealized Wealth": f"${unrealized_wealth:,.2f}",
            "Total Wealth": f"${total_wealth:,.2f}"
        })
    annual_df = pd.DataFrame(annual_data)

    # Wealth accumulation plot data
    plot_data = []
    cumulative_cash_flow_plot = 0.0
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
        equity = home_value - end_balance
        if property_tax_percent is not None:
            property_tax = property_tax_percent * home_value
        else:
            property_tax = property_tax_amount
        maintenance_cost = 0.01 * home_value
        if home_insurance_percent is not None:
            insurance_cost = home_insurance_percent * home_value
        else:
            insurance_cost = home_insurance_amount
        operating_expenses = property_tax + maintenance_cost + insurance_cost
        adjusted_monthly_rent = monthly_rent * ((1 + rental_income_growth_percent) ** (year - 1))
        annual_rent_income = adjusted_monthly_rent * 12
        annual_cash_flow = annual_rent_income - total_mortgage_payment - operating_expenses
        cumulative_cash_flow_plot += annual_cash_flow
        unrealized_wealth = equity - initial_cash
        total_wealth = cumulative_cash_flow_plot + unrealized_wealth
        plot_data.append((year, total_wealth))
    plot_df = pd.DataFrame(plot_data, columns=["Year", "Total Wealth"])

    # Sale Returns
    sale_price = home_cost * ((1 + annual_appreciation_percent) ** ownership_years)
    sale_closing_cost = sale_price * sell_closing_cost_percent
    net_sale_price = sale_price - sale_closing_cost
    final_total_value = net_sale_price + cumulative_cash_flow
    annualized_return = (final_total_value / initial_cash) ** (1 / ownership_years) - 1
    cumulative_return = (final_total_value / initial_cash - 1) * 100

    # Prepare summary results
    results = {
        "house_name": house_name,
        "initial_cash_outlay": f"${initial_cash:,.2f}",
        "loan_amount": f"${loan_amount:,.2f}",
        "monthly_payment": f"${monthly_payment:,.2f}",
        "annualized_return": f"{annualized_return * 100:.2f}%",
        "cumulative_return": f"{cumulative_return:.2f}%"
    }
    annual_table = annual_df.to_html(index=False, classes='table table-striped')

    # Generate wealth accumulation plot image
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

    # Generate Excel file
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
            "Cumulative Return (%)": [cumulative_return]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
    excel_buffer.seek(0)
    excel_data = excel_buffer.read()

    return results, annual_table, plot_url, original_data


def run_refinance_simulation(form):
    """
    Run the refinance simulation using original parameters (passed via hidden fields)
    along with new refinance inputs.
    Returns updated results, annual table, wealth accumulation plot,
    details of refinance simulation, and HTML tables for pre- and post-refinance cash flows.
    """
    # Get original data (hidden fields)
    original_data = {key: form.get(key) for key in [
        'home_cost', 'closing_cost', 'loan_type_choice', 'custom_loan_term',
        'down_payment_percent', 'annual_appreciation_percent', 'mortgage_interest_rate',
        'monthly_rent', 'rental_income_growth_percent', 'prop_tax_mode',
        'property_tax_percent', 'property_tax_amount', 'ins_mode',
        'home_insurance_percent', 'home_insurance_amount', 'house_name',
        'ownership_years', 'sell_closing_cost_percent'
    ]}
    # Run initial analysis first
    results, annual_table, _, orig_data = run_initial_analysis(original_data)
    home_cost = float(original_data['home_cost'])
    closing_cost = float(original_data['closing_cost'])
    if original_data['loan_type_choice'] == "1":
        loan_term_years = 30
    elif original_data['loan_type_choice'] == "2":
        loan_term_years = 15
    else:
        loan_term_years = int(original_data['custom_loan_term'] or 30)
    down_payment_percent = float(original_data['down_payment_percent']) / 100.0
    annual_appreciation_percent = float(original_data['annual_appreciation_percent']) / 100.0
    mortgage_interest_rate = float(original_data['mortgage_interest_rate']) / 100.0
    monthly_rent = float(original_data['monthly_rent'])
    rental_income_growth_percent = float(original_data['rental_income_growth_percent']) / 100.0
    if original_data['prop_tax_mode'].lower() == 'p':
        property_tax_percent = float(original_data['property_tax_percent']) / 100.0
        property_tax_amount = None
    else:
        property_tax_amount = float(original_data['property_tax_amount'])
        property_tax_percent = None
    if original_data['ins_mode'].lower() == 'p':
        home_insurance_percent = float(original_data['home_insurance_percent']) / 100.0
        home_insurance_amount = None
    else:
        home_insurance_amount = float(original_data['home_insurance_amount'])
        home_insurance_percent = None
    house_name = original_data['house_name']
    ownership_years = int(original_data['ownership_years'])
    sell_closing_cost_percent = float(original_data['sell_closing_cost_percent']) / 100.0

    # Recalculate initial values
    down_payment = home_cost * down_payment_percent
    initial_cash = down_payment + closing_cost
    loan_amount = home_cost - down_payment
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

    # Get refinance inputs
    refinance_type = form.get('refinance_type')  # "cashout" or "newrate"
    refinance_year = int(form.get('refinance_year'))
    refinance_cost = float(form.get('refinance_cost'))
    refinance_interest_rate = float(form.get('refinance_interest_rate')) / 100.0
    ref_loan_term_years = int(form.get('custom_ref_loan_term'))
    ref_loan_term_months = ref_loan_term_years * 12

    # Determine remaining balance at refinance (end of year prior)
    if refinance_year > 1:
        refinance_month = (refinance_year - 1) * 12
        remaining_balance = schedule_df.iloc[refinance_month - 1]["Balance"]
    else:
        remaining_balance = loan_amount

    refinance_home_value = home_cost * ((1 + annual_appreciation_percent) ** refinance_year)

    # For cash-out, new loan is based on 75% LTV; for new rate, new loan equals remaining balance.
    if refinance_type == "cashout":
        max_new_loan = refinance_home_value * 0.75
        if max_new_loan <= remaining_balance:
            refinance = False
        else:
            cash_out_amount = max_new_loan - remaining_balance
            net_cash_out = cash_out_amount - refinance_cost
            new_loan_amount = max_new_loan
            refinance_details = f"Cash-Out Refinance: Net cash-out available is ${net_cash_out:,.2f}."
    else:
        new_loan_amount = remaining_balance
        net_cash_out = 0.0
        refinance_details = "New Rate & Timeline Refinance: No cash-out; refinancing is based solely on the remaining balance."

    new_monthly_interest_rate = refinance_interest_rate / 12.0
    new_monthly_payment = new_loan_amount * (
                new_monthly_interest_rate * (1 + new_monthly_interest_rate) ** ref_loan_term_months) / \
                          ((1 + new_monthly_interest_rate) ** ref_loan_term_months - 1)
    new_schedule = []
    new_balance = new_loan_amount
    for m in range(1, ref_loan_term_months + 1):
        new_interest_payment = new_balance * new_monthly_interest_rate
        new_principal_payment = new_monthly_payment - new_interest_payment
        new_balance -= new_principal_payment
        if new_balance < 0:
            new_principal_payment += new_balance
            new_balance = 0
        new_schedule.append((m, new_monthly_payment, new_principal_payment, new_interest_payment, new_balance))
    new_schedule_df = pd.DataFrame(new_schedule, columns=["Month", "Payment", "Principal", "Interest", "Balance"])

    # Pre-refinance cash flow simulation (years before refinance_year)
    pre_data = []
    cumulative_cash_flow_pre = 0.0
    for year in range(1, refinance_year):
        start_month = (year - 1) * 12
        end_month = year * 12
        year_schedule = schedule_df.iloc[start_month:end_month]
        total_mortgage_payment = year_schedule["Payment"].sum()
        end_balance = year_schedule.iloc[-1]["Balance"]
        home_value = home_cost * ((1 + annual_appreciation_percent) ** year)
        equity = home_value - end_balance
        if property_tax_percent is not None:
            property_tax = property_tax_percent * home_value
        else:
            property_tax = property_tax_amount
        maintenance_cost = 0.01 * home_value
        if home_insurance_percent is not None:
            insurance_cost = home_insurance_percent * home_value
        else:
            insurance_cost = home_insurance_amount
        operating_expenses = property_tax + maintenance_cost + insurance_cost
        adjusted_monthly_rent = monthly_rent * ((1 + rental_income_growth_percent) ** (year - 1))
        annual_rent_income = adjusted_monthly_rent * 12
        annual_cash_flow = annual_rent_income - total_mortgage_payment - operating_expenses
        cumulative_cash_flow_pre += annual_cash_flow
        unrealized_wealth = equity - initial_cash
        total_wealth = cumulative_cash_flow_pre + unrealized_wealth
        pre_data.append({
            "Year": year,
            "Home Value": f"${home_value:,.2f}",
            "Mortgage Balance": f"${end_balance:,.2f}",
            "Equity": f"${equity:,.2f}",
            "Annual Rent Income": f"${annual_rent_income:,.2f}",
            "Operating Expenses": f"${operating_expenses:,.2f}",
            "Annual Cash Flow": f"${annual_cash_flow:,.2f}",
            "Cumulative Cash Flow": f"${cumulative_cash_flow_pre:,.2f}",
            "Unrealized Wealth": f"${unrealized_wealth:,.2f}",
            "Total Wealth": f"${total_wealth:,.2f}"
        })
    pre_df = pd.DataFrame(pre_data)
    pre_df_html = pre_df.to_html(index=False, classes='table table-striped')

    # At refinance, add net cash-out to cumulative cash flow
    cumulative_at_refinance = cumulative_cash_flow_pre + net_cash_out

    # Post-refinance simulation (years from refinance_year to ownership_years)
    post_data = []
    cumulative_cash_flow_post = cumulative_at_refinance
    post_years = ownership_years - refinance_year + 1
    for j in range(1, post_years + 1):
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
        equity_new = home_value - new_end_balance
        if property_tax_percent is not None:
            property_tax = property_tax_percent * home_value
        else:
            property_tax = property_tax_amount
        maintenance_cost = 0.01 * home_value
        if home_insurance_percent is not None:
            insurance_cost = home_insurance_percent * home_value
        else:
            insurance_cost = home_insurance_amount
        operating_expenses = property_tax + maintenance_cost + insurance_cost
        adjusted_monthly_rent = monthly_rent * ((1 + rental_income_growth_percent) ** (current_year - 1))
        annual_rent_income = adjusted_monthly_rent * 12
        annual_cash_flow_new = annual_rent_income - new_total_mortgage_payment - operating_expenses
        cumulative_cash_flow_post += annual_cash_flow_new
        unrealized_wealth_new = equity_new - initial_cash
        total_wealth_new = cumulative_cash_flow_post + unrealized_wealth_new
        post_data.append({
            "Year": current_year,
            "Home Value": f"${home_value:,.2f}",
            "Mortgage Balance": f"${new_end_balance:,.2f}",
            "Equity": f"${equity_new:,.2f}",
            "Annual Rent Income": f"${annual_rent_income:,.2f}",
            "Operating Expenses": f"${operating_expenses:,.2f}",
            "Annual Cash Flow": f"${annual_cash_flow_new:,.2f}",
            "Cumulative Cash Flow": f"${cumulative_cash_flow_post:,.2f}",
            "Unrealized Wealth": f"${unrealized_wealth_new:,.2f}",
            "Total Wealth": f"${total_wealth_new:,.2f}"
        })
    post_df = pd.DataFrame(post_data)
    post_df_html = post_df.to_html(index=False, classes='table table-striped')

    # Generate combined wealth accumulation plot from pre and post data.
    combined_plot_data = []
    for row in pre_data:
        value = float(row["Total Wealth"].replace("$", "").replace(",", ""))
        combined_plot_data.append((row["Year"], value))
    for row in post_data:
        value = float(row["Total Wealth"].replace("$", "").replace(",", ""))
        combined_plot_data.append((row["Year"], value))
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

    # Recalculate sale returns using cumulative_cash_flow_post
    sale_price = home_cost * ((1 + annual_appreciation_percent) ** ownership_years)
    sale_closing_cost = sale_price * sell_closing_cost_percent
    net_sale_price = sale_price - sale_closing_cost
    final_total_value = net_sale_price + cumulative_cash_flow_post
    annualized_return = (final_total_value / initial_cash) ** (1 / ownership_years) - 1
    cumulative_return = (final_total_value / initial_cash - 1) * 100

    # Update summary results
    results["loan_amount"] = f"${loan_amount:,.2f}"
    results["monthly_payment"] = f"${monthly_payment:,.2f}"
    results["initial_cash_outlay"] = f"${initial_cash:,.2f}"
    results["annualized_return"] = f"{annualized_return * 100:.2f}%"
    results["cumulative_return"] = f"{cumulative_return:.2f}%"
    results["refinance_details"] = refinance_details

    return results, annual_table, plot_url, refinance_details, pre_df_html, post_df_html


##########################################
# Routes
##########################################

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


if __name__ == '__main__':
    app.run(debug=True)
