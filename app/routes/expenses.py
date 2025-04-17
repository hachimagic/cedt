from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, jsonify
from flask_login import login_required, current_user
import os
import uuid
import pdfplumber
import traceback
from datetime import datetime
from ..models.transaction import Transaction
from ..utils.pdf_parser import parse_transaction_line

# Temporary in-memory categories
categories = [
    {'id': 1, 'name': 'Mortgage/Rent', 'description': 'Housing payments'},
    {'id': 2, 'name': 'Credit Card', 'description': 'Credit card payments'},
    {'id': 3, 'name': 'Food/Groceries', 'description': 'Groceries and dining out'},
    {'id': 4, 'name': 'Utilities', 'description': 'Electricity, water, internet'},
    {'id': 5, 'name': 'Transportation', 'description': 'Public transport and fuel'},
    {'id': 6, 'name': 'Entertainment', 'description': 'Movies, events, hobbies'},
    {'id': 7, 'name': 'Healthcare', 'description': 'Medical expenses'},
    {'id': 8, 'name': 'Insurance', 'description': 'Insurance payments'},
    {'id': 9, 'name': 'Savings', 'description': 'Personal savings'},
    {'id': 10, 'name': 'Investments', 'description': 'Stock market and other investments'},
    {'id': 11, 'name': 'Education', 'description': 'School and learning expenses'},
    {'id': 12, 'name': 'Clothing', 'description': 'Clothes and accessories'},
    {'id': 13, 'name': 'Miscellaneous', 'description': 'Other expenses'},
]

expenses_bp = Blueprint('expenses', __name__)

@expenses_bp.route('/')
@login_required
def index():
    transactions = Transaction.get_user_transactions(current_user.id)
    
    # Calculate totals
    total_deposits = sum(float(t.deposit.replace(',', '')) if t.deposit else 0 for t in transactions)
    total_withdrawals = sum(float(t.withdrawal.replace(',', '')) if t.withdrawal else 0 for t in transactions)
    current_balance = float(transactions[-1].balance.replace(',', '')) if transactions else 0
    
    return render_template('expenses.html', 
                         transactions=transactions,
                         categories=categories,
                         total_deposits=total_deposits,
                         total_withdrawals=total_withdrawals,
                         current_balance=current_balance)

@expenses_bp.route('/preview_transcript', methods=['POST'])
@login_required
def preview_transcript():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('expenses.index'))

    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('expenses.index'))

    if file and file.filename.lower().endswith('.pdf'):
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        parsed_transactions = []
        failed_transactions = []
        non_transactions = []
        
        try:
            import chardet
            
            # First detect the file encoding
            with open(filepath, 'rb') as f:
                raw_data = f.read()
                encoding = chardet.detect(raw_data)['encoding']
                print(f"Detected encoding: {encoding}")
            
            # Try multiple extraction methods
            page_text = None
            methods = [
                ('pdfplumber', lambda: pdfplumber.open(filepath)),
                ('PyMuPDF', lambda: fitz.open(filepath))
            ]
            
            for method_name, open_func in methods:
                try:
                    if method_name == 'pdfplumber':
                        with open_func() as pdf:
                            for page in pdf.pages:
                                page_text = page.extract_text(x_tolerance=1, y_tolerance=1, encoding=encoding)
                                if page_text:
                                    break
                    else:
                        doc = open_func()
                        page_text = ""
                        for page in doc:
                            page_text += page.get_text()
                    print(f"Successfully extracted text using {method_name}")
                    break
                except Exception as e:
                    print(f"Failed to extract text using {method_name}: {str(e)}")
                    page_text = None
                
            if page_text is None:
                print("All text extraction methods failed")
                
            if page_text:
                page_lines = page_text.split('\n')
                for line in page_lines:
                    try:
                        parsed = parse_transaction_line(line)
                        if parsed:
                            print(f"Successfully parsed line: {line}")
                            print(f"Parsed data: {parsed}")
                            # Ensure all required fields are present
                            parsed['user_id'] = current_user.id
                            parsed['explanation'] = ''
                            parsed['category_id'] = None
                            parsed['transaction_type'] = parsed.get('transaction', '')
                            parsed['branch'] = parsed.get('branch', '')
                            parsed['extra'] = parsed.get('extra', '')
                            parsed['line_text'] = line
                            parsed_transactions.append(parsed)
                            print(f"Added transaction with ID: {parsed.get('id')}")
                        else:
                            print(f"Not a transaction line: {line}")
                            non_transactions.append(line.strip())
                    except Exception as e:
                        print(f"Error parsing line: {line}")
                        print(f"Error details: {str(e)}")
                        failed_transactions.append({
                            'line': line,
                            'error': str(e)
                        })
        except Exception as e:
            print(f"Error processing PDF: {str(e)}")
            traceback.print_exc()
            flash(f'Error processing PDF: {str(e)}')
            return redirect(url_for('expenses.index'))
        finally:
            # Clean up the uploaded file
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    print(f"Cleaned up file: {filepath}")
            except Exception as e:
                print(f"Error cleaning up file: {str(e)}")

        return render_template('expenses.html', 
                             parsed_transactions=parsed_transactions,
                             failed_transactions=failed_transactions,
                             non_transactions=non_transactions,
                             categories=categories,
                             preview_mode=True,
                             total_deposits=0,
                             total_withdrawals=0,
                             current_balance=0)

    flash('Invalid file type. Please upload a PDF.')
    return redirect(url_for('expenses.index'))

