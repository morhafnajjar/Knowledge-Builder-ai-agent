from fastapi import FastAPI, Request, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import json
import os
import google.generativeai as genai
import asyncio
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Read Gemini API key from api.env
key = None
with open("api.env", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"): continue
        if "=" in line:
            k, v = line.split("=", 1)
            if k.strip() == "gapi":
                key = v.strip().strip('"')
                break

# Configure Gemini
if not key:
    raise RuntimeError("Gemini API key not found in api.env")
genai.configure(api_key=key)

app = FastAPI()

# Serve static files (index.html, logo.png, etc.) from root
app.mount("/static", StaticFiles(directory="."), name="static")

@app.get("/")
def read_index():
    return FileResponse("index.html")

# Allow CORS for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LessonRequest(BaseModel):
    grade: str
    lesson: str

class Idea(BaseModel):
    concept: str
    explanation: str
    example: str
    question: str

class FeedbackRequest(BaseModel):
    grade: str
    lesson: str
    feedback: List[Dict[str, Any]]
    subtopicPath: List[int] = []

async def generate_subtopics(concept: str, lesson: str, grade: str, parent_id: str) -> list:
    prompt = f'''
For the topic "{concept}" from the lesson "{lesson}" for grade {grade}, generate a list of 9 simpler subtopics. For each subtopic, provide:
- The concept title
- A simple explanation
- A direct, practical example with a specific solution or equation (not a conceptual definition)
- A multiple choice question with 3 options (A, B, C) and specify the correct answer
- The correct answer (A, B, or C)

Return the result as a JSON array, where each item has: concept, explanation, example, question, options, correct_answer.
'''
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        import re
        import ast
        text = response.text
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            subtopics_json = match.group(0)
        else:
            subtopics_json = text
        try:
            subtopics = json.loads(subtopics_json)
        except Exception:
            subtopics = ast.literal_eval(subtopics_json)
        result = []
        for idx, sub in enumerate(subtopics[:9]):
            result.append({
                "id": f"{parent_id}{idx+1}",
                "concept": str(sub.get("concept", "")),
                "explanation": str(sub.get("explanation", "")),
                "example": str(sub.get("example", "")),
                "question": str(sub.get("question", "")),
                "options": sub.get("options", ["Option A", "Option B", "Option C"]),
                "correct_answer": str(sub.get("correct_answer", "B")),
                "subtopics": []
            })
        return result
    except Exception as e:
        return [{"id": f"{parent_id}0", "concept": "Error", "explanation": str(e), "example": "", "question": "", "options": [], "correct_answer": "", "subtopics": []}]

@app.post("/api/lesson", response_model=Dict[str, Any])
async def get_lesson_ideas(data: LessonRequest):
    prompt = f'''
For the lesson "{data.lesson}" for grade {data.grade}, please provide:

1. First, generate a list of 9 key concepts. For each concept, provide:
- The concept title
- A simple explanation
- A direct, practical example with a specific solution or equation (not a conceptual definition)
- A multiple choice question with 3 options (A, B, C) and specify the correct answer
- The correct answer (A, B, or C)

2. Then, create a general introduction that:
- Explains what this lesson is about and why it's important to learn (2-3 sentences)
- Then format the topics list in vertical one column as follows:

Topics:
1) [First Topic Name]                  
2) [Second Topic Name]                                
3) [Third Topic Name]                                  
4) [Fourth Topic Name]                                
5) [Fifth Topic Name]            
6) [Sixth Topic Name]
7) [Seventh Topic Name]
8) [Eighth Topic Name]
9) [Ninth Topic Name]


Return the result as a JSON object with:
- "introduction": the introduction text with the topics formatted in two columns as shown above
- "topics": an array of 9 items, each with: concept, explanation, example, question, options (array of 3 options), correct_answer
'''
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        import re
        import ast
        text = response.text
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            result_json = match.group(0)
        else:
            result_json = text
        try:
            result = json.loads(result_json)
        except Exception:
            result = ast.literal_eval(result_json)
        
        # Extract introduction and topics
        introduction = result.get("introduction", f"This lesson covers {data.lesson} for grade {data.grade} students.")
        topics = result.get("topics", [])
        
        # Process topics and add id
        processed_topics = []
        for idx, topic in enumerate(topics[:9]):
            processed_topics.append({
                "id": str(idx+1),
                "concept": str(topic.get("concept", "")),
                "explanation": str(topic.get("explanation", "")),
                "example": str(topic.get("example", "")),
                "question": str(topic.get("question", "")),
                "options": topic.get("options", ["Option A", "Option B", "Option C"]),
                "correct_answer": str(topic.get("correct_answer", "B")),
                "subtopics": [],
                "feedback": ""
            })
        
        # Save to session.json (overwrite/clear file)
        db_path = "session.json"
        lesson_key = data.lesson.strip()
        db = {lesson_key: {"sessions": [{"feedback": processed_topics}]}}
        with open(db_path, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=2)
        
        return {
            "introduction": introduction,
            "topics": processed_topics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini API error: {e}")

@app.post("/api/feedback")
async def save_feedback(data: FeedbackRequest):
    db_path = "session.json"
    lesson_key = data.lesson.strip()
    # Load current session.json
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            db = json.load(f)
    else:
        return {"status": "error", "message": "No session found."}
    if lesson_key not in db or not db[lesson_key]["sessions"]:
        return {"status": "error", "message": "No session or feedback found for this lesson."}
    session_entry = db[lesson_key]["sessions"][0]

    # Helper to update feedback for all ideas by id
    def update_feedback_by_id(feedback_list, feedback_dict):
        for idea in feedback_list:
            if idea["id"] in feedback_dict:
                idea["feedback"] = feedback_dict[idea["id"]]
            if "subtopics" in idea and idea["subtopics"]:
                update_feedback_by_id(idea["subtopics"], feedback_dict)

    # Build a dict from feedback list: {id: feedback_value}
    feedback_dict = {str(item["id"]): item["feedback"] for item in data.feedback if "id" in item and "feedback" in item}
    update_feedback_by_id(session_entry["feedback"], feedback_dict)

    # Helper to collect all ideas with feedback == 'not understood' and empty subtopics
    def collect_not_understood(feedback_list, path=None):
        if path is None:
            path = []
        result = []
        for idea in feedback_list:
            if idea.get("feedback") == "not understood" and not idea.get("subtopics"):
                result.append((idea, path + [idea["id"]]))
            if "subtopics" in idea and idea["subtopics"]:
                result.extend(collect_not_understood(idea["subtopics"], path + [idea["id"]]))
        return result

    # Generate subtopics for all such ideas
    not_understood_ideas = collect_not_understood(session_entry["feedback"])
    for idea, path in not_understood_ideas:
        subtopics = await generate_subtopics(idea["concept"], lesson_key, data.grade, idea["id"])
        idea["subtopics"] = subtopics

    # Save only the updated session
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    # Return the subtopics for the first 'not understood' idea (if any)
    if not_understood_ideas:
        first_idea, first_path = not_understood_ideas[0]
        return {
            "status": "success",
            "subtopics": first_idea["subtopics"],
            "parent_id": first_idea["id"],
            "subtopicPath": first_path
        }
    else:
        return {"status": "success", "subtopics": [], "message": "No more not understood ideas."}

# Health check endpoint
@app.get("/ping")
async def ping():
    return {"msg": "pong"} 

@app.get("/api/full_explain")
def full_explain():
    db_path = "session.json"
    if not os.path.exists(db_path):
        return JSONResponse(content={"error": "No session found."}, status_code=404)
    with open(db_path, "r", encoding="utf-8") as f:
        db = json.load(f)
    # Assume only one lesson/session for simplicity
    lesson_key = next(iter(db.keys()))
    session = db[lesson_key]["sessions"][0]
    misunderstood = []
    def collect_not_understood(items, parent=None):
        for item in items:
            if item.get("feedback", "") == "not understood":
                misunderstood.append({
                    "id": item.get("id"),
                    "concept": item.get("concept"),
                    "explanation": item.get("explanation"),
                    "example": item.get("example"),
                    "question": item.get("question"),
                    "parent": parent
                })
            # Recursively check subtopics
            if "subtopics" in item:
                collect_not_understood(item["subtopics"], parent=item.get("concept"))
    collect_not_understood(session["feedback"])
    # Newer (simpler) first, older (harder) last, by id length then id value
    misunderstood.sort(key=lambda x: (len(str(x["id"])), str(x["id"])))
    return {"misunderstood": misunderstood}

@app.get("/api/full_arranged_quiz")
def full_arranged_quiz():
    db_path = "session.json"
    if not os.path.exists(db_path):
        return JSONResponse(content={"error": "No session found."}, status_code=404)
    with open(db_path, "r", encoding="utf-8") as f:
        db = json.load(f)
    lesson_key = next(iter(db.keys()))
    session = db[lesson_key]["sessions"][0]
    quiz_items = []
    def collect_quiz(items):
        for item in items:
            if item.get("feedback", "") == "not understood":
                quiz_items.append({
                    "id": item.get("id"),
                    "concept": item.get("concept"),
                    "question": item.get("question"),
                    "options": item.get("options", [])[:3],
                    "correct_answer": item.get("correct_answer", "")
                })
            if "subtopics" in item:
                collect_quiz(item["subtopics"])
    collect_quiz(session["feedback"])
    quiz_items.sort(key=lambda x: (len(str(x["id"])), str(x["id"])))
    return {"quiz": quiz_items}

@app.post("/api/very_simple_explain")
async def very_simple_explain():
    false_q_path = "false-Q.json"
    if not os.path.exists(false_q_path):
        return JSONResponse(content={"error": "No false-Q file found."}, status_code=404)
    with open(false_q_path, "r", encoding="utf-8") as f:
        false_q = json.load(f)
    explanations = []
    for item in false_q.get("incorrect", []):
        prompt = f"Explain the concept '{item['concept']}' in a very, very simple way, as if explaining to a 6-year-old."
        try:
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = await asyncio.to_thread(model.generate_content, prompt)
            explanations.append({
                "id": item["id"],
                "concept": item["concept"],
                "simple_explanation": response.text
            })
        except Exception as e:
            explanations.append({
                "id": item["id"],
                "concept": item["concept"],
                "simple_explanation": f"Error: {e}"})
    return {"very_simple_explanations": explanations} 

@app.post("/api/evaluate_quiz")
async def evaluate_quiz(answers: Dict[str, str] = Body(...)):
    db_path = "session.json"
    false_q_path = "false-Q.json"
    if not os.path.exists(db_path):
        return JSONResponse(content={"error": "No session found."}, status_code=404)
    with open(db_path, "r", encoding="utf-8") as f:
        db = json.load(f)
    lesson_key = next(iter(db.keys()))
    session = db[lesson_key]["sessions"][0]
    incorrect = []
    def collect_misunderstood(items):
        result = []
        for item in items:
            if item.get("feedback", "") == "not understood":
                result.append(item)
            if "subtopics" in item:
                result.extend(collect_misunderstood(item["subtopics"]))
        return result
    misunderstood = collect_misunderstood(session["feedback"])
    for item in misunderstood:
        user_answer = answers.get(str(item["id"]))
        correct_answer = item.get("correct_answer")
        if user_answer is None or user_answer != correct_answer:
            incorrect.append({
                "id": item["id"],
                "concept": item["concept"],
                "user_answer": user_answer,
                "correct_answer": correct_answer
            })
    if incorrect:
        with open(false_q_path, "w", encoding="utf-8") as f:
            json.dump({"incorrect": incorrect}, f, ensure_ascii=False, indent=2)
        return {"status": "incomplete", "incorrect": incorrect, "message": "Some answers were incorrect. Very simple explanation is available."}
    else:
        if os.path.exists(false_q_path):
            os.remove(false_q_path)
        return {"status": "complete", "message": "All answers correct. Session complete."} 