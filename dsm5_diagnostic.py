"""
DSM-5 Diagnostic Assessment Module
Analyzes chat conversations against DSM-5 diagnostic criteria
and provides evidence-based diagnosis recommendations.
"""

import re
from typing import Dict, List, Tuple

# ── DSM-5 Diagnostic Criteria Database ────────────────────────────────────────
# This contains the major diagnostic criteria from DSM-5
# Each entry includes: criteria text, DSM-5 page reference, and indicators to look for

DSM5_CRITERIA = {
    "Borderline Personality Disorder": {
        "dsm_page": 663,
        "pdf_page": 705,  # PDF page number may differ from book page
        "section": "Personality Disorders",
        "criteria_count_required": 5,  # Need 5 out of 9 criteria
        "criteria": {
            "A1": {
                "text": "Frantic efforts to avoid real or imagined abandonment",
                "indicators": [
                    "panic when someone doesn't respond",
                    "excessive reassurance seeking",
                    "threats when feeling abandoned",
                    "drastic measures to prevent separation",
                    "fear of being alone",
                    "clinging behavior"
                ]
            },
            "A2": {
                "text": "Pattern of unstable and intense interpersonal relationships characterized by alternating between extremes of idealization and devaluation",
                "indicators": [
                    "rapidly changing opinions of others",
                    "splitting",
                    "all good vs all bad",
                    "intense but unstable relationships",
                    "idealization followed by devaluation",
                    "you're perfect",
                    "you're terrible"
                ]
            },
            "A3": {
                "text": "Identity disturbance: markedly and persistently unstable self-image or sense of self",
                "indicators": [
                    "don't know who I am",
                    "changing goals",
                    "confusion about identity",
                    "feelings of emptiness about self",
                    "who am I"
                ]
            },
            "A4": {
                "text": "Impulsivity in at least two areas that are potentially self-damaging",
                "indicators": [
                    "impulsive spending",
                    "substance use",
                    "reckless",
                    "binge eating",
                    "risky",
                    "just did it without thinking"
                ]
            },
            "A5": {
                "text": "Recurrent suicidal behavior, gestures, or threats, or self-mutilating behavior",
                "indicators": [
                    "want to die",
                    "self-harm",
                    "cutting",
                    "suicidal",
                    "kill myself",
                    "end it all"
                ]
            },
            "A6": {
                "text": "Affective instability due to a marked reactivity of mood",
                "indicators": [
                    "mood swings",
                    "up and down",
                    "irritable",
                    "extreme reactions",
                    "emotional roller coaster"
                ]
            },
            "A7": {
                "text": "Chronic feelings of emptiness",
                "indicators": [
                    "feel empty",
                    "hollow",
                    "void",
                    "nothing inside",
                    "bored all the time"
                ]
            },
            "A8": {
                "text": "Inappropriate, intense anger or difficulty controlling anger",
                "indicators": [
                    "rage",
                    "can't control anger",
                    "explosive",
                    "angry all the time",
                    "lost it",
                    "seeing red"
                ]
            },
            "A9": {
                "text": "Transient, stress-related paranoid ideation or severe dissociative symptoms",
                "indicators": [
                    "everyone's against me",
                    "feel unreal",
                    "dissociate",
                    "paranoid",
                    "out of body"
                ]
            }
        }
    },
    
    "Major Depressive Disorder": {
        "dsm_page": 160,
        "pdf_page": 202,
        "section": "Depressive Disorders",
        "criteria_count_required": 5,
        "duration": "2 weeks",
        "criteria": {
            "A1": {
                "text": "Depressed mood most of the day, nearly every day",
                "indicators": [
                    "feeling sad",
                    "empty",
                    "hopeless",
                    "depressed",
                    "down",
                    "can't be happy"
                ],
                "required_or": "A2"
            },
            "A2": {
                "text": "Markedly diminished interest or pleasure in activities",
                "indicators": [
                    "lost interest",
                    "nothing is fun",
                    "don't enjoy",
                    "no motivation",
                    "anhedonia"
                ],
                "required_or": "A1"
            },
            "A3": {
                "text": "Significant weight/appetite changes",
                "indicators": [
                    "lost weight",
                    "gained weight",
                    "no appetite",
                    "eating too much"
                ]
            },
            "A4": {
                "text": "Insomnia or hypersomnia",
                "indicators": [
                    "can't sleep",
                    "sleeping too much",
                    "insomnia",
                    "sleep all day"
                ]
            },
            "A5": {
                "text": "Psychomotor changes",
                "indicators": [
                    "restless",
                    "can't sit still",
                    "moving slowly",
                    "everything takes effort"
                ]
            },
            "A6": {
                "text": "Fatigue or loss of energy",
                "indicators": [
                    "tired",
                    "no energy",
                    "exhausted",
                    "drained"
                ]
            },
            "A7": {
                "text": "Worthlessness or guilt",
                "indicators": [
                    "worthless",
                    "guilty",
                    "my fault",
                    "I'm a failure"
                ]
            },
            "A8": {
                "text": "Concentration difficulties",
                "indicators": [
                    "can't focus",
                    "brain fog",
                    "indecisive",
                    "can't think"
                ]
            },
            "A9": {
                "text": "Thoughts of death or suicide",
                "indicators": [
                    "want to die",
                    "suicidal",
                    "better off dead",
                    "thinking about death"
                ]
            }
        }
    },
    
    "Generalized Anxiety Disorder": {
        "dsm_page": 222,
        "pdf_page": 264,
        "section": "Anxiety Disorders",
        "criteria_count_required": 3,
        "duration": "6 months",
        "criteria": {
            "A": {
                "text": "Excessive anxiety and worry",
                "indicators": [
                    "constant worrying",
                    "anxious",
                    "can't stop worrying",
                    "nervous",
                    "worried"
                ],
                "required": True
            },
            "C1": {
                "text": "Restlessness or feeling on edge",
                "indicators": [
                    "restless",
                    "on edge",
                    "tense",
                    "can't relax"
                ]
            },
            "C2": {
                "text": "Easily fatigued",
                "indicators": [
                    "tired from worrying",
                    "exhausted",
                    "worry makes me tired"
                ]
            },
            "C3": {
                "text": "Difficulty concentrating",
                "indicators": [
                    "can't focus",
                    "mind goes blank",
                    "distracted"
                ]
            },
            "C4": {
                "text": "Irritability",
                "indicators": [
                    "irritable",
                    "annoyed",
                    "short temper",
                    "snappy"
                ]
            },
            "C5": {
                "text": "Muscle tension",
                "indicators": [
                    "tense muscles",
                    "tension",
                    "tight"
                ]
            },
            "C6": {
                "text": "Sleep disturbance",
                "indicators": [
                    "can't sleep",
                    "worry keeps me awake",
                    "restless sleep"
                ]
            }
        }
    },
    
    "Narcissistic Personality Disorder": {
        "dsm_page": 669,
        "pdf_page": 711,
        "section": "Personality Disorders",
        "criteria_count_required": 5,
        "criteria": {
            "A1": {
                "text": "Grandiose sense of self-importance",
                "indicators": [
                    "I'm better than",
                    "I'm special",
                    "I'm the best",
                    "superior"
                ]
            },
            "A2": {
                "text": "Fantasies of success/power/brilliance",
                "indicators": [
                    "when I'm famous",
                    "destined for greatness",
                    "perfect"
                ]
            },
            "A3": {
                "text": "Believes they are special and unique",
                "indicators": [
                    "nobody understands",
                    "I'm different",
                    "you wouldn't get it"
                ]
            },
            "A4": {
                "text": "Requires excessive admiration",
                "indicators": [
                    "need praise",
                    "fishing for compliments",
                    "validation"
                ]
            },
            "A5": {
                "text": "Sense of entitlement",
                "indicators": [
                    "I deserve",
                    "they should",
                    "I'm owed"
                ]
            },
            "A6": {
                "text": "Interpersonally exploitative",
                "indicators": [
                    "uses others",
                    "takes advantage",
                    "manipulates"
                ]
            },
            "A7": {
                "text": "Lacks empathy",
                "indicators": [
                    "don't care how they feel",
                    "their problem",
                    "not my concern"
                ]
            },
            "A8": {
                "text": "Envious or believes others envious",
                "indicators": [
                    "jealous of me",
                    "they want what I have",
                    "envy"
                ]
            },
            "A9": {
                "text": "Arrogant behaviors",
                "indicators": [
                    "condescending",
                    "looking down",
                    "dismissive"
                ]
            }
        }
    }
}