@expenses_bp.route('/save_transcript', methods=['POST'])
@login_required
def save_transcript():
    try:
        print("\nStarting save_transcript operation...")
        
        if not request.is_json:
            print("Error: Request is not JSON")
            return jsonify({'error': 'Request must be JSON'}), 400
            
        parsed_transactions = request.json.get('transactions', [])
        print(f"Received {len(parsed_transactions)} transactions to save")
        
        if not parsed_transactions:
            print("Error: No transactions provided")
            return jsonify({'error': 'No transactions provided'}), 400
            
        saved_transactions = []
        failed_transactions = []
        
        # Get existing transactions
        print("Fetching existing transactions...")
        existing_transactions = Transaction.get_user_transactions(current_user.id)
        print(f"Found {len(existing_transactions)} existing transactions")
        
        # Convert existing transactions to dict format
        existing_dicts = {t.id: t.__dict__ for t in existing_transactions}
        print(f"Converted {len(existing_dicts)} transactions to dict format")
        
        print("\nProcessing received transactions:")
        
        # Process transactions
        for i, parsed in enumerate(parsed_transactions, 1):
            try:
                print(f"\nProcessing transaction {i}/{len(parsed_transactions)}:")
                print(f"Transaction data: {parsed}")
                # For preview transactions or transactions with temporary IDs
                if 'id' not in parsed or not parsed['id'] or str(parsed.get('id', '')).startswith('temp_'):
                    print("Creating new transaction with generated ID")
                    new_transaction = Transaction(
                        id=str(uuid.uuid4()),
                        user_id=current_user.id,
                        date_time=parsed.get('date_time', ''),
                        transaction_type=parsed.get('transaction', ''),
                        details=parsed.get('details', ''),
                        withdrawal=parsed.get('withdrawal', ''),
                        deposit=parsed.get('deposit', ''),
                        balance=parsed.get('balance', ''),
                        explanation=parsed.get('explanation', ''),
                        category_id=int(parsed['category_id']) if parsed.get('category_id') else None,
                        branch='',
                        extra='',
                        line_text=parsed.get('line_text', '')
                    )
                    saved_transactions.append(new_transaction)
                else:
                    # For existing transactions, update them
                    transaction = next((t for t in existing_transactions if t.id == parsed['id']), None)
                    if transaction:
                        transaction.explanation = parsed.get('explanation', '')
                        category_id = parsed.get('category_id')
                        transaction.category_id = int(category_id) if category_id else None
                        transaction.updated_at = datetime.now()
                        saved_transactions.append(transaction)
            except Exception as e:
                error_msg = f'Error updating transaction: {str(e)}'
                print(f"Failed transaction: {parsed} - {error_msg}")
                failed_transactions.append({
                    'line': parsed.get('line_text', 'Unknown'),
                    'error': error_msg
                })

        print("\nPreparing to save transactions...")
        print(f"Existing transactions: {len(existing_transactions)}")
        print(f"New/Updated transactions: {len(saved_transactions)}")
        
        # For preview transactions, we want to save them all
        print(f"Saving {len(saved_transactions)} new transactions")
        
        # Add user_id to new transactions
        for transaction in saved_transactions:
            transaction.user_id = current_user.id
            
        print("\nSaving transactions to file...")
        Transaction.save_user_transactions(current_user.id, saved_transactions)
        print("Transactions saved successfully")

        if failed_transactions:
            return jsonify({
                'message': f'Successfully imported {len(saved_transactions)} transactions. Failed to import {len(failed_transactions)} transactions.',
                'failed_transactions': failed_transactions
            }), 200
        else:
            return jsonify({
                'message': 'All transactions imported successfully',
                'count': len(saved_transactions)
            }), 200
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'An error occurred while saving transactions',
            'details': str(e)
        }), 500

