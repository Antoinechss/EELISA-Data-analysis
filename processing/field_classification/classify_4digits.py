import pandas as pd
from openai import OpenAI
import os
import time
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Load data
path = '/Users/antoinechosson/Desktop/EELISA/EELISA-Data-analysis/datasets/european_jobs.csv'
ISCO_path = '/Users/antoinechosson/Desktop/EELISA/EELISA-Data-analysis/processing/field_classification/ISCO.csv'
cache_file = '/Users/antoinechosson/Desktop/EELISA/EELISA-Data-analysis/processing/field_classification/classification_4digit_cache.json'

df = pd.read_csv(path)
isco = pd.read_csv(ISCO_path)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Create lookup for 4-digit codes that match each 3-digit code
isco_4digit_by_3digit = {}
for _, row in isco.iterrows():
    three_digit = row['3_digit_code']
    four_digit = row['4_digit_code']
    four_digit_label = row['4_digit_label']
    
    if three_digit not in isco_4digit_by_3digit:
        isco_4digit_by_3digit[three_digit] = []
    isco_4digit_by_3digit[three_digit].append(f"{four_digit}: {four_digit_label}")

# Create lookup for labels
isco_4digit_lookup = dict(zip(isco['4_digit_code'], isco['4_digit_label']))

# Load cache if it exists
try:
    with open(cache_file, 'r') as f:
        cache = json.load(f)
    print(f"Loaded cache with {len(cache)} previously classified jobs")
except FileNotFoundError:
    cache = {}
    print("No cache found, starting fresh")

def save_cache():
    """Save current cache to file"""
    with open(cache_file, 'w') as f:
        json.dump(cache, f, indent=2)

def get_cache_key(job):
    """Generate unique cache key for a job"""
    return f"{job['job_title']}||{str(job['full_description'])[:500]}||{job['isco_3_digit']}"