def analyze_dsm5_diagnosis(conversation_text: str, participant_name: str) -> Dict:
    """Analyze conversation against DSM-5 criteria and return diagnosis."""
    
    messages = conversation_text.split('\n')
    patient_messages = [m for m in messages if m.startswith('[PATIENT]:')]
    
    diagnoses_assessed = []
    
    for disorder_name, disorder_info in DSM5_CRITERIA.items():
        assessment = assess_disorder(
            disorder_name,
            disorder_info,
            patient_messages
        )
        diagnoses_assessed.append(assessment)
    
    diagnoses_assessed.sort(key=lambda x: x['criteria_met_percentage'], reverse=True)
    
    primary_diagnosis = None
    for diagnosis in diagnoses_assessed:
        if diagnosis['meets_diagnostic_threshold']:
            primary_diagnosis = diagnosis
            break
    
    return {
        "primary_diagnosis": primary_diagnosis,
        "all_assessments": diagnoses_assessed,
        "disclaimer": "AI-assisted screening tool. Clinical diagnosis requires comprehensive evaluation by licensed professional."
    }


def assess_disorder(disorder_name: str, disorder_info: Dict, patient_messages: List[str]) -> Dict:
    """Assess specific disorder against conversation."""
    
    criteria_results = {}
    criteria_met_count = 0
    evidence_collection = []
    
    for criterion_id, criterion_data in disorder_info['criteria'].items():
        evidence_found = []
        
        for message in patient_messages:
            message_lower = message.lower()
            
            for indicator in criterion_data['indicators']:
                if indicator.lower() in message_lower:
                    evidence_found.append({
                        "message": message.replace('[PATIENT]:', '').strip(),
                        "indicator_matched": indicator,
                        "criterion_id": criterion_id
                    })
        
        is_met = len(evidence_found) > 0
        
        criteria_results[criterion_id] = {
            "criterion_text": criterion_data['text'],
            "is_met": is_met,
            "evidence": evidence_found[:3],
            "evidence_count": len(evidence_found)
        }
        
        if is_met:
            criteria_met_count += 1
            evidence_collection.extend(evidence_found[:2])
    
    total_criteria = len(disorder_info['criteria'])
    required_count = disorder_info.get('criteria_count_required', total_criteria)
    meets_threshold = criteria_met_count >= required_count
    percentage = (criteria_met_count / total_criteria) * 100
    
    if percentage >= 80:
        confidence = "High"
    elif percentage >= 60:
        confidence = "Moderate"
    elif percentage >= 40:
        confidence = "Low"
    else:
        confidence = "Very Low"
    
    return {
        "disorder_name": disorder_name,
        "dsm5_page": disorder_info['dsm_page'],
        "pdf_page": disorder_info.get('pdf_page', disorder_info['dsm_page']),
        "section": disorder_info['section'],
        "criteria_met": criteria_met_count,
        "total_criteria": total_criteria,
        "criteria_required": required_count,
        "criteria_met_percentage": round(percentage, 1),
        "meets_diagnostic_threshold": meets_threshold,
        "confidence_level": confidence,
        "criteria_breakdown": criteria_results,
        "key_evidence": evidence_collection[:5],
        "duration_note": disorder_info.get('duration', 'Not specified'),
        "clinical_interpretation": f"{'Meets' if meets_threshold else 'Does not meet'} diagnostic criteria ({criteria_met_count}/{required_count} criteria). {confidence} confidence."
    }


def get_dsm5_diagnosis(conversation_text: str, participant_name: str) -> Dict:
    """Main entry point for DSM-5 diagnosis analysis."""
    return analyze_dsm5_diagnosis(conversation_text, participant_name)
