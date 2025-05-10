from flask import Blueprint, render_template, jsonify, request, redirect, session, flash
from flask_login import current_user, login_required
from flask_wtf.csrf import generate_csrf
from datetime import datetime
from ..models.transaction import Transaction

main_bp = Blueprint('main', __name__)

# Temporary categories (same as in expenses.py)
categories = [
    {'id': 1, 'name': 'Food', 'description': 'Groceries and dining out'},
    {'id': 2, 'name': 'Transport', 'description': 'Public transport and fuel'},
    {'id': 3, 'name': 'Utilities', 'description': 'Electricity, water, internet'},
]

@main_bp.route('/get_csrf_token')
def get_csrf_token():
    token = generate_csrf()
    return jsonify({'token': token})

@main_bp.route('/')
@login_required
def index():
    transactions = Transaction.get_user_transactions(current_user.id)
    # Format datetime objects for JSON serialization
    for trans in transactions:
        if isinstance(trans.date_time, datetime):
            trans.date_time = trans.date_time.strftime('%d/%m/%y %H:%M')
    
    return render_template('index.html', 
                         transactions=transactions,
                         categories=categories,
                         income=25200,
                         expense=27150,
                         balance=5200)

@main_bp.route('/budget')
@login_required
def budget_planning():
    # Initialize session values if they don't exist
    if 'savings_goal' not in session:
        session['savings_goal'] = 0
    if 'current_savings' not in session:
        session['current_savings'] = 0
    
    remaining = max(0, session['savings_goal'] - session['current_savings'])
    progress = (session['current_savings'] / session['savings_goal'] * 100) if session['savings_goal'] > 0 else 0
    
    return render_template('budget_planning.html',
                         goal=session['savings_goal'],
                         current=session['current_savings'],
                         remaining=remaining,
                         progress=progress)

@main_bp.route('/compare')
@login_required
def compare_results():
    return render_template("price_compare.html")

@main_bp.route('/price-compare')
@login_required
def price_compare():
    # Example product data
    uniqlo_price = 500
    zara_price = 750
    
    # Calculate percentage change
    percent_change = ((zara_price - uniqlo_price) / uniqlo_price) * 100
    
    # Example categories data
    categories = [
        {'name': 'Shirts', 'spend': 1200, 'percent': 60},
        {'name': 'Shoes', 'spend': 800, 'percent': 40}
    ]
    
    return render_template('compare_result.html',
                         uniqlo_price=uniqlo_price,
                         zara_price=zara_price,
                         percent_change=percent_change,
                         categories=categories)

@main_bp.route('/side-hustle')
@login_required
def side_hustle():
    return render_template('side_hustle.html')

@main_bp.route('/budget/update', methods=['POST'])
@login_required
def update_budget():
    amount = float(request.form['amount'])
    action = request.form['action']
    
    if action == 'deposit':
        session['current_savings'] += amount
    elif action == 'withdraw':
        session['current_savings'] = max(0, session['current_savings'] - amount)
    elif action == 'set_goal':
        session['savings_goal'] = amount
    
    return redirect('/budget')
