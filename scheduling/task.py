from collections import defaultdict

from pydantic import parse_obj_as

from enums import ClassroomSpecialization
from json_schemas import TaskData, ClassroomsPairs
from json_schemas import StudyClassJSON, Teacher, StudentGroup, Classroom, Course, Preferences
from individual import Individual
from global_parameters import CLASSES_PER_DAY as CPD


class StudyClass:
    course:Course
    teacher:Teacher
    groups:list[StudentGroup]
    cl_spec:ClassroomSpecialization
    preferences:Preferences
    fixed_time:int|None
    fixed_classroom:Classroom|None

    def __init__(self, 
            course:Course,
            teacher:Teacher,
            groups:list[StudentGroup],
            cl_spec:ClassroomSpecialization,
            preferences:Preferences,
            fixed_time:int|None,
            fixed_classroom:Classroom|None) -> None:
        self.course = course
        self.teacher = teacher
        self.groups = groups
        self.cl_spec = cl_spec
        self.preferences = preferences
        self.fixed_time = fixed_time
        self.fixed_classroom = fixed_classroom


class SchedulingTask:
    '''
        Содержит информацию о конкретной задаче составления расписания.
        Основываясь на этой информации вычисляет ошибки, 
        содержащиеся в особях генетического алгоритма.
    '''
    classes:dict[ClassroomSpecialization, list[StudyClass]]
    classrooms:dict[int, Classroom]
    teachers:dict[int, Teacher]
    groups:dict[int, StudentGroup]
    courses:dict[int, Course]
    spec_to_n:dict[ClassroomSpecialization, int]
    cl_by_pos:dict[ClassroomSpecialization, list[Classroom]]
    cl_times:dict[ClassroomSpecialization, list[int]]

    fixed:dict[int, dict[int, list[StudyClass]]]

    def __init__(self, data:TaskData):
        self.classrooms = {cl.id: cl for cl in data.classrooms}
        self.teachers = {t.id: t for t in data.teachers}
        self.groups = {g.id: g for g in data.student_groups}
        self.courses = {c.id: c for c in data.courses}

        self.classes = defaultdict(list)
        self.fixed = defaultdict(lambda: defaultdict(list))
        for sc in map(self.__create_sc,  data.study_classes):
            if sc.fixed_time is not None:
                self.fixed[sc.fixed_classroom.id][sc.fixed_time].append(sc)
            else:
                self.classes[sc.cl_spec].append(sc)
        
        self.cl_by_pos = defaultdict(list)
        self.cl_times = defaultdict(list)
        for cl in data.classrooms:
            times = cl.available_times*cl.parallels
            self.__remove_fixed_times(times, cl.id)
            self.cl_by_pos[cl.specialization] += [cl] * len(times)
            self.cl_times[cl.specialization] += times
        
        self.spec_to_n = {spec: len(self.cl_by_pos[spec]) for spec in self.cl_by_pos}
    
    def __remove_fixed_times(self, times:list[int], cl_id):
        for fixed_time, classes in self.fixed[cl_id].items():
            for _ in range(len(classes)):
                if fixed_time not in times:
                    break
                times.remove(fixed_time)
    
    def __create_sc(self, sc_json:StudyClassJSON) -> StudyClass:
        return StudyClass(
                self.courses[sc_json.course_id],
                self.teachers[sc_json.teacher_id],
                [self.groups[group_id] for group_id in sc_json.groups_ids],
                sc_json.classroom_specialization,
                sc_json.preferences,
                sc_json.fixed_time,
                self.classrooms[sc_json.fixed_classroom_id] if sc_json.fixed_classroom_id else None
        )
    
    def get_cl_wt(self, spec:ClassroomSpecialization, pos:int) -> tuple[Classroom, int]:
        return self.cl_by_pos[spec][pos], self.cl_times[spec][pos]

    def individual_to_schedule(self, individual:Individual) -> list[ClassroomsPairs]:
        rooms = defaultdict(list)
        for classroom_id, times in self.fixed.items():
            for time, classes in times.items():
                for study_class in classes:
                    rooms[self.classrooms[classroom_id].name].append({
                            'weekday':  time // CPD,
                            'time': time % CPD,
                            'teacher': study_class.teacher.name, 
                            'course':  study_class.course.name, 
                            'groups': [group.name for group in study_class.groups]
                    })     
        for spec in individual:
            n = len(self.classes[spec])
            for pos, class_index in filter(lambda x: x[1] < n, enumerate(individual[spec])):
                study_class = self.classes[spec][class_index]
                classroom, week_time = self.get_cl_wt(spec, pos)

                rooms[classroom.name].append({
                        'weekday':  week_time // CPD,
                        'time': week_time % CPD,
                        'teacher': study_class.teacher.name, 
                        'course':  study_class.course.name, 
                        'groups': [group.name for group in study_class.groups]
                })
        return [parse_obj_as(ClassroomsPairs, {'classroom': r, 'pairs': c})
                for r, c in rooms.items()]
