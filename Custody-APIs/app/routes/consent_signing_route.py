from fastapi import FastAPI, APIRouter, HTTPException, Query
from pydantic import BaseModel
from web3 import Web3
import json
from web3.exceptions import ContractLogicError, TransactionNotFound
import datetime
from app.config.private import user_wallet_details, signed_txn_collection
from typing import Optional
from datetime import datetime, UTC
import hashlib

consentSigningRoute = APIRouter()

# Ethereum connection setup (if needed)
w3 = Web3()

def hash_value(value: str) -> str:
    """Hashes the given value using SHA-256."""
    return hashlib.sha256(value.encode()).hexdigest()

@consentSigningRoute.get("/get-user-wallet-address")
async def get_wallet_details(
    dp_id: str,
    dp_email: Optional[str] = Query(None),
    dp_mobile: Optional[str] = Query(None)
):
    try:
        # Search for an existing wallet with the provided dp_id
        existing_wallet = user_wallet_details.find_one({"dp_id": dp_id})

        # Hash the email and mobile if provided
        dp_email_hash = hash_value(dp_email) if dp_email else None
        dp_mobile_hash = hash_value(dp_mobile) if dp_mobile else None

        # If a wallet already exists for the dp_id
        if existing_wallet:
            update_data = {}

            # Ensure dp_email & dp_email_hash are stored correctly
            if dp_email and dp_email not in existing_wallet.get("dp_email", []):
                update_data["dp_email"] = existing_wallet.get("dp_email", []) + [dp_email]
                update_data["dp_email_hash"] = existing_wallet.get("dp_email_hash", []) + [dp_email_hash]

            # Ensure dp_mobile & dp_mobile_hash are stored correctly
            if dp_mobile and dp_mobile not in existing_wallet.get("dp_mobile", []):
                update_data["dp_mobile"] = existing_wallet.get("dp_mobile", []) + [dp_mobile]
                update_data["dp_mobile_hash"] = existing_wallet.get("dp_mobile_hash", []) + [dp_mobile_hash]

            # Only update if necessary
            if update_data:
                user_wallet_details.update_one(
                    {"_id": existing_wallet["_id"]},
                    {"$set": update_data}
                )

            return {"wallet_address": existing_wallet["wallet_address"]}

        # If no wallet exists for the dp_id, search for an unassigned wallet
        unassigned_wallet = user_wallet_details.find_one({"dp_id": None})

        # If no unassigned wallet is found, raise an exception
        if not unassigned_wallet:
            raise HTTPException(
                status_code=404, detail="No available unassigned wallets")

        # Prepare the update data for the unassigned wallet
        update_data = {"dp_id": dp_id}
        if dp_email:
            update_data["dp_email"] = [dp_email]
            update_data["dp_email_hash"] = [dp_email_hash]
        if dp_mobile:
            update_data["dp_mobile"] = [dp_mobile]
            update_data["dp_mobile_hash"] = [dp_mobile_hash]

        # Assign the unassigned wallet to the user
        user_wallet_details.update_one(
            {"_id": unassigned_wallet["_id"]},
            {"$set": update_data}
        )

        return {"wallet_address": unassigned_wallet["wallet_address"]}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An error occurred: {str(e)}")


@consentSigningRoute.post("/create-wallet-addresses")
async def create_wallet_addresses(n: int):
    try:
        wallet_data_list = []

        for _ in range(n):
            # Create a new Ethereum account (public/private key pair)
            account = w3.eth.account.create()

            # Store the wallet information in the specified structure
            wallet_data = {
                "dp_id": None,
                "dp_email": [],
                "dp_email_hash": [],
                "dp_mobile": [],
                "dp_mobile_hash": [],
                "wallet_address": account.address,
                "private_key": account._private_key.hex(),
                "signature_count": 0
            }

            # Append to the list for bulk insertion
            wallet_data_list.append(wallet_data)

        # Insert all created wallets into MongoDB
        result = user_wallet_details.insert_many(wallet_data_list)

        return {
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An error occurred: {str(e)}")


class BuildTransactionData(BaseModel):
    dp_id: str
    transaction: dict
    is_signed: bool


@consentSigningRoute.post("/send-build-transaction")
async def receive_build_transaction(build_txn_data: BuildTransactionData):
    try:
        # Retrieve the wallet details for the dp_id from user_wallet_details
        user_wallet_data = user_wallet_details.find_one(
            {"dp_id": build_txn_data.dp_id})
        if not user_wallet_data:
            raise HTTPException(
                status_code=404, detail="Wallet details not found for the given dp_id")

        wallet_address = user_wallet_data.get("wallet_address")
        private_key = user_wallet_data.get("private_key")

        if not wallet_address or not private_key:
            raise HTTPException(
                status_code=500, detail="Wallet address or private key not found")

        # Build the transaction from received data
        txn = build_txn_data.transaction

        # Ensure nonce is up to date
        # txn['nonce'] = w3.eth.get_transaction_count(wallet_address)

        # Sign the transaction
        signed_txn = w3.eth.account.sign_transaction(
            txn, private_key=private_key)

        # Store the signed transaction in `signed_txn_collection`
        signed_txn_data = {
            "signed_transaction": signed_txn.raw_transaction.hex(),
            "created_at": datetime.now(UTC)
        }
        signed_txn_id = signed_txn_collection.insert_one(
            signed_txn_data).inserted_id

        # Update `last_signed_at` and increment `signature_count`
        user_wallet_details.update_one(
            {"dp_id": build_txn_data.dp_id},
            {"$set": {"last_signed_at": datetime.now(UTC)},
             "$inc": {"signature_count": 1}}
        )

        return {
            "status": "success",
            "signed_txn_id": str(signed_txn_id),
            "signed_transaction": signed_txn.raw_transaction.hex()
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An error occurred: {str(e)}")
