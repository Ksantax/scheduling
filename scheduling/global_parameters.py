import os
from pathlib import Path


DAYS_PER_WEEK = 6
CLASSES_PER_DAY = 7
MAX_CLASSES_PER_DAY = 4

NUMBER_OF_ITERATIONS = 100_000
SAVE_FILE_NAME = 'test'

TEMP_DIR = Path(__file__).parent / 'temp'
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)
RESULT_DIR = TEMP_DIR / 'results'
if not os.path.exists(RESULT_DIR):
    os.makedirs(RESULT_DIR)
POPS_DIR = TEMP_DIR / 'populations'
if not os.path.exists(POPS_DIR):
    os.makedirs(POPS_DIR)
