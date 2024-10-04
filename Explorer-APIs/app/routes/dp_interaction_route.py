from fastapi import FastAPI, Request, HTTPException, APIRouter
from pydantic import BaseModel
from typing import List
import requests
from datetime import datetime
from app.models.DpInteractionModel import *

dpRoute = APIRouter()

# Helper function to call the Ethereum JSON-RPC API
def eth_api_call(rpc_url: str, method: str, params: list = []):
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }
    response = requests.post(rpc_url, json=payload)
    response.raise_for_status()
    return response.json()

# API endpoint to get all transactions based on wallet address
@dpRoute.post("/get-transactions", tags=["Data Principle Query"], summary="Returns all the transactions from DP's wallet address")
async def get_transaction(request: TransactionRequestUsingWalletAddress):
    transactions = []

    try:
        # Get the latest block number to iterate through the chain
        latest_block_response = eth_api_call(request.rpcUrl, "eth_blockNumber")
        latest_block_number_hex = latest_block_response.get("result")
        latest_block_number = int(latest_block_number_hex, 16)

        # Iterate from block 0 to the latest block to find transactions involving the wallet address
        for block_number in range(0, latest_block_number + 1):
            block_number_hex = hex(block_number)
            eth_block_by_number = eth_api_call(request.rpcUrl, "eth_getBlockByNumber", [block_number_hex, True])
            block_result = eth_block_by_number.get("result")

            if block_result:
                # Iterate through all transactions in the block
                for tx in block_result.get("transactions", []):
                    # Check if the wallet address is either in 'from' or 'to' field
                    if tx.get("from") == request.walletAddress or tx.get("to") == request.walletAddress:
                        transactions.append(tx)

        # Return the list of transactions involving the wallet address
        if transactions:
            return {"status": "success", "transactions": transactions}
        else:
            return {"status": "success", "message": "No transactions found for the given wallet address."}

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail="Node is unreachable. Ensure ports are open and client is running.") from e