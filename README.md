# PsychoGraph — Instagram Chat Analysis Pilot

A clinical-grade tool that analyzes Instagram chat exports using Claude AI to surface defense mechanisms, communication KPIs, and qualitative summaries.

---

## 🚀 Quick Start

### Option A: Web Interface (Recommended)

**1. Install dependencies:**
```bash
pip install anthropic fastapi uvicorn python-multipart
```

**2. Set your API key:**
```bash
export ANTHROPIC_API_KEY="your-key-here"
```
Get a key at: https://console.anthropic.com

**3. Start the server:**
```bash
python server.py
```

**4. Open your browser:**
Navigate to http://127.0.0.1:8000 and upload your Instagram export!

### Option B: Command Line

**Run analysis from terminal:**
```bash
# Demo mode (no Instagram data needed)
python analyzer.py

# Analyze a single conversation file
python analyzer.py path/to/message_1.json

# Analyze entire Instagram export folder
python analyzer.py path/to/your_instagram_activity/
```

Results are saved to `analysis_results.json`. Open `dashboard.html` in a browser to view them.

---

## 📦 Getting Your Instagram Data

1. Go to Instagram → Settings → Your Activity → Download your information
2. Select "Download or transfer information"
3. Choose "Some of your information" → Select "Messages"
4. Format: **JSON** (not HTML)
5. Download to device: **This device**
6. Wait for Instagram to prepare your file (can take 5-15 minutes)
7. Download the ZIP file when ready
8. You can upload the ZIP directly to PsychoGraph, or unzip it first

The export will look like:
```
your_instagram_activity/
  messages/
    inbox/
      friend1_abc123/
        message_1.json
        message_2.json
      friend2_xyz789/
        message_1.json
```

---

## 🧠 What It Analyzes

### Defense Mechanisms (per conversation)
- **Denial** — "I'm fine, nothing's wrong"
- **Projection** — "You're the one with the problem"
- **Rationalization** — "It's not a big deal because..."
- **Deflection** — Topic changes when emotions arise
- **Intellectualization** — Over-analyzing to avoid feeling
- **Repression** — Avoiding acknowledging difficult emotions
- **Displacement** — Redirecting emotions to a safer target
- **Passive Aggression** — Indirect hostility
- **Splitting** — All-or-nothing thinking about people
- **Minimization** — Downplaying significance of events

### Communication KPIs (scored 0-10)
- **Emotional Openness** — Willingness to express feelings
- **Vulnerability** — Ability to share difficult emotions
- **Conflict Avoidance** — Tendency to sidestep disagreements
- **Empathy Shown** — Recognition of others' feelings
- **Self-Awareness** — Insight into own emotional patterns
- **Communication Clarity** — Directness and honesty
- **Emotional Reactivity** — Intensity of emotional responses

### Qualitative Summary
- **Relationship Dynamic** — The overall tone and nature of the relationship
- **Behavioral Patterns** — Recurring communication habits
- **Red Flags** — Concerning patterns that may need attention
- **Strengths** — Positive communication abilities
- **Therapy Suggestions** — Areas to explore in clinical work
- **Clinical Notes** — Brief narrative summary

---

## 📊 Using the Dashboard

The dashboard provides an interactive visualization of the analysis:

- **Sidebar** — Click between different conversation partners
- **KPI Cards** — Visual scores with color coding (red/yellow/green)
- **Defense Mechanism Grid** — Counts and example quotes for each mechanism
- **Health Score** — Overall communication health rating (0-10)
- **Qualitative Cards** — Behavioral patterns, red flags, strengths, therapy suggestions

---

## 🔒 Privacy & Ethics

**CRITICAL REMINDERS:**

✅ **DO:**
- Only analyze your own exported chat data
- Get explicit consent if showing results to others
- Use as a **clinical aid** alongside professional judgment
- Keep results confidential and secure

