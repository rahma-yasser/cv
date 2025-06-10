import typing_extensions as typing#, List
from pydantic import BaseModel
from fastapi import FastAPI
import json
from google import genai
# from dotenv import load_dotenv
import os
import io
import httpx
# google.generativeai

# load_dotenv()
# KEY = os.getenv("API_KEY")
KEY = "AIzaSyC-8XdR5qokgaxsIYvLo6E6m7Uw-MjDONA"

app = FastAPI()

@app.get("/")
async def root():
    return {"Go to '/ext_cv'"}


@app.post("/ext_cv")
async def ex(cv_URL):
    class experience_(BaseModel):#
        jobTitle:str
        companyName:str
        stillWorkingThere:bool
        startDate:str
        endDate:str

    class education_(BaseModel):#
        institution:str
        degree:str
        fieldOfStudy:str
        isUnderGraduate:bool
        startDate:str
        endDate:str

    class project_(BaseModel):#
        name:str
        link:str

    class language_(BaseModel):#
        name:str
        level:str

    class schemaa(typing.TypedDict):
        experiences: list[experience_]
        skill:list[str]
        projects:list[project_]
        education:list[education_]
        languages:list[language_]
        

    CV = io.BytesIO(httpx.get(cv_URL).content)

    client = genai.Client(api_key=KEY)
    
    uploaded_cv = client.files.upload(
    file=CV,
    config=dict(mime_type='application/pdf')
    )
    
    prompt="""Extract data from this CV
    if some of the required entities are missing make there fields empty.
    note in skills you should put the soft and hard skills and in languages put the languages he speaks provided.
    startDate and endDate should be formated as YYYY-MM
    """

    response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=[uploaded_cv, prompt],
    config={
            "response_mime_type": "application/json",
            "response_schema": schemaa,
        },)
    return json.loads(response.text)