def classify_4digit_batch(jobs_batch):
    """
    Classify jobs into more specific 4-digit ISCO codes based on their 3-digit classification
    """
    
    # Check cache first
    cached_results = []
    uncached_jobs = []
    uncached_indices = []
    
    for i, job in enumerate(jobs_batch):
        cache_key = get_cache_key(job)
        if cache_key in cache:
            cached_results.append((i, cache[cache_key]))
        else:
            uncached_jobs.append(job)
            uncached_indices.append(i)
    
    # If all jobs are cached, return cached results
    if not uncached_jobs:
        result = [None] * len(jobs_batch)
        for idx, classification in cached_results:
            result[idx] = classification
        return result
    
    # Group uncached jobs by their 3-digit code for more efficient processing
    jobs_by_3digit = {}
    for i, job in enumerate(uncached_jobs):
        three_digit = job['isco_3_digit']
        if three_digit not in jobs_by_3digit:
            jobs_by_3digit[three_digit] = []
        jobs_by_3digit[three_digit].append((i, job))
    
    all_classifications = {}
    
    # Process each 3-digit group separately
    for three_digit, job_group in jobs_by_3digit.items():
        if three_digit not in isco_4digit_by_3digit:
            # If no 4-digit subcategories available, skip
            for idx, job in job_group:
                all_classifications[idx] = three_digit + "0"  # Convert to string first
            continue
        
        available_4digits = isco_4digit_by_3digit[three_digit]
        available_4digits_text = "\n".join(available_4digits)
        
        # Prepare job descriptions for this group
        job_descriptions = []
        for i, (_, job) in enumerate(job_group):
            title = job['job_title']
            description = job['full_description']
            current_3digit = job['isco_3_digit']
            current_3digit_label = job.get('isco_3_digit_label', 'Unknown')
            
            description_text = str(description)[:1500] if pd.notna(description) else "No description provided"
            job_text = f"{i+1}. Title: {title}\n   Description: {description_text}\n   Current Classification: {current_3digit} - {current_3digit_label}"
            job_descriptions.append(job_text)
        
        jobs_text = "\n\n".join(job_descriptions)
        
        prompt = f"""You are an expert job classifier. These jobs have already been classified into the 3-digit ISCO code: {three_digit}.

Now you need to classify them into more specific 4-digit ISCO subcategories.

Available 4-digit subcategories for {three_digit}:
{available_4digits_text}

Jobs to classify:
{jobs_text}

For each job, analyze the job title and description to determine the MOST SPECIFIC 4-digit ISCO code that best matches the role.
Consider:
- Specific skills and expertise required
- Level of specialization
- Industry focus
- Detailed job responsibilities

Respond with ONLY a JSON array of 4-digit ISCO codes in the same order as the jobs, like:
["{three_digit}1", "{three_digit}2", "{three_digit}1"]

Use only the 4-digit codes from the available list above. Choose the most specific and appropriate subcategory.
"""
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=300
            )
            
            result = response.choices[0].message.content.strip()
            
            # Clean response
            if result.startswith("```"):
                lines = result.split('\n')
                for i, line in enumerate(lines):
                    if line.strip().startswith('['):
                        result = '\n'.join(lines[i:])
                        break
                if result.endswith("```"):
                    result = result[:-3]
            
            group_classifications = json.loads(result)
            
            if len(group_classifications) != len(job_group):
                print(f"Warning: Expected {len(job_group)} classifications for {three_digit}, got {len(group_classifications)}")
                # Default to adding 0 to make it 4-digit
                for idx, job in job_group:
                    all_classifications[idx] = str(three_digit) + "0"  # Convert to string
            else:
                for (idx, job), classification in zip(job_group, group_classifications):
                    all_classifications[idx] = classification
        
        except json.JSONDecodeError as e:
            print(f"JSON decode error for {three_digit}: {e}")
            for idx, job in job_group:
                all_classifications[idx] = str(three_digit) + "0"  # Convert to string
        except Exception as e:
            print(f"Error classifying {three_digit} group: {e}")
            for idx, job in job_group:
                all_classifications[idx] = str(three_digit) + "0"  # Convert to string
    
    # Cache the new results
    for i, job in enumerate(uncached_jobs):
        cache_key = get_cache_key(job)
        cache[cache_key] = all_classifications[i]
    
    # Combine cached and new results
    result = [None] * len(jobs_batch)
    
    # Add cached results
    for idx, classification in cached_results:
        result[idx] = classification
    
    # Add new results
    for i, classification in all_classifications.items():
        result[uncached_indices[i]] = classification
    
    return result

# Initialize 4-digit columns
if 'isco_4_digit' not in df.columns:
    df['isco_4_digit'] = ""
if 'isco_4_digit_label' not in df.columns:
    df['isco_4_digit_label'] = ""

# Filter to only process rows that have 3-digit classification but no 4-digit
unprocessed_mask = (df['isco_3_digit'].notna()) & (df['isco_3_digit'] != "") & ((df['isco_4_digit'].isna()) | (df['isco_4_digit'] == ""))
unprocessed_df = df[unprocessed_mask]

print(f"Total jobs: {len(df)}")
print(f"Jobs needing 4-digit classification: {len(unprocessed_df)}")

if len(unprocessed_df) == 0:
    print("All jobs already have 4-digit classification!")
    exit()

# Process in batches
batch_size = 3  # Smaller batches for 4-digit classification
total_batches = (len(unprocessed_df) - 1) // batch_size + 1

print(f"Processing {total_batches} batches of {batch_size} jobs each")

