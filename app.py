from flask import Flask, render_template, request, redirect, url_for, jsonify
import mysql.connector

app = Flask(__name__)

# MySQL Configuration (Update password if your local MySQL has one)
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '', 
    'database': 'subscription_db'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

@app.route('/')
def index():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM subscriptions ORDER BY next_renewal_date ASC")
        subscriptions = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('index.html', subscriptions=subscriptions)
    except Exception as e:
        # Fallback if DB isn't imported yet so the app still runs
        return render_template('index.html', subscriptions=[], db_error=str(e))

@app.route('/add', methods=['POST'])
def add_subscription():
    service_name = request.form.get('service_name')
    category = request.form.get('category')
    cost = request.form.get('cost')
    billing_cycle = request.form.get('billing_cycle')
    next_renewal_date = request.form.get('next_renewal_date')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO subscriptions (service_name, category, cost, billing_cycle, next_renewal_date)
        VALUES (%s, %s, %s, %s, %s)
    """, (service_name, category, cost, billing_cycle, next_renewal_date))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)