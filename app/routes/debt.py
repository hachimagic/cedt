from flask import Blueprint, render_template
from flask_login import login_required

debt_bp = Blueprint('debt', __name__)

@debt_bp.route('/')
@login_required
def index():
    return render_template('debt.html')