❌ **DO NOT:**
- Analyze someone else's messages without consent
- Use this as a diagnostic tool (it's not)
- Share results without the patient's permission
- Store protected health information without HIPAA compliance
- Rely solely on AI analysis — always use clinical expertise

**This tool is designed to:**
- Surface patterns for clinician review
- Generate conversation starters for therapy
- Provide objective data on communication style
- Supplement (not replace) professional assessment

---

## 🛠️ Architecture

### Files Overview

- **`server.py`** — FastAPI web server that handles uploads and runs analysis
  - Accepts .json or .zip files
  - Extracts Instagram export structure
  - Calls Claude API for each conversation
  - Returns results in dashboard format

- **`analyzer.py`** — Core analysis engine
  - Loads Instagram JSON exports (single file or full folder)
  - Parses message structure and fixes encoding issues
  - Formats conversations for Claude
  - Runs three analysis prompts per conversation:
    1. Defense mechanisms
    2. Communication KPIs
    3. Qualitative summary

- **`dashboard.html`** — Interactive visualization interface
  - Modern dark-mode UI with custom styling
  - Real-time analysis via API calls
  - Side-by-side conversation comparison
  - Built-in demo data for exploration

### How It Works

```
User uploads file → server.py receives it → analyzer.py processes it
    ↓
Instagram JSON parsed → conversations extracted → formatted for Claude
    ↓
Claude analyzes each conversation (3 prompts × N conversations)
    ↓
Results formatted as JSON → sent to dashboard → visualized
```

---

## 🐛 Troubleshooting

**"Cannot connect to API server"**
- Make sure `python server.py` is running
- Check that you see "Server started" message in terminal
- Try refreshing the page

**"Invalid JSON file"**
- Make sure you exported in JSON format (not HTML)
- Check that the file isn't corrupted
- Try uploading the ZIP directly instead of a single file

**"Analysis failed" or timeout**
- Very long conversations may exceed API limits
- The analyzer automatically trims to the most recent 150 messages
- Try analyzing one conversation file at a time if the full export fails

**"ANTHROPIC_API_KEY not found"**
- Set it in your environment: `export ANTHROPIC_API_KEY="your-key"`
- On Windows: `set ANTHROPIC_API_KEY=your-key`
- Or add it to your `.env` file

**Empty conversations or no patient messages**
- Some threads might be read-only (groups you haven't sent messages in)
- The analyzer automatically skips these

---

## 💡 Tips for Best Results

1. **Start small** — Upload a single conversation file first to test
2. **Recent conversations** — Instagram exports newest messages first; analyzer uses the most recent 150
3. **Text-only** — Photos, videos, and reactions are filtered out automatically
4. **Combine with therapy** — Use results as discussion prompts, not conclusions
5. **Multiple sources** — Compare chat analysis with patient's self-report and clinical observation

---

## 📝 Example Output

```json
{
  "patient_name": "Alex",
  "conversations": {
    "Friend Name": {
      "message_count": 143,
      "defense_mechanisms": {
        "denial": { "count": 3, "example": "I'm totally fine" },
        "deflection": { "count": 5, "example": "Anyway, did you see that show?" }
      },
      "kpis": {
        "emotional_openness": { "score": 4, "rationale": "..." },
        "vulnerability": { "score": 2, "rationale": "..." }
      },
      "qualitative_summary": {
        "relationship_dynamic": "Caretaker-avoider dynamic",
        "behavioral_patterns": ["Topic-switching when emotions arise"],
        "red_flags": ["Consistent minimization of concern"],
        "strengths": ["Maintains relationships despite defensiveness"],
        "therapy_suggestions": ["Explore resistance to vulnerability"]
      }
    }
  }
}
```

---

## ⚖️ License & Disclaimer

This is a research/clinical tool. Not intended for:
- Self-diagnosis
- Legal proceedings
- Employment decisions
- Relationship advice without professional context

Always consult with a licensed mental health professional for clinical decisions.

**No warranty expressed or implied. Use at your own discretion and professional judgment.**
