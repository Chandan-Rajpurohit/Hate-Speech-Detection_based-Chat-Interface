from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import sqlite3
import torch
from functools import lru_cache






# --- FastAPI App Setup ---



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Load models on startup and verify they work"""
    try:
        print("\n" + "="*60)
        print("STARTING MODEL LOADING...")
        print("="*60 + "\n")
        
        # Test English model
        clf = get_classifier()
        print("✅ English toxic-bert loaded successfully\n")
        
        # Test Hinglish model
        model, tokenizer, device = get_custom_model()
        print(f"✅ Hinglish model loaded successfully on {device}")
        print(f"✅ Model type: {model.config.model_type}")
        print(f"✅ Model labels: {model.config.id2label}")
        print(f"✅ Number of labels: {model.config.num_labels}\n")
        
        # Test inference with multiple examples
        test_cases = [
            "chutiya",
            "saale kutta",
            "hello how are you",
            "tuu bahut bura hai"
        ]
        
        print("="*60)
        print("TESTING HINGLISH MODEL...")
        print("="*60 + "\n")
        
        for test_text in test_cases:
            inputs = tokenizer(test_text, return_tensors="pt", truncation=True, max_length=512, padding=True)
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = model(**inputs)
                logits = outputs.logits
                probs = torch.nn.functional.softmax(logits, dim=-1)
                predicted_class = torch.argmax(probs, dim=-1).item()
                confidence = probs[0][predicted_class].item()
            
            label = model.config.id2label.get(predicted_class, f"class_{predicted_class}")
            print(f"Text: '{test_text}'")
            print(f"  → Predicted: {label} (class {predicted_class})")
            print(f"  → Confidence: {confidence:.4f}")
            print(f"  → Probabilities: {probs[0].tolist()}\n")
        
        print("="*60)
        print("STARTUP COMPLETE - READY TO ACCEPT REQUESTS")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ STARTUP ERROR: {e}")
        import traceback
        traceback.print_exc()

# --- Pydantic Models ---
class MessageIn(BaseModel):
    user_id: int
    text: str

class MessageOut(BaseModel):
    id: int
    user_id: int
    text: str
    is_toxic: bool
    score: float

class ReportIn(BaseModel):
    message_id: int

class FlagIn(BaseModel):
    word: str

class CustomInferenceIn(BaseModel):
    text: str

class CustomInferenceOut(BaseModel):
    text: str
    label: str
    score: float

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect("students.db")
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        toxic_count INTEGER DEFAULT 0
    )''')
    
    # Messages table
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        text TEXT,
        is_toxic BOOLEAN,
        score REAL,
        reported BOOLEAN DEFAULT 0
    )''')
    
    # Flagged words table
    c.execute('''CREATE TABLE IF NOT EXISTS flagged_words (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word TEXT UNIQUE
    )''')
    
    conn.commit()
    conn.close()

init_db()

def db():
    return sqlite3.connect("students.db")

# --- Model Loading ---
@lru_cache(maxsize=1)
def get_classifier():
    """Load English toxic-bert model (cached)"""
    print("[v0] Loading English toxic-bert model...")
    return pipeline("text-classification", model="unitary/toxic-bert")

@lru_cache(maxsize=1)
def get_custom_model():
    """Load custom Hinglish hate speech model from Hugging Face (cached)"""
    MODEL_NAME = "WolfCookin/Hinglish_HateSpeech_Bert"
    print(f"[v0] Loading custom Hinglish model from Hugging Face: {MODEL_NAME}")
    
    try:
        # Load tokenizer and model from Hugging Face
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
        
        # Set to evaluation mode
        model.eval()
        
        # Check device
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = model.to(device)
        
        print(f"[v0] Custom model loaded successfully on {device}")
        print(f"[v0] Model config labels: {model.config.id2label}")
        
        return model, tokenizer, device
    except Exception as e:
        print(f"[ERROR] Failed to load custom model from Hugging Face: {e}")
        import traceback
        traceback.print_exc()
        raise

# --- Detection Functions ---
def detect_hinglish_hate(text: str) -> tuple[bool, float]:
    """Detect hate speech in Hinglish using custom model"""
    try:
        model, tokenizer, device = get_custom_model()
        
        print(f"[v0] Hinglish detection for: '{text}'")
        
        # Tokenize
        inputs = tokenizer(
            text, 
            return_tensors="pt", 
            truncation=True, 
            max_length=512,
            padding=True
        )
        
        # Move inputs to device
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        # Run inference
        with torch.no_grad():
            outputs = model(**inputs)
        
        # Get prediction
        logits = outputs.logits
        probs = torch.nn.functional.softmax(logits, dim=-1)
        predicted_class = torch.argmax(probs, dim=-1).item()
        confidence = probs[0][predicted_class].item()
        
        print(f"[v0] Hinglish model output:")
        print(f"[v0]   Logits: {logits[0].tolist()}")
        print(f"[v0]   Probabilities: {probs[0].tolist()}")
        print(f"[v0]   Predicted class: {predicted_class}")
        print(f"[v0]   Confidence: {confidence:.4f}")
        
        label = model.config.id2label.get(predicted_class, f"class_{predicted_class}")
        print(f"[v0]   Label: {label}")
        
        # Check if it's hate speech (class 1 or label contains "HATE")
        is_hate = (predicted_class == 1) or ("HATE" in label.upper() and "NOT" not in label.upper())
        
        print(f"[v0] Hinglish result: is_hate={is_hate}, confidence={confidence:.4f}")
        
        return is_hate, round(confidence, 4)
    except Exception as e:
        print(f"[ERROR] Hinglish model failed: {e}")
        import traceback
        traceback.print_exc()
        return False, 0.0

def detect_toxic(text: str) -> tuple[bool, float]:
    """Detect toxicity using BOTH English and Hinglish models"""
    
    print(f"\n[v0] ========== TOXICITY DETECTION START ==========")
    print(f"[v0] Text: '{text}'")
    
    # 1. Check flagged words first (instant detection)
    conn = db()
    c = conn.cursor()
    c.execute("SELECT word FROM flagged_words")
    flagged = [row[0] for row in c.fetchall()]
    conn.close()
    
    low = text.lower()
    for w in flagged:
        if w in low:
            print(f"[v0] ✓ Flagged word '{w}' found in text")
            print(f"[v0] ========== TOXICITY DETECTION END ==========\n")
            return True, 1.0

    # 2. Check with English toxic-bert model
    print(f"[v0] Running English toxic-bert model...")
    clf = get_classifier()
    out = clf(text)[0]
    label = (out.get("label") or "").lower()
    english_score = float(out.get("score") or 0)
    english_toxic = (label == "toxic" and english_score > 0.5)
    
    print(f"[v0] English model result: label={label}, score={english_score:.4f}, toxic={english_toxic}")
    
    # 3. Check with Hinglish hate speech model
    print(f"[v0] Running Hinglish hate speech model...")
    hinglish_hate, hinglish_score = detect_hinglish_hate(text)
    
    # 4. Flag as toxic if EITHER model detects it
    is_toxic = english_toxic or hinglish_hate
    
    # 5. Use the higher confidence score
    max_score = max(
        english_score if english_toxic else 0, 
        hinglish_score if hinglish_hate else 0
    )
    
    print(f"\n[v0] FINAL RESULT:")
    print(f"[v0]   English: {english_toxic} (score: {english_score:.4f})")
    print(f"[v0]   Hinglish: {hinglish_hate} (score: {hinglish_score:.4f})")
    print(f"[v0]   Final Decision: {'TOXIC' if is_toxic else 'NOT TOXIC'} (score: {max_score:.4f})")
    print(f"[v0] ========== TOXICITY DETECTION END ==========\n")
    
    return is_toxic, round(max_score, 2)

# --- API Endpoints ---
@app.get("/api/messages")
def list_messages():
    """List all messages"""
    conn = db()
    c = conn.cursor()
    c.execute("SELECT id, user_id, text, is_toxic, score FROM messages ORDER BY id")
    rows = c.fetchall()
    conn.close()
    
    messages = [
        {
            "id": r[0],
            "user_id": r[1],
            "text": r[2],
            "is_toxic": bool(r[3]),
            "score": r[4]
        }
        for r in rows
    ]
    return {"messages": messages}

@app.post("/api/messages", response_model=MessageOut)
def create_message(payload: MessageIn):
    """Create a new message with toxicity detection"""
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Empty text")
    
    # Detect toxicity using BOTH models
    is_toxic, score = detect_toxic(payload.text)
    
    # Store message
    conn = db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO messages (user_id, text, is_toxic, score) VALUES (?, ?, ?, ?)",
        (payload.user_id, payload.text, is_toxic, score)
    )
    msg_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return MessageOut(
        id=msg_id,
        user_id=payload.user_id,
        text=payload.text,
        is_toxic=is_toxic,
        score=score
    )

@app.post("/api/report")
def report_message(payload: ReportIn):
    """Report a message"""
    conn = db()
    c = conn.cursor()
    c.execute("UPDATE messages SET reported=1 WHERE id=?", (payload.message_id,))
    conn.commit()
    conn.close()
    return {"message": "Message reported"}

@app.post("/api/flag")
def flag_word(payload: FlagIn):
    """Flag a word as toxic"""
    word = payload.word.lower().strip()
    conn = db()
    c = conn.cursor()
    try:
        c.execute("INSERT OR IGNORE INTO flagged_words (word) VALUES (?)", (word,))
        conn.commit()
        message = f"Word '{word}' flagged as toxic"
    except Exception as e:
        message = f"Error: {str(e)}"
    finally:
        conn.close()
    return {"message": message}

@app.post("/api/custom-inference", response_model=CustomInferenceOut)
def custom_inference(payload: CustomInferenceIn):
    """Test custom Hinglish model directly"""
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Empty text")
    
    is_hate, confidence = detect_hinglish_hate(payload.text)
    label = "HATE" if is_hate else "NOT_HATE"
    
    return CustomInferenceOut(
        text=payload.text,
        label=label,
        score=confidence
    )

# --- Legacy Endpoints (for backward compatibility) ---
@app.post("/check")
def check_text(data: dict):
    """Legacy endpoint for checking toxicity"""
    user_id = data["user_id"]
    text = data["text"]
    
    is_toxic, score = detect_toxic(text)
    
    # Update user toxic count
    conn = db()
    c = conn.cursor()
    c.execute("SELECT toxic_count FROM users WHERE id=?", (user_id,))
    row = c.fetchone()
    
    if not row:
        c.execute("INSERT INTO users (id, toxic_count) VALUES (?, ?)", (user_id, 1 if is_toxic else 0))
        toxic_count = 1 if is_toxic else 0
    else:
        toxic_count = row[0]
        if is_toxic:
            toxic_count += 1
            c.execute("UPDATE users SET toxic_count=? WHERE id=?", (toxic_count, user_id))
    
    conn.commit()
    conn.close()
    
    return {"toxic": is_toxic, "score": score, "toxic_count": toxic_count}

@app.post("/reset_user")
def reset_user(data: dict):
    """Reset a user's toxic count"""
    user_id = data["user_id"]
    conn = db()
    c = conn.cursor()
    c.execute("UPDATE users SET toxic_count=0 WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    return {"message": f"User {user_id} toxic count reset"}
