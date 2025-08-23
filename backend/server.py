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

# Structured tag definitions from the uploaded document
SDOH_TAG_STRUCTURE = {
    "Economic Stability": {
        "Employment": [
            "Employed", "Under-employed", "Unemployed", "Disabled", 
            "Retired", "Homemaker", "Student", "Harmful Workplace"
        ],
        "Food Insecurity": [
            "Low Food Security", "Very Low Food Security", 
            "Physical Access Barrier", "Food Assistance Program"
        ],
        "Housing Instability": [
            "Cost-Burdened Household", "Overcrowding", "Multiple Moves",
            "Eviction or Foreclosure", "Substandard Housing", "Unhoused",
            "Housing Assistance Program"
        ],
        "Poverty": [
            "Below Poverty Threshold", "Low Socioeconomic Status", 
            "Social Assistance Program"
        ]
    },
    "Education Access and Quality": {
        "Early Childhood Development and Education": [
            "Early Learning Programs", "School Readiness Concern", "Developmental Delay",
            "Reading Impairment", "Math Impairment", "Other Learning Disability",
            "Early Intervention Services", "Learning Environment Concern"
        ],
        "Highest Level of Education": [
            "Some High School", "High School Diploma or GED", 
            "Some College or Associate Degree", "Bachelor's Degree",
            "Graduate or Professional Degree"
        ],
        "Language and Literacy": [
            "Language Barrier", "Low Health Literacy"
        ]
    },
    "Health Care Access and Quality": {
        "Access to Health Services": [
            "No Local Services Available", "Barrier to Specialist Care",
            "Insurance Coverage Limitations", "Financial Barriers to Medical Care"
        ],
        "Access to Primary Care": [
            "No Primary Care Provider", "Extended Gaps in Care",
            "Geographic Barriers to Care", "Limited Appointment Availability"
        ],
        "Health Literacy": [
            "Difficulty Understanding Medical Information", 
            "Limited Understanding of Preventative Care",
            "Language Barriers Affecting Comprehension", 
            "Digital Health Literacy Gaps"
        ]
    },
    "Neighborhood and Built Environment": {
        "Access to Healthy Foods": [
            "Distance to Food Sources", "Limited Healthy Food Options",
            "Food Environment Quality"
        ],
        "Crime and Violence": [
            "Perceived Neighborhood Safety", "Reported Criminal Activity",
            "Gang or Drug-Related Activity"
        ],
        "Environmental Conditions": [
            "Air Quality Concerns", "Water Quality Issues",
            "Proximity to Environmental Hazards"
        ],
        "Quality of Housing": [
            "Structural Deficiencies", "Pest Infestation or Mold",
            "Overcrowding or Unsafe Occupancy"
        ]
    },
    "Social and Community Context": {
        "Civic Participation": [
            "Voting and Political Engagement", "Community or Religious Involvement",
            "Volunteering or Service Activities"
        ],
        "Incarceration": [
            "Current Incarceration", "History of Incarceration",
            "Community Supervision"
        ],
        "Social Cohesion": [
            "Supportive Relationships", "Social Isolation",
            "Trust and Belonging in Community"
        ],
        "Experiences of Discrimination or Exclusion": [
            "Race", "Ethnicity", "Gender", "Sexual Orientation", "Other Identity"
        ]
    }
}

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    full_name: str
    role: str = UserRole.ANNOTATOR  # default role
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = UserRole.ANNOTATOR

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class Document(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    uploaded_by: str
    upload_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_sentences: int = 0
    processed: bool = False
    project_name: Optional[str] = None
    description: Optional[str] = None

class Sentence(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    text: str
    sentence_index: int
    subject_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StructuredTag(BaseModel):
    domain: str
    category: str
    tag: str
    valence: str  # "positive" or "negative"

class Annotation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sentence_id: str
    user_id: str
    tags: List[StructuredTag]
    notes: Optional[str] = ""
    skipped: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AnnotationCreate(BaseModel):
    sentence_id: str
    tags: List[StructuredTag]
    notes: Optional[str] = ""
    skipped: bool = False

class DocumentUpload(BaseModel):
    project_name: Optional[str] = None
    description: Optional[str] = None

class Resource(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    content_type: Optional[str] = None
    size_bytes: int
    uploaded_by: str
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BulkDeleteUsersRequest(BaseModel):
    user_ids: List[str]

class BulkDeleteDocumentsRequest(BaseModel):
    document_ids: List[str]

class BulkDeleteAnnotationsRequest(BaseModel):
    annotation_ids: List[str]

class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_name: str
    role: str
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class UpdateProfileRequest(BaseModel):
    full_name: str

# Helpers
ALLOWED_RESOURCE_EXTENSIONS = {"pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx"}
SUBJECT_KEYS = ["subject_id", "patient_id", "encounter_id", "subject", "note_id"]

def get_gridfs_bucket() -> AsyncIOMotorGridFSBucket:
    return AsyncIOMotorGridFSBucket(db)

def allowed_resource(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_RESOURCE_EXTENSIONS

# Authentication functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    user = await db.users.find_one({"email": email})
    if user is None:
        raise credentials_exception
    return User(**user)

async def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

# Text processing functions
def split_into_sentences(text: str) -> List[str]:
    text = re.sub(r'\s+', ' ', text.strip())
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    cleaned = []
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 10:
            cleaned.append(sentence)
    return cleaned

# Authentication Routes
@api_router.post("/auth/register", response_model=User)
async def register_user(user_data: UserCreate):
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    if user_data.role not in [UserRole.ADMIN, UserRole.ANNOTATOR]:
        user_data.role = UserRole.ANNOTATOR
    hashed_password = hash_password(user_data.password)
    user_dict = user_data.dict(); user_dict['password'] = hashed_password
    user_obj = User(email=user_data.email, full_name=user_data.full_name, role=user_data.role)
    user_dict['id'] = user_obj.id; user_dict['is_active'] = user_obj.is_active; user_dict['created_at'] = user_obj.created_at
    await db.users.insert_one(user_dict)
    return user_obj

@api_router.post("/auth/login", response_model=Token)
async def login_user(login_data: UserLogin):
    user = await db.users.find_one({"email": login_data.email})
    if not user or not verify_password(login_data.password, user['password']):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password", headers={"WWW-Authenticate": "Bearer"})
    if not user.get('is_active', True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")
    access_token = create_access_token(data={"sub": user['email']}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.get("/auth/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@api_router.post("/auth/change-password")
async def change_password(payload: ChangePasswordRequest, current_user: User = Depends(get_current_user)):
    user = await db.users.find_one({"id": current_user.id})
    if not user or not verify_password(payload.current_password, user['password']):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    new_hashed = hash_password(payload.new_password)
    await db.users.update_one({"id": current_user.id}, {"$set": {"password": new_hashed}})
    return {"message": "Password updated"}

@api_router.put("/auth/me/profile", response_model=User)
async def update_profile(payload: UpdateProfileRequest, current_user: User = Depends(get_current_user)):
    await db.users.update_one({"id": current_user.id}, {"$set": {"full_name": payload.full_name}})
    user = await db.users.find_one({"id": current_user.id}, {"_id": 0, "password": 0})
    return User(**user)

# Admin Routes
@api_router.get("/admin/users", response_model=List[User])
async def get_all_users(admin_user: User = Depends(get_admin_user)):
    users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
    return [User(**user) for user in users]

@api_router.post("/admin/users", response_model=User)
async def create_user_by_admin(user_data: UserCreate, admin_user: User = Depends(get_admin_user)):
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    if user_data.role not in [UserRole.ADMIN, UserRole.ANNOTATOR]:
        user_data.role = UserRole.ANNOTATOR
    hashed_password = hash_password(user_data.password)
    user_dict = user_data.dict(); user_dict['password'] = hashed_password
    user_obj = User(email=user_data.email, full_name=user_data.full_name, role=user_data.role)
    user_dict['id'] = user_obj.id; user_dict['is_active'] = user_obj.is_active; user_dict['created_at'] = user_obj.created_at
    await db.users.insert_one(user_dict)
    return user_obj

@api_router.put("/admin/users/{user_id}", response_model=User)
async def update_user_by_admin(user_id: str, user_update: UserUpdate, admin_user: User = Depends(get_admin_user)):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    update_data = {}
    if user_update.full_name is not None:
        update_data["full_name"] = user_update.full_name
    if user_update.role is not None and user_update.role in [UserRole.ADMIN, UserRole.ANNOTATOR]:
        update_data["role"] = user_update.role
    if user_update.is_active is not None:
        update_data["is_active"] = user_update.is_active
    if update_data:
        await db.users.update_one({"id": user_id}, {"$set": update_data})
        updated_user = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
        return User(**updated_user)
    return User(**{k: v for k, v in user.items() if k != "password"})

@api_router.delete("/admin/users/{user_id}")
async def delete_user_by_admin(user_id: str, admin_user: User = Depends(get_admin_user)):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user_id == admin_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete your own account")
    await db.annotations.delete_many({"user_id": user_id})
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found during deletion")
    return {"message": "User deleted successfully"}

# Document Routes
@api_router.post("/documents/upload", response_model=Document)
async def upload_document(file: UploadFile = File(...), project_name: Optional[str] = None, description: Optional[str] = None, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only administrators can upload documents")
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only CSV files are supported")
    content = await file.read(); csv_data = content.decode('utf-8')
    document = Document(filename=file.filename, uploaded_by=current_user.id, project_name=project_name, description=description)
    csv_reader = csv.DictReader(io.StringIO(csv_data))
    sentences_to_insert = []; sentence_index = 0; row_num = 0
    for row in csv_reader:
        # Extract subject id
        subject_val = None
        # 1) Try configured subject keys (exact, case-insensitive)
        for key in row.keys():
            if key and any(sk == key.strip().lower() for sk in SUBJECT_KEYS):
                val = row.get(key)
                if val is not None and str(val).strip():
                    subject_val = str(val).strip()
                    break
        # 2) Fallback to common index column names
        if subject_val is None:
            for key in row.keys():
                if key and key.strip().lower() in ["index", "idx", "row", "row_id"]:
                    val = row.get(key)
                    subject_val = (str(val).strip() if val is not None else None)
                    if subject_val:
                        break
        # 3) Fallback for pandas auto index column (Unnamed: 0)
        if subject_val is None:
            for key in row.keys():
                kl = key.strip().lower() if key else ""
                if kl.startswith("unnamed") and (kl.endswith(": 0") or kl.endswith("0")):
                    val = row.get(key)
                    subject_val = (str(val).strip() if val is not None else None)
                    if subject_val:
                        break
        # 4) Final fallback: use row number (1-based)
        if subject_val is None:
            subject_val = str(row_num + 1)

        # Extract text
        text_content = ""
        for key, value in row.items():
            if key and any(text_col in key.lower() for text_col in ['text', 'summary', 'discharge', 'note']):
                if value and isinstance(value, str):
                    text_content += value + " "
        if text_content.strip():
            for sentence_text in split_into_sentences(text_content.strip()):
                sentence = Sentence(document_id=document.id, text=sentence_text, sentence_index=sentence_index, subject_id=subject_val)
                sentences_to_insert.append(sentence.dict()); sentence_index += 1
        row_num += 1
    document.total_sentences = len(sentences_to_insert); document.processed = True
    await db.documents.insert_one(document.dict())
    if sentences_to_insert:
        await db.sentences.insert_many(sentences_to_insert)
    return document

@api_router.get("/documents", response_model=List[Document])
async def get_documents(current_user: User = Depends(get_current_user)):
    documents = await db.documents.find({}, {"_id": 0}).to_list(1000)
    return [Document(**doc) for doc in documents]

@api_router.get("/documents/{document_id}/sentences")
async def get_document_sentences(document_id: str, skip: int = 0, limit: int = 50, current_user: User = Depends(get_current_user)):
    sentences = await db.sentences.find({"document_id": document_id}, {"_id": 0}).sort("sentence_index", 1).skip(skip).limit(limit).to_list(limit)
    # Fallback subject if still missing
    for s in sentences:
        if not s.get('subject_id'):
            s['subject_id'] = str(s.get('sentence_index'))
    sentence_ids = [sentence['id'] for sentence in sentences]
    annotations = await db.annotations.find({"sentence_id": {"$in": sentence_ids}}, {"_id": 0}).to_list(1000)
    annotations_by_sentence = defaultdict(list)
    for annotation in annotations:
        annotations_by_sentence[annotation['sentence_id']].append(annotation)
    for sentence in sentences:
        sentence['annotations'] = annotations_by_sentence.get(sentence['id'], [])
    return sentences

@api_router.delete("/admin/documents/{document_id}")
async def delete_document(document_id: str, admin_user: User = Depends(get_admin_user)):
    await db.annotations.delete_many({"sentence_id": {"$in": [s["id"] for s in await db.sentences.find({"document_id": document_id}, {"id": 1}).to_list(100000)]}})
    await db.sentences.delete_many({"document_id": document_id})
    result = await db.documents.delete_one({"id": document_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Document deleted successfully"}

# Annotation Routes
@api_router.post("/annotations", response_model=Annotation)
async def create_annotation(annotation_data: AnnotationCreate, current_user: User = Depends(get_current_user)):
    if not annotation_data.skipped:
        for tag in annotation_data.tags:
            if tag.domain not in SDOH_DOMAINS:
                raise HTTPException(status_code=400, detail=f"Invalid domain: {tag.domain}. Must be one of: {SDOH_DOMAINS}")
            if tag.valence not in ["positive", "negative"]:
                raise HTTPException(status_code=400, detail="Invalid valence: must be 'positive' or 'negative'")
    annotation = Annotation(sentence_id=annotation_data.sentence_id, user_id=current_user.id, tags=annotation_data.tags, notes=annotation_data.notes, skipped=annotation_data.skipped)
    await db.annotations.insert_one(annotation.dict())
    return annotation

@api_router.delete("/annotations/{annotation_id}")
async def delete_annotation(annotation_id: str, current_user: User = Depends(get_current_user)):
    annotation = await db.annotations.find_one({"id": annotation_id})
    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")
    if annotation["user_id"] != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="You can only delete your own annotations")
    result = await db.annotations.delete_one({"id": annotation_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Annotation not found")
    return {"message": "Annotation deleted successfully"}

@api_router.post("/annotations/bulk-delete")
async def bulk_delete_annotations(payload: BulkDeleteAnnotationsRequest, current_user: User = Depends(get_current_user)):
    results: Dict[str, str] = {}
    anns = await db.annotations.find({"id": {"$in": payload.annotation_ids}}, {"_id": 0}).to_list(100000)
    anns_by_id = {a["id"]: a for a in anns}
    to_delete: List[str] = []
    for aid in payload.annotation_ids:
        a = anns_by_id.get(aid)
        if not a:
            results[aid] = "not_found"; continue
        if current_user.role == UserRole.ADMIN or a.get("user_id") == current_user.id:
            to_delete.append(aid)
        else:
            results[aid] = "forbidden"
    if to_delete:
        await db.annotations.delete_many({"id": {"$in": to_delete}})
        for aid in to_delete:
            results[aid] = "deleted"
    return {"results": results}

@api_router.get("/annotations/sentence/{sentence_id}")
async def get_sentence_annotations(sentence_id: str, current_user: User = Depends(get_current_user)):
    annotations = await db.annotations.find({"sentence_id": sentence_id}, {"_id": 0}).to_list(1000)
    return annotations

@api_router.get("/annotations/active-docs")
async def get_active_documents(scope: str = Query("me", regex="^(me|team)$"), current_user: User = Depends(get_current_user)):
    docs = await db.documents.find({}, {"_id": 0}).to_list(1000)
    results = []
    for d in docs:
        did = d['id']
        # Sentences and subjects
        sentence_docs = await db.sentences.find({"document_id": did}, {"_id": 0, "id": 1, "sentence_index": 1, "subject_id": 1}).to_list(100000)
        total_sentences = len(sentence_docs)
        if total_sentences == 0:
            continue
        sentence_ids = [s['id'] for s in sentence_docs]
        # Distinct sentence ids annotated
        filt = {"sentence_id": {"$in": sentence_ids}}
        if scope == 'me':
            filt["user_id"] = current_user.id
        annotated_ids = await db.annotations.distinct("sentence_id", filt)
        annotated_count = len(annotated_ids)
        if annotated_count == 0:
            continue  # not active
        # Last annotation index for current user (me)
        last_index = None
        if scope == 'me':
            last_ann = await db.annotations.find({"sentence_id": {"$in": sentence_ids}, "user_id": current_user.id}, {"_id": 0}).sort("created_at", -1).limit(1).to_list(1)
            if last_ann:
                last_sid = last_ann[0]['sentence_id']
                idx_map = {s['id']: s['sentence_index'] for s in sentence_docs}
                last_index = idx_map.get(last_sid)
        subjects = await db.sentences.distinct("subject_id", {"document_id": did})
        subjects = [s for s in subjects if s]
        results.append({
            "document_id": did,
            "filename": d.get("filename"),
            "total_sentences": total_sentences,
            "annotated_count": annotated_count,
            "progress": annotated_count / max(1, total_sentences),
            "last_annotation_index": last_index,
            "subjects": subjects,
        })
    # Sort most active first
    results.sort(key=lambda x: x['annotated_count'], reverse=True)
    return results

# Tag Structure Routes
@api_router.get("/tag-structure")
async def get_tag_structure():
    return {"tag_structure": SDOH_TAG_STRUCTURE}

# Analytics Routes
@api_router.get("/analytics/overview")
async def get_analytics_overview(current_user: User = Depends(get_current_user)):
    total_docs = await db.documents.count_documents({})
    total_sentences = await db.sentences.count_documents({})
    total_annotations = await db.annotations.count_documents({})
    skipped_sentences = await db.annotations.count_documents({"skipped": True})
    tagged_sentences = await db.annotations.count_documents({"skipped": False})
    unique_annotators = len(await db.annotations.distinct("user_id"))
    return {"total_documents": total_docs, "total_sentences": total_sentences, "total_annotations": total_annotations, "tagged_sentences": tagged_sentences, "skipped_sentences": skipped_sentences, "unique_annotators": unique_annotators}

@api_router.get("/analytics/enhanced")
async def get_enhanced_analytics(current_user: User = Depends(get_current_user)):
    users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
    per_user = []
    total_sentences = await db.sentences.count_documents({})
    for u in users:
        uid = u['id']
        user_total = await db.annotations.count_documents({"user_id": uid})
        user_tagged = await db.annotations.count_documents({"user_id": uid, "skipped": False})
        user_skipped = await db.annotations.count_documents({"user_id": uid, "skipped": True})
        user_sentence_ids = await db.annotations.distinct("sentence_id", {"user_id": uid})
        sentences_left = max(0, total_sentences - len(user_sentence_ids))
        per_user.append({"user_id": uid, "full_name": u.get("full_name"), "total": user_total, "tagged": user_tagged, "skipped": user_skipped, "sentences_left": sentences_left})
    annotated_sentence_ids = await db.annotations.distinct("sentence_id")
    sentences_left_overall = max(0, total_sentences - len(annotated_sentence_ids))
    anns = await db.annotations.find({}, {"_id": 0}).to_list(100000)
    sent_user_tags: Dict[str, Dict[str, set]] = defaultdict(lambda: defaultdict(set))
    for a in anns:
        sid = a.get("sentence_id"); uid = a.get("user_id")
        if a.get("skipped"):
            sent_user_tags[sid][uid] = {"__SKIPPED__"}
        else:
            tags = a.get("tags", [])
            for t in tags:
                if isinstance(t, dict):
                    tpl = (t.get("domain"), t.get("category"), t.get("tag"), t.get("valence"))
                else:
                    tpl = ("", "", str(t), "")
                sent_user_tags[sid][uid].add(tpl)
    irr_pairs = []
    user_ids = [u['id'] for u in users]
    for i in range(len(user_ids)):
        for j in range(i+1, len(user_ids)):
            u1 = user_ids[i]; u2 = user_ids[j]
            numer = 0.0; denom = 0.0; common = 0
            for sid, umap in sent_user_tags.items():
                if u1 in umap and u2 in umap:
                    s1 = umap[u1]; s2 = umap[u2]
                    inter = len(s1.intersection(s2)); union = len(s1.union(s2)) or 1
                    numer += inter / union
                    denom += 1
                    common += 1
            avg_jaccard = (numer / denom) if denom else None
            irr_pairs.append({"user1": u1, "user2": u2, "avg_jaccard": avg_jaccard, "common_sentences": common})
    return {"per_user": per_user, "sentences_left_overall": sentences_left_overall, "irr_pairs": irr_pairs}

@api_router.get("/analytics/tag-prevalence")
async def get_tag_prevalence(current_user: User = Depends(get_current_user)):
    annotations = await db.annotations.find({"skipped": False}, {"_id": 0}).to_list(100000)
    tag_counts = defaultdict(int); domain_counts = defaultdict(int); category_counts = defaultdict(int); valence_counts = {"positive": 0, "negative": 0}
    for annotation in annotations:
        for tag in annotation.get('tags', []):
            domain_counts[tag.get('domain','')] += 1
            category_counts[f"{tag.get('domain','')} - {tag.get('category','')}"] += 1
            tag_counts[f"{tag.get('category','')} - {tag.get('tag','')}"] += 1
            valence_counts[tag.get('valence','positive' if tag.get('valence') is None else tag.get('valence'))] += 1
    return {"domain_counts": dict(domain_counts), "category_counts": dict(category_counts), "tag_counts": dict(tag_counts), "valence_counts": valence_counts}

@api_router.get("/analytics/tag-prevalence-chart")
async def get_tag_prevalence_chart(current_user: User = Depends(get_current_user)):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from io import BytesIO
    annotations = await db.annotations.find({"skipped": False}, {"_id": 0}).to_list(100000)
    category_counts = defaultdict(int)
    for annotation in annotations:
        for tag in annotation.get('tags', []):
            key = f"{tag.get('domain','')} - {tag.get('category','')}"
            category_counts[key] += 1
    labels = list(category_counts.keys())[:20]
    values = [category_counts[k] for k in labels]
    plt.figure(figsize=(10, 6))
    plt.barh(labels, values, color='#3b82f6')
    plt.xlabel('Count'); plt.title('Top Category Counts'); plt.tight_layout()
    buf = BytesIO(); plt.savefig(buf, format='png'); buf.seek(0)
    return StreamingResponse(buf, media_type='image/png')

@api_router.get("/analytics/valence-chart")
async def get_valence_chart(current_user: User = Depends(get_current_user)):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from io import BytesIO
    counts = {"positive": 0, "negative": 0}
    annotations = await db.annotations.find({"skipped": False}, {"_id": 0}).to_list(100000)
    for a in annotations:
        for t in a.get('tags', []):
            v = t.get('valence') or 'positive'
            if v in counts:
                counts[v] += 1
    labels = list(counts.keys()); sizes = [counts[k] for k in labels]
    colors = ['#10b981', '#ef4444']
    plt.figure(figsize=(4, 4))
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
    plt.axis('equal'); plt.title('Valence Distribution'); plt.tight_layout()
    buf = BytesIO(); plt.savefig(buf, format='png'); buf.seek(0)
    return StreamingResponse(buf, media_type='image/png')

@api_router.get("/analytics/tag-prevalence-chart-public")
async def get_tag_prevalence_chart_public(token: str = Query("")):
    # Validate token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    # Generate chart without user-specific filtering
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from io import BytesIO
    annotations = await db.annotations.find({"skipped": False}, {"_id": 0}).to_list(100000)
    category_counts = defaultdict(int)
    for annotation in annotations:
        for tag in annotation.get('tags', []):
            key = f"{tag.get('domain','')} - {tag.get('category','')}"
            category_counts[key] += 1
    labels = list(category_counts.keys())[:20]
    values = [category_counts[k] for k in labels]
    plt.figure(figsize=(10, 6))
    plt.barh(labels, values, color='#3b82f6')
    plt.xlabel('Count'); plt.title('Top Category Counts'); plt.tight_layout()
    buf = BytesIO(); plt.savefig(buf, format='png'); buf.seek(0)
    return StreamingResponse(buf, media_type='image/png')

@api_router.get("/analytics/valence-chart-public")
async def get_valence_chart_public(token: str = Query("")):
    try:
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from io import BytesIO
    counts = {"positive": 0, "negative": 0}
    annotations = await db.annotations.find({"skipped": False}, {"_id": 0}).to_list(100000)
    for a in annotations:
        for t in a.get('tags', []):
            v = t.get('valence') or 'positive'
            if v in counts:
                counts[v] += 1
    labels = list(counts.keys()); sizes = [counts[k] for k in labels]
    colors = ['#10b981', '#ef4444']
    plt.figure(figsize=(4, 4))
    plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
    plt.axis('equal'); plt.title('Valence Distribution'); plt.tight_layout()
    buf = BytesIO(); plt.savefig(buf, format='png'); buf.seek(0)
    return StreamingResponse(buf, media_type='image/png')

# Resources, Bulk ops, Messages, and System routes remain unchanged below...