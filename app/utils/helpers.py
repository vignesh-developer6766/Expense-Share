import re

CATEGORY_MAP = {
    "Food": {
        "icon": "bi-cup-hot-fill",
        "color": "#ED64A6",
        "bg_tint": "rgba(237, 100, 166, 0.12)",
    },
    "Transport": {
        "icon": "bi-car-front-fill",
        "color": "#319795",
        "bg_tint": "rgba(49, 151, 149, 0.12)",
    },
    "Shopping": {
        "icon": "bi-bag-check-fill",
        "color": "#3182CE",
        "bg_tint": "rgba(49, 130, 206, 0.12)",
    },
    "Entertainment": {
        "icon": "bi-film",
        "color": "#805AD5",
        "bg_tint": "rgba(128, 90, 213, 0.12)",
    },
    "Utilities": {
        "icon": "bi-lightning-charge-fill",
        "color": "#D69E2E",
        "bg_tint": "rgba(214, 158, 46, 0.12)",
    },
    "Travel": {
        "icon": "bi-airplane-engines-fill",
        "color": "#48BB78",
        "bg_tint": "rgba(72, 187, 120, 0.12)",
    },
    "Rent": {
        "icon": "bi-house-heart-fill",
        "color": "#E53E3E",
        "bg_tint": "rgba(229, 62, 62, 0.12)",
    },
    "Other": {
        "icon": "bi-sliders",
        "color": "#718096",
        "bg_tint": "rgba(113, 128, 150, 0.12)",
    },
}


def format_inr(number):
    try:
        amount = float(number)
        is_negative = amount < 0
        amount = abs(amount)
        s, decimal = f"{amount:.2f}".split(".")

        if len(s) <= 3:
            formatted = s
        else:
            last3 = s[-3:]
            remaining = s[:-3]
            groups = []
            while remaining:
                groups.append(remaining[-2:])
                remaining = remaining[:-2]
            groups.reverse()
            formatted = ",".join(groups) + "," + last3

        prefix = "-₹" if is_negative else "₹"
        return f"{prefix}{formatted}.{decimal}"
    except (ValueError, TypeError):
        return f"₹{number}"


def get_category_info(category_name):
    return CATEGORY_MAP.get(category_name, CATEGORY_MAP["Other"])
