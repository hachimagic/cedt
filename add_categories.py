from app.models.transaction import Category
from app import db, create_app

def add_default_categories():
    app = create_app()
    with app.app_context():
        categories = [
            "Mortgage/Rent",
            "Credit Card",
            "Food/Groceries",
            "Utilities",
            "Transportation",
            "Entertainment",
            "Healthcare",
            "Insurance",
            "Savings",
            "Investments",
            "Education",
            "Clothing",
            "Miscellaneous"
        ]

        for cat_name in categories:
            if not Category.query.filter_by(name=cat_name).first():
                category = Category(name=cat_name)
                db.session.add(category)
        
        db.session.commit()
        print("Default categories added successfully")

if __name__ == "__main__":
    add_default_categories()
