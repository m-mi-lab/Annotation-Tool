from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta, timezone
import jwt
import bcrypt
import csv
import io
import re
from collections import defaultdict
from bson import ObjectId

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-this-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Create the main app without a prefix
app = FastAPI(title="Social Determinants of Health Annotation Tool")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()

# User Roles
class UserRole:
    ADMIN = "admin"
    ANNOTATOR = "annotator"

# Social Determinants of Health Domains and Structured Tags
SDOH_DOMAINS = [
    "Economic Stability",
    "Education Access and Quality", 
    "Health Care Access and Quality",
    "Neighborhood and Built Environment",
    "Social and Community Context"
]

# Structured tag definitions (placeholder)
SDOH_TAG_STRUCTURE = {
    "Economic Stability": {"Employment": ["Employed", "Unemployed"]},
    "Social and Community Context": {"Social Cohesion": ["Social Isolation"]}
}

# Models and helpers omitted for brevity (existing content remains the same)

# ... existing endpoints above ...

@api_router.get("/analytics/projects")
async def get_projects_analytics(current_user: User = Depends(get_current_user)):
    """Per-project analytics summary."""
    # Map documents by project
    docs = await db.documents.find({}, {"_id": 0}).to_list(10000)
    projects: Dict[str, Dict[str, Any]] = {}
    for d in docs:
        pname = d.get('project_name') or 'Unassigned'
        if pname not in projects:
            projects[pname] = {
                'project_name': pname,
                'documents': [],
                'document_ids': [],
                'documents_count': 0,
                'total_sentences': 0,
                'annotated_sentences': 0,
                'annotators_count': 0,
                'last_activity': None,
            }
        projects[pname]['documents'].append({'id': d['id'], 'filename': d.get('filename')})
        projects[pname]['document_ids'].append(d['id'])
    if not projects:
        return []
    # For each project, compute aggregates
    for pname, p in projects.items():
        ids = p['document_ids']
        p['documents_count'] = len(ids)
        # Sentences count
        p['total_sentences'] = await db.sentences.count_documents({"document_id": {"$in": ids}})
        if p['total_sentences'] == 0:
            continue
        # Sentence ids in project
        sentence_ids = await db.sentences.distinct("id", {"document_id": {"$in": ids}})
        if sentence_ids:
            # Annotated sentence ids
            annotated_sentence_ids = await db.annotations.distinct("sentence_id", {"sentence_id": {"$in": sentence_ids}})
            p['annotated_sentences'] = len(annotated_sentence_ids)
            # Annotators
            annotators = await db.annotations.distinct("user_id", {"sentence_id": {"$in": sentence_ids}})
            p['annotators_count'] = len(annotators)
            # Last activity
            last = await db.annotations.find({"sentence_id": {"$in": sentence_ids}}, {"_id": 0, "created_at": 1}).sort("created_at", -1).limit(1).to_list(1)
            if last:
                p['last_activity'] = str(last[0].get('created_at'))
    # Progress
    result = []
    for pname, p in projects.items():
        if p['total_sentences'] == 0:
            progress = 0.0
        else:
            progress = p['annotated_sentences'] / p['total_sentences']
        result.append({
            'project_name': pname,
            'documents_count': p['documents_count'],
            'total_sentences': p['total_sentences'],
            'annotated_sentences': p['annotated_sentences'],
            'progress': progress,
            'annotators_count': p['annotators_count'],
            'last_activity': p['last_activity'],
        })
    # Sort by annotated_sentences desc
    result.sort(key=lambda x: x['annotated_sentences'], reverse=True)
    return result

@api_router.get("/analytics/projects-chart")
async def get_projects_chart(current_user: User = Depends(get_current_user)):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from io import BytesIO
    # Prepare data from projects analytics
    data = await get_projects_analytics(current_user)
    if not data:
        data = []
    labels = [d['project_name'] for d in data][:20]
    values = [d['annotated_sentences'] for d in data][:20]
    plt.figure(figsize=(10, 6))
    plt.barh(labels, values, color='#2563eb')
    plt.xlabel('Annotated Sentences'); plt.title('Projects by Annotated Sentences'); plt.tight_layout()
    buf = BytesIO(); plt.savefig(buf, format='png'); buf.seek(0)
    return StreamingResponse(buf, media_type='image/png')

# ... rest of server remains unchanged ...