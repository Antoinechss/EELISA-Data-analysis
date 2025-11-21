import pandas as pd 

jobs_dataset = '/Users/antoinechosson/Desktop/EELISA/EELISA-Data-analysis/eures_jobs_full.csv'
df = pd.read_csv(jobs_dataset)
# ----------------
# Column order arangement 
# ----------------

column_order = ['job_id',
                'job_title',
                'date,company_name',
                'country,country_code',
                'region',
                'coordinates',
                'field',
                'full_description']

df = df[column_order]
df.to_csv(jobs_dataset, index=False)
