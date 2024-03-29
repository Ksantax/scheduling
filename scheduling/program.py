# Модуль дле тестовых запусков. Возможно, потом это
# всё превратится в API или останется на какое-то время просто
# модулем для запуска как программы

import json

from pydantic import parse_obj_as

from algorithm import GeneticAlgorithm
from json_schemas import *
from global_parameters import NUMBER_OF_ITERATIONS, SAVE_FILE_NAME, TEMP_DIR, RESULT_DIR


RESULT_FILE_NAME = 'result_' + SAVE_FILE_NAME + '.json'
POP_FILE_NAME = 'population_' + SAVE_FILE_NAME +'.pkl'


def load_config():
    config = dict()
    data = dict()
    data['teachers'] = json.loads((TEMP_DIR / 'teachers.json').read_text(encoding='utf-8'))
    data['classrooms'] = json.loads((TEMP_DIR / 'classrooms.json').read_text(encoding='utf-8'))
    data['studentGroups'] = json.loads((TEMP_DIR / 'groups.json').read_text(encoding='utf-8'))
    data['studyClasses'] = json.loads((TEMP_DIR / 'classes.json').read_text())
    data['courses'] = json.loads((TEMP_DIR / 'courses.json').read_text(encoding='utf-8'))
    config['params'] = json.loads((TEMP_DIR / 'params.json').read_text())
    config['weights'] = json.loads((TEMP_DIR / 'weights.json').read_text())
    config['data'] = data
    return parse_obj_as(TaskConfig, config)

config = load_config()
alg = GeneticAlgorithm(config)
alg.init_population()
try:
    alg.start_algorithm(NUMBER_OF_ITERATIONS,
            verbose_interval=100,
            save_file_name=POP_FILE_NAME)
except KeyboardInterrupt:
    pass
finally:
    best = alg.hof[0]
    alg.evaluator.print_errors(best)
    result = [i.dict() for i in alg.task.individual_to_schedule(best)]
    with open(RESULT_DIR / RESULT_FILE_NAME, 'w+', encoding='utf-8') as file:
        json.dump(result, file, ensure_ascii=False, indent=4)
    print('saved to ' + RESULT_FILE_NAME)
