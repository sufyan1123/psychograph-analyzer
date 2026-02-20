"""
Instagram Chat Mental Health Analyzer - Pilot Program
Uses Claude API to analyze defense mechanisms, KPIs, and qualitative patterns.

Instagram exports your data as a FOLDER, not a single file.
Inside that folder, messages are split across subfolders like:
  your_instagram_activity/messages/inbox/friendname_abc123/
    message_1.json
    message_2.json   <-- long conversations split into multiple files
    message_3.json

This script handles all of that automatically.
"""

import json
import os
import re
import glob
from collections import defaultdict
from anthropic import Anthropic

# ── Import DSM-5 diagnostic module ──────────────────────────────────────────
try:
    from dsm5_diagnostic_ai import get_dsm5_diagnosis_ai as analyze_dsm5_diagnosis
    DSM5_AVAILABLE = True
    print("✓ DSM-5 diagnostic module loaded")
except ImportError:
    DSM5_AVAILABLE = False
    print("⚠ Warning: DSM-5 diagnostic module not found. Diagnostic features will be disabled.")

# ── Initialize the Anthropic client (reads ANTHROPIC_API_KEY from environment) ──
client = Anthropic()

# ── List of psychological defense mechanisms Claude will look for ──
DEFENSE_MECHANISMS = [
    "denial", "projection", "rationalization", "deflection",
    "intellectualization", "repression", "displacement",
    "passive aggression", "splitting", "minimization"
]


# ════════════════════════════════════════════════════════════════
#  SECTION 1: FILE LOADING
#  Handles reading Instagram's folder/file export structure
# ════════════════════════════════════════════════════════════════

def find_message_files(path: str) -> list:
    """
    Given a path that is either:
      - A single message_X.json file
      - A conversation folder (containing message_1.json, message_2.json, etc.)
      - The top-level Instagram export folder
    Returns a flat list of all message JSON file paths found.
    """

    # If it's a single file, just return it directly
    if os.path.isfile(path) and path.endswith(".json"):
        return [path]

    # If it's a folder, search recursively for all message_*.json files
    # Instagram names them message_1.json, message_2.json, etc.
    if os.path.isdir(path):
        pattern = os.path.join(path, "**", "message_*.json")
        files = glob.glob(pattern, recursive=True)

        if not files:
            # Fallback: grab any .json files in the folder
            pattern = os.path.join(path, "**", "*.json")
            files = glob.glob(pattern, recursive=True)

        return sorted(files)  # sort so message_1 comes before message_2

    raise FileNotFoundError(f"Could not find any message files at: {path}")


