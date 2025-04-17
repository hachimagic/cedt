from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from app.services.analysis_service import AnalysisService

ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/')
@login_required
def index():
    return render_template('ai.html')

@ai_bp.route('/analysis/overview')
@login_required
def analysis_overview():
    monthly_spending = AnalysisService.get_monthly_spending(current_user.id)
    top_categories = AnalysisService.get_top_categories(current_user.id)
    savings = AnalysisService.get_savings_opportunities(current_user.id)
    
    return jsonify({
        'monthly_spending': monthly_spending,
        'top_categories': top_categories,
        'savings_opportunities': savings
    })

@ai_bp.route('/analysis/categories')
@login_required
def analysis_categories():
    categories = AnalysisService.get_top_categories(current_user.id)
    return jsonify(categories)

@ai_bp.route('/analysis/trends')
@login_required
def analysis_trends():
    trends = AnalysisService.get_monthly_spending(current_user.id)
    return jsonify(trends)

@ai_bp.route('/analysis/savings')
@login_required
def analysis_savings():
    savings = AnalysisService.get_savings_opportunities(current_user.id)
    return jsonify(savings)

@ai_bp.route('/analysis/ai')
@login_required
def ai_recommendations():
    analysis = AnalysisService.get_ai_analysis(current_user.id)
    return jsonify({'analysis': analysis})
