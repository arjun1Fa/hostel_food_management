import re
from  transactions import read_transaction

def parse_payment(texts):

    data = {
        "sender": None,
        "receiver": None,
        "amount": None,
        "date": None,
        "time": None,
        "utr": None,
        "status": None
    }

    full_text = " ".join(texts)

    # ==================================
    # SENDER
    # ==================================
    for text in texts:

        match = re.search(
            r'^from[:\s]+(.+)$',
            text.strip(),
            re.IGNORECASE
        )

        if match:
            data["sender"] = match.group(1).strip()
            break

    # ==================================
    # RECEIVER
    # ==================================
    for i, text in enumerate(texts):

        lower = text.lower().strip()

        # To: Abhin C
        if lower.startswith("to:"):
            data["receiver"] = text.split(":", 1)[1].strip()
            break

        # Paid to
        if lower == "paid to":
            if i + 1 < len(texts):
                data["receiver"] = texts[i + 1].strip()
                break

        # Credited to (PhonePe)
        if lower == "credited to":
            if i + 1 < len(texts):
                data["receiver"] = texts[i + 1].strip()
                break

        # Payment Received by XYZ
        match = re.search(
            r'payment\s+received\s+by\s+(.+)',
            text,
            re.IGNORECASE
        )

        if match:
            data["receiver"] = match.group(1).strip()
            break

    # ==================================
    # AMOUNT
    # ==================================
    amount_candidates = []

    for text in texts:

        lower = text.lower()

        if lower.startswith("from"):
            continue

        if lower.startswith("to"):
            continue

        if "+" in text:
            continue

        if "transaction id" in lower:
            continue

        if "utr" in lower:
            continue

        # ₹100
        matches = re.findall(
            r'₹\s*([\d,]+(?:\.\d{2})?)',
            text
        )

        for value in matches:

            try:
                amount_candidates.append(
                    float(value.replace(",", ""))
                )
            except:
                pass

        # Standalone number
        if re.fullmatch(
            r'[\d,]+(?:\.\d{2})?',
            text.strip()
        ):

            value = text.replace(",", "")

            try:

                number = float(value)

                # Ignore years
                if 1900 <= number <= 2100:
                    continue

                # Ignore long IDs
                if len(value) >= 10:
                    continue

                # Ignore unrealistic amounts
                if number > 100000:
                    continue

                amount_candidates.append(number)

            except:
                pass

    if amount_candidates:
        data["amount"] = max(amount_candidates)

    # ==================================
    # DATE
    # ==================================
    date_patterns = [

        # 10 Jun 2026
        r'(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})',

        # 10th Jun 26
        r'(\d{1,2}(?:st|nd|rd|th)\s+[A-Za-z]{3,9}\s+\d{2,4})',

        # 10/06/2026
        r'(\d{1,2}/\d{1,2}/\d{4})',

        # 2026-06-10
        r'(\d{4}-\d{2}-\d{2})'
    ]

    for pattern in date_patterns:

        match = re.search(
            pattern,
            full_text,
            re.IGNORECASE
        )

        if match:
            data["date"] = match.group(1)
            break

    # ==================================
    # TIME
    # ==================================
    time_match = re.search(
        r'(\d{1,2}:\d{2}\s*[APap][Mm])',
        full_text
    )

    if time_match:
        data["time"] = time_match.group(1)

    # ==================================
    # STATUS
    # ==================================
    status_words = [
        "completed",
        "successful",
        "success",
        "payment received",
        "payment successful",
        "paid"
    ]

    for text in texts:

        lower = text.lower()

        for status in status_words:

            if status in lower:
                data["status"] = status.title()
                break

    # ==================================
    # UTR
    # ==================================

    # 1. UTR:417959560328
    for text in texts:

        match = re.search(
            r'utr\s*[:\-]?\s*(\d{12})',
            text,
            re.IGNORECASE
        )

        if match:
            data["utr"] = match.group(1)
            break

    # 2. UPI Transaction ID line
    if data["utr"] is None:

        for text in texts:

            match = re.search(
                r'upi\s*transaction\s*id\s*[:\-]?\s*(\d{12})',
                text,
                re.IGNORECASE
            )

            if match:
                data["utr"] = match.group(1)
                break

    # 3. Next line after transaction id
    if data["utr"] is None:

        for i, text in enumerate(texts):

            if "transaction id" in text.lower():

                if i + 1 < len(texts):

                    candidate = texts[i + 1].strip()

                    digits = "".join(
                        re.findall(r'\d', candidate)
                    )

                    if len(digits) >= 12:
                        data["utr"] = digits[:12]
                        break

    # 4. Fallback standalone 12 digit number
    if data["utr"] is None:

        for text in texts:

            matches = re.findall(
                r'\b\d{12}\b',
                text
            )

            for candidate in matches:

                # Ignore phone numbers starting with 91
                if candidate.startswith("91"):
                    continue

                data["utr"] = candidate
                break

            if data["utr"]:
                break

    return data
