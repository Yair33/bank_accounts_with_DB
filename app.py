"""
app.py
------
This module sets up the Flask application and defines the API routes for managing bank accounts.
It uses SQLAlchemy to persist account data in a PostgreSQL database.
"""

from dotenv import load_dotenv
import os
import random
from decimal import Decimal, InvalidOperation
from flask import Flask, jsonify, request
from flask_cors import CORS

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from models import Base, Account  # Import our SQLAlchemy models

# Load environment variables from .env
load_dotenv()

# Get DATABASE_URL from environment variables
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set.")

# Set up SQLAlchemy engine and session
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(bind=engine)  # Create tables if they do not exist
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

app = Flask(__name__)
CORS(app)

# Define a maximum allowed amount for deposit/withdrawal (adjust as needed)
MAX_AMOUNT = Decimal('99999999')

@app.teardown_appcontext
def remove_session(exception=None):
    """Remove the SQLAlchemy session at the end of the request."""
    SessionLocal.remove()

@app.route('/accounts', methods=['POST'])
def create_account():
    """
    Create a new bank account with an optional initial balance.
    
    Returns:
        JSON response containing the account number and balance with status code 201.
    """
    data = request.get_json()
    if data is None:
        return jsonify({"error": "Invalid or missing JSON payload"}), 400

    balance = data.get("balance", 0.0)
    
    # Generate a unique account number using random numbers.
    account_number = str(random.randint(1000, 9999))
    
    db = SessionLocal()
    # Create a new account instance
    new_account = Account(account_number=account_number, balance=balance)
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    db.close()
    
    return jsonify({"account_number": new_account.account_number, "balance": new_account.balance}), 201

@app.route('/accounts/<account_number>/balance', methods=['GET'])
def get_balance(account_number):
    """
    Retrieve the current balance of the specified account.
    
    Returns:
        JSON response with the balance, or an error if the account is not found.
    """
    db = SessionLocal()
    account = db.query(Account).filter_by(account_number=account_number).first()
    db.close()
    if not account:
        return jsonify({"error": "Account not found"}), 404
    return jsonify({"balance": account.balance})

@app.route('/accounts/<account_number>/deposit', methods=['POST'])
def deposit(account_number):
    """
    Deposit a specified amount into the account.
    
    Validates that the amount is positive, non-zero, does not exceed the maximum value,
    and has at most 2 decimal places.
    
    Returns:
        JSON response with the updated balance or an appropriate error message.
    """
    db = SessionLocal()
    account = db.query(Account).filter_by(account_number=account_number).first()
    if not account:
        db.close()
        return jsonify({"error": "Account not found"}), 404

    data = request.get_json()
    if data is None or "amount" not in data:
        db.close()
        return jsonify({"error": "Invalid or missing JSON payload or 'amount'"}), 400

    amount = data.get("amount")
    try:
        d = Decimal(str(amount))
    except InvalidOperation:
        db.close()
        return jsonify({"error": "Deposit failed - Amount must be numeric and have at most 2 decimal places"}), 400

    if d < 0:
        db.close()
        return jsonify({"error": "Amount cannot be negative"}), 400
    if d == 0:
        db.close()
        return jsonify({"error": "Amount must be greater than zero"}), 400
    if d.as_tuple().exponent < -2:
        db.close()
        return jsonify({"error": "Deposit failed - Amount must have at most 2 decimal places"}), 400
    if d > MAX_AMOUNT:
        db.close()
        return jsonify({"error": "Amount exceeds maximum allowed value"}), 400

    # Update the account balance
    account.balance += float(d)
    db.commit()
    updated_balance = account.balance
    db.close()
    return jsonify({"balance": updated_balance})

@app.route('/accounts/<account_number>/withdraw', methods=['POST'])
def withdraw(account_number):
    """
    Withdraw a specified amount from the account.
    
    Validates that the amount is positive, non-zero, does not exceed the maximum value,
    and has at most 2 decimal places.
    
    Returns:
        JSON response with the updated balance or an appropriate error message.
    """
    db = SessionLocal()
    account = db.query(Account).filter_by(account_number=account_number).first()
    if not account:
        db.close()
        return jsonify({"error": "Account not found"}), 404

    data = request.get_json()
    if data is None or "amount" not in data:
        db.close()
        return jsonify({"error": "Invalid or missing JSON payload or 'amount'"}), 400

    amount = data.get("amount")
    try:
        d = Decimal(str(amount))
    except InvalidOperation:
        db.close()
        return jsonify({"error": "Withdrawal failed - Amount must be numeric and have at most 2 decimal places"}), 400

    if d < 0:
        db.close()
        return jsonify({"error": "Amount cannot be negative"}), 400
    if d == 0:
        db.close()
        return jsonify({"error": "Amount must be greater than zero"}), 400
    if d.as_tuple().exponent < -2:
        db.close()
        return jsonify({"error": "Withdrawal failed - Amount must have at most 2 decimal places"}), 400
    if d > MAX_AMOUNT:
        db.close()
        return jsonify({"error": "Amount exceeds maximum allowed value"}), 400

    if account.balance < float(d):
        db.close()
        return jsonify({"error": "Insufficient balance"}), 400

    # Update the account balance for withdrawal
    account.balance -= float(d)
    db.commit()
    updated_balance = account.balance
    db.close()
    return jsonify({"balance": updated_balance})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    app.run(host=host, port=port)
