import uuid
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional


from dotenv import load_dotenv

load_dotenv(override=True)

from backend.src.api.telemetry import setup_telemetry
setup_telemetry()
from backend.src.graph.workflow import app as compliance_graph
logging.basicConfig(level = logging.INFO)

logger =  logging.getlogger("api-server")

app= FastAPI(

title = "Brand Gaurdian"
description="API FOR AUDITING"
version="1.0.0"
)

class AuditRequest(BaseModel):




