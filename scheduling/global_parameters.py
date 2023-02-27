import os
from pathlib import Path


DAYS_PER_WEEK = 6
CLASSES_PER_DAY = 7
MAX_CLASSES_PER_DAY = 4

NUMBER_OF_ITERATIONS = 100_000
SAVE_FILE_NAME = 'mut03_cros08_tur3'

TEMP_DIR = Path(__file__).parent / 'temp'
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)
RESULT_DIR = TEMP_DIR / 'results'
if not os.path.exists(RESULT_DIR):
    os.makedirs(RESULT_DIR)
POPS_DIR = TEMP_DIR / 'populations'
if not os.path.exists(POPS_DIR):
    os.makedirs(POPS_DIR)

WEIGHT_TO_ERROR = {
        ('group_window', 'group_windows'),
        ('teacher_window', 'teacher_windows'),
        ('group_parallel_class', 'group_parallels'),
        ('teacher_parallel_class', 'teacher_parallels'),
        ('excess_class', 'excesses'),
        ('standart_classroom_overflow', 'standart_overflows'),
        ('special_classroom_overflow', 'special_overflows'),
        ('unavailable_group_time', 'unavailable_group_times'),
}