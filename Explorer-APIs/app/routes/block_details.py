from fastapi import FastAPI, Request, HTTPException, APIRouter
from pydantic import BaseModel
from typing import List, Optional, Any, Literal
import requests
from datetime import datetime, timezone
from app.models.QuorumBlockModel import *
from app.schema.utils import *

blockRoute = APIRouter()

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

def api_auth(request: Request):
    # Implement your authentication logic here
    return True  # Assume the session is valid for demonstration

@blockRoute.post("/get-block", tags = ["Query Blockchain"])
async def get_block(request: BlockRequestSpecific):
    quorum_block = QuorumBlock(
        statusText="error",
        number="-1",
        number_int="-1",
        hash="",
        transactionsRoot="",
        stateRoot="",
        receiptsRoot="",
        miner="",
        extraData="",
        size="",
        gasUsed="",
        gasLimit="",
        timestamp=datetime.now(),
        uncles=[],
        transactions=[]
    )

    if not api_auth(request):
        raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        # Convert block number to hexadecimal
        block_number_hex = hex(request.blockNumber)

        # Make the eth_getBlockByNumber RPC call
        eth_block_by_number = eth_api_call(request.rpcUrl, "eth_getBlockByNumber", [block_number_hex, True])
        result = eth_block_by_number.get("result")
        if result:
            quorum_block.statusText = "success"
            quorum_block.number = result.get("number", "")
            quorum_block.hash = result.get("hash", "")
            quorum_block.transactionsRoot = result.get("transactionsRoot", "")
            quorum_block.stateRoot = result.get("stateRoot", "")
            quorum_block.receiptsRoot = result.get("receiptsRoot", "")
            quorum_block.miner = result.get("miner", "")
            quorum_block.extraData = result.get("extraData", "")
            quorum_block.size = result.get("size", "")
            quorum_block.gasUsed = result.get("gasUsed", "")
            quorum_block.gasLimit = result.get("gasLimit", "")
            quorum_block.timestamp = result.get("timestamp", datetime.now())
            quorum_block.uncles = result.get("uncles", [])
            quorum_block.transactions = result.get("transactions", [])
            quorum_block.number_int = request.blockNumber
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail="Node is unreachable. Ensure ports are open and client is running!") from e

    return quorum_block

@blockRoute.post("/get-latest-blocks", tags = ["Query Blockchain"])
async def get_latest_blocks(request: BlockRequestGetLatest, blockCount: Literal["5", "10", "15", "20"] = "5" ):
    blocks = []
    block_count = int(blockCount)  # Fetch the number of blocks based on user input

    try:
        # Get the latest block number
        latest_block_response = eth_api_call(request.rpcUrl, "eth_blockNumber")
        latest_block_number_hex = latest_block_response.get("result")
        latest_block_number = int(latest_block_number_hex, 16)

        for i in range(block_count):
            quorum_block = QuorumBlock(
                statusText="error",
                number="-1",
                number_int=-1,  # Initialize with -1 or any default value
                hash="",
                transactionsRoot="",
                stateRoot="",
                receiptsRoot="",
                miner="",
                extraData="",
                size="",
                gasUsed="",
                gasLimit="",
                timestamp=datetime.now(),
                uncles=[],
                transactions=[]
            )

            try:
                block_number_hex = hex(latest_block_number - i)
                eth_block_by_number = eth_api_call(request.rpcUrl, "eth_getBlockByNumber", [block_number_hex, True])
                result = eth_block_by_number.get("result")
                
                if result:
                    quorum_block.statusText = "success"
                    quorum_block.number = result.get("number", "")
                    
                    # Convert the block number (in hex) to integer and store in number_int
                    if quorum_block.number:
                        quorum_block.number_int = int(quorum_block.number, 16)

                    quorum_block.hash = result.get("hash", "")
                    quorum_block.transactionsRoot = result.get("transactionsRoot", "")
                    quorum_block.stateRoot = result.get("stateRoot", "")
                    quorum_block.receiptsRoot = result.get("receiptsRoot", "")
                    quorum_block.miner = result.get("miner", "")
                    quorum_block.extraData = result.get("extraData", "")
                    quorum_block.size = result.get("size", "")
                    quorum_block.gasUsed = result.get("gasUsed", "")
                    quorum_block.gasLimit = result.get("gasLimit", "")
                    quorum_block.timestamp = result.get("timestamp", datetime.now())
                    quorum_block.uncles = result.get("uncles", [])
                    quorum_block.transactions = result.get("transactions", [])

                blocks.append(quorum_block)

            except requests.exceptions.RequestException as e:
                raise HTTPException(status_code=500, detail="Node is unreachable. Ensure ports are open and client is running!") from e

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail="Failed to fetch the latest block number") from e

    return blocks

