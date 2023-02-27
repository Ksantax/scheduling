from pydantic import BaseModel, Field, root_validator

from enums import ClassroomFeature, ClassroomSpecialization, Degree
from exceptions import FixedClassroomTimeError


class Preferences(BaseModel):
    '''
        Предпочтения к проведению занятий
            classrooms - Предпочитаемые аудитории
            times - Продпочитаемые моменты времени проведения пар
            dest_type - Предпочитаемый тип доски
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


class StudyClass(BaseModel):
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
    # def velidate_object(cls, values):
    #     if bool(values['fixed_time'] is None) != bool(values['fixed_time'] is None):
    #         raise FixedClassroomTimeError('Both values "fixed_time" and "fixed_classroom_id" must be set or not')

