from fastapi import FastAPI, Request, HTTPException
from typing import List, Optional, Any
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import requests
from datetime import datetime
from app.models.QuorumBlockModel import *
from app.routes.block_details import *
from app.routes.dp_interaction_route import *

app = FastAPI(
    title = "Explorer_APIs",
    docs_url = "/api"
)

app.include_router(blockRoute)
app.include_router(dpRoute)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"]
)