from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from app import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(100), nullable=True)
    language = db.Column(db.String(10), default='en')  # Language preference
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    buyer_transactions = db.relationship('EscrowTransaction', backref='buyer', foreign_keys='EscrowTransaction.buyer_id')
    seller_transactions = db.relationship('EscrowTransaction', backref='seller', foreign_keys='EscrowTransaction.seller_id')

class EscrowTransaction(db.Model):
    __tablename__ = 'escrow_transactions'

    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(20), default='awaiting_payment')
    blockchain = db.Column(db.String(50), nullable=True)  # BEP20, ERC20, etc.
    buyer_wallet = db.Column(db.String(100), nullable=True)
    seller_wallet = db.Column(db.String(100), nullable=True)
    fee_amount = db.Column(db.Numeric(10, 2), default=0.50)  # Fixed $0.50 fee
    fee_paid = db.Column(db.Boolean, default=False)
    chat_id = db.Column(db.String(100), nullable=True)  # Group chat ID where transaction was created
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    payment_confirmed_at = db.Column(db.DateTime, nullable=True)
    account_provided_at = db.Column(db.DateTime, nullable=True)
    account_verified_at = db.Column(db.DateTime, nullable=True)

    # Relationship with disputes
    disputes = db.relationship('Dispute', backref='transaction', lazy=True)

class Dispute(db.Model):
    __tablename__ = 'disputes'

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('escrow_transactions.id'), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reason = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(20), default='open')  # open, resolved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolution_notes = db.Column(db.String(500), nullable=True)

    # Relationship with user who created the dispute
    created_by = db.relationship('User', backref='disputes')
