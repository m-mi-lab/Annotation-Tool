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

# Pydantic Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    full_name: str
    role: str = UserRole.ANNOTATOR
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = UserRole.ANNOTATOR

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class DocumentUpload(BaseModel):
    filename: str
    project_name: Optional[str] = None
    description: Optional[str] = None
    total_sentences: int

class Annotation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sentence_id: str
    user_id: str
    tags: List[Dict[str, str]] = []
    notes: Optional[str] = None
    skipped: bool = False
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class AnnotationCreate(BaseModel):
    sentence_id: str
    tags: List[Dict[str, str]] = []
    notes: Optional[str] = None
    skipped: bool = False

# Authentication helpers
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(user_id: str = Depends(verify_token)):
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Convert datetime to string if needed
    if isinstance(user.get('created_at'), datetime):
        user['created_at'] = user['created_at'].isoformat()
    
    return User(**user)

async def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))):
    """Optional authentication - returns None if no token provided"""
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if user is None:
            return None
        # Convert datetime to string if needed
        if isinstance(user.get('created_at'), datetime):
            user['created_at'] = user['created_at'].isoformat()
        return User(**user)
    except jwt.PyJWTError:
        return None

# Basic endpoints
@api_router.get("/")
async def root():
    return {"message": "SDOH Annotation API"}

@api_router.get("/domains")
async def get_domains():
    return SDOH_DOMAINS

@api_router.get("/tag-structure")
async def get_tag_structure():
    return SDOH_TAG_STRUCTURE

# Authentication endpoints
@api_router.post("/auth/register", response_model=User)
async def register(user_data: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        role=user_data.role
    )
    
    # Hash password and store
    user_dict = user.dict()
    user_dict["password"] = hash_password(user_data.password)
    
    await db.users.insert_one(user_dict)
    return user

