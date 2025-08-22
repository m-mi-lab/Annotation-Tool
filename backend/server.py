from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
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

async def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

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
    
    # Validate role
    if user_data.role not in [UserRole.ADMIN, UserRole.ANNOTATOR]:
        user_data.role = UserRole.ANNOTATOR
    
    # Hash password and create user
    hashed_password = hash_password(user_data.password)
    user_dict = user_data.dict()
    user_dict['password'] = hashed_password
    user_obj = User(
        email=user_data.email, 
        full_name=user_data.full_name,
        role=user_data.role
    )
    
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
    
    if not user.get('is_active', True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user['email']}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.get("/auth/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

# Admin Routes
@api_router.get("/admin/users", response_model=List[User])
async def get_all_users(admin_user: User = Depends(get_admin_user)):
    """Admin only: Get all users"""
    users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
    return [User(**user) for user in users]

@api_router.post("/admin/users", response_model=User)
async def create_user_by_admin(
    user_data: UserCreate,
    admin_user: User = Depends(get_admin_user)
):
    """Admin only: Create new user account"""
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate role
    if user_data.role not in [UserRole.ADMIN, UserRole.ANNOTATOR]:
        user_data.role = UserRole.ANNOTATOR
    
    # Hash password and create user
    hashed_password = hash_password(user_data.password)
    user_dict = user_data.dict()
    user_dict['password'] = hashed_password
    user_obj = User(
        email=user_data.email, 
        full_name=user_data.full_name,
        role=user_data.role
    )
    
    # Store in database
    user_dict['id'] = user_obj.id
    user_dict['is_active'] = user_obj.is_active
    user_dict['created_at'] = user_obj.created_at
    
    await db.users.insert_one(user_dict)
    return user_obj

@api_router.put("/admin/users/{user_id}", response_model=User)
async def update_user_by_admin(
    user_id: str,
    user_update: UserUpdate,
    admin_user: User = Depends(get_admin_user)
):
    """Admin only: Update user account"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields
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
async def delete_user_by_admin(
    user_id: str,
    admin_user: User = Depends(get_admin_user)
):
    """Admin only: Delete user account and all related data"""
    # Check if user exists
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent admin from deleting themselves
    if user_id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    try:
        # Delete user's annotations first
        annotations_deleted = await db.annotations.delete_many({"user_id": user_id})
        
        # Delete the user
        result = await db.users.delete_one({"id": user_id})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found during deletion"
            )
        
        return {
            "message": "User deleted successfully",
            "user_name": user.get("full_name", "Unknown"),
            "annotations_deleted": annotations_deleted.deleted_count
        }
    
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )

# Document Routes
@api_router.post("/documents/upload", response_model=Document)
async def upload_document(
    file: UploadFile = File(...),
    project_name: Optional[str] = None,
    description: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    # Only admins can upload documents
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can upload documents"
        )
    
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
        uploaded_by=current_user.id,
        project_name=project_name,
        description=description
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
    # All users can see all documents (uploaded by admins)
    documents = await db.documents.find({}, {"_id": 0}).to_list(1000)
    return [Document(**doc) for doc in documents]

@api_router.get("/documents/{document_id}/sentences")
async def get_document_sentences(
    document_id: str,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    sentences = await db.sentences.find(
        {"document_id": document_id}, {"_id": 0}
    ).skip(skip).limit(limit).to_list(limit)
    
    # Get existing annotations for these sentences
    sentence_ids = [sentence['id'] for sentence in sentences]
    annotations = await db.annotations.find(
        {"sentence_id": {"$in": sentence_ids}}, {"_id": 0}
    ).to_list(1000)
    
    # Group annotations by sentence
    annotations_by_sentence = defaultdict(list)
    for annotation in annotations:
        annotations_by_sentence[annotation['sentence_id']].append(annotation)
    
    # Add annotations to sentences
    for sentence in sentences:
        sentence['annotations'] = annotations_by_sentence.get(sentence['id'], [])
    
    return sentences

@api_router.delete("/admin/documents/{document_id}")
async def delete_document(
    document_id: str,
    admin_user: User = Depends(get_admin_user)
):
    """Admin only: Delete document and all related sentences and annotations"""
    # Delete annotations first
    await db.annotations.delete_many({"sentence_id": {"$in": [
        sentence["id"] for sentence in await db.sentences.find(
            {"document_id": document_id}, {"id": 1}
        ).to_list(10000)
    ]}})
    
    # Delete sentences
    await db.sentences.delete_many({"document_id": document_id})
    
    # Delete document
    result = await db.documents.delete_one({"id": document_id})
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return {"message": "Document deleted successfully"}

# Annotation Routes
@api_router.post("/annotations", response_model=Annotation)
async def create_annotation(
    annotation_data: AnnotationCreate,
    current_user: User = Depends(get_current_user)
):
    # Validate tags if not skipped
    if not annotation_data.skipped:
        for tag in annotation_data.tags:
            if tag.domain not in SDOH_DOMAINS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid domain: {tag.domain}. Must be one of: {SDOH_DOMAINS}"
                )
            
            if tag.valence not in ["positive", "negative"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid valence: {tag.valence}. Must be 'positive' or 'negative'"
                )
    
    annotation = Annotation(
        sentence_id=annotation_data.sentence_id,
        user_id=current_user.id,
        tags=annotation_data.tags,
        notes=annotation_data.notes,
        skipped=annotation_data.skipped
    )
    
    await db.annotations.insert_one(annotation.dict())
    return annotation

@api_router.delete("/annotations/{annotation_id}")
async def delete_annotation(
    annotation_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete an annotation (user can only delete their own annotations, admins can delete any)"""
    annotation = await db.annotations.find_one({"id": annotation_id})
    if not annotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Annotation not found"
        )
    
    # Check permissions: users can only delete their own annotations, admins can delete any
    if annotation["user_id"] != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own annotations"
        )
    
    result = await db.annotations.delete_one({"id": annotation_id})
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Annotation not found"
        )
    
    return {"message": "Annotation deleted successfully"}

