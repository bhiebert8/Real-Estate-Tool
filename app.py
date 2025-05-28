from flask import Flask, render_template_string, request, send_file, url_for, session, redirect
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
import requests
import json

from HTML_TEMPLATES import *
from PDF_Report_Generator import generate_pdf_report

app = Flask(__name__)
app.secret_key = 'super_secret_secret_key_5397'  # Change this to a secure secret key

# Global variables
excel_data = None
last_results = None
last_annual_table = None

# Rentcast API configuration
RENTCAST_API_KEY = "546a30e163234403a83ca5d78f17bbec"  # Replace with your actual API key
RENTCAST_BASE_URL = "https://api.rentcast.io/v1"

# Define the question flow
QUESTION_STEPS = [
    {
        'id': 'property_search',
        'title': 'Property Search',
        'description': 'Find your property or enter address'
    },
    {
        'id': 'basic_info',
        'title': 'Basic Property Info',
        'description': 'Property cost and closing details'
    },
    {
        'id': 'financing',
        'title': 'Financing Details',
        'description': 'Loan terms and down payment'
    },
    {
        'id': 'rental_income',
        'title': 'Rental Income',
        'description': 'Monthly rent and income growth'
    },
    {
        'id': 'expenses',
        'title': 'Operating Expenses',
        'description': 'Property taxes, insurance, and fees'
    },
    {
        'id': 'investment_details',
        'title': 'Investment Parameters',
        'description': 'Ownership timeline and tax information'
    },
    {
        'id': 'remodeling',
        'title': 'Remodeling Plans',
        'description': 'Optional improvement projects'
    }
]


def get_progress_percentage(current_step):
    """Calculate progress percentage based on current step"""
    if current_step not in [s['id'] for s in QUESTION_STEPS]:
        return 0

    current_index = next(i for i, s in enumerate(QUESTION_STEPS) if s['id'] == current_step)
    return int((current_index / len(QUESTION_STEPS)) * 100)


def get_next_step(current_step):
    """Get the next step in the flow"""
    current_index = next(i for i, s in enumerate(QUESTION_STEPS) if s['id'] == current_step)
    if current_index < len(QUESTION_STEPS) - 1:
        return QUESTION_STEPS[current_index + 1]['id']
    return 'review'


def get_previous_step(current_step):
    """Get the previous step in the flow"""
    current_index = next(i for i, s in enumerate(QUESTION_STEPS) if s['id'] == current_step)
    if current_index > 0:
        return QUESTION_STEPS[current_index - 1]['id']
    return None


# Rentcast API Functions
def search_properties(address):
    """Search for properties using Rentcast API"""
    try:
        headers = {
            'X-Api-Key': RENTCAST_API_KEY,
            'Content-Type': 'application/json'
        }

        params = {
            'address': address,
            'limit': 5
        }

        response = requests.get(
            f"{RENTCAST_BASE_URL}/listings/rental/long-term",
            headers=headers,
            params=params,
            timeout=10
        )

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Rentcast API error: {response.status_code}")
            return None

    except Exception as e:
        print(f"Error calling Rentcast API: {e}")
        return None