@expenses_bp.route('/edit_transaction/<string:transaction_id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(transaction_id):
    # Get all transactions
    transactions = Transaction.get_user_transactions(current_user.id)
    
    # Find the transaction to edit
    transaction = next((t for t in transactions if t.id == transaction_id), None)
    
    if not transaction or transaction.user_id != current_user.id:
        flash('You are not authorized to edit this transaction')
        return redirect(url_for('expenses.index'))
    
    if request.method == 'POST':
        try:
            # Update transaction fields
            transaction.date_time = request.form['date_time']
            transaction.transaction_type = request.form['transaction_type']
            transaction.details = request.form['details']
            transaction.withdrawal = request.form['withdrawal'] if request.form['withdrawal'] else ''
            transaction.deposit = request.form['deposit'] if request.form['deposit'] else ''
            transaction.balance = request.form['balance']
            transaction.branch = request.form['branch']
            transaction.updated_at = datetime.now()
            
            # Save updated transactions
            Transaction.save_user_transactions(current_user.id, transactions)
            
            flash('Transaction updated successfully')
            return redirect(url_for('expenses.index'))
        except Exception as e:
            flash(f'Error updating transaction: {str(e)}')
    
    return render_template('edit_transaction.html', transaction=transaction)

@expenses_bp.route('/delete_transaction/<string:transaction_id>', methods=['POST'])
@login_required
def delete_transaction(transaction_id):
    # Get all transactions
    transactions = Transaction.get_user_transactions(current_user.id)
    
    # Find the transaction to delete
    transaction = next((t for t in transactions if t.id == transaction_id), None)
    
    if not transaction or transaction.user_id != current_user.id:
        flash('You are not authorized to delete this transaction')
        return redirect(url_for('expenses.index'))
    
    try:
        # Remove the transaction
        transactions = [t for t in transactions if t.id != transaction_id]
        
        # Save updated transactions
        Transaction.save_user_transactions(current_user.id, transactions)
        
        flash('Transaction deleted successfully')
    except Exception as e:
        flash(f'Error deleting transaction: {str(e)}')
    
    return redirect(url_for('expenses.index'))

@expenses_bp.route('/add_transaction', methods=['GET', 'POST'])
@login_required
def add_transaction():
    if request.method == 'POST':
        try:
            # Get form data
            amount = float(request.form['amount'])
            date = datetime.strptime(request.form['date'], '%Y-%m-%dT%H:%M')
            category_id = request.form['category_id'] if request.form['category_id'] else None
            description = request.form['description']
            transaction_type = request.form['type']

            # Get existing transactions
            transactions = Transaction.get_user_transactions(current_user.id)
            
            # Calculate new balance
            current_balance = float(transactions[-1].balance.replace(',', '')) if transactions else 0
            if transaction_type == 'withdrawal':
                new_balance = current_balance - amount
                withdrawal = f"{amount:,.2f}"
                deposit = ''
            else:  # deposit
                new_balance = current_balance + amount
                withdrawal = ''
                deposit = f"{amount:,.2f}"

            # Create new transaction
            new_transaction = Transaction(
                id=str(uuid.uuid4()),  # Generate a unique ID
                user_id=current_user.id,
                date_time=date.strftime('%d/%m/%y %H:%M'),
                transaction_type=transaction_type,
                details=description,
                withdrawal=withdrawal,
                deposit=deposit,
                balance=f"{new_balance:,.2f}",
                category_id=category_id,
                branch='',  # Optional fields
                extra='',
                line_text=''
            )

            # Add to transactions list
            transactions.append(new_transaction)
            
            # Save updated transactions
            Transaction.save_user_transactions(current_user.id, transactions)
            
            flash('Transaction added successfully')
            return redirect(url_for('expenses.index'))
            
        except Exception as e:
            flash(f'Error adding transaction: {str(e)}')
            return redirect(url_for('expenses.add_transaction'))

    return render_template('add_transaction.html', categories=categories)
