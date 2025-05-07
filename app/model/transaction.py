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
        file_path = Path('user_transaction') / f'{self.user_id}.csv'
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'id', 'user_id', 'date_time', 'transaction_type', 'detail', 'amount', 'extra',
                'withdrawal', 'deposit', 'balance', 'branch', 'line_text', 'explanation', 'category', 'created_at', 'updated_at'
            ])
            writer.writerow(self.__dict__)

    @classmethod
    def get_user_transactions(cls, user_id):
        """Retrieve all transactions for a given user."""
        file_path = Path('user_transaction') / f'{user_id}.csv'
        if not file_path.exists():
            return []

        transactions = []
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert string dates back to datetime objects
                row['date_time'] = datetime.strptime(row['date_time'], '%Y-%m-%d %H:%M:%S.%f')
                row['created_at'] = datetime.strptime(row['created_at'], '%Y-%m-%d %H:%M:%S.%f')
                row['updated_at'] = datetime.strptime(row['updated_at'], '%Y-%m-%d %H:%M:%S.%f')
                transactions.append(cls(**row))

        return transactions