def load_single_file(filepath: str) -> dict:
    """
    Load one Instagram message JSON file.
    Instagram sometimes encodes text in latin-1 instead of utf-8,
    so we try utf-8 first, then fall back to latin-1.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except UnicodeDecodeError:
        # Instagram occasionally uses latin-1 encoding for older exports
        with open(filepath, "r", encoding="latin-1") as f:
            return json.load(f)


def load_instagram_export(path: str) -> dict:
    """
    Main loader: finds all message files, loads them, and merges them
    into a single unified structure grouped by conversation thread.

    Returns: { "thread_folder_name": { "participants": [...], "messages": [...], "title": "..." } }
    """
    files = find_message_files(path)
    print(f"Found {len(files)} message file(s) to load")

    # Group files by their parent folder (each folder = one conversation thread)
    threads = defaultdict(list)
    for filepath in files:
        folder = os.path.dirname(filepath)
        threads[folder].append(filepath)

    # For each thread folder, merge all message_X.json files together
    merged_threads = {}
    for folder, filepaths in threads.items():
        thread_name = os.path.basename(folder)  # e.g. "alex_abc123"
        all_messages = []
        participants = []
        title = thread_name

        for fp in sorted(filepaths):  # process in order: message_1, message_2...
            data = load_single_file(fp)

            # Collect participants from first file (they're the same across all split files)
            if not participants and "participants" in data:
                participants = data["participants"]

            # Use the thread title from the JSON if available
            if "title" in data:
                title = data["title"]

            # Accumulate all messages from this split file
            all_messages.extend(data.get("messages", []))

        merged_threads[thread_name] = {
            "participants": participants,
            "messages": all_messages,
            "title": title
        }

    return merged_threads


# ════════════════════════════════════════════════════════════════
#  SECTION 2: MESSAGE PARSING
#  Converts raw Instagram JSON into clean conversation dicts
# ════════════════════════════════════════════════════════════════

def identify_patient(participants: list) -> str:
    """
    In Instagram exports, the account owner is always listed first
    in the participants array. We treat them as the 'patient'.
    """
    if participants:
        return participants[0]["name"]
    return "Patient"


def fix_encoding(text: str) -> str:
    """
    Fix Instagram's common encoding bug where UTF-8 characters get
    double-encoded as latin-1 (e.g., "donâ€™t" should be "don't").
    """
    try:
        return text.encode("latin-1").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        return text  # text was already correct, return as-is


def parse_thread(thread_data: dict, patient_name: str) -> list:
    """
    Parse one conversation thread into a clean list of message dicts.
    Filters out empty messages (photos, videos, reactions with no text).
    """
    clean_messages = []

    for msg in thread_data.get("messages", []):
        content = msg.get("content", "")
        sender  = msg.get("sender_name", "Unknown")
        timestamp = msg.get("timestamp_ms", 0)

        # Skip empty messages (stickers, reactions, unsent messages, media-only, etc.)
        if not content or content.strip() == "":
            continue

        # Fix Instagram's double-encoding bug on the message content
        content = fix_encoding(content)

        clean_messages.append({
            "sender":     sender,
            "content":    content,
            "timestamp":  timestamp,
            "is_patient": sender == patient_name
        })

    # Sort chronologically (Instagram exports messages newest-first, we want oldest-first)
    clean_messages.sort(key=lambda x: x["timestamp"])
    return clean_messages


def format_for_claude(messages: list) -> str:
    """
    Format a list of message dicts into a readable transcript string
    that Claude can analyze. Labels each line as PATIENT or OTHER.
    """
    lines = []
    for msg in messages:
        label = "PATIENT" if msg["is_patient"] else "OTHER"
        lines.append(f"[{label}]: {msg['content']}")
    return "\n".join(lines)


def trim_to_token_limit(conversation_text: str, max_lines: int = 150) -> str:
    """
    If a conversation is very long, take only the most recent N messages
    to avoid exceeding Claude's context window and to keep API costs manageable.
    """
    lines = conversation_text.split("\n")
    if len(lines) > max_lines:
        print(f"  (Conversation trimmed from {len(lines)} to last {max_lines} messages)")
        return "\n".join(lines[-max_lines:])
    return conversation_text


# ════════════════════════════════════════════════════════════════
#  SECTION 3: CLAUDE ANALYSIS
#  Three separate prompts: defense mechanisms, KPIs, qualitative summary
# ════════════════════════════════════════════════════════════════

def clean_json_response(raw: str) -> dict:
    """
    Claude sometimes wraps JSON in markdown code fences like ```json ... ```
    This strips those out and parses the clean JSON string.
    """
    raw = raw.strip()
    raw = re.sub(r"^```json\s*", "", raw)   # remove opening ```json
    raw = re.sub(r"^```\s*", "", raw)        # remove opening ``` with no language tag
    raw = re.sub(r"```$", "", raw)           # remove closing ```
    return json.loads(raw.strip())


def analyze_defense_mechanisms(conversation_text: str, participant: str) -> dict:
    """
    Ask Claude to count how many times each defense mechanism appears
    in BOTH sides of the conversation, with quoted examples.
    """
    prompt = f"""You are a clinical psychologist analyzing a conversation between a patient and {participant}.

Conversation:
{conversation_text}

Analyze defense mechanisms in BOTH the PATIENT's and OTHER person's messages. For each person, count occurrences of each defense mechanism and quote one example. Return ONLY valid JSON with no explanation or markdown.

Defense mechanisms: {', '.join(DEFENSE_MECHANISMS)}

