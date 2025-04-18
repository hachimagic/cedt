import re

def is_numeric(token):
    try:
        float(token.replace(',', ''))
        return True
    except ValueError:
        return False

def parse_transaction_line(line):
    print(f"\nParsing line: {line}")
    tokens = line.split()
    date_pattern = re.compile(r'\d{2}/\d{2}/\d{2}')
    
    # Extract transaction ID if present (e.g., "34" before the date)
    transaction_id = None
    if tokens and tokens[0].isdigit() and len(tokens) > 1 and date_pattern.match(tokens[1]):
        transaction_id = tokens[0]
        tokens = tokens[1:]
        print(f"Found transaction ID: {transaction_id}")
        
    if not tokens or not date_pattern.match(tokens[0]):
        print("Not a transaction line")
        return None  # Not a transaction line

    # Build the date/time field.
    date_time = tokens[0]
    idx = 1
    time_pattern = re.compile(r'\d{1,2}:\d{2}')
    if idx < len(tokens) and time_pattern.match(tokens[idx]):
        date_time += " " + tokens[idx]
        idx += 1
    print(f"Date/Time: {date_time}")

    # Identify numeric tokens from the end.
    num_end = len(tokens)
    numeric_tokens = []
    while num_end > idx and is_numeric(tokens[num_end - 1]):
        numeric_tokens.insert(0, tokens[num_end - 1])
        num_end -= 1
    print(f"Numeric tokens: {numeric_tokens}")

    extra = ""
    # Process numeric tokens.
    if len(numeric_tokens) == 4:
        # Check if the second token looks extraneous (no decimal point)
        if '.' not in numeric_tokens[1]:
            extra = numeric_tokens[1]
            description_section = " ".join(tokens[idx:num_end]).lower()
            print(f"Description section: {description_section}")
            if "รับเงิน" in description_section or "โอนเงินเข้า" in description_section:
                # Deposit transaction: use first token as deposit.
                withdrawal = ""
                deposit = numeric_tokens[0]
                print("Identified as deposit transaction")
            elif "จ่าย" in description_section or "โอนเงินออก" in description_section:
                # Withdrawal transaction.
                withdrawal = numeric_tokens[0]
                deposit = ""
                print("Identified as withdrawal transaction")
            else:
                # Default to deposit.
                withdrawal = ""
                deposit = numeric_tokens[0]
                print("Defaulting to deposit transaction")
            balance = numeric_tokens[2]
            branch = numeric_tokens[3]
        else:
            # If not matching the extraneous pattern, use tokens as is.
            withdrawal, deposit, balance, branch = numeric_tokens
            print("Using numeric tokens as is")
    elif len(numeric_tokens) == 3:
        description_section = " ".join(tokens[idx:num_end]).lower()
        print(f"Description section: {description_section}")
        if "รับเงิน" in description_section or "โอนเงินเข้า" in description_section:
            withdrawal = ""
            deposit, balance, branch = numeric_tokens
            print("Identified as deposit transaction")
        elif "จ่าย" in description_section or "โอนเงินออก" in description_section:
            deposit = ""
            withdrawal, balance, branch = numeric_tokens
            print("Identified as withdrawal transaction")
        else:
            withdrawal = ""
            deposit, balance, branch = numeric_tokens
            print("Defaulting to deposit transaction")
    else:
        print(f"Invalid number of numeric tokens: {len(numeric_tokens)}")
        return None  # Does not match expected numeric pattern

    # Ensure that if a deposit amount is present then the withdrawal is blank.
    if deposit:
        withdrawal = ""

    # The remaining tokens (from idx to num_end) form the description.
    description_tokens = tokens[idx:num_end]
    if description_tokens:
        transaction_field = description_tokens[0]
        details = " ".join(description_tokens[1:]) if len(description_tokens) > 1 else ""
    else:
        transaction_field = ""
        details = ""
    print(f"Transaction field: {transaction_field}")
    print(f"Details: {details}")

    # Use the extracted transaction ID or generate a temporary one
    if not transaction_id:
        # Generate a temporary ID based on the transaction data
        import hashlib
        id_str = f"{date_time}{transaction_field}{details}{withdrawal}{deposit}{balance}"
        transaction_id = 'temp_' + hashlib.md5(id_str.encode()).hexdigest()[:8]
        print(f"Generated temporary ID: {transaction_id}")
    
    result = {
        'id': transaction_id,
        'date_time': date_time,
        'transaction': transaction_field,
        'details': details,
        'extra': extra,         # Extra column for the spurious number.
        'withdrawal': withdrawal,
        'deposit': deposit,
        'balance': balance,
        'branch': branch,
        'line_text': line        # For debugging if needed.
    }
    print(f"Parsed result: {result}")
    return result
