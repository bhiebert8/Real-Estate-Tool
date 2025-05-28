# HTML_TEMPLATES.py - Complete Fixed Version

# Base template with progress bar
base_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Su Casa Edge Investment Analysis</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
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
/* Replace your existing .brand-header CSS with this Golden Elegance version */
.brand-header {
    font-family: 'Brush Script MT', 'Lucida Handwriting', 'Comic Sans MS', cursive;
    font-size: 3rem;
    color: #FFD700;
    letter-spacing: 2px;
    text-align: center;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    margin-bottom: 1.2rem;
}

/* Optional: Add a subtle hover effect for extra luxury feel */
.brand-header:hover {
    color: #FFF700;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.4), 0 0 15px rgba(255,215,0,0.4);
    transition: all 0.3s ease;
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
    <div class="brand-header">Su Casa Edge</div>
    <div class="wizard-container">
        <div class="progress-container">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5 class="mb-0">Su Casa Edge Investment Analysis</h5>
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
    <title>Su Casa Edge Investment Analysis</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
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
/* Replace your existing .brand-header CSS with this Golden Elegance version */
.brand-header {
    font-family: 'Brush Script MT', 'Lucida Handwriting', 'Comic Sans MS', cursive;
    font-size: 3rem;
    color: #FFD700;
    letter-spacing: 2px;
    text-align: center;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    margin-bottom: 1.2rem;
}

/* Optional: Add a subtle hover effect for extra luxury feel */
.brand-header:hover {
    color: #FFF700;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.4), 0 0 15px rgba(255,215,0,0.4);
    transition: all 0.3s ease;
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
    <div class="brand-header">Su Casa Edge</div>
    <div class="wizard-container">
        <div class="progress-container">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5 class="mb-0">Su Casa Edge Investment Analysis</h5>
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
    <title>Su Casa Edge Investment Analysis</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
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
/* Replace your existing .brand-header CSS with this Golden Elegance version */
.brand-header {
    font-family: 'Brush Script MT', 'Lucida Handwriting', 'Comic Sans MS', cursive;
    font-size: 3rem;
    color: #FFD700;
    letter-spacing: 2px;
    text-align: center;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    margin-bottom: 1.2rem;
}

/* Optional: Add a subtle hover effect for extra luxury feel */
.brand-header:hover {
    color: #FFF700;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.4), 0 0 15px rgba(255,215,0,0.4);
    transition: all 0.3s ease;
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
    <div class="brand-header">Su Casa Edge</div>
    <div class="wizard-container">
        <div class="progress-container">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5 class="mb-0">Su Casa Edge Investment Analysis</h5>
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
                    <small class="text-success">💡 Rentcast suggests: ${{ "{:,.0f}".format(suggested_values.property_value) }}</small>
                    {% endif %}
                </div>

                <div class="mb-4">
                    <label class="form-label fw-bold">Closing Costs</label>
                    <div class="input-group">
                        <span class="input-group-text">$</span>
                        <input type="number" class="form-control" name="closing_costs" 
                               value="{{ form_data.get('closing_costs', '') }}" 
                               placeholder="10000" required>
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
    <title>Su Casa Edge Investment Analysis</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
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
/* Replace your existing .brand-header CSS with this Golden Elegance version */
.brand-header {
    font-family: 'Brush Script MT', 'Lucida Handwriting', 'Comic Sans MS', cursive;
    font-size: 3rem;
    color: #FFD700;
    letter-spacing: 2px;
    text-align: center;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    margin-bottom: 1.2rem;
}

/* Optional: Add a subtle hover effect for extra luxury feel */
.brand-header:hover {
    color: #FFF700;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.4), 0 0 15px rgba(255,215,0,0.4);
    transition: all 0.3s ease;
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
    <div class="brand-header">Su Casa Edge</div>
    <div class="wizard-container">
        <div class="progress-container">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5 class="mb-0">Su Casa Edge Investment Analysis</h5>
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
    <title>Su Casa Edge Investment Analysis</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
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
/* Replace your existing .brand-header CSS with this Golden Elegance version */
.brand-header {
    font-family: 'Brush Script MT', 'Lucida Handwriting', 'Comic Sans MS', cursive;
    font-size: 3rem;
    color: #FFD700;
    letter-spacing: 2px;
    text-align: center;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    margin-bottom: 1.2rem;
}

/* Optional: Add a subtle hover effect for extra luxury feel */
.brand-header:hover {
    color: #FFF700;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.4), 0 0 15px rgba(255,215,0,0.4);
    transition: all 0.3s ease;
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
    <div class="brand-header">Su Casa Edge</div>
    <div class="wizard-container">
        <div class="progress-container">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5 class="mb-0">Su Casa Edge Investment Analysis</h5>
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
    <title>Su Casa Edge Investment Analysis</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
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
/* Replace your existing .brand-header CSS with this Golden Elegance version */
.brand-header {
    font-family: 'Brush Script MT', 'Lucida Handwriting', 'Comic Sans MS', cursive;
    font-size: 3rem;
    color: #FFD700;
    letter-spacing: 2px;
    text-align: center;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    margin-bottom: 1.2rem;
}

/* Optional: Add a subtle hover effect for extra luxury feel */
.brand-header:hover {
    color: #FFF700;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.4), 0 0 15px rgba(255,215,0,0.4);
    transition: all 0.3s ease;
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
    <div class="brand-header">Su Casa Edge</div>
    <div class="wizard-container">
        <div class="progress-container">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5 class="mb-0">Su Casa Edge Investment Analysis</h5>
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
    <title>Su Casa Edge Investment Analysis</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
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
/* Replace your existing .brand-header CSS with this Golden Elegance version */
.brand-header {
    font-family: 'Brush Script MT', 'Lucida Handwriting', 'Comic Sans MS', cursive;
    font-size: 3rem;
    color: #FFD700;
    letter-spacing: 2px;
    text-align: center;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    margin-bottom: 1.2rem;
}

/* Optional: Add a subtle hover effect for extra luxury feel */
.brand-header:hover {
    color: #FFF700;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.4), 0 0 15px rgba(255,215,0,0.4);
    transition: all 0.3s ease;
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
    <div class="brand-header">Su Casa Edge</div>
    <div class="wizard-container">
        <div class="progress-container">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5 class="mb-0">Su Casa Edge Investment Analysis</h5>
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
    <title>Su Casa Edge Investment Analysis</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
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
/* Replace your existing .brand-header CSS with this Golden Elegance version */
.brand-header {
    font-family: 'Brush Script MT', 'Lucida Handwriting', 'Comic Sans MS', cursive;
    font-size: 3rem;
    color: #FFD700;
    letter-spacing: 2px;
    text-align: center;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    margin-bottom: 1.2rem;
}

/* Optional: Add a subtle hover effect for extra luxury feel */
.brand-header:hover {
    color: #FFF700;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.4), 0 0 15px rgba(255,215,0,0.4);
    transition: all 0.3s ease;
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
    <div class="brand-header">Su Casa Edge</div>
    <div class="wizard-container">
        <div class="progress-container">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5 class="mb-0">Su Casa Edge Investment Analysis</h5>
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

# Results HTML template
results_html = '''
<!DOCTYPE html>
<html>
<head>
    <title>Investment Analysis Results</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
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
        <a class="btn btn-outline-primary btn-lg" href="{{ url_for('download_excel') }}"><i class="bi bi-download"></i> Download Excel File of Analysis</a>
        <a class="btn btn-outline-danger btn-lg" href="{{ url_for('download_pdf') }}"><i class="bi bi-file-pdf"></i> Download PDF Summary</a>
    </div>
    <div class="text-center my-4">
        <a href="{{ url_for('index') }}" class="btn btn-link"><i class="bi bi-arrow-left"></i> Back to Input Form</a>
    </div>
</div>
</body>
</html>
'''

# Refinance results HTML template
refinance_results_html = '''
<!DOCTYPE html>
<html>
<head>
    <title>Refinance Simulation Results</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
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
        <a class="btn btn-outline-primary btn-lg" href="{{ url_for('download_excel') }}"><i class="bi bi-download"></i> Download Excel File of Analysis</a>
        <a class="btn btn-outline-danger btn-lg" href="{{ url_for('download_pdf') }}"><i class="bi bi-file-pdf"></i> Download PDF Summary</a>
    </div>
    <div class="text-center my-4">
        <a href="{{ url_for('index') }}" class="btn btn-link"><i class="bi bi-arrow-left"></i> Back to Input Form</a>
    </div>
</div>
</body>
</html>
'''