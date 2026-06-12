import re
from  transactions import read_transaction

def parse(texts):
    return "\n".join(texts)   
import re

def parse_payment(texts):

    data = {
        "sender": None,
        "amount": None,
        "date": None,
        "time": None,
        "utr": None
    }

    # -------------------------
    # Sender
    # -------------------------

    for line in texts:

        line = line.strip()

        match = re.match(
            r'^From:?\s*(.+)$',
            line,
            re.IGNORECASE
        )

        if match:

            sender = match.group(1)

            # Ignore bank account owner
            if "bank" not in sender.lower():
                data["sender"] = sender
                break

    # -------------------------
    # UTR (12 digits)
    # -------------------------

    for line in texts:

        match = re.fullmatch(r'\d{12}', line.strip())

        if match:
            data["utr"] = match.group()
            break

    # -------------------------
    # Date
    # -------------------------

    for line in texts:

        match = re.search(
            r'\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]{3,9}\s+\d{2,4}',
            line,
            re.IGNORECASE
        )

        if match:
            data["date"] = match.group()
            break

    # -------------------------
    # Time
    # -------------------------

    for line in texts:

        match = re.search(
            r'\d{1,2}[:.]\d{2}\s*[ap]m',
            line,
            re.IGNORECASE
        )

        if match:
            data["time"] = match.group()
            break

    # -------------------------
    # Amount
    # -------------------------

    amounts = []

    for line in texts:

        line = line.strip()

        # Skip phone numbers
        if "+91" in line:
            continue

        # Skip UTR line
        if re.fullmatch(r'\d{12}', line):
            continue

        matches = re.findall(
            r'[\d,]+(?:\.\d{2})?',
            line
        )

        for match in matches:

            try:

                value = float(
                    match.replace(",", "")
                )

                # Ignore very large numbers
                if value > 1000000:
                    continue

                amounts.append(value)

            except:
                pass

    if amounts:
        data["amount"] = max(amounts)

    return data

data=read_transaction(r"images\gpay\2.jpeg")

results=parse_payment(data)
print(data)
print(results)