@api_router.get("/annotations/sentence/{sentence_id}")
async def get_sentence_annotations(
    sentence_id: str,
    current_user: User = Depends(get_current_user)
):
    annotations = await db.annotations.find({"sentence_id": sentence_id}, {"_id": 0}).to_list(1000)
    return annotations

# Tag Structure Routes
@api_router.get("/tag-structure")
async def get_tag_structure():
    """Get the structured tag definitions for annotation"""
    return {"tag_structure": SDOH_TAG_STRUCTURE}

# Analytics Routes
@api_router.get("/analytics/overview")
async def get_analytics_overview(current_user: User = Depends(get_current_user)):
    # Total documents
    total_docs = await db.documents.count_documents({})
    
    # Total sentences
    total_sentences = await db.sentences.count_documents({})
    
    # Total annotations (including skipped)
    total_annotations = await db.annotations.count_documents({})
    
    # Skipped sentences
    skipped_sentences = await db.annotations.count_documents({"skipped": True})
    
    # Tagged sentences
    tagged_sentences = await db.annotations.count_documents({"skipped": False})
    
    # Unique annotators
    unique_annotators = len(await db.annotations.distinct("user_id"))
    
    return {
        "total_documents": total_docs,
        "total_sentences": total_sentences,
        "total_annotations": total_annotations,
        "tagged_sentences": tagged_sentences,
        "skipped_sentences": skipped_sentences,
        "unique_annotators": unique_annotators
    }

@api_router.get("/analytics/tag-prevalence")
async def get_tag_prevalence(current_user: User = Depends(get_current_user)):
    """Get tag prevalence across all annotations"""
    annotations = await db.annotations.find({"skipped": False}, {"_id": 0}).to_list(10000)
    
    tag_counts = defaultdict(int)
    domain_counts = defaultdict(int)
    category_counts = defaultdict(int)
    valence_counts = {"positive": 0, "negative": 0}
    
    for annotation in annotations:
        for tag in annotation.get('tags', []):
            domain_counts[tag['domain']] += 1
            category_counts[f"{tag['domain']} - {tag['category']}"] += 1
            tag_counts[f"{tag['category']} - {tag['tag']}"] += 1
            valence_counts[tag['valence']] += 1
    
    return {
        "domain_counts": dict(domain_counts),
        "category_counts": dict(category_counts),
        "tag_counts": dict(tag_counts),
        "valence_counts": valence_counts
    }

@api_router.get("/admin/analytics/users")
async def get_user_analytics(admin_user: User = Depends(get_admin_user)):
    """Admin only: Get detailed user analytics"""
    users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
    
    # Get annotation counts per user
    user_annotations = {}
    for user in users:
        user_id = user['id']
        total_annotations = await db.annotations.count_documents({"user_id": user_id})
        tagged_count = await db.annotations.count_documents({"user_id": user_id, "skipped": False})
        skipped_count = await db.annotations.count_documents({"user_id": user_id, "skipped": True})
        
        user_annotations[user_id] = {
            "user": User(**user),
            "total_annotations": total_annotations,
            "tagged_annotations": tagged_count,
            "skipped_annotations": skipped_count
        }
    
    return user_annotations

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