from flask import Blueprint, render_template, jsonify, request
from flask_login import current_user, login_required
from datetime import datetime
import os
import json
import requests
import re

# OpenRouter configuration
OPENROUTER_API_KEY = "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"
OPENROUTER_MODEL_NAME = "deepseek/deepseek-chat-v3-0324"

ai_bp = Blueprint('ai', __name__)

from ..utils.pdf_parser import parse_transaction_line
from collections import defaultdict
import os

@ai_bp.route('/')
def index():
    # Check if user is authenticated and has a profile
    profile = None
    if current_user.is_authenticated:
        profile_path = f"user_data/user_{current_user.id}_financial_profile.json"
        if os.path.exists(profile_path):
            try:
                with open(profile_path) as f:
                    profile = json.load(f)
            except (IOError, json.JSONDecodeError):
                pass
    return render_template('ai.html', profile=profile)

import PyPDF2

def load_transactions():
    transactions = []
    with open('transcript.pdf', 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text = page.extract_text()
            for line in text.split('\n'):
                # Parse transaction using the generic parser
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
        print(f"\n[{datetime.now()}] Received request to /thai_advisor from user {current_user.id}")
        
        # First verify that user is still authenticated
        if not current_user.is_authenticated:
            print(f"[{datetime.now()}] User {current_user.id} session expired")
            return jsonify({
                'success': False,
                'message': 'Session expired',
                'data': None
            }), 401

        data = request.get_json()
        if not data:
            print(f"[{datetime.now()}] No data provided in request")
            return jsonify({
                'success': False,
                'message': 'No data provided',
                'data': None
            }), 400

        question = data.get('question')
        if not question:
            print(f"[{datetime.now()}] No question provided in request")
            return jsonify({
                'success': False,
                'message': 'No question provided',
                'data': None
            }), 400

        # Get user profile from file
        profile_path = f"user_data/user_{current_user.id}_financial_profile.json"
        if not os.path.exists(profile_path):
            print(f"[{datetime.now()}] Profile not found for user {current_user.id}")
            return jsonify({
                'success': False,
                'message': 'Please save your financial profile first',
                'data': None
            }), 400

        # Get user's transaction data
        transactions = []
        transaction_summary = {"income": 0, "expenses": 0, "categories": {}}
        
        # List all transaction files for the user
        transaction_files = [f for f in os.listdir('user_transactions') 
                           if f.startswith(f"{current_user.id}_")]
        
        print(f"[{datetime.now()}] Found {len(transaction_files)} transaction files for user {current_user.id}")
        
        # Read each transaction file
        for file_name in transaction_files:
            file_path = os.path.join('user_transactions', file_name)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    import csv
                    reader = csv.DictReader(f)
                    for row in reader:
                        transactions.append(row)
                        # Update summary
                        amount = float(row.get('amount', 0))
                        if row.get('type') == 'income':
                            transaction_summary["income"] += amount
                        else:
                            transaction_summary["expenses"] += amount
                            category = row.get('category', 'Other')
                            transaction_summary["categories"][category] = \
                                transaction_summary["categories"].get(category, 0) + amount
            except Exception as e:
                print(f"[{datetime.now()}] Error reading transaction file {file_path}: {str(e)}")

        # Verify we can read the profile
        try:
            with open(profile_path) as f:
                profile = json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            print(f"[{datetime.now()}] Error reading profile: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Error reading profile data',
                'data': None
            }), 500

        # Format prompt with transaction data
        prompt = f"""ระบบ: คุณคือที่ปรึกษาทางการเงิน พูดภาษาไทยเท่านั้น ให้คำแนะนำเฉพาะบุคคล

ข้อมูลผู้ใช้:
- รายได้: ฿{profile.get('income', 0)}
- ค่าใช้จ่าย: ฿{profile.get('expenses', 0)}
- หนี้: ฿{profile.get('debt', 0)}
- เป้าหมายการออม: ฿{profile.get('savings_goal', 0)}"""

        for debt in profile.get('debts', []):
            prompt += f"\n  - {debt['type']} ฿{debt['amount']} ดอกเบี้ย {debt['interest']}%"

        prompt += f"\n- พฤติกรรมการใช้เงินสด: {profile.get('cash_behavior', 'ไม่ระบุ')}"
        
        # Add transaction summary to prompt
        prompt += "\n\nข้อมูลธุรกรรม:"
        prompt += f"\n- รายรับรวม: ฿{transaction_summary['income']:,.2f}"
        prompt += f"\n- รายจ่ายรวม: ฿{transaction_summary['expenses']:,.2f}"
        prompt += "\n- รายจ่ายตามหมวดหมู่:"
        for category, amount in transaction_summary["categories"].items():
            percentage = (amount / transaction_summary["expenses"] * 100) if transaction_summary["expenses"] > 0 else 0
            prompt += f"\n  - {category}: ฿{amount:,.2f} ({percentage:.1f}%)"

        prompt += f"\n\nคำถาม: {question}"

        # Log the formatted prompt
        print(f"[{datetime.now()}] Formatted prompt for user {current_user.id}:")
        print(prompt)

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json; charset=utf-8",
            "HTTP-Referer": "https://your-app-url.com",
            "X-Title": "Financial Advisor"
        }

        request_data = {
            "model": OPENROUTER_MODEL_NAME,
            "messages": [
                {"role": "system", "content": "คุณเป็นที่ปรึกษาทางการเงิน ตอบสั้นๆเป็นภาษาไทย"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 300
        }

        print(f"[{datetime.now()}] Sending request to OpenRouter API...")
        print("Request payload:", json.dumps(request_data, ensure_ascii=False, indent=2))

        def parse_response(response):
            try:
                response_data = response.json()
                if response.status_code != 200:
                    error_message = response_data.get('error', {}).get('message', 'Unknown error')
                    return None, f"API Error: {error_message}"

                if 'choices' in response_data and response_data['choices']:
                    message = response_data['choices'][0].get('message', {})
                    if message and 'content' in message:
                        return message['content'].strip(), None

                return None, 'Invalid response format from API'
            except (ValueError, KeyError) as e:
                return None, f"Error parsing response: {str(e)}"

        # First attempt with full prompt
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=request_data,
            timeout=30
        )

        content, error = parse_response(response)

        # Retry with simplified prompt if necessary
        if not content or len(content) < 10:
            print("First attempt gave short/empty response, trying with simplified prompt...")
            request_data["messages"] = [
                {"role": "system", "content": "ตอบคำถามสั้นๆเป็นภาษาไทย"},
                {"role": "user", "content": question}
            ]
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=request_data,
                timeout=30
            )
            content, error = parse_response(response)

        if error:
            return jsonify({
                'success': False,
                'message': error,
                'data': None
            }), 500

        # Clean up content
        content = ''.join(char for char in content if ord(char) >= 32 and ord(char) != 0x200B)  # Remove zero-width space
        content = re.sub(r'(?<=[\u0E00-\u0E7F])\s+(?=[\u0E00-\u0E7F])', '', content)  # Remove spaces between Thai characters
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)  # Remove bold markers
        content = re.sub(r' +', ' ', content)  # Multiple spaces to single space
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)  # Multiple newlines to double newline
        content = content.strip()
        content = re.sub(r'([ก-๙])\s+(?=[ก-๙])', r'\1', content)  # Final Thai text cleanup

        if not content:
            return jsonify({
                'success': False,
                'message': 'Empty response after cleanup',
                'data': None
            }), 500

        return jsonify({
            'success': True,
            'message': 'Success',
            'data': {
                'response': content
            }
        })

    except Exception as e:
        print(f"Error in thai_advisor: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}',
            'data': None
        }), 500
