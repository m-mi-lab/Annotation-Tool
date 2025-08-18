from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timedelta, timezone
import jwt
import bcrypt
import csv
import io
import re
from collections import defaultdict

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

# Social Determinants of Health Domains
SDOH_DOMAINS = [
    "Economic Stability",
    "Education Access and Quality", 
    "Health Care Access and Quality",
    "Neighborhood and Built Environment",
    "Social and Community Context"
]

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    full_name: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str

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

class Sentence(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    text: str
    sentence_index: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Annotation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sentence_id: str
    user_id: str
    domain: str
    tags: List[str]
    notes: Optional[str] = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AnnotationCreate(BaseModel):
    sentence_id: str
    domain: str
    tags: List[str]
    notes: Optional[str] = ""

# Authentication functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
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

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

# Text processing functions
def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences, handling medical text formatting"""
    # Basic sentence splitting for medical text
    # Remove extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Split on sentence endings, but be careful with abbreviations
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    
    # Filter out very short sentences and clean up
    cleaned_sentences = []
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 10:  # Minimum sentence length
            cleaned_sentences.append(sentence)
    
    return cleaned_sentences

# Authentication Routes
@api_router.post("/auth/register", response_model=User)
async def register_user(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password and create user
    hashed_password = hash_password(user_data.password)
    user_dict = user_data.dict()
    user_dict['password'] = hashed_password
    user_obj = User(email=user_data.email, full_name=user_data.full_name)
    
    # Store in database
    user_dict['id'] = user_obj.id
    user_dict['is_active'] = user_obj.is_active
    user_dict['created_at'] = user_obj.created_at
    
    await db.users.insert_one(user_dict)
    return user_obj

@api_router.post("/auth/login", response_model=Token)
async def login_user(login_data: UserLogin):
    user = await db.users.find_one({"email": login_data.email})
    if not user or not verify_password(login_data.password, user['password']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user['email']}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.get("/auth/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

# Document Routes
@api_router.post("/documents/upload", response_model=Document)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are supported"
        )
    
    # Read CSV content
    content = await file.read()
    csv_data = content.decode('utf-8')
    
    # Create document record
    document = Document(
        filename=file.filename,
        uploaded_by=current_user.id
    )
    
    # Parse CSV and extract text
    csv_reader = csv.DictReader(io.StringIO(csv_data))
    sentences_to_insert = []
    sentence_index = 0
    
    for row in csv_reader:
        # Look for text columns (adjust column names as needed)
        text_content = ""
        for key, value in row.items():
            if any(text_col in key.lower() for text_col in ['text', 'summary', 'discharge', 'note']):
                if value and isinstance(value, str):
                    text_content += value + " "
        
        if text_content.strip():
            # Split into sentences
            sentences = split_into_sentences(text_content.strip())
            for sentence_text in sentences:
                sentence = Sentence(
                    document_id=document.id,
                    text=sentence_text,
                    sentence_index=sentence_index
                )
                sentences_to_insert.append(sentence.dict())
                sentence_index += 1
    
    # Update document with sentence count
    document.total_sentences = len(sentences_to_insert)
    document.processed = True
    
    # Insert into database
    await db.documents.insert_one(document.dict())
    if sentences_to_insert:
        await db.sentences.insert_many(sentences_to_insert)
    
    return document

@api_router.get("/documents", response_model=List[Document])
async def get_documents(current_user: User = Depends(get_current_user)):
    documents = await db.documents.find().to_list(1000)
    return [Document(**doc) for doc in documents]

@api_router.get("/documents/{document_id}/sentences")
async def get_document_sentences(
    document_id: str,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    sentences = await db.sentences.find(
        {"document_id": document_id}
    ).skip(skip).limit(limit).to_list(limit)
    
    # Get existing annotations for these sentences
    sentence_ids = [sentence['id'] for sentence in sentences]
    annotations = await db.annotations.find(
        {"sentence_id": {"$in": sentence_ids}}
    ).to_list(1000)
    
    # Group annotations by sentence
    annotations_by_sentence = defaultdict(list)
    for annotation in annotations:
        annotations_by_sentence[annotation['sentence_id']].append(annotation)
    
    # Add annotations to sentences
    for sentence in sentences:
        sentence['annotations'] = annotations_by_sentence.get(sentence['id'], [])
    
    return sentences

# Annotation Routes
@api_router.post("/annotations", response_model=Annotation)
async def create_annotation(
    annotation_data: AnnotationCreate,
    current_user: User = Depends(get_current_user)
):
    if annotation_data.domain not in SDOH_DOMAINS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid domain. Must be one of: {SDOH_DOMAINS}"
        )
    
    annotation = Annotation(
        sentence_id=annotation_data.sentence_id,
        user_id=current_user.id,
        domain=annotation_data.domain,
        tags=annotation_data.tags,
        notes=annotation_data.notes
    )
    
    await db.annotations.insert_one(annotation.dict())
    return annotation

@api_router.get("/annotations/sentence/{sentence_id}")
async def get_sentence_annotations(
    sentence_id: str,
    current_user: User = Depends(get_current_user)
):
    annotations = await db.annotations.find({"sentence_id": sentence_id}).to_list(1000)
    return annotations

# Analytics Routes
@api_router.get("/analytics/overview")
async def get_analytics_overview(current_user: User = Depends(get_current_user)):
    # Total documents
    total_docs = await db.documents.count_documents({})
    
    # Total sentences
    total_sentences = await db.sentences.count_documents({})
    
    # Total annotations
    total_annotations = await db.annotations.count_documents({})
    
    # Unique annotators
    unique_annotators = len(await db.annotations.distinct("user_id"))
    
    return {
        "total_documents": total_docs,
        "total_sentences": total_sentences,
        "total_annotations": total_annotations,
        "unique_annotators": unique_annotators
    }

@api_router.get("/analytics/domain-prevalence")
async def get_domain_prevalence(current_user: User = Depends(get_current_user)):
    pipeline = [
        {"$group": {"_id": "$domain", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    
    results = await db.annotations.aggregate(pipeline).to_list(1000)
    return {result['_id']: result['count'] for result in results}

# System Routes
@api_router.get("/")
async def root():
    return {"message": "Social Determinants of Health Annotation API"}

@api_router.get("/domains")
async def get_domains():
    return {"domains": SDOH_DOMAINS}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()