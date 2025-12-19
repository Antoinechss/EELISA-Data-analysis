import pandas as pd
import json
from openai import OpenAI
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Use the environment variable
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load the dataset
input_path = '/Users/antoinechosson/Desktop/EELISA/EELISA-Data-analysis/datasets/european_jobs2.csv'
df = pd.read_csv(input_path)

def translate_company_names(companies_batch):
    """
    Translate a batch of company names to English
    """
    companies_text = "\n".join([f"{i+1}. {company}" for i, company in enumerate(companies_batch)])
    
    prompt = f"""Translate these company names to English. Keep the names as company names (don't describe what they do). If a name is already in English or is a proper noun, keep it unchanged.

Company names:
{companies_text}

Respond ONLY with a JSON array of translated company names in the exact same order. No other text.
Example format: ["Apple Inc.", "Microsoft Corporation", "Google LLC"]
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=800
        )
        
        result = response.choices[0].message.content.strip()
        print(f"API Response preview: {result[:60]}...")
        
        # Clean response if it has markdown formatting
        if result.startswith("```"):
            lines = result.split('\n')
            for i, line in enumerate(lines):
                if line.strip().startswith('['):
                    result = '\n'.join(lines[i:])
                    break
            if result.endswith("```"):
                result = result[:-3]
        
        translations = json.loads(result)
        
        # Validate we have the right number of translations
        if len(translations) != len(companies_batch):
            print(f"Warning: Expected {len(companies_batch)} translations, got {len(translations)}")
            return companies_batch  # Return originals if mismatch
            
        return translations
    
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Raw response: {result}")
        return companies_batch  # Return originals on error
    except Exception as e:
        print(f"Error translating batch: {e}")
        return companies_batch  # Return originals on error

# Get unique company names to avoid translating duplicates
unique_companies = df['company_name'].unique().tolist()
print(f"Found {len(unique_companies)} unique company names to translate")

# Process in batches
batch_size = 20
translation_dict = {}
translated_count = 0

print(f"Translating {len(unique_companies)} unique company names...")

for i in range(0, len(unique_companies), batch_size):
    batch = unique_companies[i:i+batch_size]
    batch_num = i//batch_size + 1
    total_batches = (len(unique_companies)-1)//batch_size + 1
    
    print(f"\nBatch {batch_num}/{total_batches}")
    print(f"Companies in batch: {batch[:3]}...")  # Show first 3
    
    translations = translate_company_names(batch)
    
    # Create translation mapping
    for original, translated in zip(batch, translations):
        translation_dict[original] = translated
    
    translated_count += len(batch)
    
    # Progress indicator
    if batch_num % 5 == 0:
        print(f"Translated {translated_count} / {len(unique_companies)} unique companies...")
    
    # Delay to respect rate limits
    time.sleep(1.5)

# Apply translations to the dataframe
print("\nApplying translations to dataset...")
df['company_name_translated'] = df['company_name'].map(translation_dict)

# Handle any that weren't translated (fallback to original)
df['company_name_translated'].fillna(df['company_name'], inplace=True)

# Replace original company_name column with translated version
df['company_name'] = df['company_name_translated']
df = df.drop('company_name_translated', axis=1)

# Save the translated dataset
output_path = '/Users/antoinechosson/Desktop/EELISA/EELISA-Data-analysis/datasets/european_jobs_companies_translated.csv'
df.to_csv(output_path, index=False)

print(f"\n" + "="*50)
print("TRANSLATION COMPLETE!")
print("="*50)
print(f"Total jobs: {len(df)}")
print(f"Unique companies translated: {len(unique_companies)}")
print(f"Saved to: european_jobs_companies_translated.csv")

# Show some examples of translations
print("\nSample translations:")
for i, (original, translated) in enumerate(list(translation_dict.items())[:10]):
    if original != translated:
        print(f"  '{original}' → '{translated}'")
    else:
        print(f"  '{original}' (unchanged)")
