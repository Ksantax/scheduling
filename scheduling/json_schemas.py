'''
    Модуль для декларирования схем данных с клиентской частью
'''

from pydantic import BaseModel, Field, root_validator

from exceptions import TooMuchStudyClasses, NotEnoughSpecializations, ClassroomSpecializationError
from data_classes import StudentGroup, StudyClass, Course, Teacher, Classroom
from global_parameters import DAYS_PER_WEEK, CLASSES_PER_DAY


class FitnessWeights(BaseModel):
    '''
        Веса для штрафов за ошибки в составленном расписании
            group_window - за окно между занятиями у групп
            teacher_window - за окно между занятиями у преподавателей
            group_parallel_class - за параллельную пару у группы
            teacher_parallel_class - за параллельную пару у преподавателя
            excess_class - за лишние пары (свыше четырёх, например)
            standart_classroom_overflow - за переполнение обычной аудитории (на каждого студента)
            special_classroom_overflow - за переполнения ыпециальной аудитории (на каждого студента)
            unavailable_group_time - за недопустимое для группы время
    '''
    group_window:float = Field(ge=0.0, alias='groupWindow')
    teacher_window:float = Field(ge=0.0, alias='teacherWindow')
    group_parallel_class:float = Field(ge=0.0, alias="groupParallelClass")
    teacher_parallel_class:float = Field(ge=0.0, alias="teacherParallelClass")
    excess_class:float = Field(ge=0.0, alias="excessClass")
    standart_classroom_overflow:float = Field(ge=0.0, alias="standartClassroomOverflow")
    special_classroom_overflow:float = Field(ge=0.0, alias="specialClassroomOverflow")
    unavailable_group_time:float = Field(ge=0.0, alias='unavailableGroupTime')


class AlgorithmParams(BaseModel):
    '''
        Параметры алгоритма поиска (генетического)
            population_size - количество особей
            hof_size - размер зала славы (хранилища лучших за всё время)
            p_mutation - вероятность мутации
            p_crossover - вероятность скрещивания
            tourn_size - количество особей для турнирного отбора
            distance_trashold - растояние между расписаниями 
                    (сумма пар в одно время в одной аудитории), 
                    после которого они не считаются похожими
            sharing_extent - степень наказание за схожесть расписаний
                    (заставляет алгоритм искать непохожие расписания) 
    '''
    population_size:int = Field(gt=0, alias='populationSize')
    hof_size:int = Field(ge=0, alias='hallOfFameSize')
    p_mutation:float = Field(ge=0.0, le=1.0, alias='pMutation')
    p_crossover:float = Field(ge=0.0, le=1.0, alias='pCrossover')
    tourn_size:int = Field(gt=1, alias='tournSize')
    distance_trashold:int = Field(ge=1, alias='distanceTrashold')
    sharing_extent:float = Field(ge=1.0, alias='sharingExtent')


class TaskData(BaseModel):
    '''
        Данные для конкретной задачи
            study_classes - занятия (связки групп и преподавателей)
            teachers - преподаватели
            student_groups - студенческие группы
            classrooms - аудитории
    '''
    study_classes:list[StudyClass] = Field(alias='studyClasses')
    courses:list[Course]
    teachers:list[Teacher]
    student_groups:list[StudentGroup] = Field(alias='studentGroups')
    classrooms:list[Classroom]
    

    # @root_validator
    # def velidate_object(cls, values):
    #     study_classes = values['study_classes']
    #     classrooms = values['classrooms']
    #     classrooms_dict = {c['id']: c for c in classrooms}
    #     classes_specs = set(sc['classroom_specialization'] for sc in study_classes)
    #     classrooms_specs = set(c['specialization'] for c in classrooms)
    #     available_times = sum(len(c['available_times'] for c in classrooms))
    #     if len(classes_specs - classrooms_specs):
    #         raise NotEnoughSpecializations(f'There is no any classroom with required specialization')
    #     # TODO: calc per specialization
    #     # if len(study_classes) > available_times:
    #     #     raise TooMuchStudyClasses(f'Number of classes is {len(study_classes)},'+
    #     #             f'but number of available class times is {available_times}')
    #     for cl in study_classes:
    #         if cl['classroom_specialization'] != classrooms_dict[cl['fixed_classroom_id']]['specialization']:
    #             raise ClassroomSpecializationError('The specialization of' + 
    #                     'fixed classroom and the specialization of class don\'t match')
    #     return values


class TaskConfig(BaseModel):
    '''
        Всё, что может понадобиться для работы алгоритма, в одном месте
    '''
    data:TaskData
    weights:FitnessWeights
    params:AlgorithmParams


class Pair(BaseModel):
    '''
        Пара (занятие) для возврата на клиент
            weekday - День недели (начиная с нуля)
            time - Номер пары по счёту (начиная с нуля)
            teacher - Имя преподавателя
            course - Название предмета
            groups - Названия групп, у которых проводится пара
    '''
    weekday:int = Field(ge=0, lt=DAYS_PER_WEEK)
    time:int = Field(ge=0, le=CLASSES_PER_DAY)
    teacher:str
    course:str
    groups:list[str]


class ClassroomsPairs(BaseModel):
    '''
        Пары проводимые в аудитории
            classroom - Название аудитории
            pairs - Пары, проводимсые в аудитории
    '''
    classroom:str
    pairs:list[Pair]
