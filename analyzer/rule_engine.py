import re


def check_rules(message):
    message_lower = message.lower()

    flags = []

    # --------------------------------
    # 1. Upfront payment detection
    # --------------------------------

    payment_words = [
        "registration fee",
        "processing fee",
        "administrative fee",
        "application fee",
        "recruitment fee",
        "placement fee",
        "pay",
        "payment",
        "deposit",
        "transfer money"
    ]

    # Check whether the message explicitly says that
    # no payment/fee is required.
    no_payment_patterns = [
        r"no\s+(registration\s+)?fee",
        r"no\s+payment\s+(is\s+)?required",
        r"no\s+fees",
        r"without\s+(any\s+)?fee",
        r"there\s+are\s+no\s+fees"
    ]

    no_payment = any(
        re.search(pattern, message_lower)
        for pattern in no_payment_patterns
    )

    # Only flag payment if there is payment-related language
    # AND the message does not explicitly negate it.
    if not no_payment:
        if any(word in message_lower for word in payment_words):

            payment_request_patterns = [
                r"pay\s+(rs\.?|lkr|rm|usd|\$)?\s*\d+",
                r"pay\s+the\s+fee",
                r"pay\s+an?\s+\w+\s+fee",
                r"send\s+(the\s+)?payment",
                r"transfer\s+(the\s+)?money",
                r"deposit\s+(the\s+)?money",
                r"registration\s+fee",
                r"processing\s+fee",
                r"administrative\s+fee",
                r"application\s+fee",
                r"placement\s+fee"
            ]

            if any(
                re.search(pattern, message_lower)
                for pattern in payment_request_patterns
            ):
                flags.append("upfront payment request")

    # --------------------------------
    # 2. Urgency
    # --------------------------------

    urgency_patterns = [
        r"\bimmediately\b",
        r"\burgent\b",
        r"\btoday\b",
        r"\btomorrow\b",
        r"\blast chance\b",
        r"\blimited positions\b",
        r"\brespond by\b",
        r"\bact now\b"
    ]

    if any(
        re.search(pattern, message_lower)
        for pattern in urgency_patterns
    ):
        flags.append("urgency")

    # --------------------------------
    # 3. Sensitive information
    # --------------------------------

    sensitive_patterns = [
        r"\bnic\b",
        r"\bpassport\b",
        r"\bbank account\b",
        r"\bbank details\b",
        r"\bcard details\b",
        r"\botp\b",
        r"\bpassword\b"
    ]

    if any(
        re.search(pattern, message_lower)
        for pattern in sensitive_patterns
    ):
        flags.append("sensitive information request")

    return flags