import csv
import uuid
import traceback
from datetime import datetime
from pathlib import Path
import logging
import glob
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class Transaction:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id') or str(uuid.uuid4())
        self.user_id = kwargs.get('user_id')
        self.date_time = kwargs.get('date_time')
        self.transaction_type = kwargs.get('transaction_type')
        self.details = kwargs.get('details', '').lower()
        self.detail = kwargs.get('detail', '').lower()
        self.amount = float(kwargs.get('amount', 0))
        self.extra = kwargs.get('extra')
        self.withdrawal = kwargs.get('withdrawal')
        self.deposit = kwargs.get('deposit')
        self.balance = kwargs.get('balance')
        self.branch = kwargs.get('branch')
        self.line_text = kwargs.get('line_text')
        self.explanation = kwargs.get('explanation')
        self.category = kwargs.get('category', 'Miscellaneous')
        self.category_id = kwargs.get('category_id', 13)
        self.created_at = kwargs.get('created_at', datetime.now())
        self.updated_at = kwargs.get('updated_at', datetime.now())

    def save_user_transaction(self):
        """Save the transaction to a CSV file."""
        # Find existing file with user_id prefix or create new one
        user_id = str(self.user_id)
        dir_path = Path('user_transactions')
        dir_path.mkdir(parents=True, exist_ok=True)
        
        # Look for existing files with this user_id prefix
        existing_files = list(dir_path.glob(f"{user_id}_*.csv"))
        
        if existing_files:
            file_path = existing_files[0]  # Use the first matching file
        else:
            # Create a new file with UUID
            file_uuid = str(uuid.uuid4())
            file_path = dir_path / f"{user_id}_{file_uuid}.csv"
        
        # Check if file exists and needs header
        file_exists = os.path.exists(file_path)
        
        with open(file_path, 'a', newline='', encoding='utf-8') as f:
            fieldnames = [
                'id', 'user_id', 'date_time', 'transaction_type', 'detail', 'details', 
                'amount', 'extra', 'withdrawal', 'deposit', 'balance', 'branch', 
                'line_text', 'explanation', 'category', 'category_id', 
                'created_at', 'updated_at'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            # Write header if new file
            if not file_exists:
                writer.writeheader()
                
            writer.writerow(self.__dict__)
        
        logger.info(f"Transaction saved to {file_path}")

    @classmethod
    def save_user_transactions(cls, user_id, transactions):
        """Save multiple transactions to a single CSV file."""
        if not transactions:
            logger.warning("No transactions to save")
            return

        # Find existing file with user_id prefix or create new one
        user_id = str(user_id)
        dir_path = Path('user_transactions')
        dir_path.mkdir(parents=True, exist_ok=True)
        
        # Look for existing files with this user_id prefix
        existing_files = list(dir_path.glob(f"{user_id}_*.csv"))
        
        if existing_files:
            file_path = existing_files[0]  # Use the first matching file
        else:
            # Create a new file with UUID
            file_uuid = str(uuid.uuid4())
            file_path = dir_path / f"{user_id}_{file_uuid}.csv"
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                fieldnames = [
                    'id', 'user_id', 'date_time', 'transaction_type', 'details', 'detail', 
                    'amount', 'extra', 'withdrawal', 'deposit', 'balance', 'branch', 
                    'line_text', 'explanation', 'category', 'category_id', 
                    'created_at', 'updated_at'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for transaction in transactions:
                    row = {field: getattr(transaction, field) for field in fieldnames}
                    writer.writerow(row)
                    
            logger.info(f"Successfully saved {len(transactions)} transactions to {file_path}")
            
        except Exception as e:
            logger.error(f"Error saving transactions: {str(e)}")
            logger.error(traceback.format_exc())
            raise Exception(f"Failed to save transactions: {str(e)}")

    @classmethod
    def get_user_transactions(cls, user_id):
        """Retrieve all transactions for a specific user."""
        transactions = []
        seen_ids = set()
        user_id = str(user_id)
        
        # Search in both possible directories
        for dir_name in ['user_transactions', 'user_transaction']:
            dir_path = Path(dir_name)
            if not dir_path.exists():
                continue
                
            # Look specifically for files with user_id prefix
            pattern = f"{user_id}_*.csv"
            matching_files = list(dir_path.glob(pattern))
            
            # Debug log
            logger.info(f"Found {len(matching_files)} transaction files for user {user_id} in {dir_name}")
            
            for file_path in matching_files:
                try:
                    logger.info(f"Reading transactions from file: {file_path}")
                    with open(file_path, 'r', newline='', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            try:
                                # Skip duplicate transactions
                                if row.get('id') in seen_ids:
                                    continue
                                seen_ids.add(row.get('id'))
                                
                                # Parse dates
                                if 'date_time' in row and row['date_time']:
                                    row['date_time'] = cls._parse_date(row['date_time'])
                                    
                                for date_field in ['created_at', 'updated_at']:
                                    if date_field in row and row[date_field]:
                                        try:
                                            row[date_field] = cls._parse_date(row[date_field])
                                        except:
                                            row[date_field] = datetime.now()
                                
                                # Ensure category_id is valid
                                try:
                                    row['category_id'] = int(row.get('category_id', 13))
                                except (ValueError, TypeError):
                                    row['category_id'] = 13
                                
                                # Create transaction object
                                transaction = cls(**row)
                                transaction.source_file = str(file_path)
                                transactions.append(transaction)
                                
                            except Exception as e:
                                logger.error(f"Error processing transaction: {str(e)}")
                                logger.error(traceback.format_exc())
                except Exception as e:
                    logger.error(f"Error reading file {file_path}: {str(e)}")
                    logger.error(traceback.format_exc())

        # Sort transactions by date
        transactions.sort(key=lambda t: t.date_time if hasattr(t, 'date_time') and t.date_time else datetime.now())
        logger.info(f"Loaded {len(transactions)} transactions for user {user_id}")
        return transactions

    @staticmethod
    def _parse_date(date_str):
        """Parse date string in multiple formats."""
        if isinstance(date_str, datetime):
            return date_str
            
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%d/%m/%y %H:%M',
            '%d/%m/%y',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(str(date_str), fmt)
            except ValueError:
                continue
                
        return datetime.now()

    def auto_categorize(self):
        """Automatically categorize transactions using advanced pattern matching."""
        from fuzzywuzzy import fuzz
        import re
        from datetime import datetime
        
        # Enhanced category mapping with weights and patterns
        category_rules = [
            {
                'name': 'Food/Groceries',
                'patterns': [
                    (r'(supermarket|grocery|restaurant|cafe|food|bakery|coffee|dining|market|takeout|delivery|convenience)', 0.8),
                    (r'(7-eleven|big c|tesco|lotus|makro|tops|foodland)', 0.9),
                    (r'(ร้านอาหาร|ซุปเปอร์มาร์เก็ต|ร้านกาแฟ|อาหาร|ตลาด|เดลิเวอรี่|เซเว่น|บิ๊กซี|เทสโก้|โลตัส|แม็คโคร)', 0.9)
                ],
                'amount_ranges': [(0, 1000, 0.7)],  # Typical food/grocery amounts
                'time_ranges': [(6, 9, 0.6), (11, 14, 0.8), (17, 21, 0.9)]  # Meal times
            },
            {
                'name': 'Utilities',
                'patterns': [
                    (r'(electric|water|internet|phone|mobile|utility|bill|payment)', 0.8),
                    (r'(ptt|true|ais|dtac|3bb|tot)', 0.9),
                    (r'(ไฟฟ้า|น้ำประปา|อินเทอร์เน็ต|โทรศัพท์|มือถือ|บิล|การชำระเงิน|ทรู|เอไอเอส|ดีแทค|ทรีบีบี|ทีโอที)', 0.9)
                ],
                'amount_ranges': [(500, 10000, 0.8)],  # Typical utility amounts
                'time_ranges': []  # No specific time pattern
            },
            # ... (similar structure for other categories)
        ]

        # Merchant database
        merchant_mapping = {
            '7-eleven': {'category': 'Food/Groceries', 'weight': 0.95},
            'big c': {'category': 'Food/Groceries', 'weight': 0.9},
            'tesco': {'category': 'Food/Groceries', 'weight': 0.9},
            # ... (add more merchants)
        }

        # Clean and combine text for matching
        text = f"{self.details} {self.detail} {self.transaction_type}".lower()
        text = ''.join(c for c in text if c.isalnum() or c.isspace())
        
        # Get transaction amount and time
        amount = float(self.amount) if self.amount else 0
        transaction_time = self.date_time.time() if isinstance(self.date_time, datetime) else None

        # Initialize scoring
        category_scores = {}
        
        # Apply merchant matching
        for merchant, data in merchant_mapping.items():
            if fuzz.partial_ratio(merchant, text) > 85:
                category_scores[data['category']] = category_scores.get(data['category'], 0) + data['weight']

        # Apply pattern matching
        for category in category_rules:
            total_score = 0
            
            # Pattern matching
            for pattern, weight in category['patterns']:
                if re.search(pattern, text, re.IGNORECASE):
                    total_score += weight
            
            # Amount-based scoring
            for min_amt, max_amt, weight in category['amount_ranges']:
                if min_amt <= amount <= max_amt:
                    total_score += weight
            
            # Time-based scoring
            if transaction_time:
                for start_hour, end_hour, weight in category['time_ranges']:
                    if start_hour <= transaction_time.hour <= end_hour:
                        total_score += weight
            
            category_scores[category['name']] = total_score

        # Select best category
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            if category_scores[best_category] > 0.5:  # Minimum confidence threshold
                self.category = best_category
                self.category_id = {
                    'Food/Groceries': 3,
                    'Utilities': 4,
                    'Transportation': 5,
                    'Shopping': 6,
                    'Entertainment': 7,
                    'Healthcare': 8,
                    'Savings': 9
                }.get(best_category, 13)
                return self

        # Default to Miscellaneous if no good match
        self.category = "Miscellaneous"
        self.category_id = 13
                
        return self
