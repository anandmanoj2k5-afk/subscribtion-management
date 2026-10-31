# auth_billing.py - Managed by Adhish (Auth Policy, Billing Day Engine & Finance KPIs)
import re
from datetime import datetime, timedelta

def validate_password(pw):
    """Enforces >8 chars, 1 uppercase, 1 lowercase, 1 special char."""
    if len(pw) <= 8:
        return False, "Password must be more than 8 characters."
    if not re.search(r'[A-Z]', pw):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r'[a-z]', pw):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', pw):
        return False, "Password must contain at least one special character."
    return True, "Valid"

def run_billing_day_batch(subscriptions, invoices):
    """Auto-creates invoices from Active subscriptions without double-billing."""
    created = 0
    existing_subs = {i['sub_number'] for i in invoices}
    for s in subscriptions:
        if s['status'] == 'Active' and s['sub_number'] not in existing_subs:
            inv_id = len(invoices) + 101
            subtotal = s['unit_price'] * s['qty']
            tax_amt = round((subtotal - s['discount']) * 0.18, 2)
            invoices.insert(0, {
                "id": len(invoices) + 1,
                "inv_number": f"INV-2026-{inv_id}",
                "sub_number": s['sub_number'],
                "customer": s['customer'],
                "subtotal": subtotal,
                "tax": tax_amt,
                "discount": s['discount'],
                "total": s['total'],
                "date": datetime.now().strftime("%Y-%m-%d"),
                "due": (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d"),
                "status": "Draft",
                "method": "Unpaid",
                "note": "Auto-generated on Billing Day"
            })
            created += 1
    return created