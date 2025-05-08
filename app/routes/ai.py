from flask import Blueprint, render_template, jsonify, request
from flask_login import current_user, login_required
from datetime import datetime
import os
import json

ai_bp = Blueprint('ai', __name__)

from app.utils.pdf_parser import parse_transaction_line
from collections import defaultdict
import os

@ai_bp.route('/')
def index():
    return render_template('ai.html')

import PyPDF2

def load_transactions():
    transactions = []
    with open('transcript.pdf', 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text = page.extract_text()
            for line in text.split('\n'):
                # Try parsing as Thai transaction first
                transaction = parse_thai_transaction(line)
                if not transaction:
                    # Fallback to generic parsero
                    transaction = parse_transaction_line(line)
                if transaction:
                    transactions.append(transaction)
    return transactions

def analyze_transactions(transactions):
    categories = defaultdict(float)
    total_income = 0
    total_expenses = 0
    
    for t in transactions:
        if t['deposit']:
            amount = float(t['deposit'].replace(',', ''))
            total_income += amount
        if t['withdrawal']:
            amount = float(t['withdrawal'].replace(',', ''))
            total_expenses += amount
        
        # Use the automatically assigned category
        if 'category' in t:
            categories[t['category']] += amount
    
    return {
        'categories': dict(categories),
        'total_income': total_income,
        'total_expenses': total_expenses
    }

def categorize_transaction(transaction):
    details = transaction['details'].lower()
    if 'food' in details or 'restaurant' in details:
        return 'Food'
    elif 'clothing' in details or 'apparel' in details:
        return 'Clothing'
    elif 'health' in details or 'medical' in details:
        return 'Health Care'
    elif 'utility' in details or 'electric' in details or 'water' in details:
        return 'Utilities'
    elif 'rent' in details or 'housing' in details:
        return 'Housing Rent'
    else:
        return 'Others'

def generate_ai_advice(analysis):
    advice = []
    total_expenses = analysis['total_expenses']
    categories = analysis['categories']
    
    if total_expenses > 0:
        for category, amount in categories.items():
            percentage = (amount / total_expenses) * 100
            if percentage > 30:
                advice.append(f"Your {category} expenses are high ({percentage:.1f}% of total expenses). Consider reducing this spending.")
            elif percentage < 10:
                advice.append(f"Your {category} expenses are low ({percentage:.1f}% of total expenses). This is well managed.")
            else:
                advice.append(f"Your {category} expenses are within a reasonable range ({percentage:.1f}% of total expenses).")
    
    if not advice:
        advice.append("No significant spending patterns detected. Your expenses appear balanced.")
    
    return "\n".join(advice)

@ai_bp.route('/analysis/overview')
def analysis_overview():
    from app.models.transaction import Transaction
    
    # Initialize category totals
    categories = defaultdict(float)
    
    # Check if user is authenticated
    if current_user.is_authenticated:
        # Get user's transactions
        transactions = Transaction.get_user_transactions(current_user.id)
        
        # Analyze transactions
        for t in transactions:
            # Ensure transaction is categorized
            if not t.category:
                t.auto_categorize()
            
            # Process withdrawals (expenses)
            if t.withdrawal:
                try:
                    withdrawal = float(t.withdrawal.replace(',', ''))
                    categories[t.category] += withdrawal
                except ValueError:
                    pass
    
    # Convert to format suitable for chart
    chart_data = dict(categories)
    
    return jsonify({
        'categories': chart_data
    })

@ai_bp.route('/analysis/categories')
def analysis_categories():
    transactions = load_transactions()
    analysis = analyze_transactions(transactions)
    return jsonify(analysis['categories'])

@ai_bp.route('/analysis/ai')
def ai_recommendations():
    transactions = load_transactions()
    analysis = analyze_transactions(transactions)
    advice = generate_ai_advice(analysis)
    return jsonify({'analysis': advice})

@ai_bp.route('/save_financial_profile', methods=['POST'])
@login_required
def save_financial_profile():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Prepare profile data including categories
        profile = {
            'timestamp': datetime.now().isoformat(),
            'income': data.get('income', 0),
            'expenses': data.get('expenses', 0),
            'debt': data.get('debt', 0),
            'savings_goal': data.get('savings_goal', 0),
            'categories': data.get('categories', {})
        }

        # Ensure user_data directory exists
        os.makedirs('user_data', exist_ok=True)

        # Save to user-specific file
        filename = f"user_data/user_{current_user.id}_financial_profile.json"
        with open(filename, 'w') as f:
            json.dump(profile, f, indent=2)

        return jsonify({'message': 'Financial profile saved successfully'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/thai_advisor', methods=['POST'])
@login_required
def thai_advisor():
    try:
        data = request.get_json()
        question = data.get('question')
        if not question:
            return jsonify({'error': 'No question provided'}), 400
        
        # Get user profile
        profile = current_user.profile
        if not profile:
            return jsonify({'error': 'User profile not found'}), 400
        
        # Format prompt
        prompt = f"""ระบบ: คุณคือที่ปรึกษาทางการเงิน พูดภาษาไทยเท่านั้น ให้คำแนะนำเฉพาะบุคคล

ข้อมูลผู้ใช้:
- รายได้: ฿{profile.get('salary', 0)}
- อาชีพ: {profile.get('occupation', 'ไม่ระบุ')}
- หนี้:"""
        
        for debt in profile.get('debts', []):
            prompt += f"\n  - {debt['type']} ฿{debt['amount']} ดอกเบี้ย {debt['interest']}%"
        
        prompt += f"\n- พฤติกรรมการใช้เงินสด: {profile.get('cash_behavior', 'ไม่ระบุ')}\n\n"
        prompt += f"คำถาม: {question}"
        
        # Call AI API (using OpenAI as default)
        import openai
        openai.api_key = os.getenv('OPENAI_API_KEY')
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful financial advisor that speaks only Thai."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return jsonify({
            'response': response['choices'][0]['message']['content']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
