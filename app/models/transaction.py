import csv
import uuid
from datetime import datetime
from pathlib import Path

class Category:
    def __init__(self, id, name, description):
        self.id = id
        self.name = name
        self.description = description

class Transaction:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.user_id = kwargs.get('user_id')
        self.date_time = kwargs.get('date_time')
        self.transaction_type = kwargs.get('transaction_type')
        self.details = kwargs.get('details')
        self.extra = kwargs.get('extra')
        self.withdrawal = kwargs.get('withdrawal')
        self.deposit = kwargs.get('deposit')
        self.balance = kwargs.get('balance')
        self.branch = kwargs.get('branch')
        self.line_text = kwargs.get('line_text')
        self.explanation = kwargs.get('explanation')
        category_id = kwargs.get('category_id')
        self.category_id = int(category_id) if category_id and category_id.strip() else None
        self.created_at = kwargs.get('created_at', datetime.now())
        self.updated_at = kwargs.get('updated_at', datetime.now())

    @staticmethod
    def get_user_transactions(user_id):
        """Read existing transactions from CSV"""
        file_path = Transaction._get_user_csv_path(user_id)
        print(f"Getting transactions for user {user_id}")
        if not file_path.exists():
            print(f"No transaction file found at {file_path}")
            # Create an empty CSV file with headers
            try:
                file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=[
                        'id', 'user_id', 'date_time', 'transaction_type', 'details', 'extra',
                        'withdrawal', 'deposit', 'balance', 'branch', 'line_text',
                        'explanation', 'category_id', 'created_at', 'updated_at'
                    ])
                    writer.writeheader()
                print(f"Created new transaction file: {file_path}")
            except Exception as e:
                print(f"Error creating transaction file: {str(e)}")
                raise
            return []
        
        transactions = []
        try:
            print(f"Reading transactions from {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        # Convert date_time string to datetime object
                        if 'date_time' in row:
                            try:
                                row['date_time'] = datetime.strptime(row['date_time'], '%d/%m/%y %H:%M')
                            except ValueError:
                                # If parsing fails, keep as string
                                print(f"Failed to parse date_time: {row['date_time']}")
                                pass
                        transactions.append(Transaction(**row))
                    except Exception as e:
                        print(f"Error processing row: {row}")
                        print(f"Error details: {str(e)}")
                        raise
            print(f"Successfully loaded {len(transactions)} transactions")
            return transactions
        except Exception as e:
            print(f"Error reading transactions: {str(e)}")
            raise

    @staticmethod
    def save_user_transactions(user_id, transactions):
        """Save transactions to CSV, sorted by date"""
        file_path = Transaction._get_user_csv_path(user_id)
        
        # Convert transactions to dicts
        transactions_dicts = [t.__dict__ for t in transactions]
        
        # Sort transactions by date_time
        def get_datetime(x):
            date_time = x['date_time']
            if isinstance(date_time, datetime):
                return date_time
            try:
                return datetime.strptime(date_time, '%d/%m/%y %H:%M')
            except (ValueError, TypeError):
                # If parsing fails, return a default date to avoid sorting errors
                return datetime.min
            
        transactions_dicts.sort(key=get_datetime)
        
        try:
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Filter out fields we don't want to save
            filtered_dicts = []
            for t_dict in transactions_dicts:
                # Convert datetime to string if needed
                date_time = t_dict['date_time']
                if isinstance(date_time, datetime):
                    date_time = date_time.strftime('%d/%m/%y %H:%M')
                
                filtered_dict = {
                    'id': t_dict['id'],
                    'user_id': t_dict.get('user_id', user_id),  # Use provided user_id if not in dict
                    'date_time': date_time,
                    'transaction_type': t_dict['transaction_type'],
                    'details': t_dict['details'],
                    'extra': t_dict.get('extra', ''),
                    'withdrawal': t_dict.get('withdrawal', ''),
                    'deposit': t_dict.get('deposit', ''),
                    'balance': t_dict['balance'],
                    'branch': t_dict.get('branch', ''),
                    'line_text': t_dict.get('line_text', ''),
                    'explanation': t_dict.get('explanation', ''),
                    'category_id': str(t_dict.get('category_id')) if t_dict.get('category_id') is not None else '',
                    'created_at': t_dict.get('created_at', datetime.now().isoformat()),
                    'updated_at': t_dict.get('updated_at', datetime.now().isoformat())
                }
                filtered_dicts.append(filtered_dict)
            
            # Define fieldnames for CSV
            fieldnames = [
                'id', 'user_id', 'date_time', 'transaction_type', 'details', 'extra',
                'withdrawal', 'deposit', 'balance', 'branch', 'line_text',
                'explanation', 'category_id', 'created_at', 'updated_at'
            ]
            
            print(f"Saving {len(filtered_dicts)} transactions to {file_path}")
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for row in filtered_dicts:
                    try:
                        writer.writerow(row)
                    except Exception as e:
                        print(f"Error writing row: {row}")
                        print(f"Error details: {str(e)}")
                        raise
                print("Transactions written to CSV successfully")
        except Exception as e:
            print(f"Error saving transactions: {str(e)}")
            raise

    @staticmethod
    def _get_user_csv_path(user_id):
        """Get the path to the user's CSV file"""
        try:
            # Get base directory from current working directory
            base_dir = Path.cwd()
            print(f"Using base directory: {base_dir}")
            
            # Create transactions directory
            transactions_dir = base_dir / 'user_transactions'
            transactions_dir.mkdir(parents=True, exist_ok=True)
            print(f"Using transactions directory: {transactions_dir}")
            
            # Verify directory is accessible
            if not transactions_dir.exists():
                raise Exception(f"Failed to create or access transactions directory: {transactions_dir}")
            
            print(f"Looking for transaction files in: {transactions_dir}")
            
            # Use proper path joining
            pattern = f"{user_id}_*.csv"
            user_files = list(transactions_dir.glob(pattern))
            print(f"Found {len(user_files)} existing transaction files")
            
            if user_files:
                chosen_file = user_files[0]
                print(f"Using existing file: {chosen_file}")
                return chosen_file
            else:
                new_file = transactions_dir / f"{user_id}_{uuid.uuid4()}.csv"
                print(f"Creating new file: {new_file}")
                return new_file
                
        except Exception as e:
            print(f"Error resolving transaction file path: {str(e)}")
            raise
