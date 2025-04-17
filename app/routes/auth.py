from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, current_user
from ..models.user import User
from .. import login_manager

auth_bp = Blueprint('auth', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.get_by_username(username)
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('expenses.index'))
        flash('Invalid username or password')
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if User.get_by_username(username):
            flash('Username already exists')
            return redirect(url_for('auth.register'))
        
        if any(u.email == email for u in User.get_all_users()):
            flash('Email already exists')
            return redirect(url_for('auth.register'))
        
        new_user = User.create_user(username, email, password)
        login_user(new_user)
        return redirect(url_for('expenses.index'))
    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
