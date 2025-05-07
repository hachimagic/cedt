from flask import Blueprint, render_template, jsonify
from flask_login import current_user
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
