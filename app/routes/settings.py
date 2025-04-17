from flask import Blueprint, render_template
from flask_login import login_required

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/')
@login_required
def index():
    return render_template('settings.html')
