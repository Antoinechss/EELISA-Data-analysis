import pandas as pd 

path = '/Users/antoinechosson/Desktop/EELISA/EELISA-Data-analysis/datasets/european_jobs.csv'
df = pd.read_csv(path)
df = df.drop(columns=['city_clean'])

df = df[['job_id',
         'job_title',
         'date',
         'company_name',
         'country',
         'country_code',
         'region',
         'coordinates',
         'field',
         'full_description']]

df.to_csv(path, index=False)
