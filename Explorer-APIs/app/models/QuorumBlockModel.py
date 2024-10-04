from pydantic import BaseModel
from typing import List, Optional, Any, Literal
from datetime import datetime


class QuorumBlock(BaseModel):
    statusText: str
    number: str
    number_int: int
    hash: str
    transactionsRoot: str
    stateRoot: str
    receiptsRoot: str
    miner: str
    extraData: str
    size: str
    gasUsed: str
    gasLimit: str
    timestamp: Any
    uncles: List[str]
    transactions: List[dict]

class BlockRequestSpecific(BaseModel):
    blockNumber: int
    rpcUrl: str = "http://127.0.0.1:22000"

class BlockRequestGetLatest(BaseModel):
    rpcUrl: str = "http://127.0.0.1:22000"

class TransactionRequestUsingHash(BaseModel):
    rpcUrl: str = "http://127.0.0.1:22000"  # The RPC URL to connect to the Ethereum node
    txHash: str  # Wallet address to filter transactions for

class BlockRequestTimestamp(BaseModel):
    rpcUrl: str
    timestamp: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "rpcUrl": "http://127.0.0.1:22000",
                "timestamp": "2024-09-03T12:30:00"
            }
        }
