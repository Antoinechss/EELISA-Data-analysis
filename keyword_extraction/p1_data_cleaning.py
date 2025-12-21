import pandas as pd
import re

path = "/Users/antoinechosson/Desktop/EELISA/EELISA-Data-analysis/datasets/european_jobs.csv"
df = pd.read_csv(path)

def clean_job_text(text: str) -> str:
    """
    Light pipeline to clean job descriptions for NLP
    """
    if pd.isna(text):
        return ""

    t = str(text)

    # Normalize whitespace
    t = t.replace("\xa0", " ")
    t = re.sub(r"\s+", " ", t).strip()
    # Remove very common boilerplate markers (conservative)
    t = re.sub(r"(?i)\b(eoe|equal opportunity employer)\b.*", "", t)
    t = re.sub(r"(?i)\b(apply now|apply today)\b", " ", t)
    # Remove URLs/emails
    t = re.sub(r"https?://\S+|www\.\S+", " ", t)
    t = re.sub(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", " ", t)
    # Keep useful punctuation for phrase boundaries
    t = re.sub(r"[^\w\s\-\.\,\;\:\(\)\/\+]", " ", t)
    # Final whitespace cleanup
    t = re.sub(r"\s+", " ", t).strip()

    return t


# Building corpus for Keyword Extraction 
corpus_df = df[[
    "job_id",
    "country",
    "isco_3_digit_label",
    "full_description"
]].copy()

corpus_df["clean_description"] = corpus_df["full_description"].apply(clean_job_text)

corpus_df = corpus_df[[
    "job_id",
    "country",
    "isco_3_digit_label",
    "clean_description"
]].reset_index(drop=True)

print("\nExample cleaned description:\n")
print(corpus_df["clean_description"].iloc[0][:500])
