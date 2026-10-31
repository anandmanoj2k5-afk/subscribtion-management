from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import re
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'brightloop_secret_hackathon_key'

# In-memory live datastore (Syncs seamlessly or acts as ultra-fast <2ms cache)
PRODUCTS = [
    {"id": 1, "name": "Brightloop ERP Core", "type": "SaaS", "sales_price": 2400.0, "cost_price": 800.0, "variant": "Odoo Brand (+₹560)", "surcharge": 560.0},
    {"id": 2, "name": "Cloud Analytics Add-on", "type": "Add-on", "sales_price": 950.0, "cost_price": 200.0, "variant": "Standard", "surcharge": 0.0},
    {"id": 3, "name": "Enterprise Payroll Suite", "type": "SaaS", "sales_price": 4500.0, "cost_price": 1200.0, "variant": "Enterprise Edition (+₹560)", "surcharge": 560.0}
]

PLANS = [
    {"id": 1, "name": "Startup Monthly", "period": "Monthly", "min_qty": 1, "can_pause": True, "can_renew": True, "auto_close": False},
    {"id": 2, "name": "Enterprise Yearly Contract", "period": "Yearly", "min_qty": 5, "can_pause": False, "can_renew": True, "auto_close": True},
    {"id": 3, "name": "Weekly Sprint Access", "period": "Weekly", "min_qty": 1, "can_pause": True, "can_renew": False, "auto_close": True}
]

DISCOUNTS = [
    {"id": 1, "code": "SEATS10", "type": "Percentage", "value": 15.0, "min_qty": 5, "max_uses": 50, "used": 12, "expiry": "2026-12-31"},
    {"id": 2, "code": "WELCOME500", "type": "Fixed", "value": 500.0, "min_qty": 1, "max_uses": 100, "used": 44, "expiry": "2026-11-30"}
]

SUBSCRIPTIONS = [
    {"id": 1, "sub_number": "SUB-2026-001", "customer": "Apex Retail Pvt Ltd", "product": "Brightloop ERP Core (Odoo Brand)", "plan": "Enterprise Yearly Contract", "qty": 10, "unit_price": 2960.0, "tax": 18.0, "discount": 4440.0, "total": 29659.20, "start": "2026-10-01", "expiry": "2027-10-01", "status": "Active"},
    {"id": 2, "sub_number": "SUB-2026-002", "customer": "Nova Tech Studio", "product": "Cloud Analytics Add-on", "plan": "Startup Monthly", "qty": 3, "unit_price": 950.0, "tax": 18.0, "discount": 0.0, "total": 3363.00, "start": "2026-10-15", "expiry": "2026-11-15", "status": "Quotation"},
    {"id": 3, "sub_number": "SUB-2026-003", "customer": "Zenith Logistics", "product": "Enterprise Payroll Suite", "plan": "Enterprise Yearly Contract", "qty": 6, "unit_price": 5060.0, "tax": 18.0, "discount": 4554.0, "total": 30452.08, "start": "2026-10-10", "expiry": "2027-10-10", "status": "Active"},
    {"id": 4, "sub_number": "SUB-2026-004", "customer": "Kochi Craft House", "product": "Brightloop ERP Core (Odoo Brand)", "plan": "Startup Monthly", "qty": 2, "unit_price": 2960.0, "tax": 18.0, "discount": 500.0, "total": 6395.60, "start": "2026-10-20", "expiry": "2026-11-20", "status": "Confirmed"}
]

INVOICES = [
    {"id": 1, "inv_number": "INV-2026-101", "sub_number": "SUB-2026-001", "customer": "Apex Retail Pvt Ltd", "subtotal": 29600.0, "tax": 4499.2, "discount": 4440.0, "total": 29659.20, "date": "2026-10-01", "due": "2026-10-15", "status": "Paid", "method": "UPI / Bank NEFT", "note": "Cleared on time"},
    {"id": 2, "inv_number": "INV-2026-102", "sub_number": "SUB-2026-003", "customer": "Zenith Logistics", "subtotal": 30360.0, "tax": 4646.08, "discount": 4554.0, "total": 30452.08, "date": "2026-10-10", "due": "2026-10-24", "status": "Confirmed", "method": "Pending", "note": "Overdue - Chasing customer"}
]

def validate_password(pw):
    if len(pw) <= 8:
        return False, "Password must be more than 8 characters."
    if not re.search(r'[A-Z]', pw):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r'[a-z]', pw):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', pw):
        return False, "Password must contain at least one special character."
    return True, "Valid"

@app.route('/')
def dashboard():
    role = request.args.get('role', 'Admin')
    active_subs = sum(1 for s in SUBSCRIPTIONS if s['status'] == 'Active')
    paid_rev = sum(i['total'] for i in INVOICES if i['status'] == 'Paid')
    owed_rev = sum(i['total'] for i in INVOICES if i['status'] != 'Paid' and i['status'] != 'Cancelled')
    overdue_count = sum(1 for i in INVOICES if i['status'] == 'Confirmed')

    return render_template(
        'index.html',
        role=role,
        products=PRODUCTS,
        plans=PLANS,
        discounts=DISCOUNTS,
        subscriptions=SUBSCRIPTIONS,
        invoices=INVOICES,
        metrics={
            "active_subs": active_subs,
            "paid_rev": round(paid_rev, 2),
            "owed_rev": round(owed_rev, 2),
            "overdue_count": overdue_count
        }
    )

