"""
models.py
---------
Defines the SQLAlchemy model for the bank account system.
"""

from sqlalchemy import Column, Integer, Float, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Account(Base):
    __tablename__ = 'accounts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_number = Column(String, unique=True, nullable=False)
    balance = Column(Float, default=0.0)
    
    def __init__(self, account_number, balance=0.0):
        self.account_number = account_number
        self.balance = balance
