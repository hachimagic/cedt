from datetime import datetime
from collections import defaultdict
import requests
from app.models.transaction import Transaction

class AnalysisService:
    OPENROUTER_API_KEY = "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"
    OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

    @staticmethod
    def get_ai_analysis(user_id):
        """Get AI-powered financial analysis and recommendations"""
        transactions = Transaction.get_user_transactions(user_id)
        
        # Prepare transaction summary
        summary = "\n".join([
            f"{t.date_time}: {t.transaction_type} - {t.withdrawal or t.deposit}"
            for t in transactions
        ])
        
        # Prepare AI prompt
        prompt = f"""Analyze these transactions and provide financial recommendations:
        {summary}
        
        Please provide:
        1. Spending patterns
        2. Potential savings opportunities
        3. Recommendations for better financial management
        """
        
        # Call OpenRouter API
        response = requests.post(
            AnalysisService.OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {AnalysisService.OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "microsoft/phi-3.5-mini-128k-instruct",
                "messages": [{"role": "user", "content": prompt}]
            }
        )
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        return "Unable to get AI analysis at this time"

    @staticmethod
    def get_monthly_spending(user_id):
        """Calculate monthly spending totals"""
        transactions = Transaction.get_user_transactions(user_id)
        monthly_totals = defaultdict(float)
        
        for t in transactions:
            if t.withdrawal:
                try:
                    date = datetime.strptime(t.date_time, '%d/%m/%y %H:%M')
                    month_key = date.strftime('%Y-%m')
                    monthly_totals[month_key] += float(t.withdrawal)
                except (ValueError, TypeError):
                    continue
                    
        return dict(monthly_totals)

    @staticmethod
    def get_top_categories(user_id):
        """Identify top spending categories"""
        transactions = Transaction.get_user_transactions(user_id)
        category_totals = defaultdict(float)
        
        for t in transactions:
            if t.withdrawal and t.category_id:
                try:
                    category_totals[t.category_id] += float(t.withdrawal)
                except (ValueError, TypeError):
                    continue
                    
        return dict(sorted(category_totals.items(), key=lambda x: x[1], reverse=True))

    @staticmethod
    def get_recurring_payments(user_id):
        """Detect recurring payments"""
        transactions = Transaction.get_user_transactions(user_id)
        payment_patterns = defaultdict(list)
        
        for t in transactions:
            if t.withdrawal:
                try:
                    amount = float(t.withdrawal)
                    payment_patterns[amount].append(t.date_time)
                except (ValueError, TypeError):
                    continue
                    
        return {amount: dates for amount, dates in payment_patterns.items() 
                if len(dates) > 1}

    @staticmethod
    def get_savings_opportunities(user_id):
        """Identify potential savings opportunities"""
        recurring = AnalysisService.get_recurring_payments(user_id)
        return {
            'recurring_payments': {
                amount: len(dates) for amount, dates in recurring.items()
            }
        }
