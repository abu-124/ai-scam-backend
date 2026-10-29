import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai

app = FastAPI()

# Enable CORS so your Chrome Extension can talk to this server from anywhere
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------
# STEP A: ADD YOUR GEMINI API KEY HERE 
# (Or configure it as GEMINI_API_KEY environment variable on Render)
# -------------------------------------------------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

class PagePayload(BaseModel):
    text: str
    url: str

@app.get("/")
def home():
    return {"status": "AI Scam Detector Backend is Running online!"}

@app.post("/analyze")
async def analyze_page(payload: PagePayload):
    if not payload.text or len(payload.text.strip()) < 20:
        return {
            "level": "safe",
            "reason": "Not enough textual content on the page to analyze."
        }

    prompt = f"""
    You are an expert AI recruitment fraud detector. Analyze the following webpage content and URL for job scams, phishing, or suspicious hiring practices.

    Target Indicators:
    1. High Risk (danger): Asks for upfront registration/training fees, payment via wire transfer, high pay for zero skill, buying equipment first.
    2. Moderate Risk (warning): Using generic free webmail (@gmail, @yahoo) for official company recruitment, external-only chat interviews (Telegram/WhatsApp), vague job scope with urgent hiring.
    3. Safe (safe): Legitimate job post, normal hiring workflow, corporate domain.

    Page URL: {payload.url}
    Page Text Excerpt:
    {payload.text[:3500]}

    Respond STRICTLY in JSON format without markdown code blocks:
    {{"level": "safe" | "warning" | "danger", "reason": "1-2 sentences explaining your AI analysis reasoning."}}
    """

    try:
        response = model.generate_content(prompt)
        raw_text = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw_text)
        return data
    except Exception as e:
        return {
            "level": "warning",
            "reason": f"AI Parsing Fallback: Scanned text with notice. ({str(e)})"
        }