import pandas as pd
import json
from openai import OpenAI
import time
import re
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load the dataset
path = '/Users/antoinechosson/Desktop/EELISA/EELISA-Data-analysis/datasets/european_jobs_translated_fixed.csv'
df = pd.read_csv(path)

def classify_job_titles(titles_batch):
    """
    Use OpenAI to classify job titles as technical or non-technical with more lenient criteria
    """
    titles_text = "\n".join([f"{i+1}. {title}" for i, title in enumerate(titles_batch)])
    
    prompt = f"""You are a job classification expert. Classify these job titles as either TECHNICAL or NON_TECHNICAL.

Be LENIENT and consider jobs TECHNICAL if they involve:
- Engineering, software development, data science, research, laboratory work
- IT, manufacturing, automation, quality control, scientific roles
- Technical operations, production management, maintenance, dispatching
- Technical support, analysis, design, programming
- Process optimization, technical coordination
- ANY role that requires technical knowledge or works with technical systems

Only classify as NON_TECHNICAL if clearly:
- Pure sales/marketing (without technical products)
- HR/administration (without technical focus)
- Pure customer service, retail, hospitality
- Cleaning, security, general office work
- Finance/accounting (without technical analysis)

Examples:
- "Manager, Production" → TECHNICAL (manages technical processes)
- "Dispatcher, vehicles" → TECHNICAL (technical coordination)
- "Employee, maintenance" → TECHNICAL (technical work)
- "Sales Representative" → NON_TECHNICAL (unless technical sales)

Job titles:
{titles_text}

Respond ONLY with a valid JSON array of classifications in the exact same order. No other text.
Example format: ["TECHNICAL", "NON_TECHNICAL", "TECHNICAL"]
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=500
        )
        
        result = response.choices[0].message.content.strip()
        print(f"API Response: {result[:50]}...")
        
        # Clean response if it has markdown formatting
        if result.startswith("```"):
            lines = result.split('\n')
            for i, line in enumerate(lines):
                if line.strip().startswith('['):
                    result = '\n'.join(lines[i:])
                    break
            if result.endswith("```"):
                result = result[:-3]
        
        classifications = json.loads(result)
        
        # Validate we have the right number of classifications
        if len(classifications) != len(titles_batch):
            print(f"Warning: Expected {len(titles_batch)} classifications, got {len(classifications)}")
            return ["UNKNOWN"] * len(titles_batch)
            
        return classifications
    
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Raw response: {result}")
        return ["UNKNOWN"] * len(titles_batch)
    except Exception as e:
        print(f"Error processing batch: {e}")
        return ["UNKNOWN"] * len(titles_batch)

def is_valid_job_title_minimal(title):
    """
    Minimal filtering - only removes obvious spam/invalid entries
    """
    if not title or len(title.strip()) < 1:
        return False
    
    title_clean = title.strip()
    
    # Only remove the most obvious non-job-titles
    obvious_invalid = [
        # Empty or just punctuation
        len(title_clean) == 0,
        # Just numbers
        title_clean.isdigit(),
        # Email addresses
        '@' in title_clean and '.' in title_clean.split('@')[-1] if '@' in title_clean else False,
        # Phone numbers (simple pattern)
        bool(re.match(r'^\+?[\d\s\-\(\)]{7,}$', title_clean)),
        # Extremely long (likely spam)
        len(title_clean) > 150,
        # Repeated characters (obvious spam)
        bool(re.search(r'(.)\1{15,}', title_clean)),
        # No letters at all
        not bool(re.search(r'[a-zA-Z]', title_clean))
    ]
    
    return not any(obvious_invalid)

# Apply minimal filter to only remove obvious spam
print("Before minimal filtering:", len(df))
df_filtered = df[df['job_title'].apply(is_valid_job_title_minimal)].copy()
print("After minimal filtering:", len(df_filtered))

# Check what we're removing
removed_titles = set(df['job_title']) - set(df_filtered['job_title'])
if removed_titles:
    print(f"\nRemoved {len(removed_titles)} invalid titles:")
    for title in list(removed_titles)[:10]:
        print(f"  '{title}'")

# Verify target titles are kept
target_titles = [
    "Dispatcher, vehicles",
    "Employee, maintenance", 
    "Organizer, processing of production information",
    "Manager, Production"
]

print("\nChecking target titles:")
for title in target_titles:
    kept = title in df_filtered['job_title'].values
    print(f"  '{title}': {'✓ KEPT' if kept else '✗ REMOVED'}")

# Process in batches with OpenAI
batch_size = 15
all_classifications = []

print(f"\nProcessing {len(df_filtered)} job titles with OpenAI...")

for i in range(0, len(df_filtered), batch_size):
    batch = df_filtered['job_title'].iloc[i:i+batch_size].tolist()
    batch_num = i//batch_size + 1
    total_batches = (len(df_filtered)-1)//batch_size + 1
    
    print(f"\nBatch {batch_num}/{total_batches}")
    
    classifications = classify_job_titles(batch)
    all_classifications.extend(classifications)
    
    # Progress indicator
    if batch_num % 10 == 0:
        print(f"Processed {batch_num * batch_size} / {len(df_filtered)} titles...")
    
    # Delay to respect rate limits
    time.sleep(1.5)

# Add classifications to dataframe
df_filtered['classification'] = all_classifications

# Filter for potentially non-technical jobs
non_technical_jobs = df_filtered[df_filtered['classification'] == 'NON_TECHNICAL']

# Save results
non_technical_jobs.to_csv(
    '/Users/antoinechosson/Desktop/EELISA/EELISA-Data-analysis/datasets/non_technical_for_manual_review_v2.csv',
    index=False
)

# Save all classifications for reference
df_filtered.to_csv(
    '/Users/antoinechosson/Desktop/EELISA/EELISA-Data-analysis/datasets/jobs_with_classifications.csv',
    index=False
)

print(f"\n" + "="*50)
print("CLASSIFICATION COMPLETE!")
print("="*50)
print(f"Total processed jobs: {len(df_filtered)}")
print(f"Technical jobs: {len(df_filtered[df_filtered['classification'] == 'TECHNICAL'])}")
print(f"Non-technical jobs: {len(non_technical_jobs)}")
print(f"Unknown/Error: {len(df_filtered[df_filtered['classification'] == 'UNKNOWN'])}")
print(f"\nFiles saved:")
print("- non_technical_for_manual_review_v2.csv (for your review)")
print("- jobs_with_classifications.csv (all jobs with classifications)")
print("\nNext step: Review the non_technical_for_manual_review_v2.csv file")
print("and confirm which jobs should actually be removed.")