processed_count = 0
for i in range(0, len(unprocessed_df), batch_size):
    batch_jobs = unprocessed_df.iloc[i:i+batch_size].to_dict('records')
    batch_indices = unprocessed_df.iloc[i:i+batch_size].index
    batch_num = (i // batch_size) + 1
    
    print(f"\nBatch {batch_num}/{total_batches}")
    print(f"Processing jobs {i+1} to {min(i+batch_size, len(unprocessed_df))}")
    
    # Show what 3-digit codes we're refining
    three_digits = [job['isco_3_digit'] for job in batch_jobs]
    print(f"Refining 3-digit codes: {three_digits}")
    
    classifications_4digit = classify_4digit_batch(batch_jobs)
    
    # Apply classifications to dataframe
    for j, (batch_idx, isco_4_code) in enumerate(zip(batch_indices, classifications_4digit)):
        df.loc[batch_idx, 'isco_4_digit'] = isco_4_code
        # Add the label
        label = isco_4digit_lookup.get(isco_4_code, "Unknown")
        df.loc[batch_idx, 'isco_4_digit_label'] = label
    
    processed_count += len(batch_jobs)
    
    # Save progress every 20 batches
    if batch_num % 20 == 0:
        df.to_csv(path, index=False)
        save_cache()
        print(f"Saved progress... ({processed_count} jobs processed)")
    
    # Rate limiting
    time.sleep(3)

# Save final results
df.to_csv(path, index=False)
save_cache()

print(f"\n" + "="*50)
print("4-DIGIT CLASSIFICATION COMPLETE!")
print("="*50)

# Show statistics
isco_4_counts = df['isco_4_digit'].value_counts()
print(f"Classified into {len(isco_4_counts)} different 4-digit ISCO codes")

print("\nTop 10 4-digit ISCO classifications:")
for code, count in isco_4_counts.head(10).items():
    label = isco_4digit_lookup.get(code, "Unknown")
    print(f"  {code}: {label} ({count} jobs)")

print(f"\nSaved classified dataset to: {path}")

# Add this function to check if a job is already in cache AND in the dataframe:
def is_job_already_processed(job_index, job_row):
    """Check if job is already processed (has 4-digit code or is in cache)"""
    # Check if already in dataframe
    if pd.notna(job_row['isco_4_digit']) and job_row['isco_4_digit'] != "" and job_row['isco_4_digit'] != "0":
        return True
    
    # Check cache
    cache_key = get_cache_key(job_row.to_dict())
    return cache_key in cache

# Then modify the main processing loop:
print(f"Total jobs: {len(df)}")

processed_count = 0
skipped_count = 0

for i in range(0, len(df), batch_size):
    batch_df = df.iloc[i:i+batch_size]
    
    # Check which jobs in this batch are already processed
    unprocessed_jobs = []
    unprocessed_indices = []
    
    for idx, (_, row) in enumerate(batch_df.iterrows()):
        if not is_job_already_processed(i + idx, row):
            unprocessed_jobs.append(row.to_dict())
            unprocessed_indices.append(i + idx)
        else:
            skipped_count += 1
    
    if not unprocessed_jobs:
        print(f"Batch {(i // batch_size) + 1}: All jobs already processed, skipping...")
        continue
    
    print(f"\nBatch {(i // batch_size) + 1}: Processing {len(unprocessed_jobs)} new jobs, skipping {len(batch_df) - len(unprocessed_jobs)}")
    
    # Process the unprocessed jobs
    classifications_4digit = classify_4digit_batch(unprocessed_jobs)
    
    # Apply classifications
    for j, isco_4_code in enumerate(classifications_4digit):
        actual_index = unprocessed_indices[j]
        df.loc[actual_index, 'isco_4_digit'] = isco_4_code
        label = isco_4digit_lookup.get(isco_4_code, "Unknown")
        df.loc[actual_index, 'isco_4_digit_label'] = label
    
    processed_count += len(unprocessed_jobs)
    
    # Save progress
    if (i // batch_size + 1) % 20 == 0:
        df.to_csv(path, index=False)
        save_cache()
        print(f"Saved progress... ({processed_count} new jobs processed, {skipped_count} skipped)")
    
    time.sleep(3)

# Save final results
df.to_csv(path, index=False)
save_cache()

print(f"\n" + "="*50)
print("4-DIGIT CLASSIFICATION COMPLETE!")
print("="*50)

# Show statistics
isco_4_counts = df['isco_4_digit'].value_counts()
print(f"Classified into {len(isco_4_counts)} different 4-digit ISCO codes")

print("\nTop 10 4-digit ISCO classifications:")
for code, count in isco_4_counts.head(10).items():
    label = isco_4digit_lookup.get(code, "Unknown")
    print(f"  {code}: {label} ({count} jobs)")

print(f"\nSaved classified dataset to: {path}")

