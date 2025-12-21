
import pandas as pd 
import re

path = '/Users/antoinechosson/Desktop/EELISA/EELISA-Data-analysis/datasets/european_jobs.csv'

df = pd.read_csv(path)

def clean_job_description(text):
    """
    Light cleaning pipeline to prepare description for NLP 
    """
    if pd.isna(text):
        return ""
    
    t = str(text)

    # Normalize whitespace
    t = t.replace("\xa0", " ")
    t = re.sub(r"\s+", " ", t).strip()
    # Remove very common boilerplate markers (conservative)
    # You can extend later without changing methodology
    t = re.sub(r"(?i)\b(eoe|equal opportunity employer)\b.*", "", t)
    t = re.sub(r"(?i)\b(apply now|apply today)\b", " ", t)
    # Remove URLs/emails (they add noise)
    t = re.sub(r"https?://\S+|www\.\S+", " ", t)
    t = re.sub(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", " ", t)
    # Keep letters/numbers/basic punctuation that helps phrase boundaries
    # (We keep hyphens because they matter: "life-cycle", "problem-solving")
    t = re.sub(r"[^\w\s\-\.\,\;\:\(\)\/\+]", " ", t)
    # Final whitespace cleanup
    t = re.sub(r"\s+", " ", t).strip()

    return t
