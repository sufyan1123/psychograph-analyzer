"""
AI-Powered DSM-5 Diagnostic Module
Uses Claude to intelligently match conversation content to DSM-5 criteria
instead of simple keyword matching.
"""

from anthropic import Anthropic
import json
import os

client = Anthropic()

# Import the criteria database from the original module
from dsm5_diagnostic import DSM5_CRITERIA


def analyze_dsm5_with_ai(conversation_text: str, participant_name: str) -> dict:
    """
    Use Claude to intelligently analyze conversation against DSM-5 criteria.
    This replaces keyword matching with AI understanding.
    """
    
    # Get top 5 most relevant disorders to check (to save API calls)
    priority_disorders = [
        "Separation Anxiety Disorder",
        "Generalized Anxiety Disorder", 
        "Panic Disorder",
        "Major Depressive Disorder",
        "Social Anxiety Disorder"
    ]
    
    all_assessments = []
    
    for disorder_name in DSM5_CRITERIA.keys():
        # Prioritize likely disorders, skip others for efficiency
        if disorder_name not in priority_disorders:
            # Quick keyword check - if no anxiety/mood keywords, skip
            if not any(word in conversation_text.lower() for word in ['scared', 'worried', 'anxious', 'panic', 'afraid', 'miss', 'sad', 'depressed']):
                continue
        
        print(f"    Analyzing: {disorder_name}...")
        assessment = analyze_disorder_with_ai(
            conversation_text,
            disorder_name,
            DSM5_CRITERIA[disorder_name]
        )
        
        if assessment:
            all_assessments.append(assessment)
    
    # Sort by criteria met
    all_assessments.sort(key=lambda x: x['criteria_met_percentage'], reverse=True)
    
    # Find primary diagnosis
    primary = None
    for assessment in all_assessments:
        if assessment['meets_diagnostic_threshold']:
            primary = assessment
            break
    
    return {
        "primary_diagnosis": primary,
        "all_assessments": all_assessments,
        "disclaimer": "AI-assisted screening tool. Clinical diagnosis requires comprehensive evaluation by licensed professional."
    }


def analyze_disorder_with_ai(conversation_text: str, disorder_name: str, disorder_info: dict) -> dict:
    """
    Use Claude to determine if conversation matches DSM-5 criteria for a disorder.
    """
    
    # Build criteria text
    criteria_text = ""
    for crit_id, crit_data in disorder_info['criteria'].items():
        criteria_text += f"\n{crit_id}: {crit_data['text']}\n"
    
    prompt = f"""You are a clinical psychologist analyzing a conversation for signs of {disorder_name}.

CONVERSATION (Patient's messages marked with [PATIENT]):
{conversation_text[:4000]}

DSM-5 DIAGNOSTIC CRITERIA FOR {disorder_name}:
{criteria_text}

REQUIRED: {disorder_info['criteria_count_required']} out of {len(disorder_info['criteria'])} criteria must be met.
{f"DURATION: {disorder_info.get('duration', 'Not specified')}" if 'duration' in disorder_info else ''}

TASK: Determine which criteria are met based on the conversation. Return ONLY valid JSON:

{{
  "criteria_met": {{
    "A1": {{
      "is_met": true/false,
      "evidence": "Direct quote from conversation showing this criterion" or null,
      "rationale": "Brief explanation of why this is/isn't met"
    }},
    "A2": {{ ... }}
  }},
  "total_criteria_met": 5,
  "meets_threshold": true/false,
  "confidence": "High/Moderate/Low",
  "clinical_notes": "Brief summary of why this diagnosis does/doesn't fit"
}}

BE STRICT: Only mark criteria as met if there's clear evidence in the conversation."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        raw = response.content[0].text.strip()
        
        # Clean JSON
        if raw.startswith("```json"):
            raw = raw[7:]
        if raw.startswith("```"):
            raw = raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        
        result = json.loads(raw.strip())
        
        # Build assessment in our format
        criteria_breakdown = {}
        evidence_collection = []
        
        for crit_id, crit_result in result['criteria_met'].items():
            criteria_breakdown[crit_id] = {
                "criterion_text": disorder_info['criteria'].get(crit_id, {}).get('text', ''),
                "is_met": crit_result['is_met'],
                "evidence": [{"message": crit_result['evidence'], "indicator_matched": "AI analysis", "criterion_id": crit_id}] if crit_result['evidence'] else [],
                "evidence_count": 1 if crit_result['evidence'] else 0
            }
            
            if crit_result['is_met'] and crit_result['evidence']:
                evidence_collection.append({
                    "message": crit_result['evidence'],
                    "indicator_matched": "AI analysis",
                    "criterion_id": crit_id
                })
        
        total_met = result['total_criteria_met']
        required = disorder_info['criteria_count_required']
        percentage = (total_met / len(disorder_info['criteria'])) * 100
        
        return {
            "disorder_name": disorder_name,
            "dsm5_page": disorder_info['dsm_page'],
            "pdf_page": disorder_info.get('pdf_page', disorder_info['dsm_page']),
            "section": disorder_info['section'],
            "criteria_met": total_met,
            "total_criteria": len(disorder_info['criteria']),
            "criteria_required": required,
            "criteria_met_percentage": round(percentage, 1),
            "meets_diagnostic_threshold": result['meets_threshold'],
            "confidence_level": result['confidence'],
            "criteria_breakdown": criteria_breakdown,
            "key_evidence": evidence_collection[:5],
            "duration_note": disorder_info.get('duration', 'Not specified'),
            "clinical_interpretation": result['clinical_notes']
        }
    
    except Exception as e:
        print(f"      Error: {e}")
        return None


# Export function
def get_dsm5_diagnosis_ai(conversation_text: str, participant_name: str) -> dict:
    """Main entry point - uses AI analysis instead of keyword matching."""
    return analyze_dsm5_with_ai(conversation_text, participant_name)
