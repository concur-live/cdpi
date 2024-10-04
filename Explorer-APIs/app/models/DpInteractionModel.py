from pydantic import BaseModel
from typing import List, Optional, Any, Literal
from datetime import datetime

class TransactionRequestUsingWalletAddress(BaseModel):
    rpcUrl: str = "http://127.0.0.1:22000"
    walletAddress: str