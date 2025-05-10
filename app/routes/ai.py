from flask import Blueprint, render_template, jsonify, request
from flask_login import current_user, login_required
from datetime import datetime
import os
import json

ai_bp = Blueprint('ai', __name__)

# Demo data
DEMO_CATEGORIES = {
    'Food': 20,
    'Clothing': 15,
    'Health Care': 15,
    'Utilities': 15,
    'Housing Rent': 20,
    'Others': 15
}

DEMO_AI_ADVICE = """จากการวิเคราะห์การใช้จ่ายของคุณ:
1. ค่าใช้จ่ายด้านอาหารอยู่ในเกณฑ์ที่เหมาะสม
2. ควรทบทวนงบประมาณด้านเสื้อผ้า
3. ค่าใช้จ่ายด้านสุขภาพได้รับการจัดการที่ดี
4. ค่าสาธารณูปโภคอยู่ในระดับเฉลี่ยของพื้นที่
5. ค่าเช่าที่พักอาศัยเป็นค่าใช้จ่ายหลัก - ควรวางแผนออมระยะยาวสำหรับการซื้อบ้าน"""

@ai_bp.route('/')
@login_required
def index():
    return render_template('ai.html')

@ai_bp.route('/analysis/overview')
@login_required
def analysis_overview():
    return jsonify({
        'categories': DEMO_CATEGORIES,
        'total_spending': sum(DEMO_CATEGORIES.values())
    })

@ai_bp.route('/analysis/categories')
@login_required
def analysis_categories():
    return jsonify(DEMO_CATEGORIES)

@ai_bp.route('/analysis/ai')
@login_required
def ai_recommendations():
    return jsonify({'analysis': DEMO_AI_ADVICE})

@ai_bp.route('/save_financial_profile', methods=['POST'])
@login_required
def save_financial_profile():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Prepare profile data
        profile = {
            'timestamp': datetime.now().isoformat(),
            'income': data.get('income', 0),
            'expenses': data.get('expenses', 0),
            'debt': data.get('debt', 0),
            'savings_goal': data.get('savings_goal', 0)
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