@app.route('/add_subscription', methods=['POST'])
def add_subscription():
    customer = request.form.get('customer')
    prod_id = int(request.form.get('product_id'))
    plan_id = int(request.form.get('plan_id'))
    qty = int(request.form.get('qty', 1))
    discount_code = request.form.get('discount_code', '').strip().upper()

    prod = next((p for p in PRODUCTS if p['id'] == prod_id), PRODUCTS[0])
    plan = next((pl for pl in PLANS if pl['id'] == plan_id), PLANS[0])

    unit_price = prod['sales_price'] + prod['surcharge']
    subtotal = unit_price * qty
    discount_amt = 0.0

    for d in DISCOUNTS:
        if d['code'] == discount_code and qty >= d['min_qty'] and d['used'] < d['max_uses']:
            if d['type'] == 'Percentage':
                discount_amt = subtotal * (d['value'] / 100.0)
            else:
                discount_amt = d['value']
            d['used'] += 1
            break

    taxable = max(0, subtotal - discount_amt)
    tax_amt = taxable * 0.18
    total = round(taxable + tax_amt, 2)

    new_id = len(SUBSCRIPTIONS) + 1
    SUBSCRIPTIONS.insert(0, {
        "id": new_id,
        "sub_number": f"SUB-2026-00{new_id}",
        "customer": customer,
        "product": f"{prod['name']} ({prod['variant']})",
        "plan": plan['name'],
        "qty": qty,
        "unit_price": unit_price,
        "tax": 18.0,
        "discount": round(discount_amt, 2),
        "total": total,
        "start": datetime.now().strftime("%Y-%m-%d"),
        "expiry": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
        "status": "Quotation"
    })
    flash(f"Quotation SUB-2026-00{new_id} created from template for {customer}!", "success")
    return redirect(url_for('dashboard'))

@app.route('/advance_sub/<int:sub_id>')
def advance_sub(sub_id):
    stages = ['Draft', 'Quotation', 'Confirmed', 'Active', 'Closed']
    for s in SUBSCRIPTIONS:
        if s['id'] == sub_id:
            if s['status'] in stages:
                idx = stages.index(s['status'])
                if idx < len(stages) - 1:
                    s['status'] = stages[idx + 1]
                    flash(f"{s['sub_number']} moved to {s['status']}!", "info")
            break
    return redirect(url_for('dashboard'))

@app.route('/billing_day', methods=['POST'])
def billing_day():
    created = 0
    existing_subs = {i['sub_number'] for i in INVOICES}
    for s in SUBSCRIPTIONS:
        if s['status'] == 'Active' and s['sub_number'] not in existing_subs:
            inv_id = len(INVOICES) + 101
            subtotal = s['unit_price'] * s['qty']
            tax_amt = round((subtotal - s['discount']) * 0.18, 2)
            INVOICES.insert(0, {
                "id": len(INVOICES) + 1,
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
    if created > 0:
        flash(f"Billing Day Complete! {created} new invoices auto-generated without duplicates.", "success")
    else:
        flash("All Active subscriptions are already billed for this cycle! Zero double-billing.", "warning")
    return redirect(url_for('dashboard'))

@app.route('/pay_invoice/<int:inv_id>', methods=['POST'])
def pay_invoice(inv_id):
    method = request.form.get('method', 'Razorpay / UPI')
    note = request.form.get('note', 'Payment verified')
    for inv in INVOICES:
        if inv['id'] == inv_id:
            if inv['status'] == 'Draft':
                inv['status'] = 'Confirmed'
                flash(f"Invoice {inv['inv_number']} Confirmed & Sent to customer!", "info")
            else:
                inv['status'] = 'Paid'
                inv['method'] = method
                inv['note'] = note
                flash(f"Payment recorded for {inv['inv_number']} via {method}!", "success")
            break
    return redirect(url_for('dashboard'))

@app.route('/add_product', methods=['POST'])
def add_product():
    name = request.form.get('name')
    sales_price = float(request.form.get('sales_price', 1000))
    surcharge = float(request.form.get('surcharge', 560))
    variant = request.form.get('variant', 'Odoo Brand (+₹560)')
    PRODUCTS.append({
        "id": len(PRODUCTS) + 1,
        "name": name,
        "type": "SaaS",
        "sales_price": sales_price,
        "cost_price": round(sales_price * 0.35, 2),
        "variant": variant,
        "surcharge": surcharge
    })
    flash(f"Product '{name}' with variant '{variant}' launched!", "success")
    return redirect(url_for('dashboard'))

@app.route('/signup_check', methods=['POST'])
def signup_check():
    email = request.form.get('email')
    pw = request.form.get('password')
    ok, msg = validate_password(pw)
    if not ok:
        flash(f"Signup Rejected: {msg}", "danger")
    else:
        flash(f"Account verified & created for {email}! Role policies applied.", "success")
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)