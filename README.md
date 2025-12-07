# EELISA Job Market Data Scraping Pipeline

This project builds a complete data pipeline for collecting, cleaning, translating, and enriching job postings for the EELISA Data Science Mission.
It integrates job vacancies from:

* EURES (European Commission job mobility portal)
* Yenibiris (Turkey’s leading job platform)

and outputs a unified, analysis-ready dataset.

Pipeline Overview

Scraping

* python scraping/eures_scraper.py
* python scraping/turkey_scraper.py


Cleaning & Preprocessing

* python processing/deduplicate.py
* python processing/dates.py
* python processing/coordinates.py


Translation 

* python processing/translation/translate.py


Job Field Classification

* python processing/enrich_field.py

License : Research use — part of the EELISA Data Science Mission.
