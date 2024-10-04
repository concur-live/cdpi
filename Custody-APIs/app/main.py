from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi.middleware.cors import CORSMiddleware
from app.routes.consent_signing_route import *

app = FastAPI(
    title="Custody APIs",
    docs_url="/api"
)

# scheduler = BackgroundScheduler()
# scheduler.add_job(check_cp, "interval", minutes=10) 
# scheduler.start()

# @app.on_event("shutdown")
# def shutdown_event():
#     scheduler.shutdown()

app.include_router(consentSigningRoute)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"]
)