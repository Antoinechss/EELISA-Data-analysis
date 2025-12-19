import pandas as pd 

path = '/Users/antoinechosson/Desktop/EELISA/EELISA-Data-analysis/datasets/european_jobs_translated.csv'
df = pd.read_csv(path)

# The cjob_id column contains both index and job_id - let's split them
# First, let's see what's in the cjob_id column
print("cjob_id column values:")
print(df['cjob_id'].head())

# It looks like the first column contains "0 BG1", "1 BG2" etc.
# Let's extract just the job_id part (after the space)
df['job_id'] = df['cjob_id'].astype(str).str.split().str[1]

# Drop the problematic cjob_id column
df = df.drop('cjob_id', axis=1)

# Reorder columns properly
df = df[['job_id', 'job_title', 'date', 'company_name', 'field', 'country', 'country_code', 'region', 'coordinates', 'full_description']]

# Save to new file as backup
new_path = '/Users/antoinechosson/Desktop/EELISA/EELISA-Data-analysis/datasets/european_jobs_translated_fixed.csv'
df.to_csv(new_path, index=False)

print("Fixed and saved to european_jobs_translated_fixed.csv")
print(df.head())