@api_router.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    # Find user
    user = await db.users.find_one({"email": user_data.email})
    if not user or not verify_password(user_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create token
    access_token = create_access_token(data={"sub": user["id"]})
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# Document endpoints
@api_router.get("/documents")
async def get_documents(current_user: User = Depends(get_current_user)):
    documents = await db.documents.find({}, {"_id": 0}).to_list(1000)
    return documents

@api_router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    project_name: Optional[str] = None,
    description: Optional[str] = None,
    current_user: User = Depends(get_admin_user)
):
    # Read CSV content
    content = await file.read()
    csv_content = content.decode('utf-8')
    
    # Parse CSV and extract sentences
    csv_reader = csv.DictReader(io.StringIO(csv_content))
    sentences = []
    
    for row in csv_reader:
        # Extract text from discharge_summary column
        text = row.get('discharge_summary', '').strip()
        if text:
            # Split into sentences (simple approach)
            sentence_texts = re.split(r'[.!?]+', text)
            for sentence_text in sentence_texts:
                sentence_text = sentence_text.strip()
                if sentence_text:
                    sentence = {
                        "id": str(uuid.uuid4()),
                        "text": sentence_text,
                        "subject_id": row.get('patient_id', row.get('note_id', 'unknown')),
                        "document_id": "",  # Will be set after document creation
                        "created_at": datetime.utcnow().isoformat()
                    }
                    sentences.append(sentence)
    
    # Create document
    document_id = str(uuid.uuid4())
    document = {
        "id": document_id,
        "filename": file.filename,
        "project_name": project_name or "Default Project",
        "description": description,
        "total_sentences": len(sentences),
        "uploaded_by": current_user.id,
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Set document_id for sentences
    for sentence in sentences:
        sentence["document_id"] = document_id
    
    # Insert document and sentences
    await db.documents.insert_one(document)
    if sentences:
        await db.sentences.insert_many(sentences)
    
    # Return document without ObjectId
    return {
        "id": document["id"],
        "filename": document["filename"],
        "project_name": document["project_name"],
        "description": document["description"],
        "total_sentences": document["total_sentences"],
        "uploaded_by": document["uploaded_by"],
        "created_at": document["created_at"]
    }

@api_router.get("/documents/{document_id}/sentences")
async def get_document_sentences(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    sentences = await db.sentences.find(
        {"document_id": document_id}, 
        {"_id": 0}
    ).to_list(1000)
    
    # Add existing annotations to each sentence
    for sentence in sentences:
        annotations = await db.annotations.find(
            {"sentence_id": sentence["id"]}, 
            {"_id": 0}
        ).to_list(100)
        sentence["annotations"] = annotations
    
    return sentences

# Annotation endpoints
@api_router.post("/annotations", response_model=Annotation)
async def create_annotation(
    annotation_data: AnnotationCreate,
    current_user: User = Depends(get_current_user)
):
    annotation = Annotation(
        sentence_id=annotation_data.sentence_id,
        user_id=current_user.id,
        tags=annotation_data.tags,
        notes=annotation_data.notes,
        skipped=annotation_data.skipped
    )
    
    annotation_dict = annotation.dict()
    await db.annotations.insert_one(annotation_dict)
    return annotation

@api_router.get("/annotations/sentence/{sentence_id}")
async def get_sentence_annotations(
    sentence_id: str,
    current_user: User = Depends(get_current_user)
):
    annotations = await db.annotations.find(
        {"sentence_id": sentence_id}, 
        {"_id": 0}
    ).to_list(100)
    return annotations

@api_router.delete("/annotations/{annotation_id}")
async def delete_annotation(
    annotation_id: str,
    current_user: User = Depends(get_current_user)
):
    # Find annotation
    annotation = await db.annotations.find_one({"id": annotation_id})
    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")
    
    # Check permissions
    if annotation["user_id"] != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Delete annotation
    await db.annotations.delete_one({"id": annotation_id})
    return {"message": "Annotation deleted"}

# Analytics endpoints
@api_router.get("/analytics/overview")
async def get_analytics_overview(current_user: User = Depends(get_current_user)):
    total_documents = await db.documents.count_documents({})
    total_sentences = await db.sentences.count_documents({})
    total_annotations = await db.annotations.count_documents({})
    tagged_annotations = await db.annotations.count_documents({"skipped": False})
    skipped_annotations = await db.annotations.count_documents({"skipped": True})
    unique_annotators = len(await db.annotations.distinct("user_id"))
    
    return {
        "total_documents": total_documents,
        "total_sentences": total_sentences,
        "total_annotations": total_annotations,
        "tagged_annotations": tagged_annotations,
        "skipped_annotations": skipped_annotations,
        "unique_annotators": unique_annotators
    }

@api_router.get("/analytics/enhanced")
async def get_enhanced_analytics(current_user: User = Depends(get_current_user)):
    # Per-user stats
    users = await db.users.find({}, {"_id": 0}).to_list(1000)
    per_user = []
    
    for user in users:
        user_annotations = await db.annotations.count_documents({"user_id": user["id"]})
        tagged = await db.annotations.count_documents({"user_id": user["id"], "skipped": False})
        skipped = await db.annotations.count_documents({"user_id": user["id"], "skipped": True})
        
        per_user.append({
            "user_id": user["id"],
            "full_name": user["full_name"],
            "total": user_annotations,
            "tagged": tagged,
            "skipped": skipped,
            "sentences_left": 0  # Simplified
        })
    
    # Overall sentences left
    total_sentences = await db.sentences.count_documents({})
    annotated_sentences = len(await db.annotations.distinct("sentence_id"))
    sentences_left_overall = total_sentences - annotated_sentences
    
    # IRR pairs (simplified)
    irr_pairs = []
    
    return {
        "per_user": per_user,
        "sentences_left_overall": sentences_left_overall,
        "irr_pairs": irr_pairs
    }

@api_router.get("/analytics/tag-prevalence-chart")
async def get_tag_prevalence_chart(current_user: Optional[User] = Depends(get_current_user_optional), token: Optional[str] = None):
    # Allow ?token for image rendering in <img> tags
    if token and not current_user:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            if user_id:
                u = await db.users.find_one({"id": user_id}, {"_id": 0})
                if u:
                    current_user = User(**u)
                else:
                    raise HTTPException(status_code=401, detail="Invalid token user")
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid token")
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from io import BytesIO

    # Placeholder simple chart (replace with real counts if needed)
    plt.figure(figsize=(10, 6))
    plt.bar(['Economic', 'Social', 'Health'], [10, 15, 8], color=['#2563eb','#9333ea','#059669'])
    plt.title('Tag Prevalence')
    plt.ylabel('Count')

    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    return StreamingResponse(buf, media_type='image/png')

# Deprecated: valence chart removed per request
# Admin endpoints
@api_router.get("/admin/users")
async def get_all_users(current_user: User = Depends(get_admin_user)):
    users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
    return users

@api_router.post("/admin/users", response_model=User)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_admin_user)
):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        role=user_data.role
    )
    
    # Hash password and store
    user_dict = user.dict()
    user_dict["password"] = hash_password(user_data.password)
    
    await db.users.insert_one(user_dict)
    return user

