import pandas as pd
import os
import pickle
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
from tqdm import tqdm
from langdetect import detect, LangDetectException

jobs_dataset = '/Users/antoinechosson/Desktop/EELISA/EELISA-Data-analysis/eures_jobs_full.csv'
cache_path = '/Users/antoinechosson/Desktop/EELISA/EELISA-Data-analysis/processing/translation_cache.pkl'
output_path = '/Users/antoinechosson/Desktop/EELISA/EELISA-Data-analysis/eures_jobs_full_translated.csv'

df = pd.read_csv(jobs_dataset)

# Load or initialize translation cache
if os.path.exists(cache_path):
    with open(cache_path, 'rb') as f:
        translation_cache = pickle.load(f)
else:
    translation_cache = {}

# Load NLLB model and tokenizer
model_name = "facebook/nllb-200-distilled-600M"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
translator = pipeline("translation", model=model, tokenizer=tokenizer, src_lang="auto", tgt_lang="eng_Latn", device=0, max_length=512)

def is_english(text):
    try:
        return detect(text.strip()) == "en"
    except LangDetectException:
        return False

def translate_column(column):
    results = []
    save_every = 50
    for i, text in enumerate(tqdm(df[column], desc=f"Translating {column}")):
        if pd.isnull(text) or not str(text).strip():
            results.append("")
            continue
        text = str(text)
        if text in translation_cache:
            results.append(translation_cache[text])
            continue
        if is_english(text):
            translation_cache[text] = text
            results.append(text)
            continue
        try:
            translation = translator(text)[0]['translation_text']
            translation_cache[text] = translation
            results.append(translation)
        except Exception as e:
            print(f"Translation error: {e}")
            results.append(text)
        if i % save_every == 0 and i > 0:
            with open(cache_path, 'wb') as f:
                pickle.dump(translation_cache, f)
    # Save at the end of the column too
    with open(cache_path, 'wb') as f:
        pickle.dump(translation_cache, f)
    return results

df['job_title_en'] = translate_column('job_title')
df['full_description_en'] = translate_column('full_description')

df.to_csv(output_path, index=False)