{{
  "patient_defense_mechanisms": {{
    "denial": {{"count": 0, "example": null}},
    "projection": {{"count": 0, "example": null}},
    "rationalization": {{"count": 0, "example": null}},
    "deflection": {{"count": 0, "example": null}},
    "intellectualization": {{"count": 0, "example": null}},
    "repression": {{"count": 0, "example": null}},
    "displacement": {{"count": 0, "example": null}},
    "passive_aggression": {{"count": 0, "example": null}},
    "splitting": {{"count": 0, "example": null}},
    "minimization": {{"count": 0, "example": null}}
  }},
  "other_defense_mechanisms": {{
    "denial": {{"count": 0, "example": null}},
    "projection": {{"count": 0, "example": null}},
    "rationalization": {{"count": 0, "example": null}},
    "deflection": {{"count": 0, "example": null}},
    "intellectualization": {{"count": 0, "example": null}},
    "repression": {{"count": 0, "example": null}},
    "displacement": {{"count": 0, "example": null}},
    "passive_aggression": {{"count": 0, "example": null}},
    "splitting": {{"count": 0, "example": null}},
    "minimization": {{"count": 0, "example": null}}
  }},
  "patient_total": 0,
  "other_total": 0,
  "patient_dominant": "none",
  "other_dominant": "none",
  "interaction_pattern": "Brief description of how their defense patterns interact"
}}"""

    # Send the defense mechanism prompt to Claude
    response = client.messages.create(
        model="claude-opus-4-5-20251101",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    # Strip any markdown formatting and parse the JSON response
    return clean_json_response(response.content[0].text)


def analyze_kpis(conversation_text: str, participant: str) -> dict:
    """
    Ask Claude to score 7 communication KPIs from 0-10 with rationale for BOTH sides,
    plus overall scores and flags if concerning patterns exist.
    """
    prompt = f"""You are a clinical psychologist. Analyze the communication patterns of BOTH people in this conversation.

Conversation:
{conversation_text}

Score each KPI 0-10 for BOTH the patient and the other person with one-sentence rationales. Return ONLY valid JSON, no markdown.

{{
  "patient_kpis": {{
    "emotional_openness": {{"score": 0, "rationale": ""}},
    "vulnerability": {{"score": 0, "rationale": ""}},
    "conflict_avoidance": {{"score": 0, "rationale": ""}},
    "empathy_shown": {{"score": 0, "rationale": ""}},
    "self_awareness": {{"score": 0, "rationale": ""}},
    "communication_clarity": {{"score": 0, "rationale": ""}},
    "emotional_reactivity": {{"score": 0, "rationale": ""}}
  }},
  "other_kpis": {{
    "emotional_openness": {{"score": 0, "rationale": ""}},
    "vulnerability": {{"score": 0, "rationale": ""}},
    "conflict_avoidance": {{"score": 0, "rationale": ""}},
    "empathy_shown": {{"score": 0, "rationale": ""}},
    "self_awareness": {{"score": 0, "rationale": ""}},
    "communication_clarity": {{"score": 0, "rationale": ""}},
    "emotional_reactivity": {{"score": 0, "rationale": ""}}
  }},
  "patient_overall_score": 0,
  "other_overall_score": 0,
  "relationship_health_score": 0,
  "flag_for_review": false,
  "flag_reason": null,
  "dynamic_analysis": "Brief description of how their communication patterns interact"
}}"""

    # Send the KPI scoring prompt to Claude
    response = client.messages.create(
        model="claude-opus-4-5-20251101",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    # Parse and return the JSON response
    return clean_json_response(response.content[0].text)


def qualitative_summary(conversation_text: str, participant: str) -> dict:
    """
    Ask Claude to write brief clinical case notes about BOTH people's
    communication styles, patterns, and how they interact.
    """
    prompt = f"""You are a clinical psychologist writing brief case notes about a conversation between a patient and {participant}.

Conversation:
{conversation_text}

Analyze BOTH sides of this conversation - how they each communicate and how they interact. Return ONLY valid JSON, no markdown.

