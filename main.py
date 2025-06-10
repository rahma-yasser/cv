
# google.generativeai

# load_dotenv()
# KEY = os.getenv("API_KEY")
import typing_extensions as typing
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
import json
import os
import httpx
import logging
from google import genai

# Configure logging for Heroku
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()


# Load API key from environment variables
KEY = "AIzaSyC-8XdR5qokgaxsIYvLo6E6m7Uw-MjDONA"
if not KEY:
    logger.error("API_KEY not set in environment variables")
    raise ValueError("API_KEY environment variable is required")

# Initialize Google GenAI client
try:
    client = genai.Client(api_key=KEY)
except Exception as e:
    logger.error(f"Failed to initialize Google GenAI client: {e}")
    raise

# Define Pydantic models
class Experience(BaseModel):
    jobTitle: str
    companyName: str
    stillWorkingThere: bool
    startDate: str
    endDate: str

class Education(BaseModel):
    institution: str
    degree: str
    fieldOfStudy: str
    isUnderGraduate: bool
    startDate: str
    endDate: str

class Project(BaseModel):
    name: str
    link: str

class Language(BaseModel):
    name: str
    level: str

class Schema(typing.TypedDict):
    experiences: list[Experience]
    skill: list[str]
    projects: list[Project]
    education: list[Education]
    languages: list[Language]

@app.get("/")
async def root():
    return {"message": "Go to '/ext_cv'"}

@app.post("/ext_cv")
async def extract_cv(cv_url: str):
    try:
        # Use async HTTP client with timeout
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(cv_url)
            response.raise_for_status()  # Raise exception for bad status codes
            cv_content = io.BytesIO(response.content)

        # Upload CV to Google GenAI
        uploaded_cv = client.files.upload(
            file=cv_content,
            config=dict(mime_type='application/pdf')
        )

        # Define extraction prompt
        prompt = """
        Extract data from this CV. If some required entities are missing, make their fields empty.
        Note: In skills, include both soft and hard skills. In languages, include spoken languages provided.
        Format startDate and endDate as YYYY-MM.
        """

        # Generate content with schema
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[uploaded_cv, prompt],
            config={
                "response_mime_type": "application/json",
                "response_schema": Schema,
            },
        )

        return json.loads(response.text)

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching CV: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to fetch CV: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing CV: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Cleanup to avoid resource leaks
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down FastAPI application")
