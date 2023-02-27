from typing import Iterable, Callable
from collections import defaultdict
import random

from pydantic import parse_obj_as

from enums import ClassroomSpecialization
from json_schemas import TaskData, ClassroomsPairs
from data_classes import StudyClass, Teacher, StudentGroup, Classroom, Course
from global_parameters import DAYS_PER_WEEK as DPW, CLASSES_PER_DAY as CPD, MAX_CLASSES_PER_DAY as MCPD

# id -> week - list of days -> day_time -> list of classes
class ShortSchedule(dict[int, list[defaultdict[int, list[StudyClass]]]]):
    def __init__(self, ids:list[int]):
        for i in ids:
            self[i] = [defaultdict(list) for _ in range(DPW)]

    def add_class(self, week_time:int, ids:list[int], study_class:StudyClass):
        week_day = week_time // CPD
        day_time = week_time % CPD
        for i in ids:
            self[i][week_day][day_time].append(study_class)
    
    def del_class(self, week_time, ids:list[int], study_class:StudyClass):
        week_day = week_time // CPD
        day_time = week_time % CPD
        for i in ids:
            self[i][week_day][day_time].remove(study_class)

    
    @staticmethod
    def count_windows(day_times:dict[int, list[StudyClass]]) -> int:
        day_set = set(day_times.keys())
        return max(day_set) - min(day_set) - len(day_set) + 1

    @staticmethod
    def count_parallels(day:dict[int, list[StudyClass]]) -> int:
        return sum([max(len(c)-1, 0) for c in day.values()])