{{
  "relationship_dynamic": "Overall dynamic between both people",
  "patient_patterns": ["Patient's behavioral patterns"],
  "other_patterns": ["{participant}'s behavioral patterns"],
  "interaction_patterns": ["How their patterns interact or conflict"],
  "patient_red_flags": ["Concerning patterns in patient"],
  "other_red_flags": ["Concerning patterns in other person"],
  "patient_strengths": ["Patient's communication strengths"],
  "other_strengths": ["Other person's communication strengths"],
  "therapy_suggestions": ["Areas to explore in therapy"],
  "clinical_notes": "2-3 sentence narrative analyzing the bidirectional dynamic"
}}"""

    # Send the qualitative summary prompt to Claude
    response = client.messages.create(
        model="claude-opus-4-5-20251101",
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}]
    )

    # Parse and return the JSON response
    return clean_json_response(response.content[0].text)


# ════════════════════════════════════════════════════════════════
#  SECTION 4: MAIN PIPELINE
#  Orchestrates loading → parsing → analysis → saving
# ════════════════════════════════════════════════════════════════

def run_analysis(path: str) -> dict:
    """
    Full pipeline: load all files from the Instagram export path,
    parse every conversation, run all three Claude analyses on each,
    and return the compiled results dict.
    """

    # Load and merge all message files from the given path (file or folder)
    print(f"\nLoading Instagram export from: {path}")
    threads = load_instagram_export(path)
    print(f"Found {len(threads)} conversation thread(s)\n")

    # Identify the patient's name from the first thread's participant list
    first_thread = next(iter(threads.values()))
    patient_name = identify_patient(first_thread["participants"])
    print(f"Patient identified as: {patient_name}\n")

    # Build the top-level results container
    results = {
        "patient_name": patient_name,
        "conversations": {}
    }

    # Loop through every conversation thread and run analysis
    for thread_key, thread_data in threads.items():

        # Use the human-readable thread title if available, otherwise use folder name
        participant_label = thread_data.get("title", thread_key)

        # Parse raw Instagram messages into clean format
        messages = parse_thread(thread_data, patient_name)

        # Skip threads where the patient sent no messages (read-only threads, etc.)
        patient_messages = [m for m in messages if m["is_patient"]]
        if not patient_messages:
            print(f"Skipping '{participant_label}' (no patient messages found)")
            continue

        print(f"Analyzing: {participant_label} ({len(messages)} total, {len(patient_messages)} from patient)")

        # Format the messages as a Claude-readable transcript and trim if too long
        conversation_text = format_for_claude(messages)
        conversation_text = trim_to_token_limit(conversation_text)

        # Run all three Claude analyses and store the results
        try:
            defense_data = analyze_defense_mechanisms(conversation_text, participant_label)
            kpi_data     = analyze_kpis(conversation_text, participant_label)
            summary_data = qualitative_summary(conversation_text, participant_label)
            
            # Run DSM-5 diagnostic assessment if available
            dsm5_data = None
            if DSM5_AVAILABLE:
                try:
                    print(f"  Running DSM-5 diagnostic assessment...")
                    dsm5_data = analyze_dsm5_diagnosis(conversation_text, participant_label)
                except Exception as dsm_error:
                    print(f"  ⚠ DSM-5 analysis failed: {dsm_error}")
                    dsm5_data = {"error": str(dsm_error)}

            results["conversations"][participant_label] = {
                "message_count":       len(messages),
                "defense_mechanisms":  defense_data,
                "kpis":                kpi_data,
                "qualitative_summary": summary_data,
                "dsm5_diagnosis":      dsm5_data  # Add DSM-5 diagnosis
            }
            print(f"  ✓ Done\n")

        except Exception as e:
            # If one conversation fails, log the error and continue with the others
            print(f"  ✗ Error analyzing '{participant_label}': {e}\n")
            results["conversations"][participant_label] = {"error": str(e)}

    return results


def save_results(results: dict, output_path: str = "analysis_results.json"):
    """Save the full results dict to a JSON file for the dashboard to load."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Results saved to: {output_path}")


# ════════════════════════════════════════════════════════════════
#  SECTION 5: DEMO MODE
#  Runs without needing a real Instagram export
# ════════════════════════════════════════════════════════════════