@blockRoute.post("/get-block-transactions", tags = ["Query Blockchain"])
async def get_block_transactions(request: BlockRequestSpecific):
    try:
        block_number_hex = hex(request.blockNumber)
        block = eth_api_call(request.rpcUrl, "eth_getBlockByNumber", [block_number_hex, True])
        transactions = block.get("result", {}).get("transactions", [])
        return {"blockNumber": request.blockNumber, "transactions": transactions}
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail="Failed to fetch transactions") from e

@blockRoute.post("/get-transaction", tags = ["Query Blockchain"] , summary ="Takes hash of the transaction and outputs the transaction detail")
async def get_transaction(request: TransactionRequestUsingHash):
    try:
        transaction = eth_api_call(request.rpcUrl, "eth_getTransactionByHash", [request.txHash])
        return transaction.get("result", {})
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail="Failed to fetch transaction") from e

@blockRoute.post("/get-latest-transactions", tags = ["Query Blockchain"])
async def get_latest_transactions(request: BlockRequestGetLatest, blockCount: Literal["1","2","5", "10", "15", "20"] = "5" ):
    transactions = []
    block_count = int(blockCount)  # Fetch the number of blocks based on user input

    try:
        latest_block_response = eth_api_call(request.rpcUrl, "eth_blockNumber")
        latest_block_number = int(latest_block_response.get("result"), 16)

        for i in range(block_count):
            block_number_hex = hex(latest_block_number - i)
            block = eth_api_call(request.rpcUrl, "eth_getBlockByNumber", [block_number_hex, True])
            block_transactions = block.get("result", {}).get("transactions", [])
            transactions.extend(block_transactions)

        return {"transactions": transactions}
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail="Failed to fetch transactions") from e

# Function to find a block by timestamp
def find_block_by_timestamp(target_timestamp: datetime, rpc_url: str):
    # Ensure that the target timestamp is timezone-aware and in UTC
    if target_timestamp.tzinfo is None:
        target_timestamp = target_timestamp.replace(tzinfo=timezone.utc)
    else:
        target_timestamp = target_timestamp.astimezone(timezone.utc)

    latest_block = eth_api_call(rpc_url, "eth_blockNumber")
    latest_block_number = int(latest_block.get("result"), 16)

    for block_number in range(latest_block_number, 0, -1):
        block_number_hex = hex(block_number)
        eth_block_by_number = eth_api_call(rpc_url, "eth_getBlockByNumber", [block_number_hex, True])
        block_result = eth_block_by_number.get("result")

        if block_result:
            block_timestamp = int(block_result.get("timestamp"), 16)
            block_datetime = datetime.utcfromtimestamp(block_timestamp).replace(tzinfo=timezone.utc)

            # Compare block timestamp and target timestamp (both should be aware now)
            if block_datetime == target_timestamp:
                return block_result
            elif block_datetime < target_timestamp:
                break  # Once we go past the target timestamp, stop searching

    return None

@blockRoute.post("/get-block-by-timestamp", tags = ["Query Blockchain"])
async def get_block_by_timestamp(request: BlockRequestTimestamp):
    try:
        # Implement a binary search using eth_getBlockByNumber and timestamps to find closest block
        block = find_block_by_timestamp(request.timestamp, request.rpcUrl)
        return block
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail="Failed to fetch block") from e