@api_router.delete("/admin/documents/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_admin_user)
):
    # Delete document and related data
    await db.documents.delete_one({"id": document_id})
    await db.sentences.delete_many({"document_id": document_id})
    
    # Get sentence IDs to delete annotations
    sentence_ids = await db.sentences.distinct("id", {"document_id": document_id})
    if sentence_ids:
        await db.annotations.delete_many({"sentence_id": {"$in": sentence_ids}})
    
    return {"message": "Document deleted"}

@api_router.get("/admin/download/annotated-csv-inline/{document_id}")
async def download_annotated_csv(
    document_id: str,
    current_user: User = Depends(get_admin_user)
):
    # Get document
    document = await db.documents.find_one({"id": document_id})
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get sentences and annotations
    sentences = await db.sentences.find({"document_id": document_id}).to_list(1000)
    
    # Create CSV content
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['sentence_id', 'sentence_text', 'user_id', 'tags', 'notes', 'skipped'])
    
    for sentence in sentences:
        annotations = await db.annotations.find({"sentence_id": sentence["id"]}).to_list(100)
        if annotations:
            for annotation in annotations:
                writer.writerow([
                    sentence["id"],
                    sentence["text"],
                    annotation["user_id"],
                    str(annotation.get("tags", [])),
                    annotation.get("notes", ""),
                    annotation.get("skipped", False)
                ])
        else:
            writer.writerow([sentence["id"], sentence["text"], "", "", "", ""])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"inline; filename=annotated_inline_{document['filename']}.csv"}
    )

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
async def get_projects_chart(current_user: Optional[User] = Depends(get_current_user_optional), token: Optional[str] = None):
    """
    Stacked bar chart (Option B): Completed vs Remaining sentences per project.
    Supports token query param for environments where <img> requests cannot send Authorization headers.
    """
    # If token query param is provided (e.g., from frontend <img src>), validate it and set current_user
    if token and not current_user:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            if user_id:
                u = await db.users.find_one({"id": user_id}, {"_id": 0})
                if u:
                    if isinstance(u.get('created_at'), datetime):
                        u['created_at'] = u['created_at'].isoformat()
                    current_user = User(**u)
                else:
                    raise HTTPException(status_code=401, detail="Invalid token user")
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    # Require authentication (either via header or query param)
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from io import BytesIO

    # Prepare data from projects analytics
    data = await get_projects_analytics(current_user)
    if not data:
        data = []

    # Limit to top 20 by total_sentences for readability
    data = data[:20]

    labels = [d['project_name'] for d in data]
    completed = [int(d.get('annotated_sentences') or 0) for d in data]
    totals = [int(d.get('total_sentences') or 0) for d in data]
    remaining = [max(t - c, 0) for t, c in zip(totals, completed)]

    # Build stacked horizontal bars
    plt.figure(figsize=(12, 7))
    y_pos = range(len(labels))
    plt.barh(y_pos, completed, color='#16a34a', label='Completed (Annotated)')
    plt.barh(y_pos, remaining, left=completed, color='#93c5fd', label='Remaining')

    plt.yticks(y_pos, labels)
    plt.xlabel('Sentences')
    plt.title('Project Progress: Completed vs Remaining Sentences')
    plt.legend(loc='lower right')
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    return StreamingResponse(buf, media_type='image/png')

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router with /api prefix for all endpoints
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)