def run_demo() -> dict:
    """
    Generate synthetic conversation data and run the full analysis pipeline on it.
    Useful for testing without a real Instagram export file or folder.
    """
    print("Running in DEMO MODE with synthetic data...\n")

    # Synthetic Instagram-style data mimicking two different conversation threads
    demo_threads = {
        "alex_demo": {
            "title": "Alex",
            "participants": [{"name": "Patient"}, {"name": "Alex"}],
            "messages": [
                {"sender_name": "Patient", "content": "I'm fine, nothing's wrong, I just don't want to talk about it.", "timestamp_ms": 1000},
                {"sender_name": "Alex",    "content": "You seem really upset though?", "timestamp_ms": 2000},
                {"sender_name": "Patient", "content": "I'm not upset. You're always projecting onto me.", "timestamp_ms": 3000},
                {"sender_name": "Alex",    "content": "I'm just worried about you", "timestamp_ms": 4000},
                {"sender_name": "Patient", "content": "It's literally not a big deal, you're overreacting as always.", "timestamp_ms": 5000},
                {"sender_name": "Patient", "content": "Also did you see that movie? Totally different subject lol", "timestamp_ms": 6000},
                {"sender_name": "Alex",    "content": "You keep changing the subject when I try to talk about feelings", "timestamp_ms": 7000},
                {"sender_name": "Patient", "content": "That's just how I communicate, it's not a problem.", "timestamp_ms": 8000},
            ]
        },
        "jordan_demo": {
            "title": "Jordan",
            "participants": [{"name": "Patient"}, {"name": "Jordan"}],
            "messages": [
                {"sender_name": "Jordan",  "content": "Hey are you coming tonight?", "timestamp_ms": 9000},
                {"sender_name": "Patient", "content": "Yeah totally! Can't wait to see everyone", "timestamp_ms": 10000},
                {"sender_name": "Jordan",  "content": "How are you doing?", "timestamp_ms": 11000},
                {"sender_name": "Patient", "content": "Amazing honestly, everything is great.", "timestamp_ms": 12000},
                {"sender_name": "Jordan",  "content": "Really? I heard you've been having a hard time", "timestamp_ms": 13000},
                {"sender_name": "Patient", "content": "Who told you that? I'm totally fine, people exaggerate.", "timestamp_ms": 14000},
            ]
        }
    }

    # Identify patient from the first demo thread
    patient_name = identify_patient(demo_threads["alex_demo"]["participants"])
    results = {"patient_name": patient_name, "conversations": {}}

    # Run the full three-part analysis on each demo thread
    for thread_key, thread_data in demo_threads.items():
        participant_label = thread_data["title"]
        print(f"Analyzing demo conversation with {participant_label}...")

        # Parse and format the demo messages into a Claude-readable transcript
        messages = parse_thread(thread_data, patient_name)
        conversation_text = format_for_claude(messages)

        try:
            defense_data = analyze_defense_mechanisms(conversation_text, participant_label)
            kpi_data     = analyze_kpis(conversation_text, participant_label)
            summary_data = qualitative_summary(conversation_text, participant_label)
            
            # Run DSM-5 diagnostic assessment if available
            dsm5_data = None
            if DSM5_AVAILABLE:
                try:
                    dsm5_data = analyze_dsm5_diagnosis(conversation_text, participant_label)
                except Exception as dsm_error:
                    dsm5_data = {"error": str(dsm_error)}

            results["conversations"][participant_label] = {
                "message_count":       len(messages),
                "defense_mechanisms":  defense_data,
                "kpis":                kpi_data,
                "qualitative_summary": summary_data,
                "dsm5_diagnosis":      dsm5_data
            }
            print(f"  ✓ Done\n")

        except Exception as e:
            print(f"  ✗ Error: {e}\n")
            results["conversations"][participant_label] = {"error": str(e)}

    return results


# ════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # A path was passed as a command-line argument — can be a file OR folder
        path = sys.argv[1]
        results = run_analysis(path)
    else:
        # No argument provided: fall back to demo mode
        results = run_demo()

    # Save the results JSON file for the dashboard to load
    save_results(results)
    print(json.dumps(results, indent=2, ensure_ascii=False))
