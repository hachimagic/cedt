from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, jsonify
from flask_login import login_required, current_user
import os
import uuid
import pdfplumber
import traceback
from datetime import datetime
from pathlib import Path
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
    import logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    
    logger.info(f"Index route: Loading transactions for user {current_user.id}")
    
    # List all files in user_transactions directory
    import os
    import glob
    from pathlib import Path
    
    user_transactions_dir = Path('user_transactions')
    if user_transactions_dir.exists():
        # Look specifically for files with user_id prefix
        files = list(user_transactions_dir.glob(f'{current_user.id}_*.csv'))
        logger.info(f"Found {len(files)} transaction files for user {current_user.id}: {files}")
    else:
        logger.warning("user_transactions directory does not exist")
    
    # Get transactions for the current user
    transactions = Transaction.get_user_transactions(current_user.id)
    
    logger.info(f"Loaded {len(transactions)} transactions for user {current_user.id}")
    
    # Calculate totals
    total_deposits = sum(float(t.deposit.replace(',', '')) if t.deposit and t.deposit.strip() else 0 for t in transactions)
    total_withdrawals = sum(float(t.withdrawal.replace(',', '')) if t.withdrawal and t.withdrawal.strip() else 0 for t in transactions)
    current_balance = float(transactions[-1].balance.replace(',', '')) if transactions else 0
    
    logger.info(f"Calculated totals: deposits={total_deposits}, withdrawals={total_withdrawals}, balance={current_balance}")
    
    # Print debug information about each transaction
    for i, t in enumerate(transactions):
        logger.debug(f"Transaction {i+1}: {t.__dict__}")
    
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
                            page_text = ""
                            for page in pdf.pages:
                                current_page_text = page.extract_text(x_tolerance=1, y_tolerance=1, encoding=encoding)
                                if current_page_text:
                                    # Add page separator if needed
                                    if page_text and not page_text.endswith('\n'):
                                        page_text += '\n'
                                    page_text += current_page_text
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
                # Process text with special handling for page breaks
                page_lines = page_text.split('\n')
                buffer = ""
                for line in page_lines:
                    try:
                        # If line looks like a continuation (starts with whitespace or is numeric)
                        if line.startswith(' ') or line.strip().isdigit():
                            buffer += " " + line.strip()
                            continue
                            
                        # Process any buffered content first
                        if buffer:
                            parsed = parse_transaction_line(buffer)
                            if parsed:
                                parsed_transactions.append(parsed)
                            buffer = ""
                            
                        # Process current line
                        parsed = parse_transaction_line(line)
                        if parsed:
                            print(f"Successfully parsed line: {line}")
                            print(f"Parsed data: {parsed}")
                            # Ensure all required fields are present
                            parsed['user_id'] = current_user.id
                            parsed['explanation'] = ''
                            parsed['category_id'] = 13  # Default to Miscellaneous
                            parsed['category'] = 'Miscellaneous'  # Default category
                            parsed['transaction_type'] = parsed.get('transaction', '')
                            parsed['branch'] = parsed.get('branch', '')
                            parsed['extra'] = parsed.get('extra', '')
                            parsed['line_text'] = line
                            parsed['detail'] = parsed.get('details', '')  # Ensure detail is set
                            parsed['details'] = parsed.get('details', '')  # Ensure details is set
                            
                            # Create temporary transaction object for auto-categorization
                            temp_transaction = Transaction(**parsed)
                            temp_transaction.auto_categorize()
                            
                            # Update parsed data with auto-categorized values
                            parsed['category_id'] = temp_transaction.category_id
                            parsed['category'] = temp_transaction.category
                            
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
    import logging
    from decimal import Decimal, InvalidOperation
    
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    try:
        logger.info("Starting save_transcript operation...")
        
        if not request.is_json:
            logger.error("Error: Request is not JSON")
            return jsonify({'error': 'Request must be JSON'}), 400
            
        parsed_transactions = request.json.get('transactions', [])
        logger.info(f"Received {len(parsed_transactions)} transactions to save")
        
        if not parsed_transactions:
            logger.error("Error: No transactions provided")
            return jsonify({'error': 'No transactions provided'}), 400
            
        saved_transactions = []
        failed_transactions = []
        
        # Process transactions
        for i, parsed in enumerate(parsed_transactions, 1):
            try:
                logger.info(f"Processing transaction {i}/{len(parsed_transactions)}:")
                logger.debug(f"Transaction data: {parsed}")
                
                # Validate required fields
                required_fields = ['date_time', 'transaction', 'details', 'withdrawal', 'deposit', 'balance']
                missing_fields = [field for field in required_fields if field not in parsed]
                if missing_fields:
                    raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
                
                # Validate and format amounts
                for amount_field in ['withdrawal', 'deposit', 'balance']:
                    try:
                        if parsed[amount_field] and parsed[amount_field].strip():
                            parsed[amount_field] = str(Decimal(parsed[amount_field].replace(',', '')))
                        else:
                            parsed[amount_field] = '0'
                    except (InvalidOperation, AttributeError):
                        raise ValueError(f"Invalid {amount_field} amount: {parsed[amount_field]}")
                
                # Parse and validate date - handle multiple formats
                date_formats = [
                    '%Y-%m-%d %H:%M:%S',  # Full datetime with seconds
                    '%Y-%m-%d %H:%M',     # Datetime without seconds
                    '%d/%m/%y %H:%M'      # Short date format
                ]
                
                parsed_date = None
                for date_format in date_formats:
                    try:
                        parsed_date = datetime.strptime(parsed['date_time'], date_format)
                        break
                    except ValueError:
                        continue
                
                if parsed_date is None:
                    raise ValueError(
                        f"Invalid date format: {parsed['date_time']}. "
                        "Supported formats: YYYY-MM-DD HH:MM:SS, YYYY-MM-DD HH:MM, or DD/MM/YY HH:MM"
                    )
                
                parsed['date_time'] = parsed_date.isoformat()
                
                # Validate category
                category_id = parsed.get('category_id')
                if category_id:
                    try:
                        category_id = int(category_id)
                        if category_id < 1 or category_id > 13:
                            raise ValueError("Category ID must be between 1 and 13")
                    except (ValueError, TypeError):
                        category_id = 13  # Default to Miscellaneous
                else:
                    category_id = 13  # Default to Miscellaneous
                
                # Create transaction
                new_transaction = Transaction(
                    id=str(uuid.uuid4()),
                    user_id=current_user.id,
                    date_time=parsed['date_time'],
                    transaction_type=parsed['transaction'],
                    details=parsed['details'],
                    withdrawal=parsed['withdrawal'],
                    deposit=parsed['deposit'],
                    balance=parsed['balance'],
                    explanation=parsed.get('explanation', ''),
                    category_id=category_id,
                    branch=parsed.get('branch', ''),
                    extra=parsed.get('extra', ''),
                    line_text=parsed.get('line_text', '')
                )
                
                # Auto-categorize if needed
                if not new_transaction.category_id:
                    new_transaction.auto_categorize()
                
                saved_transactions.append(new_transaction)
                logger.info(f"Successfully processed transaction {i}")
                
            except Exception as e:
                error_msg = f'Error processing transaction: {str(e)}'
                logger.error(f"Failed transaction: {parsed} - {error_msg}")
                logger.error(traceback.format_exc())
                failed_transactions.append({
                    'line': parsed.get('line_text', 'Unknown'),
                    'error': error_msg
                })

        logger.info(f"Processed {len(saved_transactions)} transactions successfully")
        logger.info(f"Failed to process {len(failed_transactions)} transactions")
        
        if saved_transactions:
            logger.info("Saving transactions to file...")
            try:
                # Generate a unique file identifier
                file_id = str(uuid.uuid4())[:8]
                # Save to file with the pattern user_id_file_id.csv
                file_path = Path('user_transactions') / f'{current_user.id}_{file_id}.csv'
                logger.info(f"Saving transactions to file: {file_path}")
                
                # Save with rollback protection
                Transaction.save_user_transactions(current_user.id, saved_transactions)
                logger.info("Transactions saved successfully")
            except Exception as e:
                logger.error(f"Error saving transactions: {str(e)}")
                logger.error(traceback.format_exc())
                return jsonify({
                    'error': 'An error occurred while saving transactions',
                    'details': str(e),
                    'failed_transactions': failed_transactions,
                    'count': 0
                }), 500

        result = {
            'message': f'Successfully imported {len(saved_transactions)} transactions. Failed to import {len(failed_transactions)} transactions.',
            'count': len(saved_transactions),
            'failed_transactions': failed_transactions
        }
        logger.info(f"Operation result: {result}")
        return jsonify(result), 200
            
    except Exception as e:
        logger.error(f"An error occurred while processing transactions: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': 'An error occurred while processing transactions',
            'details': str(e),
            'count': 0
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
