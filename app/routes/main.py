from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from flask_login import current_user, login_required
from flask_wtf.csrf import generate_csrf
from datetime import datetime
from ..models.transaction import Transaction
from ..models.user import User

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
def index():
    transactions = []
    if current_user.is_authenticated:
        # Call the correct static method (pluralized)
        transactions = Transaction.get_user_transactions(current_user.id)

        # Format datetime for rendering, but preserve datetime object if needed
        for trans in transactions:
            if isinstance(trans.date_time, datetime):
                trans.formatted_date_time = trans.date_time.strftime('%d/%m/%y %H:%M')
            else:
                trans.formatted_date_time = trans.date_time  # Already formatted

    return render_template(
        'index.html', 
        transactions=transactions,
        categories=categories
    )

@main_bp.route('/user/background', methods=['GET', 'POST'])
@login_required
def user_background():
    if request.method == 'POST':
        # Get form data
        salary = request.form.get('salary')
        occupation = request.form.get('occupation')
        debt_types = request.form.getlist('debt_type[]')
        debt_amounts = request.form.getlist('debt_amount[]')
        debt_interests = request.form.getlist('debt_interest[]')
        cash_behavior = request.form.get('cash_behavior')
        
        # Process debts into list of dicts
        debts = []
        for i in range(len(debt_types)):
            debts.append({
                'type': debt_types[i],
                'amount': float(debt_amounts[i]),
                'interest': float(debt_interests[i])
            })
        
        # Save to user profile
        current_user.profile = {
            'salary': float(salary),
            'occupation': occupation,
            'debts': debts,
            'cash_behavior': cash_behavior
        }
        current_user.save()
        
        return redirect(url_for('ai.overview'))
    
    return render_template('user_background.html')

def get_user_profile(user_id):
    user = User.query.get(user_id)
    if user and user.profile:
        return user.profile
    return None
