from langchain_core.tools import tool
from typing import Dict, List, Any
import json
import random
from datetime import datetime, timedelta

# Simulated banking database
MOCK_ACCOUNTS = {
    "user123": {
        "checking": {"balance": 2500.00, "account_id": "CHK-001"},
        "savings": {"balance": 15000.00, "account_id": "SAV-001"}
    }
}

MOCK_TRANSACTIONS = {
    "user123": [
        {"date": "2025-09-01", "description": "Coffee Shop", "amount": -4.50, "type": "debit"},
        {"date": "2025-09-02", "description": "Salary Deposit", "amount": 3000.00, "type": "credit"},
        {"date": "2025-08-30", "description": "Grocery Store", "amount": -89.23, "type": "debit"}
    ]
}

@tool
def get_account_balance(account_type: str = "checking") -> str:
    """
    Get current account balance for the user.
    
    Args:
        account_type: Type of account ('checking' or 'savings')
    
    Returns:
        JSON string with account balance information
    """
    user_id = "user123"  # In real app, get from session
    
    if user_id not in MOCK_ACCOUNTS:
        return json.dumps({"error": "Account not found"})
    
    if account_type not in MOCK_ACCOUNTS[user_id]:
        return json.dumps({"error": f"Account type {account_type} not found"})
    
    account_info = MOCK_ACCOUNTS[user_id][account_type]
    return json.dumps({
        "account_type": account_type,
        "balance": account_info["balance"],
        "account_id": account_info["account_id"],
        "timestamp": datetime.now().isoformat()
    })

@tool
def get_recent_transactions(limit: int = 5) -> str:
    """
    Get recent transaction history for the user.
    
    Args:
        limit: Maximum number of transactions to return
    
    Returns:
        JSON string with transaction history
    """
    user_id = "user123"
    
    if user_id not in MOCK_TRANSACTIONS:
        return json.dumps({"error": "No transaction history found"})
    
    transactions = MOCK_TRANSACTIONS[user_id][:limit]
    return json.dumps({
        "transactions": transactions,
        "count": len(transactions),
        "user_id": user_id
    })

@tool
def transfer_funds(to_account: str, amount: float, description: str = "") -> str:
    """
    Transfer funds to another account. REQUIRES USER CONFIRMATION.
    
    Args:
        to_account: Destination account identifier
        amount: Amount to transfer (positive number)
        description: Optional description for the transfer
    
    Returns:
        JSON string with transfer confirmation details
    """
    # Simulate security check
    if amount > 1000:
        return json.dumps({
            "status": "requires_verification",
            "message": "Transfers over $1000 require additional verification",
            "amount": amount,
            "to_account": to_account
        })
    
    # Simulate successful transfer
    transaction_id = f"TXN-{random.randint(100000, 999999)}"
    return json.dumps({
        "status": "completed",
        "transaction_id": transaction_id,
        "amount": amount,
        "to_account": to_account,
        "description": description,
        "timestamp": datetime.now().isoformat(),
        "message": "Transfer completed successfully"
    })

# Banking tools collection
banking_tools = [get_account_balance, get_recent_transactions, transfer_funds]