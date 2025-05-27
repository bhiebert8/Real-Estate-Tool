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


# Base template with progress bar
base_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Real Estate Investment Analysis</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            min-height: 100vh;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .wizard-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .progress-container {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .question-card {
            background: white;
            border-radius: 15px;
            padding: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .progress-bar {
            height: 12px;
            border-radius: 6px;
            background: linear-gradient(90deg, #667eea, #764ba2);
        }
        .step-indicator {
            display: flex;
            justify-content: space-between;
            margin-top: 15px;
        }
        .step-dot {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 12px;
        }
        .step-dot.completed {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
        .step-dot.current {
            background: #ffc107;
            color: #333;
        }
        .step-dot.pending {
            background: #e9ecef;
            color: #6c757d;
        }
        .question-title {
            color: #333;
            font-weight: 700;
            margin-bottom: 10px;
        }
        .question-subtitle {
            color: #666;
            margin-bottom: 30px;
        }
        .form-control, .form-select {
            border-radius: 10px;
            border: 2px solid #e9ecef;
            padding: 12px 15px;
        }
        .form-control:focus, .form-select:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
        }
        .btn-wizard {
            background: linear-gradient(135deg, #667eea, #764ba2);
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            font-weight: 600;
            color: white;
        }
        .btn-wizard:hover {
            background: linear-gradient(135deg, #5a6fd8, #6a4190);
            color: white;
        }
        .btn-secondary-wizard {
            background: #6c757d;
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            font-weight: 600;
            color: white;
        }
        .rentcast-suggestion {
            background: #e3f2fd;
            border: 1px solid #2196f3;
            border-radius: 10px;
            padding: 15px;
            margin: 15px 0;
        }
        .confidence-badge {
            font-size: 0.8em;
            padding: 4px 8px;
            border-radius: 12px;
        }
        .confidence-high { background: #d4edda; color: #155724; }
        .confidence-medium { background: #fff3cd; color: #856404; }
        .confidence-low { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="wizard-container">
        <div class="progress-container">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5 class="mb-0">Real Estate Investment Analysis</h5>
                <span class="badge bg-primary">{{ progress }}% Complete</span>
            </div>
            <div class="progress mb-3">
                <div class="progress-bar" style="width: {{ progress }}%"></div>
            </div>
            <div class="step-indicator">
                {% for step in steps %}
                <div class="step-dot {{ step.status }}" title="{{ step.title }}">
                    {{ loop.index }}
                </div>
                {% endfor %}
            </div>
        </div>

        <div class="question-card">
            {% block content %}{% endblock %}
        </div>
    </div>
</body>
</html>
'''

# Step 1: Property Search
property_search_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Real Estate Investment Analysis</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            min-height: 100vh;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .wizard-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .progress-container {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .question-card {
            background: white;
            border-radius: 15px;
            padding: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .progress-bar {
            height: 12px;
            border-radius: 6px;
            background: linear-gradient(90deg, #667eea, #764ba2);
        }
        .step-indicator {
            display: flex;
            justify-content: space-between;
            margin-top: 15px;
        }
        .step-dot {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 12px;
        }
        .step-dot.completed {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
        .step-dot.current {
            background: #ffc107;
            color: #333;
        }
        .step-dot.pending {
            background: #e9ecef;
            color: #6c757d;
        }
        .question-title {
            color: #333;
            font-weight: 700;
            margin-bottom: 10px;
        }
        .question-subtitle {
            color: #666;
            margin-bottom: 30px;
        }
        .form-control, .form-select {
            border-radius: 10px;
            border: 2px solid #e9ecef;
            padding: 12px 15px;
        }
        .form-control:focus, .form-select:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
        }
        .btn-wizard {
            background: linear-gradient(135deg, #667eea, #764ba2);
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            font-weight: 600;
            color: white;
        }
        .btn-wizard:hover {
            background: linear-gradient(135deg, #5a6fd8, #6a4190);
            color: white;
        }
        .btn-secondary-wizard {
            background: #6c757d;
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            font-weight: 600;
            color: white;
        }
        .rentcast-suggestion {
            background: #e3f2fd;
            border: 1px solid #2196f3;
            border-radius: 10px;
            padding: 15px;
            margin: 15px 0;
        }
        .confidence-badge {
            font-size: 0.8em;
            padding: 4px 8px;
            border-radius: 12px;
        }
        .confidence-high { background: #d4edda; color: #155724; }
        .confidence-medium { background: #fff3cd; color: #856404; }
        .confidence-low { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="wizard-container">
        <div class="progress-container">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5 class="mb-0">Real Estate Investment Analysis</h5>
                <span class="badge bg-primary">{{ progress }}% Complete</span>
            </div>
            <div class="progress mb-3">
                <div class="progress-bar" style="width: {{ progress }}%"></div>
            </div>
            <div class="step-indicator">
                {% for step in steps %}
                <div class="step-dot {{ step.status }}" title="{{ step.title }}">
                    {{ loop.index }}
                </div>
                {% endfor %}
            </div>
        </div>

        <div class="question-card">
            <h2 class="question-title">Find Your Investment Property</h2>
            <p class="question-subtitle">Enter the property address to get market data and estimates</p>

            <form method="POST">
                <div class="mb-4">
                    <label class="form-label fw-bold">Property Address</label>
                    <input type="text" class="form-control" name="property_address" 
                           value="{{ form_data.get('property_address', '') }}" 
                           placeholder="123 Main St, City, State ZIP" required>
                    <small class="text-muted">We'll use this to fetch current market data and rental estimates</small>
                </div>

                <div class="mb-4">
                    <label class="form-label fw-bold">Property Name/Nickname</label>
                    <input type="text" class="form-control" name="house_name" 
                           value="{{ form_data.get('house_name', '') }}" 
                           placeholder="My Investment Property" required>
                    <small class="text-muted">Give your property a memorable name for your records</small>
                </div>

                {% if rentcast_data %}
    {% if rentcast_data.property_value or rentcast_data.rent_estimate %}
    <div class="rentcast-suggestion">
        <h6><i class="bi bi-check-circle"></i> Market Data Found via Rentcast</h6>
        {% if rentcast_data.property_value %}
        <p><strong>Estimated Property Value:</strong> ${{ "{:,.0f}".format(rentcast_data.property_value) }}
        {% if rentcast_data.property_confidence %}
        <span class="confidence-badge confidence-{{ rentcast_data.property_confidence|lower }}">
            {{ rentcast_data.property_confidence }} Confidence
        </span>
        {% endif %}
        </p>
        {% endif %}
        {% if rentcast_data.rent_estimate %}
        <p><strong>Estimated Monthly Rent:</strong> ${{ "{:,.0f}".format(rentcast_data.rent_estimate) }}
        {% if rentcast_data.rent_confidence %}
        <span class="confidence-badge confidence-{{ rentcast_data.rent_confidence|lower }}">
            {{ rentcast_data.rent_confidence }} Confidence
        </span>
        {% endif %}
        </p>
        {% endif %}
        <small class="text-muted">These estimates will pre-fill forms in the next steps.</small>
    </div>
    {% else %}
    <div class="alert alert-warning">
        <i class="bi bi-exclamation-triangle"></i> <strong>No market data found</strong><br>
        <small>Try a more complete address or check if the property exists in Rentcast's database.</small>
    </div>
    {% endif %}
{% endif %}

                <div class="d-flex justify-content-between">
                    <button type="button" class="btn btn-secondary-wizard" onclick="window.location='{{ url_for('index') }}'">
                        Start Over
                    </button>
                    <button type="submit" class="btn btn-wizard">
                        Continue <i class="bi bi-arrow-right"></i>
                    </button>
                </div>
            </form>
        </div>
    </div>
</body>
</html>
'''

# Step 2: Basic Property Info
basic_info_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Real Estate Investment Analysis</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            min-height: 100vh;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .wizard-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .progress-container {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .question-card {
            background: white;
            border-radius: 15px;
            padding: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .progress-bar {
            height: 12px;
            border-radius: 6px;
            background: linear-gradient(90deg, #667eea, #764ba2);
        }
        .step-indicator {
            display: flex;
            justify-content: space-between;
            margin-top: 15px;
        }
        .step-dot {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 12px;
        }
        .step-dot.completed {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
        .step-dot.current {
            background: #ffc107;
            color: #333;
        }
        .step-dot.pending {
            background: #e9ecef;
            color: #6c757d;
        }
        .question-title {
            color: #333;
            font-weight: 700;
            margin-bottom: 10px;
        }
        .question-subtitle {
            color: #666;
            margin-bottom: 30px;
        }
        .form-control, .form-select {
            border-radius: 10px;
            border: 2px solid #e9ecef;
            padding: 12px 15px;
        }
        .form-control:focus, .form-select:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
        }
        .btn-wizard {
            background: linear-gradient(135deg, #667eea, #764ba2);
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            font-weight: 600;
            color: white;
        }
        .btn-wizard:hover {
            background: linear-gradient(135deg, #5a6fd8, #6a4190);
            color: white;
        }
        .btn-secondary-wizard {
            background: #6c757d;
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            font-weight: 600;
            color: white;
        }
    </style>
</head>
<body>
    <div class="wizard-container">
        <div class="progress-container">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5 class="mb-0">Real Estate Investment Analysis</h5>
                <span class="badge bg-primary">{{ progress }}% Complete</span>
            </div>
            <div class="progress mb-3">
                <div class="progress-bar" style="width: {{ progress }}%"></div>
            </div>
            <div class="step-indicator">
                {% for step in steps %}
                <div class="step-dot {{ step.status }}" title="{{ step.title }}">
                    {{ loop.index }}
                </div>
                {% endfor %}
            </div>
        </div>

        <div class="question-card">
            <h2 class="question-title">Property Purchase Details</h2>
            <p class="question-subtitle">Tell us about the property cost and closing expenses</p>

            <form method="POST">
                <div class="mb-4">
                    <label class="form-label fw-bold">Purchase Price</label>
                    <div class="input-group">
                        <span class="input-group-text">$</span>
                        <input type="number" class="form-control" name="home_cost" 
                               value="{{ form_data.get('home_cost', suggested_values.get('property_value', '')) }}" 
                               placeholder="350000" required>
                    </div>
                    {% if suggested_values.get('property_value') %}
                    <small class="text-success">Suggested based on market data: ${{ "{:,.0f}".format(suggested_values.property_value) }}</small>
                    {% endif %}
                </div>

                <div class="mb-4">
    {% if suggested_values.get('property_value') %}
    <small class="text-success">💡 Rentcast suggests: ${{ "{:,.0f}".format(suggested_values.property_value) }}</small>
    {% endif %}
</div>
                    <small class="text-muted">Typical closing costs range from 2-5% of purchase price</small>
                </div>

                <div class="d-flex justify-content-between">
                    <button type="button" class="btn btn-secondary-wizard" onclick="window.location='{{ url_for('wizard_step', step='property_search') }}'">
                        <i class="bi bi-arrow-left"></i> Previous
                    </button>
                    <button type="submit" class="btn btn-wizard">
                        Continue <i class="bi bi-arrow-right"></i>
                    </button>
                </div>
            </form>
        </div>
    </div>
</body>
</html>
'''

# Step 3: Financing
financing_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Real Estate Investment Analysis</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            min-height: 100vh;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .wizard-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .progress-container {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .question-card {
            background: white;
            border-radius: 15px;
            padding: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .progress-bar {
            height: 12px;
            border-radius: 6px;
            background: linear-gradient(90deg, #667eea, #764ba2);
        }
        .step-indicator {
            display: flex;
            justify-content: space-between;
            margin-top: 15px;
        }
        .step-dot {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 12px;
        }
        .step-dot.completed {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
        .step-dot.current {
            background: #ffc107;
            color: #333;
        }
        .step-dot.pending {
            background: #e9ecef;
            color: #6c757d;
        }
        .question-title {
            color: #333;
            font-weight: 700;
            margin-bottom: 10px;
        }
        .question-subtitle {
            color: #666;
            margin-bottom: 30px;
        }
        .form-control, .form-select {
            border-radius: 10px;
            border: 2px solid #e9ecef;
            padding: 12px 15px;
        }
        .form-control:focus, .form-select:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
        }
        .btn-wizard {
            background: linear-gradient(135deg, #667eea, #764ba2);
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            font-weight: 600;
            color: white;
        }
        .btn-wizard:hover {
            background: linear-gradient(135deg, #5a6fd8, #6a4190);
            color: white;
        }
        .btn-secondary-wizard {
            background: #6c757d;
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            font-weight: 600;
            color: white;
        }
    </style>
</head>
<body>
    <div class="wizard-container">
        <div class="progress-container">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5 class="mb-0">Real Estate Investment Analysis</h5>
                <span class="badge bg-primary">{{ progress }}% Complete</span>
            </div>
            <div class="progress mb-3">
                <div class="progress-bar" style="width: {{ progress }}%"></div>
            </div>
            <div class="step-indicator">
                {% for step in steps %}
                <div class="step-dot {{ step.status }}" title="{{ step.title }}">
                    {{ loop.index }}
                </div>
                {% endfor %}
            </div>
        </div>

        <div class="question-card">
            <h2 class="question-title">Financing Options</h2>
            <p class="question-subtitle">Configure your mortgage terms and down payment</p>

            <form method="POST">
                <div class="mb-4">
                    <label class="form-label fw-bold">Loan Type</label>
                    <select class="form-select" name="loan_type_choice" onchange="toggleCustomTerm()">
                        <option value="1" {{ 'selected' if form_data.get('loan_type_choice') == '1' else '' }}>30-Year Fixed</option>
                        <option value="2" {{ 'selected' if form_data.get('loan_type_choice') == '2' else '' }}>15-Year Fixed</option>
                        <option value="3" {{ 'selected' if form_data.get('loan_type_choice') == '3' else '' }}>Custom Term</option>
                    </select>
                </div>

                <div class="mb-4" id="custom_term_div" style="{{ 'display: block' if form_data.get('loan_type_choice') == '3' else 'display: none' }}">
                    <label class="form-label fw-bold">Custom Loan Term (Years)</label>
                    <input type="number" class="form-control" name="custom_loan_term" 
                           value="{{ form_data.get('custom_loan_term', '30') }}">
                </div>

                <div class="mb-4">
                    <label class="form-label fw-bold">Down Payment</label>
                    <div class="input-group">
                        <input type="number" class="form-control" name="down_payment_percent" 
                               value="{{ form_data.get('down_payment_percent', '20') }}" 
                               step="0.1" min="0" max="100" required>
                        <span class="input-group-text">%</span>
                    </div>
                    <small class="text-muted">Investment properties typically require 20-25% down</small>
                </div>

                <div class="mb-4">
                    <label class="form-label fw-bold">Interest Rate</label>
                    <div class="input-group">
                        <input type="number" class="form-control" name="mortgage_interest_rate" 
                               value="{{ form_data.get('mortgage_interest_rate', '6.5') }}" 
                               step="0.01" min="0" max="20" required>
                        <span class="input-group-text">%</span>
                    </div>
                    <small class="text-muted">Current rates for investment properties are typically 0.5-1% higher than primary residence</small>
                </div>

                <div class="mb-4">
                    <label class="form-label fw-bold">Expected Annual Appreciation</label>
                    <div class="input-group">
                        <input type="number" class="form-control" name="annual_appreciation_percent" 
                               value="{{ form_data.get('annual_appreciation_percent', '3') }}" 
                               step="0.1" min="0" max="20" required>
                        <span class="input-group-text">%</span>
                    </div>
                    <small class="text-muted">Conservative estimate is 2-4% annually</small>
                </div>

                <script>
                function toggleCustomTerm() {
                    const select = document.querySelector('[name="loan_type_choice"]');
                    const customDiv = document.getElementById('custom_term_div');
                    customDiv.style.display = select.value === '3' ? 'block' : 'none';
                }
                </script>

                <div class="d-flex justify-content-between">
                    <button type="button" class="btn btn-secondary-wizard" onclick="window.location='{{ url_for('wizard_step', step='basic_info') }}'">
                        <i class="bi bi-arrow-left"></i> Previous
                    </button>
                    <button type="submit" class="btn btn-wizard">
                        Continue <i class="bi bi-arrow-right"></i>
                    </button>
                </div>
            </form>
        </div>
    </div>
</body>
</html>
'''

# Step 4: Rental Income
rental_income_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Real Estate Investment Analysis</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            min-height: 100vh;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .wizard-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .progress-container {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .question-card {
            background: white;
            border-radius: 15px;
            padding: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .progress-bar {
            height: 12px;
            border-radius: 6px;
            background: linear-gradient(90deg, #667eea, #764ba2);
        }
        .step-indicator {
            display: flex;
            justify-content: space-between;
            margin-top: 15px;
        }
        .step-dot {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 12px;
        }
        .step-dot.completed {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
        .step-dot.current {
            background: #ffc107;
            color: #333;
        }
        .step-dot.pending {
            background: #e9ecef;
            color: #6c757d;
        }
        .question-title {
            color: #333;
            font-weight: 700;
            margin-bottom: 10px;
        }
        .question-subtitle {
            color: #666;
            margin-bottom: 30px;
        }
        .form-control, .form-select {
            border-radius: 10px;
            border: 2px solid #e9ecef;
            padding: 12px 15px;
        }
        .form-control:focus, .form-select:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
        }
        .btn-wizard {
            background: linear-gradient(135deg, #667eea, #764ba2);
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            font-weight: 600;
            color: white;
        }
        .btn-wizard:hover {
            background: linear-gradient(135deg, #5a6fd8, #6a4190);
            color: white;
        }
        .btn-secondary-wizard {
            background: #6c757d;
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            font-weight: 600;
            color: white;
        }
    </style>
</head>
<body>
    <div class="wizard-container">
        <div class="progress-container">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5 class="mb-0">Real Estate Investment Analysis</h5>
                <span class="badge bg-primary">{{ progress }}% Complete</span>
            </div>
            <div class="progress mb-3">
                <div class="progress-bar" style="width: {{ progress }}%"></div>
            </div>
            <div class="step-indicator">
                {% for step in steps %}
                <div class="step-dot {{ step.status }}" title="{{ step.title }}">
                    {{ loop.index }}
                </div>
                {% endfor %}
            </div>
        </div>

        <div class="question-card">
            <h2 class="question-title">Rental Income Projections</h2>
            <p class="question-subtitle">Estimate your rental income and vacancy assumptions</p>

            <form method="POST">
                <div class="mb-4">
    <label class="form-label fw-bold">Monthly Rent</label>
    <div class="input-group">
        <span class="input-group-text">$</span>
        <input type="number" class="form-control" name="monthly_rent" 
               value="{{ form_data.get('monthly_rent', form_data.get('suggested_monthly_rent', '')) }}" 
               placeholder="2500" required>
    </div>
    {% if suggested_values.get('rent_estimate') %}
    <small class="text-success">💡 Rentcast suggests: ${{ "{:,.0f}".format(suggested_values.rent_estimate) }}</small>
    {% endif %}
</div>
                    {% if suggested_values.get('rent_estimate') %}
                    <small class="text-success">Suggested based on market data: ${{ "{:,.0f}".format(suggested_values.rent_estimate) }}</small>
                    {% endif %}
                </div>

                <div class="mb-4">
                    <label class="form-label fw-bold">Annual Rent Growth</label>
                    <div class="input-group">
                        <input type="number" class="form-control" name="rental_income_growth_percent" 
                               value="{{ form_data.get('rental_income_growth_percent', '3') }}" 
                               step="0.1" min="0" max="20" required>
                        <span class="input-group-text">%</span>
                    </div>
                    <small class="text-muted">Typical rent increases are 2-5% annually</small>
                </div>

                <div class="mb-4">
                    <label class="form-label fw-bold">Vacancy Rate</label>
                    <div class="input-group">
                        <input type="number" class="form-control" name="vacancy_rate" 
                               value="{{ form_data.get('vacancy_rate', '5') }}" 
                               step="0.1" min="0" max="50" required>
                        <span class="input-group-text">%</span>
                    </div>
                    <small class="text-muted">Good properties typically have 3-8% vacancy</small>
                </div>

                <div class="mb-4">
                    <label class="form-label fw-bold">Property Management Fee</label>
                    <div class="input-group">
                        <input type="number" class="form-control" name="management_fee_percent" 
                               value="{{ form_data.get('management_fee_percent', '8') }}" 
                               step="0.1" min="0" max="20">
                        <span class="input-group-text">%</span>
                    </div>
                    <small class="text-muted">Enter 0 if self-managing. Professional management typically costs 6-12%</small>
                </div>

                <div class="d-flex justify-content-between">
                    <button type="button" class="btn btn-secondary-wizard" onclick="window.location='{{ url_for('wizard_step', step='financing') }}'">
                        <i class="bi bi-arrow-left"></i> Previous
                    </button>
                    <button type="submit" class="btn btn-wizard">
                        Continue <i class="bi bi-arrow-right"></i>
                    </button>
                </div>
            </form>
        </div>
    </div>
</body>
</html>
'''

# Step 5: Expenses
expenses_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Real Estate Investment Analysis</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            min-height: 100vh;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .wizard-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .progress-container {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .question-card {
            background: white;
            border-radius: 15px;
            padding: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .progress-bar {
            height: 12px;
            border-radius: 6px;
            background: linear-gradient(90deg, #667eea, #764ba2);
        }
        .step-indicator {
            display: flex;
            justify-content: space-between;
            margin-top: 15px;
        }
        .step-dot {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 12px;
        }
        .step-dot.completed {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
        .step-dot.current {
            background: #ffc107;
            color: #333;
        }
        .step-dot.pending {
            background: #e9ecef;
            color: #6c757d;
        }
        .question-title {
            color: #333;
            font-weight: 700;
            margin-bottom: 10px;
        }
        .question-subtitle {
            color: #666;
            margin-bottom: 30px;
        }
        .form-control, .form-select {
            border-radius: 10px;
            border: 2px solid #e9ecef;
            padding: 12px 15px;
        }
        .form-control:focus, .form-select:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
        }
        .btn-wizard {
            background: linear-gradient(135deg, #667eea, #764ba2);
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            font-weight: 600;
            color: white;
        }
        .btn-wizard:hover {
            background: linear-gradient(135deg, #5a6fd8, #6a4190);
            color: white;
        }
        .btn-secondary-wizard {
            background: #6c757d;
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            font-weight: 600;
            color: white;
        }
    </style>
</head>
<body>
    <div class="wizard-container">
        <div class="progress-container">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5 class="mb-0">Real Estate Investment Analysis</h5>
                <span class="badge bg-primary">{{ progress }}% Complete</span>
            </div>
            <div class="progress mb-3">
                <div class="progress-bar" style="width: {{ progress }}%"></div>
            </div>
            <div class="step-indicator">
                {% for step in steps %}
                <div class="step-dot {{ step.status }}" title="{{ step.title }}">
                    {{ loop.index }}
                </div>
                {% endfor %}
            </div>
        </div>

        <div class="question-card">
            <h2 class="question-title">Operating Expenses</h2>
            <p class="question-subtitle">Configure property taxes, insurance, and other costs</p>

            <form method="POST">
                <div class="mb-4">
                    <label class="form-label fw-bold">Property Tax Method</label>
                    <select class="form-select" name="prop_tax_mode" onchange="toggleTaxInput()">
                        <option value="p" {{ 'selected' if form_data.get('prop_tax_mode') == 'p' else '' }}>Percentage of Property Value</option>
                        <option value="d" {{ 'selected' if form_data.get('prop_tax_mode') == 'd' else '' }}>Fixed Dollar Amount</option>
                    </select>
                </div>

                <div class="mb-4" id="tax_percent_div" style="{{ 'display: block' if form_data.get('prop_tax_mode', 'p') == 'p' else 'display: none' }}">
                    <label class="form-label fw-bold">Property Tax Rate</label>
                    <div class="input-group">
                        <input type="number" class="form-control" name="property_tax_percent" 
                               value="{{ form_data.get('property_tax_percent', '1.2') }}" 
                               step="0.01" min="0" max="10">
                        <span class="input-group-text">%</span>
                    </div>
                    <small class="text-muted">Varies by location. Check local rates</small>
                </div>

                <div class="mb-4" id="tax_amount_div" style="{{ 'display: none' if form_data.get('prop_tax_mode', 'p') == 'p' else 'display: block' }}">
                    <label class="form-label fw-bold">Annual Property Tax</label>
                    <div class="input-group">
                        <span class="input-group-text">$</span>
                        <input type="number" class="form-control" name="property_tax_amount" 
                               value="{{ form_data.get('property_tax_amount', '') }}">
                    </div>
                </div>

                <div class="mb-4">
                    <label class="form-label fw-bold">Property Tax Appraisal Growth</label>
                    <div class="input-group">
                        <input type="number" class="form-control" name="tax_appraisal_growth" 
                               value="{{ form_data.get('tax_appraisal_growth', '2') }}" 
                               step="0.1" min="0" max="20" required>
                        <span class="input-group-text">%</span>
                    </div>
                    <small class="text-muted">How much assessed value increases annually (may be capped by local law)</small>
                </div>

                <div class="mb-4">
                    <label class="form-label fw-bold">Insurance Method</label>
                    <select class="form-select" name="ins_mode" onchange="toggleInsuranceInput()">
                        <option value="p" {{ 'selected' if form_data.get('ins_mode') == 'p' else '' }}>Percentage of Property Value</option>
                        <option value="d" {{ 'selected' if form_data.get('ins_mode') == 'd' else '' }}>Fixed Dollar Amount</option>
                    </select>
                </div>

                <div class="mb-4" id="ins_percent_div" style="{{ 'display: block' if form_data.get('ins_mode', 'p') == 'p' else 'display: none' }}">
                    <label class="form-label fw-bold">Insurance Rate</label>
                    <div class="input-group">
                        <input type="number" class="form-control" name="home_insurance_percent" 
                               value="{{ form_data.get('home_insurance_percent', '0.5') }}" 
                               step="0.01" min="0" max="5">
                        <span class="input-group-text">%</span>
                    </div>
                </div>

                <div class="mb-4" id="ins_amount_div" style="{{ 'display: none' if form_data.get('ins_mode', 'p') == 'p' else 'display: block' }}">
                    <label class="form-label fw-bold">Annual Insurance Premium</label>
                    <div class="input-group">
                        <span class="input-group-text">$</span>
                        <input type="number" class="form-control" name="home_insurance_amount" 
                               value="{{ form_data.get('home_insurance_amount', '') }}">
                    </div>
                </div>

                <div class="mb-4">
                    <label class="form-label fw-bold">Annual HOA Fees</label>
                    <div class="input-group">
                        <span class="input-group-text">$</span>
                        <input type="number" class="form-control" name="hoa_fee" 
                               value="{{ form_data.get('hoa_fee', '0') }}" required>
                    </div>
                    <small class="text-muted">Enter 0 if no HOA</small>
                </div>

                <script>
                function toggleTaxInput() {
                    const select = document.querySelector('[name="prop_tax_mode"]');
                    const percentDiv = document.getElementById('tax_percent_div');
                    const amountDiv = document.getElementById('tax_amount_div');
                    if (select.value === 'p') {
                        percentDiv.style.display = 'block';
                        amountDiv.style.display = 'none';
                    } else {
                        percentDiv.style.display = 'none';
                        amountDiv.style.display = 'block';
                    }
                }

                function toggleInsuranceInput() {
                    const select = document.querySelector('[name="ins_mode"]');
                    const percentDiv = document.getElementById('ins_percent_div');
                    const amountDiv = document.getElementById('ins_amount_div');
                    if (select.value === 'p') {
                        percentDiv.style.display = 'block';
                        amountDiv.style.display = 'none';
                    } else {
                        percentDiv.style.display = 'none';
                        amountDiv.style.display = 'block';
                    }
                }
                </script>

                <div class="d-flex justify-content-between">
                    <button type="button" class="btn btn-secondary-wizard" onclick="window.location='{{ url_for('wizard_step', step='rental_income') }}'">
                        <i class="bi bi-arrow-left"></i> Previous
                    </button>
                    <button type="submit" class="btn btn-wizard">
                        Continue <i class="bi bi-arrow-right"></i>
                    </button>
                </div>
            </form>
        </div>
    </div>
</body>
</html>
'''

# Step 6: Investment Details
investment_details_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Real Estate Investment Analysis</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            min-height: 100vh;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .wizard-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .progress-container {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .question-card {
            background: white;
            border-radius: 15px;
            padding: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .progress-bar {
            height: 12px;
            border-radius: 6px;
            background: linear-gradient(90deg, #667eea, #764ba2);
        }
        .step-indicator {
            display: flex;
            justify-content: space-between;
            margin-top: 15px;
        }
        .step-dot {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 12px;
        }
        .step-dot.completed {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
        .step-dot.current {
            background: #ffc107;
            color: #333;
        }
        .step-dot.pending {
            background: #e9ecef;
            color: #6c757d;
        }
        .question-title {
            color: #333;
            font-weight: 700;
            margin-bottom: 10px;
        }
        .question-subtitle {
            color: #666;
            margin-bottom: 30px;
        }
        .form-control, .form-select {
            border-radius: 10px;
            border: 2px solid #e9ecef;
            padding: 12px 15px;
        }
        .form-control:focus, .form-select:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
        }
        .btn-wizard {
            background: linear-gradient(135deg, #667eea, #764ba2);
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            font-weight: 600;
            color: white;
        }
        .btn-wizard:hover {
            background: linear-gradient(135deg, #5a6fd8, #6a4190);
            color: white;
        }
        .btn-secondary-wizard {
            background: #6c757d;
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            font-weight: 600;
            color: white;
        }
    </style>
</head>
<body>
    <div class="wizard-container">
        <div class="progress-container">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5 class="mb-0">Real Estate Investment Analysis</h5>
                <span class="badge bg-primary">{{ progress }}% Complete</span>
            </div>
            <div class="progress mb-3">
                <div class="progress-bar" style="width: {{ progress }}%"></div>
            </div>
            <div class="step-indicator">
                {% for step in steps %}
                <div class="step-dot {{ step.status }}" title="{{ step.title }}">
                    {{ loop.index }}
                </div>
                {% endfor %}
            </div>
        </div>

        <div class="question-card">
            <h2 class="question-title">Investment Parameters</h2>
            <p class="question-subtitle">Set your investment timeline and tax assumptions</p>

            <form method="POST">
                <div class="mb-4">
                    <label class="form-label fw-bold">How long will you own this property?</label>
                    <div class="input-group">
                        <input type="number" class="form-control" name="ownership_years" 
                               value="{{ form_data.get('ownership_years', '10') }}" 
                               min="1" max="50" required>
                        <span class="input-group-text">years</span>
                    </div>
                </div>

                <div class="mb-4">
                    <label class="form-label fw-bold">Selling Costs</label>
                    <div class="input-group">
                        <input type="number" class="form-control" name="sell_closing_cost_percent" 
                               value="{{ form_data.get('sell_closing_cost_percent', '6') }}" 
                               step="0.1" min="0" max="20" required>
                        <span class="input-group-text">%</span>
                    </div>
                    <small class="text-muted">Includes realtor commissions, closing costs, etc. Typically 6-8%</small>
                </div>

                <div class="mb-4">
                    <label class="form-label fw-bold">Property Type</label>
                    <select class="form-select" name="is_rental" required>
                        <option value="yes" {{ 'selected' if form_data.get('is_rental') == 'yes' else '' }}>Rental Property</option>
                        <option value="no" {{ 'selected' if form_data.get('is_rental') == 'no' else '' }}>Primary Residence</option>
                    </select>
                    <small class="text-muted">Affects depreciation and capital gains tax treatment</small>
                </div>

                <div class="mb-4">
                    <label class="form-label fw-bold">Structure Value (for depreciation)</label>
                    <div class="input-group">
                        <input type="number" class="form-control" name="structure_percent" 
                               value="{{ form_data.get('structure_percent', '80') }}" 
                               min="50" max="95" required>
                        <span class="input-group-text">%</span>
                    </div>
                    <small class="text-muted">Percentage of purchase price allocated to the building (not land). Typically 75-85%</small>
                </div>

                <div class="mb-4">
                    <label class="form-label fw-bold">Your Marginal Tax Rate</label>
                    <div class="input-group">
                        <input type="number" class="form-control" name="tax_rate" 
                               value="{{ form_data.get('tax_rate', '25') }}" 
                               min="0" max="50">
                        <span class="input-group-text">%</span>
                    </div>
                    <small class="text-muted">Federal + State income tax rate for rental income</small>
                </div>

                <div class="mb-4">
                    <label class="form-label fw-bold">Capital Gains Tax Rate</label>
                    <div class="input-group">
                        <input type="number" class="form-control" name="cap_gains_rate" 
                               value="{{ form_data.get('cap_gains_rate', '20') }}" 
                               min="0" max="40">
                        <span class="input-group-text">%</span>
                    </div>
                    <small class="text-muted">Long-term capital gains rate (usually 15-20% federal)</small>
                </div>

                <div class="d-flex justify-content-between">
                    <button type="button" class="btn btn-secondary-wizard" onclick="window.location='{{ url_for('wizard_step', step='expenses') }}'">
                        <i class="bi bi-arrow-left"></i> Previous
                    </button>
                    <button type="submit" class="btn btn-wizard">
                        Continue <i class="bi bi-arrow-right"></i>
                    </button>
                </div>
            </form>
        </div>
    </div>
</body>
</html>
'''

# Step 7: Remodeling
remodeling_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Real Estate Investment Analysis</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            min-height: 100vh;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .wizard-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .progress-container {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .question-card {
            background: white;
            border-radius: 15px;
            padding: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .progress-bar {
            height: 12px;
            border-radius: 6px;
            background: linear-gradient(90deg, #667eea, #764ba2);
        }
        .step-indicator {
            display: flex;
            justify-content: space-between;
            margin-top: 15px;
        }
        .step-dot {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 12px;
        }
        .step-dot.completed {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
        .step-dot.current {
            background: #ffc107;
            color: #333;
        }
        .step-dot.pending {
            background: #e9ecef;
            color: #6c757d;
        }
        .question-title {
            color: #333;
            font-weight: 700;
            margin-bottom: 10px;
        }
        .question-subtitle {
            color: #666;
            margin-bottom: 30px;
        }
        .form-control, .form-select {
            border-radius: 10px;
            border: 2px solid #e9ecef;
            padding: 12px 15px;
        }
        .form-control:focus, .form-select:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
        }
        .btn-wizard {
            background: linear-gradient(135deg, #667eea, #764ba2);
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            font-weight: 600;
            color: white;
        }
        .btn-wizard:hover {
            background: linear-gradient(135deg, #5a6fd8, #6a4190);
            color: white;
        }
        .btn-secondary-wizard {
            background: #6c757d;
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            font-weight: 600;
            color: white;
        }
    </style>
</head>
<body>
    <div class="wizard-container">
        <div class="progress-container">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5 class="mb-0">Real Estate Investment Analysis</h5>
                <span class="badge bg-primary">{{ progress }}% Complete</span>
            </div>
            <div class="progress mb-3">
                <div class="progress-bar" style="width: {{ progress }}%"></div>
            </div>
            <div class="step-indicator">
                {% for step in steps %}
                <div class="step-dot {{ step.status }}" title="{{ step.title }}">
                    {{ loop.index }}
                </div>
                {% endfor %}
            </div>
        </div>

        <div class="question-card">
            <h2 class="question-title">Remodeling & Improvements</h2>
            <p class="question-subtitle">Optional: Plan any renovations or improvements</p>

            <form method="POST">
                <div class="mb-4">
                    <label class="form-label fw-bold">Do you plan to remodel?</label>
                    <select class="form-select" name="is_remodeling" onchange="toggleRemodeling()">
                        <option value="no" {{ 'selected' if form_data.get('is_remodeling') != 'yes' else '' }}>No renovations planned</option>
                        <option value="yes" {{ 'selected' if form_data.get('is_remodeling') == 'yes' else '' }}>Yes, I have renovation plans</option>
                    </select>
                </div>

                <div id="remodeling_details" style="{{ 'display: block' if form_data.get('is_remodeling') == 'yes' else 'display: none' }}">
                    <div class="mb-4">
                        <label class="form-label fw-bold">Number of Renovation Projects</label>
                        <select class="form-select" name="num_remodels" onchange="updateRemodelSections()">
                            <option value="1" {{ 'selected' if form_data.get('num_remodels', '1') == '1' else '' }}>1 Project</option>
                            <option value="2" {{ 'selected' if form_data.get('num_remodels') == '2' else '' }}>2 Projects</option>
                            <option value="3" {{ 'selected' if form_data.get('num_remodels') == '3' else '' }}>3 Projects</option>
                        </select>
                    </div>

                    <!-- Remodel Project 1 -->
                    <div id="remodel_1" class="border rounded p-3 mb-3">
                        <h5>Renovation Project 1</h5>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Project Cost</label>
                                <div class="input-group">
                                    <span class="input-group-text">$</span>
                                    <input type="number" class="form-control" name="remodel_cost_1" 
                                           value="{{ form_data.get('remodel_cost_1', '0') }}">
                                </div>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Value Added</label>
                                <div class="input-group">
                                    <span class="input-group-text">$</span>
                                    <input type="number" class="form-control" name="remodel_value_1" 
                                           value="{{ form_data.get('remodel_value_1', '0') }}">
                                </div>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Year of Project</label>
                                <input type="number" class="form-control" name="remodel_year_1" 
                                       value="{{ form_data.get('remodel_year_1', '1') }}" min="1">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Months Without Rent</label>
                                <input type="number" class="form-control" name="remodel_months_1" 
                                       value="{{ form_data.get('remodel_months_1', '0') }}" min="0" max="12">
                            </div>
                        </div>
                    </div>

                    <!-- Remodel Project 2 -->
                    <div id="remodel_2" class="border rounded p-3 mb-3" style="{{ 'display: block' if form_data.get('num_remodels', '1')|int >= 2 else 'display: none' }}">
                        <h5>Renovation Project 2</h5>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Project Cost</label>
                                <div class="input-group">
                                    <span class="input-group-text">$</span>
                                    <input type="number" class="form-control" name="remodel_cost_2" 
                                           value="{{ form_data.get('remodel_cost_2', '0') }}">
                                </div>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Value Added</label>
                                <div class="input-group">
                                    <span class="input-group-text">$</span>
                                    <input type="number" class="form-control" name="remodel_value_2" 
                                           value="{{ form_data.get('remodel_value_2', '0') }}">
                                </div>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Year of Project</label>
                                <input type="number" class="form-control" name="remodel_year_2" 
                                       value="{{ form_data.get('remodel_year_2', '2') }}" min="1">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Months Without Rent</label>
                                <input type="number" class="form-control" name="remodel_months_2" 
                                       value="{{ form_data.get('remodel_months_2', '0') }}" min="0" max="12">
                            </div>
                        </div>
                    </div>

                    <!-- Remodel Project 3 -->
                    <div id="remodel_3" class="border rounded p-3 mb-3" style="{{ 'display: block' if form_data.get('num_remodels', '1')|int >= 3 else 'display: none' }}">
                        <h5>Renovation Project 3</h5>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Project Cost</label>
                                <div class="input-group">
                                    <span class="input-group-text">$</span>
                                    <input type="number" class="form-control" name="remodel_cost_3" 
                                           value="{{ form_data.get('remodel_cost_3', '0') }}">
                                </div>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Value Added</label>
                                <div class="input-group">
                                    <span class="input-group-text">$</span>
                                    <input type="number" class="form-control" name="remodel_value_3" 
                                           value="{{ form_data.get('remodel_value_3', '0') }}">
                                </div>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Year of Project</label>
                                <input type="number" class="form-control" name="remodel_year_3" 
                                       value="{{ form_data.get('remodel_year_3', '3') }}" min="1">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Months Without Rent</label>
                                <input type="number" class="form-control" name="remodel_months_3" 
                                       value="{{ form_data.get('remodel_months_3', '0') }}" min="0" max="12">
                            </div>
                        </div>
                    </div>
                </div>

                <script>
                function toggleRemodeling() {
                    const select = document.querySelector('[name="is_remodeling"]');
                    const details = document.getElementById('remodeling_details');
                    details.style.display = select.value === 'yes' ? 'block' : 'none';
                }

                function updateRemodelSections() {
                    const numRemodels = parseInt(document.querySelector('[name="num_remodels"]').value);
                    for (let i = 1; i <= 3; i++) {
                        const section = document.getElementById('remodel_' + i);
                        section.style.display = i <= numRemodels ? 'block' : 'none';
                    }
                }
                </script>

                <div class="d-flex justify-content-between">
                    <button type="button" class="btn btn-secondary-wizard" onclick="window.location='{{ url_for('wizard_step', step='investment_details') }}'">
                        <i class="bi bi-arrow-left"></i> Previous
                    </button>
                    <button type="submit" class="btn btn-wizard">
                        Generate Analysis <i class="bi bi-chart-bar"></i>
                    </button>
                </div>
            </form>
        </div>
    </div>
</body>
</html>
'''

# Template storage
templates = {
    'base.html': base_template,
    'property_search.html': property_search_template,
    'basic_info.html': basic_info_template,
    'financing.html': financing_template,
    'rental_income.html': rental_income_template,
    'expenses.html': expenses_template,
    'investment_details.html': investment_details_template,
    'remodeling.html': remodeling_template
}


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


# Base template with progress bar
base_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Real Estate Investment Analysis</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            min-height: 100vh;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .wizard-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .progress-container {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .question-card {
            background: white;
            border-radius: 15px;
            padding: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .progress-bar {
            height: 12px;
            border-radius: 6px;
            background: linear-gradient(90deg, #667eea, #764ba2);
        }
        .step-indicator {
            display: flex;
            justify-content: space-between;
            margin-top: 15px;
        }
        .step-dot {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 12px;
        }
        .step-dot.completed {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
        .step-dot.current {
            background: #ffc107;
            color: #333;
        }
        .step-dot.pending {
            background: #e9ecef;
            color: #6c757d;
        }
        .question-title {
            color: #333;
            font-weight: 700;
            margin-bottom: 10px;
        }
        .question-subtitle {
            color: #666;
            margin-bottom: 30px;
        }
        .form-control, .form-select {
            border-radius: 10px;
            border: 2px solid #e9ecef;
            padding: 12px 15px;
        }
        .form-control:focus, .form-select:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
        }
        .btn-wizard {
            background: linear-gradient(135deg, #667eea, #764ba2);
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            font-weight: 600;
            color: white;
        }
        .btn-wizard:hover {
            background: linear-gradient(135deg, #5a6fd8, #6a4190);
            color: white;
        }
        .btn-secondary-wizard {
            background: #6c757d;
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            font-weight: 600;
            color: white;
        }
        .rentcast-suggestion {
            background: #e3f2fd;
            border: 1px solid #2196f3;
            border-radius: 10px;
            padding: 15px;
            margin: 15px 0;
        }
        .confidence-badge {
            font-size: 0.8em;
            padding: 4px 8px;
            border-radius: 12px;
        }
        .confidence-high { background: #d4edda; color: #155724; }
        .confidence-medium { background: #fff3cd; color: #856404; }
        .confidence-low { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="wizard-container">
        <div class="progress-container">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5 class="mb-0">Real Estate Investment Analysis</h5>
                <span class="badge bg-primary">{{ progress }}% Complete</span>
            </div>
            <div class="progress mb-3">
                <div class="progress-bar" style="width: {{ progress }}%"></div>
            </div>
            <div class="step-indicator">
                {% for step in steps %}
                <div class="step-dot {{ step.status }}" title="{{ step.title }}">
                    {{ loop.index }}
                </div>
                {% endfor %}
            </div>
        </div>

        <div class="question-card">
            {% block content %}{% endblock %}
        </div>
    </div>
</body>
</html>
'''

# Step 1: Property Search
property_search_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Real Estate Investment Analysis</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            min-height: 100vh;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .wizard-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .progress-container {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .question-card {
            background: white;
            border-radius: 15px;
            padding: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .progress-bar {
            height: 12px;
            border-radius: 6px;
            background: linear-gradient(90deg, #667eea, #764ba2);
        }
        .step-indicator {
            display: flex;
            justify-content: space-between;
            margin-top: 15px;
        }
        .step-dot {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 12px;
        }
        .step-dot.completed {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
        .step-dot.current {
            background: #ffc107;
            color: #333;
        }
        .step-dot.pending {
            background: #e9ecef;
            color: #6c757d;
        }
        .question-title {
            color: #333;
            font-weight: 700;
            margin-bottom: 10px;
        }
        .question-subtitle {
            color: #666;
            margin-bottom: 30px;
        }
        .form-control, .form-select {
            border-radius: 10px;
            border: 2px solid #e9ecef;
            padding: 12px 15px;
        }
        .form-control:focus, .form-select:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
        }
        .btn-wizard {
            background: linear-gradient(135deg, #667eea, #764ba2);
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            font-weight: 600;
            color: white;
        }
        .btn-wizard:hover {
            background: linear-gradient(135deg, #5a6fd8, #6a4190);
            color: white;
        }
        .btn-secondary-wizard {
            background: #6c757d;
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            font-weight: 600;
            color: white;
        }
        .rentcast-suggestion {
            background: #e3f2fd;
            border: 1px solid #2196f3;
            border-radius: 10px;
            padding: 15px;
            margin: 15px 0;
        }
        .confidence-badge {
            font-size: 0.8em;
            padding: 4px 8px;
            border-radius: 12px;
        }
        .confidence-high { background: #d4edda; color: #155724; }
        .confidence-medium { background: #fff3cd; color: #856404; }
        .confidence-low { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="wizard-container">
        <div class="progress-container">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5 class="mb-0">Real Estate Investment Analysis</h5>
                <span class="badge bg-primary">{{ progress }}% Complete</span>
            </div>
            <div class="progress mb-3">
                <div class="progress-bar" style="width: {{ progress }}%"></div>
            </div>
            <div class="step-indicator">
                {% for step in steps %}
                <div class="step-dot {{ step.status }}" title="{{ step.title }}">
                    {{ loop.index }}
                </div>
                {% endfor %}
            </div>
        </div>

        <div class="question-card">
            <h2 class="question-title">Find Your Investment Property</h2>
            <p class="question-subtitle">Enter the property address to get market data and estimates</p>

            <form method="POST">
                <div class="mb-4">
                    <label class="form-label fw-bold">Property Address</label>
                    <input type="text" class="form-control" name="property_address" 
                           value="{{ form_data.get('property_address', '') }}" 
                           placeholder="123 Main St, City, State ZIP" required>
                    <small class="text-muted">We'll use this to fetch current market data and rental estimates</small>
                </div>

                <div class="mb-4">
                    <label class="form-label fw-bold">Property Name/Nickname</label>
                    <input type="text" class="form-control" name="house_name" 
                           value="{{ form_data.get('house_name', '') }}" 
                           placeholder="My Investment Property" required>
                    <small class="text-muted">Give your property a memorable name for your records</small>
                </div>

                {% if rentcast_data %}
    {% if rentcast_data.property_value or rentcast_data.rent_estimate %}
    <div class="rentcast-suggestion">
        <h6><i class="bi bi-check-circle"></i> Market Data Found via Rentcast</h6>
        {% if rentcast_data.property_value %}
        <p><strong>Estimated Property Value:</strong> ${{ "{:,.0f}".format(rentcast_data.property_value) }}
        {% if rentcast_data.property_confidence %}
        <span class="confidence-badge confidence-{{ rentcast_data.property_confidence|lower }}">
            {{ rentcast_data.property_confidence }} Confidence
        </span>
        {% endif %}
        </p>
        {% endif %}
        {% if rentcast_data.rent_estimate %}
        <p><strong>Estimated Monthly Rent:</strong> ${{ "{:,.0f}".format(rentcast_data.rent_estimate) }}
        {% if rentcast_data.rent_confidence %}
        <span class="confidence-badge confidence-{{ rentcast_data.rent_confidence|lower }}">
            {{ rentcast_data.rent_confidence }} Confidence
        </span>
        {% endif %}
        </p>
        {% endif %}
        <small class="text-muted">These estimates will pre-fill forms in the next steps.</small>
    </div>
    {% else %}
    <div class="alert alert-warning">
        <i class="bi bi-exclamation-triangle"></i> <strong>No market data found</strong><br>
        <small>Try a more complete address or check if the property exists in Rentcast's database.</small>
    </div>
    {% endif %}
{% endif %}

                <div class="d-flex justify-content-between">
                    <button type="button" class="btn btn-secondary-wizard" onclick="window.location='{{ url_for('index') }}'">
                        Start Over
                    </button>
                    <button type="submit" class="btn btn-wizard">
                        Continue <i class="bi bi-arrow-right"></i>
                    </button>
                </div>
            </form>
        </div>
    </div>
</body>
</html>
'''

# Step 2: Basic Property Info
basic_info_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Real Estate Investment Analysis</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            min-height: 100vh;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .wizard-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .progress-container {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .question-card {
            background: white;
            border-radius: 15px;
            padding: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .progress-bar {
            height: 12px;
            border-radius: 6px;
            background: linear-gradient(90deg, #667eea, #764ba2);
        }
        .step-indicator {
            display: flex;
            justify-content: space-between;
            margin-top: 15px;
        }
        .step-dot {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 12px;
        }
        .step-dot.completed {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
        .step-dot.current {
            background: #ffc107;
            color: #333;
        }
        .step-dot.pending {
            background: #e9ecef;
            color: #6c757d;
        }
        .question-title {
            color: #333;
            font-weight: 700;
            margin-bottom: 10px;
        }
        .question-subtitle {
            color: #666;
            margin-bottom: 30px;
        }
        .form-control, .form-select {
            border-radius: 10px;
            border: 2px solid #e9ecef;
            padding: 12px 15px;
        }
        .form-control:focus, .form-select:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
        }
        .btn-wizard {
            background: linear-gradient(135deg, #667eea, #764ba2);
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            font-weight: 600;
            color: white;
        }
        .btn-wizard:hover {
            background: linear-gradient(135deg, #5a6fd8, #6a4190);
            color: white;
        }
        .btn-secondary-wizard {
            background: #6c757d;
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            font-weight: 600;
            color: white;
        }
    </style>
</head>
<body>
    <div class="wizard-container">
        <div class="progress-container">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5 class="mb-0">Real Estate Investment Analysis</h5>
                <span class="badge bg-primary">{{ progress }}% Complete</span>
            </div>
            <div class="progress mb-3">
                <div class="progress-bar" style="width: {{ progress }}%"></div>
            </div>
            <div class="step-indicator">
                {% for step in steps %}
                <div class="step-dot {{ step.status }}" title="{{ step.title }}">
                    {{ loop.index }}
                </div>
                {% endfor %}
            </div>
        </div>

        <div class="question-card">
            <h2 class="question-title">Property Purchase Details</h2>
            <p class="question-subtitle">Tell us about the property cost and closing expenses</p>

            <form method="POST">
                <div class="mb-4">
                    <label class="form-label fw-bold">Purchase Price</label>
                    <div class="input-group">
                        <span class="input-group-text">$</span>
                        <input type="number" class="form-control" name="home_cost" 
                               value="{{ form_data.get('home_cost', suggested_values.get('property_value', '')) }}" 
                               placeholder="350000" required>
                    </div>
                    {% if suggested_values.get('property_value') %}
                    <small class="text-success">Suggested based on market data: ${{ "{:,.0f}".format(suggested_values.property_value) }}</small>
                    {% endif %}
                </div>

                <div class="mb-4">
    {% if suggested_values.get('property_value') %}
    <small class="text-success">💡 Rentcast suggests: ${{ "{:,.0f}".format(suggested_values.property_value) }}</small>
    {% endif %}
</div>
                    <small class="text-muted">Typical closing costs range from 2-5% of purchase price</small>
                </div>

                <div class="d-flex justify-content-between">
                    <button type="button" class="btn btn-secondary-wizard" onclick="window.location='{{ url_for('wizard_step', step='property_search') }}'">
                        <i class="bi bi-arrow-left"></i> Previous
                    </button>
                    <button type="submit" class="btn btn-wizard">
                        Continue <i class="bi bi-arrow-right"></i>
                    </button>
                </div>
            </form>
        </div>
    </div>
</body>
</html>
'''

# Step 3: Financing
financing_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Real Estate Investment Analysis</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            min-height: 100vh;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .wizard-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .progress-container {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .question-card {
            background: white;
            border-radius: 15px;
            padding: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .progress-bar {
            height: 12px;
            border-radius: 6px;
            background: linear-gradient(90deg, #667eea, #764ba2);
        }
        .step-indicator {
            display: flex;
            justify-content: space-between;
            margin-top: 15px;
        }
        .step-dot {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 12px;
        }
        .step-dot.completed {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
        .step-dot.current {
            background: #ffc107;
            color: #333;
        }
        .step-dot.pending {
            background: #e9ecef;
            color: #6c757d;
        }
        .question-title {
            color: #333;
            font-weight: 700;
            margin-bottom: 10px;
        }
        .question-subtitle {
            color: #666;
            margin-bottom: 30px;
        }
        .form-control, .form-select {
            border-radius: 10px;
            border: 2px solid #e9ecef;
            padding: 12px 15px;
        }
        .form-control:focus, .form-select:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
        }
        .btn-wizard {
            background: linear-gradient(135deg, #667eea, #764ba2);
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            font-weight: 600;
            color: white;
        }
        .btn-wizard:hover {
            background: linear-gradient(135deg, #5a6fd8, #6a4190);
            color: white;
        }
        .btn-secondary-wizard {
            background: #6c757d;
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            font-weight: 600;
            color: white;
        }
    </style>
</head>
<body>
    <div class="wizard-container">
        <div class="progress-container">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5 class="mb-0">Real Estate Investment Analysis</h5>
                <span class="badge bg-primary">{{ progress }}% Complete</span>
            </div>
            <div class="progress mb-3">
                <div class="progress-bar" style="width: {{ progress }}%"></div>
            </div>
            <div class="step-indicator">
                {% for step in steps %}
                <div class="step-dot {{ step.status }}" title="{{ step.title }}">
                    {{ loop.index }}
                </div>
                {% endfor %}
            </div>
        </div>

        <div class="question-card">
            <h2 class="question-title">Financing Options</h2>
            <p class="question-subtitle">Configure your mortgage terms and down payment</p>

            <form method="POST">
                <div class="mb-4">
                    <label class="form-label fw-bold">Loan Type</label>
                    <select class="form-select" name="loan_type_choice" onchange="toggleCustomTerm()">
                        <option value="1" {{ 'selected' if form_data.get('loan_type_choice') == '1' else '' }}>30-Year Fixed</option>
                        <option value="2" {{ 'selected' if form_data.get('loan_type_choice') == '2' else '' }}>15-Year Fixed</option>
                        <option value="3" {{ 'selected' if form_data.get('loan_type_choice') == '3' else '' }}>Custom Term</option>
                    </select>
                </div>

                <div class="mb-4" id="custom_term_div" style="{{ 'display: block' if form_data.get('loan_type_choice') == '3' else 'display: none' }}">
                    <label class="form-label fw-bold">Custom Loan Term (Years)</label>
                    <input type="number" class="form-control" name="custom_loan_term" 
                           value="{{ form_data.get('custom_loan_term', '30') }}">
                </div>

                <div class="mb-4">
                    <label class="form-label fw-bold">Down Payment</label>
                    <div class="input-group">
                        <input type="number" class="form-control" name="down_payment_percent" 
                               value="{{ form_data.get('down_payment_percent', '20') }}" 
                               step="0.1" min="0" max="100" required>
                        <span class="input-group-text">%</span>
                    </div>
                    <small class="text-muted">Investment properties typically require 20-25% down</small>
                </div>

                <div class="mb-4">
                    <label class="form-label fw-bold">Interest Rate</label>
                    <div class="input-group">
                        <input type="number" class="form-control" name="mortgage_interest_rate" 
                               value="{{ form_data.get('mortgage_interest_rate', '6.5') }}" 
                               step="0.01" min="0" max="20" required>
                        <span class="input-group-text">%</span>
                    </div>
                    <small class="text-muted">Current rates for investment properties are typically 0.5-1% higher than primary residence</small>
                </div>

                <div class="mb-4">
                    <label class="form-label fw-bold">Expected Annual Appreciation</label>
                    <div class="input-group">
                        <input type="number" class="form-control" name="annual_appreciation_percent" 
                               value="{{ form_data.get('annual_appreciation_percent', '3') }}" 
                               step="0.1" min="0" max="20" required>
                        <span class="input-group-text">%</span>
                    </div>
                    <small class="text-muted">Conservative estimate is 2-4% annually</small>
                </div>

                <script>
                function toggleCustomTerm() {
                    const select = document.querySelector('[name="loan_type_choice"]');
                    const customDiv = document.getElementById('custom_term_div');
                    customDiv.style.display = select.value === '3' ? 'block' : 'none';
                }
                </script>

                <div class="d-flex justify-content-between">
                    <button type="button" class="btn btn-secondary-wizard" onclick="window.location='{{ url_for('wizard_step', step='basic_info') }}'">
                        <i class="bi bi-arrow-left"></i> Previous
                    </button>
                    <button type="submit" class="btn btn-wizard">
                        Continue <i class="bi bi-arrow-right"></i>
                    </button>
                </div>
            </form>
        </div>
    </div>
</body>
</html>
'''

# Step 4: Rental Income
rental_income_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Real Estate Investment Analysis</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            min-height: 100vh;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .wizard-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .progress-container {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .question-card {
            background: white;
            border-radius: 15px;
            padding: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .progress-bar {
            height: 12px;
            border-radius: 6px;
            background: linear-gradient(90deg, #667eea, #764ba2);
        }
        .step-indicator {
            display: flex;
            justify-content: space-between;
            margin-top: 15px;
        }
        .step-dot {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 12px;
        }
        .step-dot.completed {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
        .step-dot.current {
            background: #ffc107;
            color: #333;
        }
        .step-dot.pending {
            background: #e9ecef;
            color: #6c757d;
        }
        .question-title {
            color: #333;
            font-weight: 700;
            margin-bottom: 10px;
        }
        .question-subtitle {
            color: #666;
            margin-bottom: 30px;
        }
        .form-control, .form-select {
            border-radius: 10px;
            border: 2px solid #e9ecef;
            padding: 12px 15px;
        }
        .form-control:focus, .form-select:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
        }
        .btn-wizard {
            background: linear-gradient(135deg, #667eea, #764ba2);
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            font-weight: 600;
            color: white;
        }
        .btn-wizard:hover {
            background: linear-gradient(135deg, #5a6fd8, #6a4190);
            color: white;
        }
        .btn-secondary-wizard {
            background: #6c757d;
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            font-weight: 600;
            color: white;
        }
    </style>
</head>
<body>
    <div class="wizard-container">
        <div class="progress-container">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5 class="mb-0">Real Estate Investment Analysis</h5>
                <span class="badge bg-primary">{{ progress }}% Complete</span>
            </div>
            <div class="progress mb-3">
                <div class="progress-bar" style="width: {{ progress }}%"></div>
            </div>
            <div class="step-indicator">
                {% for step in steps %}
                <div class="step-dot {{ step.status }}" title="{{ step.title }}">
                    {{ loop.index }}
                </div>
                {% endfor %}
            </div>
        </div>

        <div class="question-card">
            <h2 class="question-title">Rental Income Projections</h2>
            <p class="question-subtitle">Estimate your rental income and vacancy assumptions</p>

            <form method="POST">
                <div class="mb-4">
    <label class="form-label fw-bold">Monthly Rent</label>
    <div class="input-group">
        <span class="input-group-text">$</span>
        <input type="number" class="form-control" name="monthly_rent" 
               value="{{ form_data.get('monthly_rent', form_data.get('suggested_monthly_rent', '')) }}" 
               placeholder="2500" required>
    </div>
    {% if suggested_values.get('rent_estimate') %}
    <small class="text-success">💡 Rentcast suggests: ${{ "{:,.0f}".format(suggested_values.rent_estimate) }}</small>
    {% endif %}
</div>
                    {% if suggested_values.get('rent_estimate') %}
                    <small class="text-success">Suggested based on market data: ${{ "{:,.0f}".format(suggested_values.rent_estimate) }}</small>
                    {% endif %}
                </div>

                <div class="mb-4">
                    <label class="form-label fw-bold">Annual Rent Growth</label>
                    <div class="input-group">
                        <input type="number" class="form-control" name="rental_income_growth_percent" 
                               value="{{ form_data.get('rental_income_growth_percent', '3') }}" 
                               step="0.1" min="0" max="20" required>
                        <span class="input-group-text">%</span>
                    </div>
                    <small class="text-muted">Typical rent increases are 2-5% annually</small>
                </div>

                <div class="mb-4">
                    <label class="form-label fw-bold">Vacancy Rate</label>
                    <div class="input-group">
                        <input type="number" class="form-control" name="vacancy_rate" 
                               value="{{ form_data.get('vacancy_rate', '5') }}" 
                               step="0.1" min="0" max="50" required>
                        <span class="input-group-text">%</span>
                    </div>
                    <small class="text-muted">Good properties typically have 3-8% vacancy</small>
                </div>

                <div class="mb-4">
                    <label class="form-label fw-bold">Property Management Fee</label>
                    <div class="input-group">
                        <input type="number" class="form-control" name="management_fee_percent" 
                               value="{{ form_data.get('management_fee_percent', '8') }}" 
                               step="0.1" min="0" max="20">
                        <span class="input-group-text">%</span>
                    </div>
                    <small class="text-muted">Enter 0 if self-managing. Professional management typically costs 6-12%</small>
                </div>

                <div class="d-flex justify-content-between">
                    <button type="button" class="btn btn-secondary-wizard" onclick="window.location='{{ url_for('wizard_step', step='financing') }}'">
                        <i class="bi bi-arrow-left"></i> Previous
                    </button>
                    <button type="submit" class="btn btn-wizard">
                        Continue <i class="bi bi-arrow-right"></i>
                    </button>
                </div>
            </form>
        </div>
    </div>
</body>
</html>
'''

# Step 5: Expenses
expenses_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Real Estate Investment Analysis</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            min-height: 100vh;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .wizard-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .progress-container {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .question-card {
            background: white;
            border-radius: 15px;
            padding: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .progress-bar {
            height: 12px;
            border-radius: 6px;
            background: linear-gradient(90deg, #667eea, #764ba2);
        }
        .step-indicator {
            display: flex;
            justify-content: space-between;
            margin-top: 15px;
        }
        .step-dot {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 12px;
        }
        .step-dot.completed {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
        .step-dot.current {
            background: #ffc107;
            color: #333;
        }
        .step-dot.pending {
            background: #e9ecef;
            color: #6c757d;
        }
        .question-title {
            color: #333;
            font-weight: 700;
            margin-bottom: 10px;
        }
        .question-subtitle {
            color: #666;
            margin-bottom: 30px;
        }
        .form-control, .form-select {
            border-radius: 10px;
            border: 2px solid #e9ecef;
            padding: 12px 15px;
        }
        .form-control:focus, .form-select:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
        }
        .btn-wizard {
            background: linear-gradient(135deg, #667eea, #764ba2);
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            font-weight: 600;
            color: white;
        }
        .btn-wizard:hover {
            background: linear-gradient(135deg, #5a6fd8, #6a4190);
            color: white;
        }
        .btn-secondary-wizard {
            background: #6c757d;
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            font-weight: 600;
            color: white;
        }
    </style>
</head>
<body>
    <div class="wizard-container">
        <div class="progress-container">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5 class="mb-0">Real Estate Investment Analysis</h5>
                <span class="badge bg-primary">{{ progress }}% Complete</span>
            </div>
            <div class="progress mb-3">
                <div class="progress-bar" style="width: {{ progress }}%"></div>
            </div>
            <div class="step-indicator">
                {% for step in steps %}
                <div class="step-dot {{ step.status }}" title="{{ step.title }}">
                    {{ loop.index }}
                </div>
                {% endfor %}
            </div>
        </div>

        <div class="question-card">
            <h2 class="question-title">Operating Expenses</h2>
            <p class="question-subtitle">Configure property taxes, insurance, and other costs</p>

            <form method="POST">
                <div class="mb-4">
                    <label class="form-label fw-bold">Property Tax Method</label>
                    <select class="form-select" name="prop_tax_mode" onchange="toggleTaxInput()">
                        <option value="p" {{ 'selected' if form_data.get('prop_tax_mode') == 'p' else '' }}>Percentage of Property Value</option>
                        <option value="d" {{ 'selected' if form_data.get('prop_tax_mode') == 'd' else '' }}>Fixed Dollar Amount</option>
                    </select>
                </div>

                <div class="mb-4" id="tax_percent_div" style="{{ 'display: block' if form_data.get('prop_tax_mode', 'p') == 'p' else 'display: none' }}">
                    <label class="form-label fw-bold">Property Tax Rate</label>
                    <div class="input-group">
                        <input type="number" class="form-control" name="property_tax_percent" 
                               value="{{ form_data.get('property_tax_percent', '1.2') }}" 
                               step="0.01" min="0" max="10">
                        <span class="input-group-text">%</span>
                    </div>
                    <small class="text-muted">Varies by location. Check local rates</small>
                </div>

                <div class="mb-4" id="tax_amount_div" style="{{ 'display: none' if form_data.get('prop_tax_mode', 'p') == 'p' else 'display: block' }}">
                    <label class="form-label fw-bold">Annual Property Tax</label>
                    <div class="input-group">
                        <span class="input-group-text">$</span>
                        <input type="number" class="form-control" name="property_tax_amount" 
                               value="{{ form_data.get('property_tax_amount', '') }}">
                    </div>
                </div>

                <div class="mb-4">
                    <label class="form-label fw-bold">Property Tax Appraisal Growth</label>
                    <div class="input-group">
                        <input type="number" class="form-control" name="tax_appraisal_growth" 
                               value="{{ form_data.get('tax_appraisal_growth', '2') }}" 
                               step="0.1" min="0" max="20" required>
                        <span class="input-group-text">%</span>
                    </div>
                    <small class="text-muted">How much assessed value increases annually (may be capped by local law)</small>
                </div>

                <div class="mb-4">
                    <label class="form-label fw-bold">Insurance Method</label>
                    <select class="form-select" name="ins_mode" onchange="toggleInsuranceInput()">
                        <option value="p" {{ 'selected' if form_data.get('ins_mode') == 'p' else '' }}>Percentage of Property Value</option>
                        <option value="d" {{ 'selected' if form_data.get('ins_mode') == 'd' else '' }}>Fixed Dollar Amount</option>
                    </select>
                </div>

                <div class="mb-4" id="ins_percent_div" style="{{ 'display: block' if form_data.get('ins_mode', 'p') == 'p' else 'display: none' }}">
                    <label class="form-label fw-bold">Insurance Rate</label>
                    <div class="input-group">
                        <input type="number" class="form-control" name="home_insurance_percent" 
                               value="{{ form_data.get('home_insurance_percent', '0.5') }}" 
                               step="0.01" min="0" max="5">
                        <span class="input-group-text">%</span>
                    </div>
                </div>

                <div class="mb-4" id="ins_amount_div" style="{{ 'display: none' if form_data.get('ins_mode', 'p') == 'p' else 'display: block' }}">
                    <label class="form-label fw-bold">Annual Insurance Premium</label>
                    <div class="input-group">
                        <span class="input-group-text">$</span>
                        <input type="number" class="form-control" name="home_insurance_amount" 
                               value="{{ form_data.get('home_insurance_amount', '') }}">
                    </div>
                </div>

                <div class="mb-4">
                    <label class="form-label fw-bold">Annual HOA Fees</label>
                    <div class="input-group">
                        <span class="input-group-text">$</span>
                        <input type="number" class="form-control" name="hoa_fee" 
                               value="{{ form_data.get('hoa_fee', '0') }}" required>
                    </div>
                    <small class="text-muted">Enter 0 if no HOA</small>
                </div>

                <script>
                function toggleTaxInput() {
                    const select = document.querySelector('[name="prop_tax_mode"]');
                    const percentDiv = document.getElementById('tax_percent_div');
                    const amountDiv = document.getElementById('tax_amount_div');
                    if (select.value === 'p') {
                        percentDiv.style.display = 'block';
                        amountDiv.style.display = 'none';
                    } else {
                        percentDiv.style.display = 'none';
                        amountDiv.style.display = 'block';
                    }
                }

                function toggleInsuranceInput() {
                    const select = document.querySelector('[name="ins_mode"]');
                    const percentDiv = document.getElementById('ins_percent_div');
                    const amountDiv = document.getElementById('ins_amount_div');
                    if (select.value === 'p') {
                        percentDiv.style.display = 'block';
                        amountDiv.style.display = 'none';
                    } else {
                        percentDiv.style.display = 'none';
                        amountDiv.style.display = 'block';
                    }
                }
                </script>

                <div class="d-flex justify-content-between">
                    <button type="button" class="btn btn-secondary-wizard" onclick="window.location='{{ url_for('wizard_step', step='rental_income') }}'">
                        <i class="bi bi-arrow-left"></i> Previous
                    </button>
                    <button type="submit" class="btn btn-wizard">
                        Continue <i class="bi bi-arrow-right"></i>
                    </button>
                </div>
            </form>
        </div>
    </div>
</body>
</html>
'''

# Step 6: Investment Details
investment_details_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Real Estate Investment Analysis</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            min-height: 100vh;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .wizard-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .progress-container {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .question-card {
            background: white;
            border-radius: 15px;
            padding: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .progress-bar {
            height: 12px;
            border-radius: 6px;
            background: linear-gradient(90deg, #667eea, #764ba2);
        }
        .step-indicator {
            display: flex;
            justify-content: space-between;
            margin-top: 15px;
        }
        .step-dot {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 12px;
        }
        .step-dot.completed {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
        .step-dot.current {
            background: #ffc107;
            color: #333;
        }
        .step-dot.pending {
            background: #e9ecef;
            color: #6c757d;
        }
        .question-title {
            color: #333;
            font-weight: 700;
            margin-bottom: 10px;
        }
        .question-subtitle {
            color: #666;
            margin-bottom: 30px;
        }
        .form-control, .form-select {
            border-radius: 10px;
            border: 2px solid #e9ecef;
            padding: 12px 15px;
        }
        .form-control:focus, .form-select:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
        }
        .btn-wizard {
            background: linear-gradient(135deg, #667eea, #764ba2);
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            font-weight: 600;
            color: white;
        }
        .btn-wizard:hover {
            background: linear-gradient(135deg, #5a6fd8, #6a4190);
            color: white;
        }
        .btn-secondary-wizard {
            background: #6c757d;
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            font-weight: 600;
            color: white;
        }
    </style>
</head>
<body>
    <div class="wizard-container">
        <div class="progress-container">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5 class="mb-0">Real Estate Investment Analysis</h5>
                <span class="badge bg-primary">{{ progress }}% Complete</span>
            </div>
            <div class="progress mb-3">
                <div class="progress-bar" style="width: {{ progress }}%"></div>
            </div>
            <div class="step-indicator">
                {% for step in steps %}
                <div class="step-dot {{ step.status }}" title="{{ step.title }}">
                    {{ loop.index }}
                </div>
                {% endfor %}
            </div>
        </div>

        <div class="question-card">
            <h2 class="question-title">Investment Parameters</h2>
            <p class="question-subtitle">Set your investment timeline and tax assumptions</p>

            <form method="POST">
                <div class="mb-4">
                    <label class="form-label fw-bold">How long will you own this property?</label>
                    <div class="input-group">
                        <input type="number" class="form-control" name="ownership_years" 
                               value="{{ form_data.get('ownership_years', '10') }}" 
                               min="1" max="50" required>
                        <span class="input-group-text">years</span>
                    </div>
                </div>

                <div class="mb-4">
                    <label class="form-label fw-bold">Selling Costs</label>
                    <div class="input-group">
                        <input type="number" class="form-control" name="sell_closing_cost_percent" 
                               value="{{ form_data.get('sell_closing_cost_percent', '6') }}" 
                               step="0.1" min="0" max="20" required>
                        <span class="input-group-text">%</span>
                    </div>
                    <small class="text-muted">Includes realtor commissions, closing costs, etc. Typically 6-8%</small>
                </div>

                <div class="mb-4">
                    <label class="form-label fw-bold">Property Type</label>
                    <select class="form-select" name="is_rental" required>
                        <option value="yes" {{ 'selected' if form_data.get('is_rental') == 'yes' else '' }}>Rental Property</option>
                        <option value="no" {{ 'selected' if form_data.get('is_rental') == 'no' else '' }}>Primary Residence</option>
                    </select>
                    <small class="text-muted">Affects depreciation and capital gains tax treatment</small>
                </div>

                <div class="mb-4">
                    <label class="form-label fw-bold">Structure Value (for depreciation)</label>
                    <div class="input-group">
                        <input type="number" class="form-control" name="structure_percent" 
                               value="{{ form_data.get('structure_percent', '80') }}" 
                               min="50" max="95" required>
                        <span class="input-group-text">%</span>
                    </div>
                    <small class="text-muted">Percentage of purchase price allocated to the building (not land). Typically 75-85%</small>
                </div>

                <div class="mb-4">
                    <label class="form-label fw-bold">Your Marginal Tax Rate</label>
                    <div class="input-group">
                        <input type="number" class="form-control" name="tax_rate" 
                               value="{{ form_data.get('tax_rate', '25') }}" 
                               min="0" max="50">
                        <span class="input-group-text">%</span>
                    </div>
                    <small class="text-muted">Federal + State income tax rate for rental income</small>
                </div>

                <div class="mb-4">
                    <label class="form-label fw-bold">Capital Gains Tax Rate</label>
                    <div class="input-group">
                        <input type="number" class="form-control" name="cap_gains_rate" 
                               value="{{ form_data.get('cap_gains_rate', '20') }}" 
                               min="0" max="40">
                        <span class="input-group-text">%</span>
                    </div>
                    <small class="text-muted">Long-term capital gains rate (usually 15-20% federal)</small>
                </div>

                <div class="d-flex justify-content-between">
                    <button type="button" class="btn btn-secondary-wizard" onclick="window.location='{{ url_for('wizard_step', step='expenses') }}'">
                        <i class="bi bi-arrow-left"></i> Previous
                    </button>
                    <button type="submit" class="btn btn-wizard">
                        Continue <i class="bi bi-arrow-right"></i>
                    </button>
                </div>
            </form>
        </div>
    </div>
</body>
</html>
'''

# Step 7: Remodeling
remodeling_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Real Estate Investment Analysis</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            min-height: 100vh;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .wizard-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .progress-container {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .question-card {
            background: white;
            border-radius: 15px;
            padding: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .progress-bar {
            height: 12px;
            border-radius: 6px;
            background: linear-gradient(90deg, #667eea, #764ba2);
        }
        .step-indicator {
            display: flex;
            justify-content: space-between;
            margin-top: 15px;
        }
        .step-dot {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 12px;
        }
        .step-dot.completed {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
        .step-dot.current {
            background: #ffc107;
            color: #333;
        }
        .step-dot.pending {
            background: #e9ecef;
            color: #6c757d;
        }
        .question-title {
            color: #333;
            font-weight: 700;
            margin-bottom: 10px;
        }
        .question-subtitle {
            color: #666;
            margin-bottom: 30px;
        }
        .form-control, .form-select {
            border-radius: 10px;
            border: 2px solid #e9ecef;
            padding: 12px 15px;
        }
        .form-control:focus, .form-select:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
        }
        .btn-wizard {
            background: linear-gradient(135deg, #667eea, #764ba2);
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            font-weight: 600;
            color: white;
        }
        .btn-wizard:hover {
            background: linear-gradient(135deg, #5a6fd8, #6a4190);
            color: white;
        }
        .btn-secondary-wizard {
            background: #6c757d;
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            font-weight: 600;
            color: white;
        }
    </style>
</head>
<body>
    <div class="wizard-container">
        <div class="progress-container">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5 class="mb-0">Real Estate Investment Analysis</h5>
                <span class="badge bg-primary">{{ progress }}% Complete</span>
            </div>
            <div class="progress mb-3">
                <div class="progress-bar" style="width: {{ progress }}%"></div>
            </div>
            <div class="step-indicator">
                {% for step in steps %}
                <div class="step-dot {{ step.status }}" title="{{ step.title }}">
                    {{ loop.index }}
                </div>
                {% endfor %}
            </div>
        </div>

        <div class="question-card">
            <h2 class="question-title">Remodeling & Improvements</h2>
            <p class="question-subtitle">Optional: Plan any renovations or improvements</p>

            <form method="POST">
                <div class="mb-4">
                    <label class="form-label fw-bold">Do you plan to remodel?</label>
                    <select class="form-select" name="is_remodeling" onchange="toggleRemodeling()">
                        <option value="no" {{ 'selected' if form_data.get('is_remodeling') != 'yes' else '' }}>No renovations planned</option>
                        <option value="yes" {{ 'selected' if form_data.get('is_remodeling') == 'yes' else '' }}>Yes, I have renovation plans</option>
                    </select>
                </div>

                <div id="remodeling_details" style="{{ 'display: block' if form_data.get('is_remodeling') == 'yes' else 'display: none' }}">
                    <div class="mb-4">
                        <label class="form-label fw-bold">Number of Renovation Projects</label>
                        <select class="form-select" name="num_remodels" onchange="updateRemodelSections()">
                            <option value="1" {{ 'selected' if form_data.get('num_remodels', '1') == '1' else '' }}>1 Project</option>
                            <option value="2" {{ 'selected' if form_data.get('num_remodels') == '2' else '' }}>2 Projects</option>
                            <option value="3" {{ 'selected' if form_data.get('num_remodels') == '3' else '' }}>3 Projects</option>
                        </select>
                    </div>

                    <!-- Remodel Project 1 -->
                    <div id="remodel_1" class="border rounded p-3 mb-3">
                        <h5>Renovation Project 1</h5>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Project Cost</label>
                                <div class="input-group">
                                    <span class="input-group-text">$</span>
                                    <input type="number" class="form-control" name="remodel_cost_1" 
                                           value="{{ form_data.get('remodel_cost_1', '0') }}">
                                </div>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Value Added</label>
                                <div class="input-group">
                                    <span class="input-group-text">$</span>
                                    <input type="number" class="form-control" name="remodel_value_1" 
                                           value="{{ form_data.get('remodel_value_1', '0') }}">
                                </div>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Year of Project</label>
                                <input type="number" class="form-control" name="remodel_year_1" 
                                       value="{{ form_data.get('remodel_year_1', '1') }}" min="1">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Months Without Rent</label>
                                <input type="number" class="form-control" name="remodel_months_1" 
                                       value="{{ form_data.get('remodel_months_1', '0') }}" min="0" max="12">
                            </div>
                        </div>
                    </div>

                    <!-- Remodel Project 2 -->
                    <div id="remodel_2" class="border rounded p-3 mb-3" style="{{ 'display: block' if form_data.get('num_remodels', '1')|int >= 2 else 'display: none' }}">
                        <h5>Renovation Project 2</h5>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Project Cost</label>
                                <div class="input-group">
                                    <span class="input-group-text">$</span>
                                    <input type="number" class="form-control" name="remodel_cost_2" 
                                           value="{{ form_data.get('remodel_cost_2', '0') }}">
                                </div>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Value Added</label>
                                <div class="input-group">
                                    <span class="input-group-text">$</span>
                                    <input type="number" class="form-control" name="remodel_value_2" 
                                           value="{{ form_data.get('remodel_value_2', '0') }}">
                                </div>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Year of Project</label>
                                <input type="number" class="form-control" name="remodel_year_2" 
                                       value="{{ form_data.get('remodel_year_2', '2') }}" min="1">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Months Without Rent</label>
                                <input type="number" class="form-control" name="remodel_months_2" 
                                       value="{{ form_data.get('remodel_months_2', '0') }}" min="0" max="12">
                            </div>
                        </div>
                    </div>

                    <!-- Remodel Project 3 -->
                    <div id="remodel_3" class="border rounded p-3 mb-3" style="{{ 'display: block' if form_data.get('num_remodels', '1')|int >= 3 else 'display: none' }}">
                        <h5>Renovation Project 3</h5>
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Project Cost</label>
                                <div class="input-group">
                                    <span class="input-group-text">$</span>
                                    <input type="number" class="form-control" name="remodel_cost_3" 
                                           value="{{ form_data.get('remodel_cost_3', '0') }}">
                                </div>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Value Added</label>
                                <div class="input-group">
                                    <span class="input-group-text">$</span>
                                    <input type="number" class="form-control" name="remodel_value_3" 
                                           value="{{ form_data.get('remodel_value_3', '0') }}">
                                </div>
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Year of Project</label>
                                <input type="number" class="form-control" name="remodel_year_3" 
                                       value="{{ form_data.get('remodel_year_3', '3') }}" min="1">
                            </div>
                            <div class="col-md-6 mb-3">
                                <label class="form-label">Months Without Rent</label>
                                <input type="number" class="form-control" name="remodel_months_3" 
                                       value="{{ form_data.get('remodel_months_3', '0') }}" min="0" max="12">
                            </div>
                        </div>
                    </div>
                </div>

                <script>
                function toggleRemodeling() {
                    const select = document.querySelector('[name="is_remodeling"]');
                    const details = document.getElementById('remodeling_details');
                    details.style.display = select.value === 'yes' ? 'block' : 'none';
                }

                function updateRemodelSections() {
                    const numRemodels = parseInt(document.querySelector('[name="num_remodels"]').value);
                    for (let i = 1; i <= 3; i++) {
                        const section = document.getElementById('remodel_' + i);
                        section.style.display = i <= numRemodels ? 'block' : 'none';
                    }
                }
                </script>

                <div class="d-flex justify-content-between">
                    <button type="button" class="btn btn-secondary-wizard" onclick="window.location='{{ url_for('wizard_step', step='investment_details') }}'">
                        <i class="bi bi-arrow-left"></i> Previous
                    </button>
                    <button type="submit" class="btn btn-wizard">
                        Generate Analysis <i class="bi bi-chart-bar"></i>
                    </button>
                </div>
            </form>
        </div>
    </div>
</body>
</html>
'''

# Template storage
templates = {
    'base.html': base_template,
    'property_search.html': property_search_template,
    'basic_info.html': basic_info_template,
    'financing.html': financing_template,
    'rental_income.html': rental_income_template,
    'expenses.html': expenses_template,
    'investment_details.html': investment_details_template,
    'remodeling.html': remodeling_template
}


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

    app.run(debug=True, port=5001)
