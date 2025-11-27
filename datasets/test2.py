import pandas as pd
from nuts import NUTS_COORDINATES, NUTS_REGIONS

# Load CSV
path = '/Users/antoinechosson/Desktop/EELISA/EELISA-Data-analysis/datasets/european_jobs_withcoordinates.csv'
output_path = '/Users/antoinechosson/Desktop/EELISA/EELISA-Data-analysis/datasets/european_jobs_withcoordinates.csv'
df = pd.read_csv(path)

# -------------------------------------------
# 1. Prepare CITY coordinate dictionary (Turkey only)
# -------------------------------------------
CITY_COORDINATES_TR = {
    "İstanbul": (41.0082, 28.9784),
    "Ankara": (39.9208, 32.8541),
    "İzmir": (38.4192, 27.1287),
    "Bursa": (40.1950, 29.0600),
    "Antalya": (36.8969, 30.7133),
    "Adana": (37.0017, 35.3289),
    "Konya": (37.8667, 32.4833),
    "Gaziantep": (37.0662, 37.3833),
    "Kocaeli": (40.8533, 29.8815),
    "Tekirdağ": (40.9780, 27.5110),
    "Balıkesir": (39.6484, 27.8826),
    "Muğla": (37.2153, 28.3636),
    "Aydın": (37.8444, 27.8458),
    "Samsun": (41.2867, 36.3300),
    "Ordu": (40.9862, 37.8797),
    "Şanlıurfa": (37.1591, 38.7969),
    "Erzurum": (39.9043, 41.2679),
    "Trabzon": (41.0015, 39.7178),
    "Giresun": (40.9128, 38.3895),
    "Elazığ": (38.6810, 39.2260),
    "Diyarbakır": (37.9144, 40.2306),
    "Osmaniye": (37.0680, 36.2616),
    "Karabük": (41.2044, 32.6204),
    "Karaman": (37.1790, 33.2150),
    "Kırklareli": (41.7350, 27.2252),
    "Sakarya": (40.7731, 30.3948),
    "Eskişehir": (39.7767, 30.5206),
    "Yalova": (40.6550, 29.2769),
    "K.Maraş": (37.5736, 36.9371)
}

# -------------------------------------------
# 2. Create city_clean column
# -------------------------------------------
df['city_clean'] = df['region']

# -------------------------------------------
# 3. Apply cleaning ONLY to Turkey rows
# -------------------------------------------
mask_tr = df['country_code'] == 'TR'

# Simplify: remove district
df.loc[mask_tr, 'city_clean'] = (
    df.loc[mask_tr, 'region']
      .str.split('-')
      .str[0]
      .str.strip()
)

# Normalize Istanbul
df.loc[mask_tr, 'city_clean'] = (
    df.loc[mask_tr, 'city_clean']
      .replace({
          'İstanbul Avrupa Yakası': 'İstanbul',
          'İstanbul Anadolu Yakası': 'İstanbul'
      })
)

# -------------------------------------------
# 4. Assign coordinates only for Turkey
# -------------------------------------------
df.loc[mask_tr, 'coordinates'] = df.loc[mask_tr, 'city_clean'].apply(
    lambda x: CITY_COORDINATES_TR.get(x, (None, None))
)

# -------------------------------------------
# 5. Save
# -------------------------------------------
df.to_csv(output_path, index=False)