class SchedulingErrors:
    '''
        Содержит ошибки в составлении расписания.
    '''
    group_windows:int
    teacher_windows:int
    group_parallels:int
    teacher_parallels:int
    excesses:int
    standart_overflows:int
    special_overflows:int
    unavailable_group_times:int

    def __init__(self):
        self.empty()
    
    def empty(self):
        self.group_windows = 0
        self.group_parallels = 0
        self.excesses = 0
        self.unavailable_group_times = 0
        self.teacher_windows = 0
        self.teacher_parallels = 0
        self.standart_overflows = 0
        self.special_overflows = 0

    def __str__(self) -> str:
        return (f'group windows = {self.group_windows}\n' +
                f'group parallels = {self.group_parallels}\n' +
                f'excess classes = {self.excesses}\n' +
                f'teacher windows = {self.teacher_windows}\n' +
                f'teacher parallels = {self.teacher_parallels}\n' +
                f'standart classroom overflows = {self.standart_overflows}\n' +
                f'special classroom overflows = {self.special_overflows}\n' + 
                f'unavailable group times = {self.unavailable_group_times}')

    def copy(self):
        temp = SchedulingErrors()
        temp.group_windows = self.group_windows
        temp.group_parallels = self.group_parallels
        temp.excesses = self.excesses
        temp.unavailable_group_times = self.unavailable_group_times
        temp.teacher_windows = self.teacher_windows
        temp.teacher_parallels = self.teacher_parallels
        temp.standart_overflows = self.standart_overflows
        temp.special_overflows = self.special_overflows
        return temp
    
    def get_tuple(self):
        return (self.group_parallels, self.teacher_parallels, self.excesses,
                self.group_windows, self.unavailable_group_times, self.teacher_windows,
                self.special_overflows, self.standart_overflows)

    def __lt__(self, other):
        return self.get_tuple() < other.get_tuple()

    def __eq__(self, other):
        return self.get_tuple() == other.get_tuple()


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
    errors:SchedulingErrors

    # room_id -> (time -> [classes])
    __fixed:dict[int, dict[int, list[StudyClass]]]
    __cl_ids:dict[ClassroomSpecialization, list[int]]
    __cl_times:dict[ClassroomSpecialization, list[int]]

    def __init__(self, data:TaskData):
        self.classrooms = {cl.id: cl for cl in data.classrooms}
        self.teachers = {t.id: t for t in data.teachers}
        self.groups = {g.id: g for g in data.student_groups}
        self.courses = {c.id: c for c in data.courses}
        self.errors = SchedulingErrors()

        self.classes = defaultdict(list)
        self.__fixed = defaultdict(lambda: defaultdict(list))
        for sc in data.study_classes:
            if sc.fixed_classroom_id is not None:
                self.__fixed[sc.fixed_classroom_id][sc.fixed_time].append(sc)
            else:
                self.classes[sc.classroom_specialization].append(sc)
        
        self.__cl_ids = defaultdict(list)
        self.__cl_times = defaultdict(list)
        for cl in data.classrooms:
            times = cl.available_times*cl.parallels
            for fixed_time, classes in self.__fixed[cl.id].items():
                for _ in range(len(classes)):
                    if fixed_time not in times:
                        break
                    times.remove(fixed_time)
            self.__cl_ids[cl.specialization] += [cl.id] * len(times)
            self.__cl_times[cl.specialization] += times


    def evaluate(self, individ:dict[ClassroomSpecialization, list[int]]) -> SchedulingErrors:
        self.errors.empty()
        groups_schedule, teachers_schedule, classrooms_schedule = self.__get_schedules()

        for spec in individ:
            for i in range(len(individ[spec])):
                class_num = individ[spec][i]
                if class_num >= len(self.classes[spec]):
                    continue
                study_class = self.classes[spec][class_num]
                classroom_id = self.__cl_ids[spec][i]
                time = self.__cl_times[spec][i]

                groups_schedule.add_class(time, study_class.groups_ids, study_class)
                teachers_schedule.add_class(time, [study_class.teacher_id], study_class)
                classrooms_schedule.add_class(time, [classroom_id], study_class)
            

        self.update_group_errors(groups_schedule)
        self.update_teacher_errors(teachers_schedule)
        self.update_classroom_errors(classrooms_schedule)

        return self.errors
    
    def __get_schedules(self):
        groups_schedule = ShortSchedule(self.groups.keys())
        teachers_schedule = ShortSchedule(self.teachers.keys())
        classrooms_schedule = ShortSchedule(self.classrooms.keys())
        for classroom_id, times in self.__fixed.items():
            for time, classes in times.items():
                for study_class in classes:
                    groups_schedule.add_class(time, study_class.groups_ids, study_class)
                    teachers_schedule.add_class(time, [study_class.teacher_id], study_class)
                    classrooms_schedule.add_class(time, [classroom_id], study_class)
        return groups_schedule, teachers_schedule, classrooms_schedule
    
    def update_group_errors(self, groups_schedule:ShortSchedule) -> None:
        self.__process_targets(groups_schedule, self.__process_group_day)

    def update_teacher_errors(self, teachers_schedule:ShortSchedule) -> None:
        self.__process_targets(teachers_schedule, self.__process_teacher_day)
    
    def update_classroom_errors(self, classroom_schedule:ShortSchedule) -> None:
        self.__process_targets(classroom_schedule, self.__process_classroom_day)
    
    def __process_targets(self, schedule:ShortSchedule, 
            processor:Callable[[int, int, dict[int, list[StudyClass]]], None]) -> None:
        for target_id, week in schedule.items():
            for day_num, day in filter(lambda x: len(x[1]), enumerate(week)):
                processor(target_id, day_num, day)
        
    def __process_group_day(self, group_id:int, 
            day_num:int, day:dict[int, list[StudyClass]]) -> None:
        group = self.groups[group_id]
        day_times = set(day.keys())
        self.errors.group_parallels += ShortSchedule.count_parallels(day)
        self.errors.group_windows += ShortSchedule.count_windows(day)
        self.errors.excesses += max(len(day_times) - MCPD, 0)
        for day_time, classes in day.items():
            time = day_num*CPD + day_time
            self.errors.unavailable_group_times += time not in group.available_times
    
    def __process_teacher_day(self, teacher_id:int,
            day_num:int, day:dict[int, list[StudyClass]]) -> None:
        teacher = self.teachers[teacher_id]
        self.errors.teacher_parallels += ShortSchedule.count_parallels(day)
        if not teacher.windows_allowed:
            self.errors.teacher_windows += ShortSchedule.count_windows(day.keys())

    def __process_classroom_day(self, classroom_id:int,
            day_num:int, day:dict[int, list[StudyClass]]) -> None:
        classroom = self.classrooms[classroom_id]
        for classes in day.values():
            amount_of_students = sum([self.groups[i].size for sc in classes for i in sc.groups_ids])
            overflow = max(amount_of_students - classroom.capacity, 0)
            if classroom.specialization is ClassroomSpecialization.DEFAULT:
                self.errors.standart_overflows += overflow
            else:
                self.errors.special_overflows += overflow
    
    def create_individual(self, by_algorithm=False) -> dict[ClassroomSpecialization, list]:
        if not by_algorithm:
            return {spec: random.sample(range(len(self.__cl_ids[spec])), len(self.__cl_ids[spec]))
                    for spec in self.__cl_ids}
        ind = {spec:[1_000_000]*len(self.__cl_ids[spec]) for spec in self.__cl_ids}
        for spec in self.classes:
            n = len(self.classes[spec])
            for class_num in random.sample(range(n), n):
                best_places = list()
                for i in range(len(ind[spec])):
                    if ind[spec][i] != 1_000_000:
                        continue
                    ind[spec][i] = class_num
                    errors = self.evaluate(ind).copy()
                    ind[spec][i] = 1_000_000
                    if not best_places or errors == best_places[0][1]:
                        best_places.append((i, errors))
                    elif self.errors < best_places[0][1]:
                        best_places = [(i, errors)]
                if best_places:
                    idx = random.randint(0, len(best_places) - 1)
                    ind[spec][best_places[idx][0]] = class_num
        return self.__fill_ind(ind)
    
    def __fill_ind(self, ind):
        for spec in self.classes:
            spec_set = set(ind[spec])
            idx = 0
            for ptr in range(len(ind[spec])):
                if ind[spec][ptr] != 1_000_000:
                    continue
                while idx in spec_set:
                    spec_set.add(idx)
                    idx += 1
                ind[spec][ptr] = idx
                spec_set.add(idx)
        return ind

    def individ_to_schedule(self, individ:dict[ClassroomSpecialization, list[int]]) -> list[ClassroomsPairs]:
        
        rooms = defaultdict(list)
        for classroom_id, times in self.__fixed.items():
            for time, classes in times.items():
                for study_class in classes:
                    rooms[self.classrooms[classroom_id].name].append({
                            'weekday':  time // CPD,
                            'time': time % CPD,
                            'teacher': self.teachers[study_class.teacher_id].name, 
                            'course':  self.courses[study_class.course_id].name, 
                            'groups': [self.groups[g_id].name for g_id in study_class.groups_ids]
                    })
                    
        for spec in individ:
            for num, class_index in enumerate(individ[spec]):
                if class_index >= len(self.classes[spec]):
                    continue
                study_class = self.classes[spec][class_index]
                cl_id = self.__cl_ids[spec][num]
                classroom = self.classrooms[cl_id].name
                week_time = self.__cl_times[spec][num]

                rooms[classroom].append({
                        'weekday':  week_time // CPD,
                        'time': week_time % CPD,
                        'teacher': self.teachers[study_class.teacher_id].name, 
                        'course':  self.courses[study_class.course_id].name, 
                        'groups': [self.groups[g_id].name for g_id in study_class.groups_ids]
                })
        return [parse_obj_as(ClassroomsPairs, {'classroom': r, 'pairs': c})
                for r, c in rooms.items()]
    
