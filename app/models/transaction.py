import csv
import uuid
from datetime import datetime
from pathlib import Path

class Transaction:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id') or str(uuid.uuid4())
        self.user_id = kwargs.get('user_id')
        self.date_time = kwargs.get('date_time')
        self.transaction_type = kwargs.get('transaction_type')
        self.detail = kwargs.get('detail', '').lower()
        self.amount = float(kwargs.get('amount', 0))
        self.extra = kwargs.get('extra')
        self.withdrawal = kwargs.get('withdrawal')
        self.deposit = kwargs.get('deposit')
        self.balance = kwargs.get('balance')
        self.branch = kwargs.get('branch')
        self.line_text = kwargs.get('line_text')
        self.explanation = kwargs.get('explanation')
        self.category = kwargs.get('category')
        self.created_at = kwargs.get('created_at', datetime.now())
        self.updated_at = kwargs.get('updated_at', datetime.now())

    def save_user_transaction(self):
        """Save the transaction to a CSV file."""
        file_path = Path('user_transactions') / f'{self.user_id}.csv'
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'id', 'user_id', 'date_time', 'transaction_type', 'detail', 'amount', 'extra',
                'withdrawal', 'deposit', 'balance', 'branch', 'line_text', 'explanation', 'category', 'created_at', 'updated_at'
            ])
            writer.writerow(self.__dict__)

    @classmethod
    def save_user_transactions(cls, user_id, transactions):
        """Save multiple transactions to a CSV file.
        
        Args:
            user_id (str): The ID of the user
            transactions (list[Transaction]): List of Transaction objects to save
            
        Raises:
            Exception: If there's an error saving the transactions
        """
        import logging
        logger = logging.getLogger(__name__)
        
        if not transactions:
            logger.warning("No transactions to save")
            return

        try:
            file_path = Path('user_transactions') / f'{user_id}.csv'
            file_path.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"Saving transactions to: {file_path}")

            # Get fieldnames from first transaction
            fieldnames = list(transactions[0].__dict__.keys())
            logger.debug(f"Using fieldnames: {fieldnames}")

            # Write all transactions at once
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for i, transaction in enumerate(transactions, 1):
                    try:
                        writer.writerow(transaction.__dict__)
                        logger.debug(f"Successfully wrote transaction {i}/{len(transactions)}")
                    except Exception as e:
                        logger.error(f"Error writing transaction {i}: {str(e)}")
                        logger.debug(f"Transaction data: {transaction.__dict__}")
                        raise

            logger.info(f"Successfully saved {len(transactions)} transactions")
        except Exception as e:
            logger.error(f"Error saving transactions: {str(e)}")
            raise Exception(f"Failed to save transactions: {str(e)}")

    @classmethod
    def get_user_transactions(cls, user_id):
        """Retrieve all transactions for a specific user.
        
        Args:
            user_id (str): The ID of the user whose transactions to retrieve
            
        Returns:
            list[Transaction]: List of Transaction objects
        """
        file_path = Path('user_transactions') / f'{user_id}.csv'
        if not file_path.exists():
            return []

        transactions = []
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert string dates to datetime objects
                try:
                    # Try ISO format first
                    row['date_time'] = datetime.fromisoformat(row['date_time'])
                except ValueError:
                    try:
                        # Try custom format with time
                        row['date_time'] = datetime.strptime(row['date_time'], '%d/%m/%y %H:%M')
                    except ValueError:
                        try:
                            # Try custom format without time
                            row['date_time'] = datetime.strptime(row['date_time'], '%d/%m/%y')
                        except ValueError:
                            # Fallback to current time if all formats fail
                            row['date_time'] = datetime.now()
                
                try:
                    row['created_at'] = datetime.fromisoformat(row['created_at'])
                except ValueError:
                    try:
                        row['created_at'] = datetime.strptime(row['created_at'], '%Y-%m-%d %H:%M:%S.%f')
                    except ValueError:
                        row['created_at'] = datetime.now()
                
                try:
                    row['updated_at'] = datetime.fromisoformat(row['updated_at'])
                except ValueError:
                    try:
                        row['updated_at'] = datetime.strptime(row['updated_at'], '%Y-%m-%d %H:%M:%S.%f')
                    except ValueError:
                        row['updated_at'] = datetime.now()
                transactions.append(cls(**row))
        
        return transactions

    def auto_categorize(self):
        """Automatically categorize transactions based on patterns in details and descriptions."""
        import logging
        
        # Mapping of patterns to categories
        CATEGORY_MAPPING = {
            "Food/Groceries": [
                "supermarket", "grocery", "restaurant", "cafe", "food", "bakery",
                "coffee", "dining", "market", "takeout", "delivery", "convenience",
                "7-eleven", "big c", "tesco", "lotus", "makro", "tops", "foodland",
                "canteen", "food court", "foodcourt", "foodpanda", "grab food",
                "kfc", "mcdonalds", "pizza", "burger", "sushi", "noodle", "rice",
                "beverage", "drink", "snack", "dessert", "ice cream", "chocolate"
            ],
            "Utilities": [
                "electric", "water", "internet", "phone", "mobile", "utility",
                "bill", "payment", "ptt", "true", "ais", "dtac", "3bb", "tot",
                "cable tv", "television", "tv", "streaming", "netflix", "spotify",
                "youtube", "disney+", "prime video", "electricity", "power",
                "gas", "petrol", "lpg", "ngv", "piped gas", "utility bill"
            ],
            "Transportation": [
                "bus", "train", "mrt", "bts", "taxi", "grab", "bolt", "airport",
                "rail", "transport", "fuel", "gasoline", "petrol", "parking",
                "toll", "expressway", "highway", "car", "motorcycle", "bike",
                "bicycle", "rental", "uber", "lyft", "commute", "travel",
                "airline", "flight", "boat", "ferry", "subway", "metro"
            ],
            "Savings": [
                "transfer", "withdraw", "deposit", "savings", "investment",
                "interest", "dividend", "fund", "stock", "bond", "mutual fund",
                "retirement", "pension", "insurance", "premium", "policy",
                "wealth", "asset", "portfolio", "bank", "account", "atm",
                "withdrawal", "deposit", "โอนเงิน", "เงินโอน", "พร้อมเพย์"
            ]
        }

        # Normalize text for case-insensitive matching
        detail = self.detail.lower()
        description = (self.transaction_type or "").lower()

        # Find matching category
        self.category = "Miscellaneous"  # Default category
        for category, patterns in CATEGORY_MAPPING.items():
            if any(pattern in detail or pattern in description for pattern in patterns):
                self.category = category
                break

        # Log uncategorized transactions for review
        if self.category == "Miscellaneous":
            logging.info(f"Uncategorized transaction: {self.detail} ({self.transaction_type})")

        return self
