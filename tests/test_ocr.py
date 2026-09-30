import pytest
from app.ocr.receipt_processor import ReceiptProcessor


def test_receipt_text_processor():
    raw_ocr_text = """
    ABC RESTAURANT
    123 Main Street
    Tax Invoice
    Date: 28/09/2026

    2x Pizza - 800.00
    1x Drinks - 450.00

    Grand Total: ₹1250.00
    Thank you for dining with us!
    """

    res = ReceiptProcessor.process_receipt_text(raw_ocr_text)

    assert res["vendor"] == "Abc Restaurant"
    assert res["amount"] == 1250.0
    assert res["category"] == "Food"
    assert "28/09/2026" in res["date_string"]
