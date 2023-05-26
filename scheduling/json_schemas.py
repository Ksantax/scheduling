'''
    Модуль для декларирования схем данных с клиентской частью
'''

from pydantic import BaseModel, Field, root_validator

from exceptions import TooMuchStudyClasses, NotEnoughSpecializations, ClassroomSpecializationError
from global_parameters import DAYS_PER_WEEK, CLASSES_PER_DAY
from enums import ClassroomFeature, ClassroomSpecialization, Degree


class Preferences(BaseModel):
    '''
        Предпочтения к проведению занятий
            classrooms - Предпочитаемые аудитории
            times - Предпочитаемые моменты времени проведения пар
            classroom_features - Предпочтительные особенности аудитории
    '''
    classrooms:set[int]
    times:set[int]
    classroom_features:set[ClassroomFeature] = Field(alias='classroomFeatures')


class Classroom(BaseModel):
    '''
        Аудитория
            id        - id
            name      - Номер/название аудитории/места проведения (например: "312", "123а", "Спортзал")
            capacity  - Вместимость
            parallels - Количество допустимых пар параллельно
            features  - Набор особенностей аудитории
            desk_type - Типы досок, доступных в аудитории
            available_times - Моменты времени, когда доступна аудитория
    '''
    id:int
    name:str
    capacity:int = Field(gt=0)
    parallels:int = Field(gt=0)
    specialization:ClassroomSpecialization
    features:set[ClassroomFeature]
    available_times:list[int] = Field(alias='availableTimes')
    


class StudentGroup(BaseModel):
    '''
        Группа
            id - id
            name - название группы
            size - количество студентов в группе
            degree - степень обучения
    '''
    id:int
    name:str
    size:int = Field(gt=0)
    degree:Degree
    available_times:set[int] = Field(alias='availableTimes')


class Course(BaseModel):
    '''
        Дисциплина
            id - id
            name - Название
    '''
    id:int
    name:str


class Teacher(BaseModel):
    '''
        Преподаватель
            id - id
            name - Имя (например: "Перязев Н. А.", "Попова Виктория Алексеевна")
            preferences - Пожелания преподавателя
    '''
    id:int
    name:str
    preferences:Preferences
    windows_allowed:bool = Field(alias='windowsAllowed')


class StudyClassJSON(BaseModel):
    '''
      Занятие - связанные друг с другом преподаватель и группы
        course_id - id дисциплины
        teacher_id - id преподаватель
        groups_ids - id групп
        classroom_specialization - Специализация аудитории
        preferences - Предпочтения в обстановке проводимого занятия
        fixed_time - Фиксированное время
        fixed_classroom_id - id фиксированной аудитории аудитории
    '''
    course_id:int = Field(alias='courseId')
    teacher_id:int = Field(alias='teacherId')
    groups_ids:set[int] = Field(alias='groupsIds')
    classroom_specialization:ClassroomSpecialization = Field(alias='classroomSpecialization')
    preferences:Preferences
    fixed_time:int|None = Field(alias='fixedTime')
    fixed_classroom_id:int|None = Field(alias='fixedClassroomId')

    # @root_validator
    # def validate_object(cls, values):
    #     if bool(values['fixed_time'] is None) != bool(values['fixed_time'] is None):
    #         raise FixedClassroomTimeError('Both values "fixed_time" and "fixed_classroom_id" must be set or not')


class FitnessWeights(BaseModel):
    '''
        Веса для штрафов за ошибки в составленном расписании
            group_window - за окно между занятиями у групп
            teacher_window - за окно между занятиями у преподавателей
            group_parallel_class - за параллельную пару у группы
            teacher_parallel_class - за параллельную пару у преподавателя
            excess_class - за лишние пары (свыше четырёх, например)
            standard_classroom_overflow - за переполнение обычной аудитории (на каждого студента)
            special_classroom_overflow - за переполнения специальной аудитории (на каждого студента)
            unavailable_group_time - за недопустимое для группы время
    '''
    g_window:float = Field(ge=0.0, alias='gWindow')
    t_window:float = Field(ge=0.0, alias='tWindow')
    g_parallel_class:float = Field(ge=0.0, alias='gParallelClass')
    t_parallel_class:float = Field(ge=0.0, alias='tParallelClass')
    g_excess_class:float = Field(ge=0.0, alias='gExcessClass')
    c_standard_overflow:float = Field(ge=0.0, alias='cStandardOverflow')
    c_special_overflow:float = Field(ge=0.0, alias='cSpecialOverflow')
    g_unavailable_time:float = Field(ge=0.0, alias='gUnavailableTime')
    t_pref_classroom:float = Field(ge=0.0, alias='tPrefClassroom')
    t_pref_time:float = Field(ge=0.0, alias='tPrefTime')
    t_pref_classroom_feature:float = Field(ge=0.0, alias='tPrefClassroomFeature')
    sc_pref_classroom:float = Field(ge=0.0, alias='scPrefClassroom')
    sc_pref_time:float = Field(ge=0.0, alias='scPrefTime')
    sc_pref_classroom_feature:float = Field(ge=0.0, alias='scPrefClassroomFeature')


class AlgorithmParams(BaseModel):
    '''
        Параметры алгоритма поиска (генетического)
            population_size - количество особей
            hof_size - размер зала славы (хранилища лучших за всё время)
            p_mutation - вероятность мутации
            p_crossover - вероятность скрещивания
            tourn_size - количество особей для турнирного отбора
            distance_threshold - растояние между расписаниями 
                    (сумма пар в одно время в одной аудитории), 
                    после которого они не считаются похожими
            sharing_extent - степень наказание за схожесть расписаний
                    (заставляет алгоритм искать непохожие расписания) 
    '''
    population_size:int = Field(gt=0, alias='populationSize')
    proportion_by_algorithm:float = Field(ge=0, le=1, alias='pMadeByAlgorithm')
    hof_size:int = Field(ge=0, alias='hallOfFameSize')
    p_mutation:float = Field(ge=0.0, le=1.0, alias='pMutation')
    p_crossover:float = Field(ge=0.0, le=1.0, alias='pCrossover')
    tour_size:int = Field(gt=1, alias='tourSize')


class TaskData(BaseModel):
    '''
        Данные для конкретной задачи
            study_classes - занятия (связки групп и преподавателей)
            teachers - преподаватели
            student_groups - студенческие группы
            classrooms - аудитории
    '''
    study_classes:list[StudyClassJSON] = Field(alias='studyClasses')
    courses:list[Course]
    teachers:list[Teacher]
    student_groups:list[StudentGroup] = Field(alias='studentGroups')
    classrooms:list[Classroom]
    

    # @root_validator
    # def validate_object(cls, values):
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
