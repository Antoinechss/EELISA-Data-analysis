import pandas as pd

jobs_dataset = '/Users/antoinechosson/Desktop/EELISA/EELISA-Data-analysis/eures_jobs_full.csv'
df = pd.read_csv(jobs_dataset)

# ------------------------
# Date processing
# ------------------------
# ------------------------
# Translating timestamp to proper  YYYY-MM-DD format 
# ------------------------

def parse_date(val):
    try:
        # Try to parse as integer timestamp (milliseconds)
        if pd.notnull(val) and str(val).isdigit() and len(str(val)) > 10:
            return pd.to_datetime(int(val), unit='ms')
        # Try to parse as normal date string
        return pd.to_datetime(val, errors='coerce')
    except Exception:
        return pd.NaT

df['date'] = df['date'].apply(parse_date).dt.strftime('%Y-%m-%d')
df.to_csv('/Users/antoinechosson/Desktop/EELISA/EELISA-Data-analysis/eures_jobs_full.csv', index=False)

# ------------------------
# Restrict to recent job posts
# ------------------------

# Convert 'date' to datetime first (handles both strings and timestamps)
def parse_date(val):
    try:
        if pd.notnull(val) and str(val).isdigit() and len(str(val)) > 10:
            return pd.to_datetime(int(val), unit='ms')
        return pd.to_datetime(val, errors='coerce')
    except Exception:
        return pd.NaT

df['date'] = df['date'].apply(parse_date)

# Filter for posts from 2025 and later
df = df[df['date'] >= pd.to_datetime("2025-01-01")]

# Calculate the average date and print stats
average_timestamp = df['date'].dropna().astype(int).mean()
average_date = pd.to_datetime(average_timestamp)

print("Average date:", average_date.strftime('%Y-%m-%d'))
print(df.shape)
print(df['date'].min())
print(df['date'].max())
print(df.shape)