def get_property_estimate(address):
    """Get property value and rent estimates from Rentcast"""
    global RENTCAST_API_KEY

    print(f"🔍 Starting property estimate for: '{address}'")
    print(f"🔍 API Key in get_property_estimate: '{RENTCAST_API_KEY}'")
    print(f"🔍 Checking if API key equals placeholder: {RENTCAST_API_KEY == 'YOUR_RENTCAST_API_KEY'}")
    print(f"🔍 API key is valid: {RENTCAST_API_KEY and RENTCAST_API_KEY != 'YOUR_RENTCAST_API_KEY'}")

    if not address:
        print("❌ No address provided")
        return None

    # Fix the API key check
    if not RENTCAST_API_KEY or RENTCAST_API_KEY == "YOUR_RENTCAST_API_KEY":
        print("❌ API key not configured")
        return None

    print("✅ API key is configured, proceeding with API calls...")

    try:
        headers = {
            'X-Api-Key': RENTCAST_API_KEY,
            'Content-Type': 'application/json'
        }
        print(f"🔍 Headers prepared: {headers}")

        result = {}

        # Get property value estimate
        value_url = f"{RENTCAST_BASE_URL}/avm/value"
        print(f"🔍 Attempting value API call to: {value_url}")
        print(f"🔍 With params: {{'address': '{address}'}}")

        try:
            value_response = requests.get(
                value_url,
                headers=headers,
                params={'address': address},
                timeout=10
            )

            print(f"🔍 Value API Status: {value_response.status_code}")
            print(f"🔍 Value API Headers: {dict(value_response.headers)}")

            if value_response.status_code == 200:
                try:
                    value_data = value_response.json()
                    print(f"🔍 Value API Response: {value_data}")

                    # Handle different response formats
                    if isinstance(value_data, dict):
                        if 'price' in value_data:
                            price_data = value_data['price']
                            if isinstance(price_data, dict):
                                result['property_value'] = price_data.get('value')
                                result['property_confidence'] = price_data.get('confidence', 'Unknown')
                            elif isinstance(price_data, (int, float)):
                                result['property_value'] = price_data
                                result['property_confidence'] = 'Unknown'
                        elif 'value' in value_data:
                            result['property_value'] = value_data['value']
                            result['property_confidence'] = value_data.get('confidence', 'Unknown')

                        print(f"🔍 Extracted property value: {result.get('property_value')}")

                except Exception as json_error:
                    print(f"❌ JSON parsing error for value API: {json_error}")
                    print(f"❌ Raw response: {value_response.text[:500]}")

            else:
                print(f"❌ Value API error - Status: {value_response.status_code}")
                print(f"❌ Response text: {value_response.text[:200]}")

        except requests.RequestException as req_error:
            print(f"❌ Value API request failed: {req_error}")
        except Exception as e:
            print(f"❌ Unexpected error in value API: {e}")

        # Get rent estimate
        rent_url = f"{RENTCAST_BASE_URL}/avm/rent/long-term"
        print(f"🔍 Attempting rent API call to: {rent_url}")

        try:
            rent_response = requests.get(
                rent_url,
                headers=headers,
                params={'address': address},
                timeout=10
            )

            print(f"🔍 Rent API Status: {rent_response.status_code}")

            if rent_response.status_code == 200:
                try:
                    rent_data = rent_response.json()
                    print(f"🔍 Rent API Response: {rent_data}")

                    if isinstance(rent_data, dict):
                        if 'rent' in rent_data:
                            rent_info = rent_data['rent']
                            if isinstance(rent_info, dict):
                                result['rent_estimate'] = rent_info.get('value')
                                result['rent_confidence'] = rent_info.get('confidence', 'Unknown')
                            elif isinstance(rent_info, (int, float)):
                                result['rent_estimate'] = rent_info
                                result['rent_confidence'] = 'Unknown'
                        elif 'value' in rent_data:
                            result['rent_estimate'] = rent_data['value']
                            result['rent_confidence'] = rent_data.get('confidence', 'Unknown')

                        print(f"🔍 Extracted rent estimate: {result.get('rent_estimate')}")

                except Exception as json_error:
                    print(f"❌ JSON parsing error for rent API: {json_error}")
                    print(f"❌ Raw response: {rent_response.text[:500]}")

            else:
                print(f"❌ Rent API error - Status: {rent_response.status_code}")
                print(f"❌ Response text: {rent_response.text[:200]}")

        except requests.RequestException as req_error:
            print(f"❌ Rent API request failed: {req_error}")
        except Exception as e:
            print(f"❌ Unexpected error in rent API: {e}")

        print(f"🔍 Final result: {result}")
        return result if result else None

    except Exception as e:
        print(f"❌ Overall Rentcast API error: {e}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        return None


def get_property_details(address):
    """Get detailed property information"""
    try:
        headers = {
            'X-Api-Key': RENTCAST_API_KEY,
            'Content-Type': 'application/json'
        }

        response = requests.get(
            f"{RENTCAST_BASE_URL}/properties",
            headers=headers,
            params={'address': address},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            return {
                'bedrooms': data.get('bedrooms'),
                'bathrooms': data.get('bathrooms'),
                'square_footage': data.get('squareFootage'),
                'property_type': data.get('propertyType'),
                'lot_size': data.get('lotSize'),
                'year_built': data.get('yearBuilt'),
                'tax_assessment': data.get('taxAssessment', {}).get('value'),
                'owner_name': data.get('owner', {}).get('name')
            }

        return None

    except Exception as e:
        print(f"Error getting property details: {e}")
        return None


def render_wizard_template(template_name, **kwargs):
    """Render a wizard template with step progress"""
    current_step = kwargs.get('current_step', 'property_search')

    # Calculate step status for progress indicator
    steps = []
    current_index = next((i for i, s in enumerate(QUESTION_STEPS) if s['id'] == current_step), 0)

    for i, step in enumerate(QUESTION_STEPS):
        if i < current_index:
            status = 'completed'
        elif i == current_index:
            status = 'current'
        else:
            status = 'pending'

        steps.append({
            'title': step['title'],
            'status': status
        })

    progress = get_progress_percentage(current_step)

    # Get the template content
    template_content = templates[template_name]

    # Remove current_step from kwargs to avoid conflict
    clean_kwargs = {k: v for k, v in kwargs.items() if k != 'current_step'}

    # Use Flask's render_template_string with all Flask functions available
    return render_template_string(
        template_content,
        steps=steps,
        progress=progress,
        current_step=current_step,
        **clean_kwargs
    )


# ROUTES

@app.route('/')
def index():
    """Initialize the wizard"""
    session.clear()  # Start fresh
    return redirect(url_for('wizard_step', step='property_search'))


@app.route('/wizard/<step>', methods=['GET', 'POST'])
def wizard_step(step):
    """Handle wizard steps"""
    if 'form_data' not in session:
        session['form_data'] = {}

    form_data = session['form_data']

    if request.method == 'POST':
        # Save form data
        for key, value in request.form.items():
            form_data[key] = value
        session['form_data'] = form_data

        # Handle special cases
        if step == 'property_search':
            # Get Rentcast data for the address
            address = request.form.get('property_address')
            print(f"🔍 Property search - Address: '{address}'")
            print(f"🔍 API Key configured: {RENTCAST_API_KEY != 'YOUR_RENTCAST_API_KEY'}")
            print(f"🔍 API Key length: {len(RENTCAST_API_KEY) if RENTCAST_API_KEY else 0}")

            if address and RENTCAST_API_KEY != "YOUR_RENTCAST_API_KEY":
                print(f"🔍 Looking up property data for: {address}")
                rentcast_data = get_property_estimate(address)
                if rentcast_data:
                    print(
                        f"✅ Found data: Value=${rentcast_data.get('property_value')}, Rent=${rentcast_data.get('rent_estimate')}")
                    session['rentcast_data'] = rentcast_data
                    # Store suggested values in form_data for later steps
                    if rentcast_data.get('property_value'):
                        form_data['suggested_home_cost'] = str(int(rentcast_data['property_value']))
                    if rentcast_data.get('rent_estimate'):
                        form_data['suggested_monthly_rent'] = str(int(rentcast_data['rent_estimate']))
                    session['form_data'] = form_data
                else:
                    print("❌ No property data found")
                    session['rentcast_data'] = {}
            else:
                if not address:
                    print("⚠️ No address provided")
                elif RENTCAST_API_KEY == "YOUR_RENTCAST_API_KEY":
                    print("⚠️ Rentcast API key not configured")
                else:
                    print("⚠️ Unknown issue with Rentcast setup")
                session['rentcast_data'] = {}

        # Determine next step
        if step == 'remodeling':
            # Last step - generate analysis
            return redirect(url_for('generate_analysis'))
        else:
            next_step = get_next_step(step)
            return redirect(url_for('wizard_step', step=next_step))

    # GET request - show the form
    rentcast_data = session.get('rentcast_data', {})

    # Create suggested values for form pre-population
    suggested_values = {}
    if rentcast_data:
        if rentcast_data.get('property_value'):
            suggested_values['property_value'] = rentcast_data['property_value']
        if rentcast_data.get('rent_estimate'):
            suggested_values['rent_estimate'] = rentcast_data['rent_estimate']

    # Also use stored suggested values from previous API calls
    if form_data.get('suggested_home_cost'):
        suggested_values['property_value'] = float(form_data['suggested_home_cost'])
    if form_data.get('suggested_monthly_rent'):
        suggested_values['rent_estimate'] = float(form_data['suggested_monthly_rent'])

    template_map = {
        'property_search': 'property_search.html',
        'basic_info': 'basic_info.html',
        'financing': 'financing.html',
        'rental_income': 'rental_income.html',
        'expenses': 'expenses.html',
        'investment_details': 'investment_details.html',
        'remodeling': 'remodeling.html'
    }

    template_name = template_map.get(step, 'property_search.html')

    return render_wizard_template(
        template_name,
        current_step=step,
        form_data=form_data,
        rentcast_data=rentcast_data,
        suggested_values=suggested_values
    )


@app.route('/analysis')
def generate_analysis():
    """Generate the final analysis"""
    if 'form_data' not in session:
        return redirect(url_for('index'))

    form_data = session['form_data']

    # Use your existing analysis function
    try:
        results, annual_table, plot_url, original_data = run_initial_analysis(form_data)

        # Store results for downloads
        global last_results, last_annual_table
        last_results = results
        last_annual_table = annual_table

        return render_template_string(results_html,
                                      results=results,
                                      annual_table=annual_table,
                                      plot_url=plot_url,
                                      original_data=original_data)
    except Exception as e:
        return f"Error generating analysis: {str(e)}"


# ========== Analysis Functions (from your original code) ==========

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
    global excel_data, last_results, last_annual_table

    # Helper function for safe float conversion
    def safe_float(value, default=0.0):
        """Convert value to float, return default if None or empty"""
        if value is None or value == '' or value == 'None':
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    # Parse all inputs with safe conversion
    home_cost = safe_float(form.get('home_cost'))
    closing_cost = safe_float(form.get('closing_cost'))

    loan_type_choice = form.get('loan_type_choice')
    if loan_type_choice == "1":
        loan_term_years = 30
    elif loan_type_choice == "2":
        loan_term_years = 15
    elif loan_type_choice == "3":
        loan_term_years = int(safe_float(form.get('custom_loan_term'), 30))
    else:
        loan_term_years = 30

    down_payment_percent = safe_float(form.get('down_payment_percent')) / 100.0
    annual_appreciation_percent = safe_float(form.get('annual_appreciation_percent')) / 100.0
    mortgage_interest_rate = safe_float(form.get('mortgage_interest_rate')) / 100.0
    monthly_rent = safe_float(form.get('monthly_rent'))
    rental_income_growth_percent = safe_float(form.get('rental_income_growth_percent')) / 100.0
    vacancy_rate = safe_float(form.get('vacancy_rate')) / 100.0
    management_fee_percent = safe_float(form.get('management_fee_percent')) / 100.0  # This was likely None
    hoa_fee = safe_float(form.get('hoa_fee'))

    prop_tax_mode = form.get('prop_tax_mode')
    property_tax_percent = safe_float(form.get('property_tax_percent')) / 100.0 if form.get(
        'property_tax_percent') else 0
    property_tax_amount = safe_float(form.get('property_tax_amount'))
    tax_appraisal_growth = safe_float(form.get('tax_appraisal_growth')) / 100.0

    ins_mode = form.get('ins_mode')
    home_insurance_percent = safe_float(form.get('home_insurance_percent')) / 100.0 if form.get(
        'home_insurance_percent') else 0
    home_insurance_amount = safe_float(form.get('home_insurance_amount'))

    house_name = form.get('house_name', 'My Property')
    ownership_years = int(safe_float(form.get('ownership_years'), 10))
    sell_closing_cost_percent = safe_float(form.get('sell_closing_cost_percent')) / 100.0
    is_rental = form.get('is_rental') == "yes"
    structure_percent = safe_float(form.get('structure_percent'), 80) / 100.0
    tax_rate = safe_float(form.get('tax_rate'), 25) / 100.0
    cap_gains_rate = safe_float(form.get('cap_gains_rate'), 20) / 100.0

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

    original_data = dict(form)
    return results, annual_table, plot_url, original_data


# ========== REPLACE WITH YOUR ORIGINAL RESULTS TEMPLATES ==========
# ADD YOUR ORIGINAL results_html HERE (with refinance form)
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
                <input type="number" class="form-control" name="refinance_interest_rate" step="0.01" min="0" max="20" required>
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

# ADD YOUR ORIGINAL refinance_results_html HERE
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


# ========== ADD YOUR ORIGINAL run_refinance_simulation FUNCTION HERE ==========
def run_refinance_simulation(form):
    # Helper function for safe float conversion
    def safe_float(value, default=0.0):
        """Convert value to float, return default if None or empty"""
        if value is None or value == '' or value == 'None':
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    # Unpack original data with safe conversion
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

    ownership_years = int(safe_float(orig.get('ownership_years'), 10))
    refinance_type = form.get('refinance_type')
    refinance_year = int(safe_float(form.get('refinance_year'), 1))
    refinance_cost = safe_float(form.get('refinance_cost'))
    refinance_interest_rate = safe_float(form.get('refinance_interest_rate')) / 100.0
    ref_loan_term_years = int(safe_float(form.get('custom_ref_loan_term'), 30))
    ref_loan_term_months = ref_loan_term_years * 12

    # Parse remodeling data
    remodeling_data = parse_remodeling_data(orig)

    # Run the initial analysis to get full data
    res, annual_table, plot_url, _ = run_initial_analysis(orig)

    # Extract key values with safe conversion
    home_cost = safe_float(orig.get('home_cost'))
    down_payment_percent = safe_float(orig.get('down_payment_percent')) / 100.0
    closing_cost = safe_float(orig.get('closing_cost'))  # This was the failing line
    loan_type_choice = orig.get('loan_type_choice')

    if loan_type_choice == "1":
        loan_term_years = 30
    elif loan_type_choice == "2":
        loan_term_years = 15
    elif loan_type_choice == "3":
        loan_term_years = int(safe_float(orig.get('custom_loan_term'), 30))
    else:
        loan_term_years = 30

    mortgage_interest_rate = safe_float(orig.get('mortgage_interest_rate')) / 100.0
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

    # Get other parameters with safe conversion
    annual_appreciation_percent = safe_float(orig.get('annual_appreciation_percent')) / 100.0
    monthly_rent = safe_float(orig.get('monthly_rent'))
    rental_income_growth_percent = safe_float(orig.get('rental_income_growth_percent')) / 100.0
    vacancy_rate = safe_float(orig.get('vacancy_rate')) / 100.0
    management_fee_percent = safe_float(orig.get('management_fee_percent')) / 100.0
    hoa_fee = safe_float(orig.get('hoa_fee'))
    prop_tax_mode = orig.get('prop_tax_mode')
    property_tax_percent = safe_float(orig.get('property_tax_percent')) / 100.0 if orig.get(
        'property_tax_percent') else 0
    property_tax_amount = safe_float(orig.get('property_tax_amount'))
    tax_appraisal_growth = safe_float(orig.get('tax_appraisal_growth')) / 100.0
    ins_mode = orig.get('ins_mode')
    home_insurance_percent = safe_float(orig.get('home_insurance_percent')) / 100.0 if orig.get(
        'home_insurance_percent') else 0
    home_insurance_amount = safe_float(orig.get('home_insurance_amount'))
    house_name = orig.get('house_name', 'My Property')
    sell_closing_cost_percent = safe_float(orig.get('sell_closing_cost_percent')) / 100.0
    is_rental = orig.get('is_rental') == "yes"
    structure_percent = safe_float(orig.get('structure_percent'), 80) / 100.0
    tax_rate = safe_float(orig.get('tax_rate'), 25) / 100.0
    cap_gains_rate = safe_float(orig.get('cap_gains_rate'), 20) / 100.0

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



from flask import Flask, render_template_string, request, send_file, url_for, session, redirect
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
import requests
import json

app = Flask(__name__)
app.secret_key = 'super_secret_secret_key_5397'  # Change this to a secure secret key

# Global variables
excel_data = None
last_results = None
last_annual_table = None

# Rentcast API configuration
RENTCAST_API_KEY = "546a30e163234403a83ca5d78f17bbec"  # Replace with your actual API key
RENTCAST_BASE_URL = "https://api.rentcast.io/v1"

# Define the question flow
QUESTION_STEPS = [
    {
        'id': 'property_search',
        'title': 'Property Search',
        'description': 'Find your property or enter address'
    },
    {
        'id': 'basic_info',
        'title': 'Basic Property Info',
        'description': 'Property cost and closing details'
    },
    {
        'id': 'financing',
        'title': 'Financing Details',
        'description': 'Loan terms and down payment'
    },
    {
        'id': 'rental_income',
        'title': 'Rental Income',
        'description': 'Monthly rent and income growth'
    },
    {
        'id': 'expenses',
        'title': 'Operating Expenses',
        'description': 'Property taxes, insurance, and fees'
    },
    {
        'id': 'investment_details',
        'title': 'Investment Parameters',
        'description': 'Ownership timeline and tax information'
    },
    {
        'id': 'remodeling',
        'title': 'Remodeling Plans',
        'description': 'Optional improvement projects'
    }
]


def get_progress_percentage(current_step):
    """Calculate progress percentage based on current step"""
    if current_step not in [s['id'] for s in QUESTION_STEPS]:
        return 0

    current_index = next(i for i, s in enumerate(QUESTION_STEPS) if s['id'] == current_step)
    return int((current_index / len(QUESTION_STEPS)) * 100)


def get_next_step(current_step):
    """Get the next step in the flow"""
    current_index = next(i for i, s in enumerate(QUESTION_STEPS) if s['id'] == current_step)
    if current_index < len(QUESTION_STEPS) - 1:
        return QUESTION_STEPS[current_index + 1]['id']
    return 'review'


def get_previous_step(current_step):
    """Get the previous step in the flow"""
    current_index = next(i for i, s in enumerate(QUESTION_STEPS) if s['id'] == current_step)
    if current_index > 0:
        return QUESTION_STEPS[current_index - 1]['id']
    return None


# Rentcast API Functions
def search_properties(address):
    """Search for properties using Rentcast API"""
    try:
        headers = {
            'X-Api-Key': RENTCAST_API_KEY,
            'Content-Type': 'application/json'
        }

        params = {
            'address': address,
            'limit': 5
        }

        response = requests.get(
            f"{RENTCAST_BASE_URL}/listings/rental/long-term",
            headers=headers,
            params=params,
            timeout=10
        )

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Rentcast API error: {response.status_code}")
            return None

    except Exception as e:
        print(f"Error calling Rentcast API: {e}")
        return None


def get_property_estimate(address):
    """Get property value and rent estimates from Rentcast"""
    global RENTCAST_API_KEY

    print(f"🔍 Starting property estimate for: '{address}'")
    print(f"🔍 API Key in get_property_estimate: '{RENTCAST_API_KEY}'")
    print(f"🔍 Checking if API key equals placeholder: {RENTCAST_API_KEY == 'YOUR_RENTCAST_API_KEY'}")
    print(f"🔍 API key is valid: {RENTCAST_API_KEY and RENTCAST_API_KEY != 'YOUR_RENTCAST_API_KEY'}")

    if not address:
        print("❌ No address provided")
        return None

    # Fix the API key check
    if not RENTCAST_API_KEY or RENTCAST_API_KEY == "YOUR_RENTCAST_API_KEY":
        print("❌ API key not configured")
        return None

    print("✅ API key is configured, proceeding with API calls...")

    try:
        headers = {
            'X-Api-Key': RENTCAST_API_KEY,
            'Content-Type': 'application/json'
        }
        print(f"🔍 Headers prepared: {headers}")

        result = {}

        # Get property value estimate
        value_url = f"{RENTCAST_BASE_URL}/avm/value"
        print(f"🔍 Attempting value API call to: {value_url}")
        print(f"🔍 With params: {{'address': '{address}'}}")

        try:
            value_response = requests.get(
                value_url,
                headers=headers,
                params={'address': address},
                timeout=10
            )

            print(f"🔍 Value API Status: {value_response.status_code}")
            print(f"🔍 Value API Headers: {dict(value_response.headers)}")

            if value_response.status_code == 200:
                try:
                    value_data = value_response.json()
                    print(f"🔍 Value API Response: {value_data}")

                    # Handle different response formats
                    if isinstance(value_data, dict):
                        if 'price' in value_data:
                            price_data = value_data['price']
                            if isinstance(price_data, dict):
                                result['property_value'] = price_data.get('value')
                                result['property_confidence'] = price_data.get('confidence', 'Unknown')
                            elif isinstance(price_data, (int, float)):
                                result['property_value'] = price_data
                                result['property_confidence'] = 'Unknown'
                        elif 'value' in value_data:
                            result['property_value'] = value_data['value']
                            result['property_confidence'] = value_data.get('confidence', 'Unknown')

                        print(f"🔍 Extracted property value: {result.get('property_value')}")

                except Exception as json_error:
                    print(f"❌ JSON parsing error for value API: {json_error}")
                    print(f"❌ Raw response: {value_response.text[:500]}")

            else:
                print(f"❌ Value API error - Status: {value_response.status_code}")
                print(f"❌ Response text: {value_response.text[:200]}")

        except requests.RequestException as req_error:
            print(f"❌ Value API request failed: {req_error}")
        except Exception as e:
            print(f"❌ Unexpected error in value API: {e}")

        # Get rent estimate
        rent_url = f"{RENTCAST_BASE_URL}/avm/rent/long-term"
        print(f"🔍 Attempting rent API call to: {rent_url}")

        try:
            rent_response = requests.get(
                rent_url,
                headers=headers,
                params={'address': address},
                timeout=10
            )

            print(f"🔍 Rent API Status: {rent_response.status_code}")

            if rent_response.status_code == 200:
                try:
                    rent_data = rent_response.json()
                    print(f"🔍 Rent API Response: {rent_data}")

                    if isinstance(rent_data, dict):
                        if 'rent' in rent_data:
                            rent_info = rent_data['rent']
                            if isinstance(rent_info, dict):
                                result['rent_estimate'] = rent_info.get('value')
                                result['rent_confidence'] = rent_info.get('confidence', 'Unknown')
                            elif isinstance(rent_info, (int, float)):
                                result['rent_estimate'] = rent_info
                                result['rent_confidence'] = 'Unknown'
                        elif 'value' in rent_data:
                            result['rent_estimate'] = rent_data['value']
                            result['rent_confidence'] = rent_data.get('confidence', 'Unknown')

                        print(f"🔍 Extracted rent estimate: {result.get('rent_estimate')}")

                except Exception as json_error:
                    print(f"❌ JSON parsing error for rent API: {json_error}")
                    print(f"❌ Raw response: {rent_response.text[:500]}")

            else:
                print(f"❌ Rent API error - Status: {rent_response.status_code}")
                print(f"❌ Response text: {rent_response.text[:200]}")

        except requests.RequestException as req_error:
            print(f"❌ Rent API request failed: {req_error}")
        except Exception as e:
            print(f"❌ Unexpected error in rent API: {e}")

        print(f"🔍 Final result: {result}")
        return result if result else None

    except Exception as e:
        print(f"❌ Overall Rentcast API error: {e}")
        import traceback
        print(f"❌ Full traceback: {traceback.format_exc()}")
        return None


def get_property_details(address):
    """Get detailed property information"""
    try:
        headers = {
            'X-Api-Key': RENTCAST_API_KEY,
            'Content-Type': 'application/json'
        }

        response = requests.get(
            f"{RENTCAST_BASE_URL}/properties",
            headers=headers,
            params={'address': address},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            return {
                'bedrooms': data.get('bedrooms'),
                'bathrooms': data.get('bathrooms'),
                'square_footage': data.get('squareFootage'),
                'property_type': data.get('propertyType'),
                'lot_size': data.get('lotSize'),
                'year_built': data.get('yearBuilt'),
                'tax_assessment': data.get('taxAssessment', {}).get('value'),
                'owner_name': data.get('owner', {}).get('name')
            }

        return None

    except Exception as e:
        print(f"Error getting property details: {e}")
        return None



def render_wizard_template(template_name, **kwargs):
    """Render a wizard template with step progress"""
    current_step = kwargs.get('current_step', 'property_search')

    # Calculate step status for progress indicator
    steps = []
    current_index = next((i for i, s in enumerate(QUESTION_STEPS) if s['id'] == current_step), 0)

    for i, step in enumerate(QUESTION_STEPS):
        if i < current_index:
            status = 'completed'
        elif i == current_index:
            status = 'current'
        else:
            status = 'pending'

        steps.append({
            'title': step['title'],
            'status': status
        })

    progress = get_progress_percentage(current_step)

    # Get the template content
    template_content = templates[template_name]

    # Remove current_step from kwargs to avoid conflict
    clean_kwargs = {k: v for k, v in kwargs.items() if k != 'current_step'}

    # Use Flask's render_template_string with all Flask functions available
    return render_template_string(
        template_content,
        steps=steps,
        progress=progress,
        current_step=current_step,
        **clean_kwargs
    )


# ROUTES

@app.route('/')
def index():
    """Initialize the wizard"""
    session.clear()  # Start fresh
    return redirect(url_for('wizard_step', step='property_search'))


@app.route('/wizard/<step>', methods=['GET', 'POST'])
def wizard_step(step):
    """Handle wizard steps"""
    if 'form_data' not in session:
        session['form_data'] = {}

    form_data = session['form_data']

    if request.method == 'POST':
        # Save form data
        for key, value in request.form.items():
            form_data[key] = value
        session['form_data'] = form_data

        # Handle special cases
        if step == 'property_search':
            # Get Rentcast data for the address
            address = request.form.get('property_address')
            print(f"🔍 Property search - Address: '{address}'")
            print(f"🔍 API Key configured: {RENTCAST_API_KEY != 'YOUR_RENTCAST_API_KEY'}")
            print(f"🔍 API Key length: {len(RENTCAST_API_KEY) if RENTCAST_API_KEY else 0}")

            if address and RENTCAST_API_KEY != "YOUR_RENTCAST_API_KEY":
                print(f"🔍 Looking up property data for: {address}")
                rentcast_data = get_property_estimate(address)
                if rentcast_data:
                    print(
                        f"✅ Found data: Value=${rentcast_data.get('property_value')}, Rent=${rentcast_data.get('rent_estimate')}")
                    session['rentcast_data'] = rentcast_data
                    # Store suggested values in form_data for later steps
                    if rentcast_data.get('property_value'):
                        form_data['suggested_home_cost'] = str(int(rentcast_data['property_value']))
                    if rentcast_data.get('rent_estimate'):
                        form_data['suggested_monthly_rent'] = str(int(rentcast_data['rent_estimate']))
                    session['form_data'] = form_data
                else:
                    print("❌ No property data found")
                    session['rentcast_data'] = {}
            else:
                if not address:
                    print("⚠️ No address provided")
                elif RENTCAST_API_KEY == "YOUR_RENTCAST_API_KEY":
                    print("⚠️ Rentcast API key not configured")
                else:
                    print("⚠️ Unknown issue with Rentcast setup")
                session['rentcast_data'] = {}

        # Determine next step
        if step == 'remodeling':
            # Last step - generate analysis
            return redirect(url_for('generate_analysis'))
        else:
            next_step = get_next_step(step)
            return redirect(url_for('wizard_step', step=next_step))

    # GET request - show the form
    rentcast_data = session.get('rentcast_data', {})

    # Create suggested values for form pre-population
    suggested_values = {}
    if rentcast_data:
        if rentcast_data.get('property_value'):
            suggested_values['property_value'] = rentcast_data['property_value']
        if rentcast_data.get('rent_estimate'):
            suggested_values['rent_estimate'] = rentcast_data['rent_estimate']

    # Also use stored suggested values from previous API calls
    if form_data.get('suggested_home_cost'):
        suggested_values['property_value'] = float(form_data['suggested_home_cost'])
    if form_data.get('suggested_monthly_rent'):
        suggested_values['rent_estimate'] = float(form_data['suggested_monthly_rent'])

    template_map = {
        'property_search': 'property_search.html',
        'basic_info': 'basic_info.html',
        'financing': 'financing.html',
        'rental_income': 'rental_income.html',
        'expenses': 'expenses.html',
        'investment_details': 'investment_details.html',
        'remodeling': 'remodeling.html'
    }

    template_name = template_map.get(step, 'property_search.html')

    return render_wizard_template(
        template_name,
        current_step=step,
        form_data=form_data,
        rentcast_data=rentcast_data,
        suggested_values=suggested_values
    )


@app.route('/analysis')
def generate_analysis():
    """Generate the final analysis"""
    if 'form_data' not in session:
        return redirect(url_for('index'))

    form_data = session['form_data']

    # Use your existing analysis function
    try:
        results, annual_table, plot_url, original_data = run_initial_analysis(form_data)

        # Store results for downloads
        global last_results, last_annual_table
        last_results = results
        last_annual_table = annual_table

        return render_template_string(results_html,
                                      results=results,
                                      annual_table=annual_table,
                                      plot_url=plot_url,
                                      original_data=original_data)
    except Exception as e:
        return f"Error generating analysis: {str(e)}"


# ========== Analysis Functions (from your original code) ==========

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
    global excel_data, last_results, last_annual_table

    # Helper function for safe float conversion
    def safe_float(value, default=0.0):
        """Convert value to float, return default if None or empty"""
        if value is None or value == '' or value == 'None':
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    # Parse all inputs with safe conversion
    home_cost = safe_float(form.get('home_cost'))
    closing_cost = safe_float(form.get('closing_cost'))

    loan_type_choice = form.get('loan_type_choice')
    if loan_type_choice == "1":
        loan_term_years = 30
    elif loan_type_choice == "2":
        loan_term_years = 15
    elif loan_type_choice == "3":
        loan_term_years = int(safe_float(form.get('custom_loan_term'), 30))
    else:
        loan_term_years = 30

    down_payment_percent = safe_float(form.get('down_payment_percent')) / 100.0
    annual_appreciation_percent = safe_float(form.get('annual_appreciation_percent')) / 100.0
    mortgage_interest_rate = safe_float(form.get('mortgage_interest_rate')) / 100.0
    monthly_rent = safe_float(form.get('monthly_rent'))
    rental_income_growth_percent = safe_float(form.get('rental_income_growth_percent')) / 100.0
    vacancy_rate = safe_float(form.get('vacancy_rate')) / 100.0
    management_fee_percent = safe_float(form.get('management_fee_percent')) / 100.0  # This was likely None
    hoa_fee = safe_float(form.get('hoa_fee'))

    prop_tax_mode = form.get('prop_tax_mode')
    property_tax_percent = safe_float(form.get('property_tax_percent')) / 100.0 if form.get(
        'property_tax_percent') else 0
    property_tax_amount = safe_float(form.get('property_tax_amount'))
    tax_appraisal_growth = safe_float(form.get('tax_appraisal_growth')) / 100.0

    ins_mode = form.get('ins_mode')
    home_insurance_percent = safe_float(form.get('home_insurance_percent')) / 100.0 if form.get(
        'home_insurance_percent') else 0
    home_insurance_amount = safe_float(form.get('home_insurance_amount'))

    house_name = form.get('house_name', 'My Property')
    ownership_years = int(safe_float(form.get('ownership_years'), 10))
    sell_closing_cost_percent = safe_float(form.get('sell_closing_cost_percent')) / 100.0
    is_rental = form.get('is_rental') == "yes"
    structure_percent = safe_float(form.get('structure_percent'), 80) / 100.0
    tax_rate = safe_float(form.get('tax_rate'), 25) / 100.0
    cap_gains_rate = safe_float(form.get('cap_gains_rate'), 20) / 100.0

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

    original_data = dict(form)
    return results, annual_table, plot_url, original_data


# ========== ADD YOUR ORIGINAL run_refinance_simulation FUNCTION HERE ==========
def run_refinance_simulation(form):
    # Helper function for safe float conversion
    def safe_float(value, default=0.0):
        """Convert value to float, return default if None or empty"""
        if value is None or value == '' or value == 'None':
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    # Unpack original data with safe conversion
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

    ownership_years = int(safe_float(orig.get('ownership_years'), 10))
    refinance_type = form.get('refinance_type')
    refinance_year = int(safe_float(form.get('refinance_year'), 1))
    refinance_cost = safe_float(form.get('refinance_cost'))
    refinance_interest_rate = safe_float(form.get('refinance_interest_rate')) / 100.0
    ref_loan_term_years = int(safe_float(form.get('custom_ref_loan_term'), 30))
    ref_loan_term_months = ref_loan_term_years * 12

    # Parse remodeling data
    remodeling_data = parse_remodeling_data(orig)

    # Run the initial analysis to get full data
    res, annual_table, plot_url, _ = run_initial_analysis(orig)

    # Extract key values with safe conversion
    home_cost = safe_float(orig.get('home_cost'))
    down_payment_percent = safe_float(orig.get('down_payment_percent')) / 100.0
    closing_cost = safe_float(orig.get('closing_cost'))  # This was the failing line
    loan_type_choice = orig.get('loan_type_choice')

    if loan_type_choice == "1":
        loan_term_years = 30
    elif loan_type_choice == "2":
        loan_term_years = 15
    elif loan_type_choice == "3":
        loan_term_years = int(safe_float(orig.get('custom_loan_term'), 30))
    else:
        loan_term_years = 30

    mortgage_interest_rate = safe_float(orig.get('mortgage_interest_rate')) / 100.0
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

    # Get other parameters with safe conversion
    annual_appreciation_percent = safe_float(orig.get('annual_appreciation_percent')) / 100.0
    monthly_rent = safe_float(orig.get('monthly_rent'))
    rental_income_growth_percent = safe_float(orig.get('rental_income_growth_percent')) / 100.0
    vacancy_rate = safe_float(orig.get('vacancy_rate')) / 100.0
    management_fee_percent = safe_float(orig.get('management_fee_percent')) / 100.0
    hoa_fee = safe_float(orig.get('hoa_fee'))
    prop_tax_mode = orig.get('prop_tax_mode')
    property_tax_percent = safe_float(orig.get('property_tax_percent')) / 100.0 if orig.get(
        'property_tax_percent') else 0
    property_tax_amount = safe_float(orig.get('property_tax_amount'))
    tax_appraisal_growth = safe_float(orig.get('tax_appraisal_growth')) / 100.0
    ins_mode = orig.get('ins_mode')
    home_insurance_percent = safe_float(orig.get('home_insurance_percent')) / 100.0 if orig.get(
        'home_insurance_percent') else 0
    home_insurance_amount = safe_float(orig.get('home_insurance_amount'))
    house_name = orig.get('house_name', 'My Property')
    sell_closing_cost_percent = safe_float(orig.get('sell_closing_cost_percent')) / 100.0
    is_rental = orig.get('is_rental') == "yes"
    structure_percent = safe_float(orig.get('structure_percent'), 80) / 100.0
    tax_rate = safe_float(orig.get('tax_rate'), 25) / 100.0
    cap_gains_rate = safe_float(orig.get('cap_gains_rate'), 20) / 100.0

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


# ========== MISSING ROUTES - ADD THESE ==========

@app.route('/simulate_refinance', methods=['POST'])
def simulate_refinance():
    """Refinance simulation route"""
    results, annual_table, plot_url, refinance_details, pre_table, post_table = run_refinance_simulation(
        request.form.to_dict())
    return render_template_string(refinance_results_html,
                                  results=results,
                                  annual_table=annual_table,
                                  plot_url=plot_url,
                                  refinance_details=refinance_details,
                                  pre_table=pre_table,
                                  post_table=post_table)


@app.route('/download/pdf')
def download_pdf():
    """PDF download route"""
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


@app.route('/download')  # Keep this route for backward compatibility
@app.route('/download/excel')  # Add this new route for clarity
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
    print("🏠 Real Estate Investment Wizard Starting...")
    print("📊 Features: Step-by-step analysis + Rentcast API integration")

    # Check Rentcast API configuration
    if RENTCAST_API_KEY == "YOUR_RENTCAST_API_KEY":
        print("⚠️  WARNING: Rentcast API key not configured!")
        print("   To enable market data integration:")
        print("   1. Sign up at https://www.rentcast.io/api")
        print("   2. Get your API key")
        print("   3. Replace 'YOUR_RENTCAST_API_KEY' with your actual key")
        print("   4. App will work fine without it, just no auto-suggestions")
    else:
        print("✅ Rentcast API key configured - market data enabled!")

    app.run(debug=True, port=5002)
