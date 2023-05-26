from collections import defaultdict
from abc import ABC, abstractmethod

from json_schemas import Classroom
from tools import get_wd_and_dt
from task import StudyClass
from enums import ClassroomSpecialization
from global_parameters import MAX_CLASSES_PER_DAY as MCPD

class ErrorsCounter(ABC):
    def __init__(self):
        super().__init__()
        self.cur_count = 0
    
    @abstractmethod
    def count(self, week_time:int, study_class:StudyClass, classroom:Classroom):
        pass  

    # Посчитать ошибку, но не сохранять данных о ней, 
    # а вернуть то количество ошибок, которое получилось бы,
    # если бы почитали методом `count`
    @abstractmethod
    def temp_count(self, week_time:int, study_class:StudyClass, classroom:Classroom) -> int:
        pass

    def get_count(self) -> int:
        return self.cur_count
    
    def reset(self):
        self.cur_count = 0 
    

class WindowCounter(ErrorsCounter):
    def __init__(self):
        super().__init__()
        self.schedule = defaultdict(lambda: defaultdict(set))
    
    def reset(self):
        super().reset()
        del self.schedule
        self.schedule = defaultdict(lambda: defaultdict(set))
    
    def calc_count_in_day(self, day:set[int]) -> int:
        if not day:
            return 0
        return max(day) - min(day) - len(day) + 1


class GroupWindow(WindowCounter):    
    def count(self, week_time:int, study_class:StudyClass, classroom:Classroom):
        week_day, day_time = get_wd_and_dt(week_time)
        for group in study_class.groups:
            day = self.schedule[group.id][week_day]
            self.cur_count -= self.calc_count_in_day(day)
            day.add(day_time)
            self.cur_count += self.calc_count_in_day(day)
    
    def temp_count(self, week_time: int, study_class: StudyClass, classroom: Classroom) -> int:
        week_day, day_time = get_wd_and_dt(week_time)
        temp_err_count = self.cur_count
        for group in study_class.groups:
            day = self.schedule[group.id][week_day]
            if day_time not in day:
                temp_err_count -= self.calc_count_in_day(day)
                day.add(day_time)
                temp_err_count += self.calc_count_in_day(day)
                day.remove(day_time)
        return temp_err_count


class TeacherWindow(WindowCounter):     
    def count(self, week_time:int, study_class:StudyClass, classroom:Classroom):
        if not study_class.teacher.windows_allowed:
            week_day, day_time = get_wd_and_dt(week_time)
            day = self.schedule[study_class.teacher.id][week_day]
            self.cur_count -= self.calc_count_in_day(day)
            day.add(day_time)
            self.cur_count += self.calc_count_in_day(day)
    
    def temp_count(self, week_time: int, study_class: StudyClass, classroom: Classroom) -> int:
        temp_err_count = self.cur_count
        if not study_class.teacher.windows_allowed:
            week_day, day_time = get_wd_and_dt(week_time)
            day = self.schedule[study_class.teacher.id][week_day]
            temp_err_count -= self.calc_count_in_day(day)
            day.add(day_time)
            temp_err_count += self.calc_count_in_day(day)
            day.remove(day_time)
        return temp_err_count


class ParallelCounter(ErrorsCounter):
    def __init__(self):
        super().__init__()
        self.schedule = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))   
    
    def reset(self):
        super().reset()
        del self.schedule
        self.schedule = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))


class GroupParallel(ParallelCounter):
    def count(self, week_time:int, study_class:StudyClass, classroom:Classroom):
        week_day, day_time = get_wd_and_dt(week_time)
        for group in study_class.groups:
            self.schedule[group.id][week_day][day_time] += 1
            if self.schedule[group.id][week_day][day_time] > 1:
                self.cur_count += 1
    
    def temp_count(self, week_time: int, study_class: StudyClass, classroom: Classroom) -> int:
        week_day, day_time = get_wd_and_dt(week_time)
        temp_err_count = self.cur_count
        for group in study_class.groups:
            if self.schedule[group.id][week_day][day_time] > 0:
                temp_err_count += 1
        return temp_err_count


class TeacherParallel(ParallelCounter):
    def count(self, week_time:int, study_class:StudyClass, classroom:Classroom):
        week_day, day_time = get_wd_and_dt(week_time)
        self.schedule[study_class.teacher.id][week_day][day_time] += 1
        if self.schedule[study_class.teacher.id][week_day][day_time] > 1:
            self.cur_count += 1
    
    def temp_count(self, week_time: int, study_class: StudyClass, classroom: Classroom) -> int:
        week_day, day_time = get_wd_and_dt(week_time)
        return self.cur_count + int(self.schedule[study_class.teacher.id][week_day][day_time] > 0) 


class ExcessClass(ErrorsCounter):
    def __init__(self):
        super().__init__()
        self.schedule = defaultdict(lambda: defaultdict(int))
    
    def count(self, week_time:int, study_class:StudyClass, classroom:Classroom):
        week_day, _ = get_wd_and_dt(week_time)
        for group in study_class.groups:
            self.schedule[group.id][week_day] += 1
            if self.schedule[group.id][week_day] > MCPD:
                self.cur_count += 1
    
    def temp_count(self, week_time:int, study_class:StudyClass, classroom:Classroom) -> int:
        week_day, _ = get_wd_and_dt(week_time)
        temp_err_count = self.cur_count
        for group in study_class.groups:
            if self.schedule[group.id][week_day] + 1 > MCPD:
                temp_err_count += 1
        return temp_err_count

    def reset(self):
        super().reset()
        del self.schedule
        self.schedule = defaultdict(lambda: defaultdict(int))


class ClassroomOverflow(ErrorsCounter):
    def __init__(self):
        super().__init__()
        self.schedule = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    
    def count(self, week_time:int, study_class:StudyClass, classroom:Classroom):
        week_day, day_time = get_wd_and_dt(week_time)
        already_in_room = self.schedule[classroom.id][week_day][day_time]
        self.cur_count -= max(0, already_in_room - classroom.capacity)
        already_in_room += sum(group.size for group in study_class.groups)
        self.cur_count += max(0, already_in_room - classroom.capacity)
        self.schedule[classroom.id][week_day][day_time] = already_in_room
    
    def temp_count(self, week_time:int, study_class:StudyClass, classroom:Classroom) -> int:
        week_day, day_time = get_wd_and_dt(week_time)
        temp_err_count = self.cur_count
        already_in_room = self.schedule[classroom.id][week_day][day_time]
        temp_err_count -= max(0, already_in_room - classroom.capacity)
        already_in_room += sum(group.size for group in study_class.groups)
        return temp_err_count + max(0, already_in_room - classroom.capacity)

    def reset(self):
        super().reset()
        del self.schedule
        self.schedule = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))


class StandardClassroomOverflow(ClassroomOverflow):
    def count(self, week_time:int, study_class:StudyClass, classroom:Classroom):
        if classroom.specialization is ClassroomSpecialization.DEFAULT:
            super().count(week_time, study_class, classroom)
    
    def temp_count(self, week_time:int, study_class:StudyClass, classroom:Classroom) -> int:
        if classroom.specialization is ClassroomSpecialization.DEFAULT:
            return super().temp_count(week_time, study_class, classroom)
        return self.cur_count
    

class SpecialClassroomOverflow(ClassroomOverflow):
    def count(self, week_time:int, study_class:StudyClass, classroom:Classroom):
        if classroom.specialization is not ClassroomSpecialization.DEFAULT:
            super().count(week_time, study_class, classroom)
    
    def temp_count(self, week_time:int, study_class:StudyClass, classroom:Classroom) -> int:
        if classroom.specialization is not ClassroomSpecialization.DEFAULT:
            return super().temp_count(week_time, study_class, classroom)
        return self.cur_count


class UnavailableGroupTime(ErrorsCounter):
    def count(self, week_time:int, study_class:StudyClass, classroom:Classroom):
        for group in study_class.groups:
            if week_time not in group.available_times:
                self.cur_count += 1
    
    def temp_count(self, week_time: int, study_class: StudyClass, classroom: Classroom) -> int:
        temp_err_count = self.cur_count
        for group in study_class.groups:
            if week_time not in group.available_times:
                temp_err_count += 1
        return temp_err_count


class TeacherPrefClassroom(ErrorsCounter):
    def count(self, week_time:int, study_class:StudyClass, classroom:Classroom):
        if study_class.teacher.preferences.classrooms and \
                classroom.id not in study_class.teacher.preferences.classrooms:
            self.cur_count += 1
    
    def temp_count(self, week_time: int, study_class: StudyClass, classroom: Classroom) -> int:
        if study_class.teacher.preferences.classrooms and \
                classroom.id not in study_class.teacher.preferences.classrooms:
            return self.cur_count + 1
        return self.cur_count


class TeacherPrefTime(ErrorsCounter):
    def count(self, week_time:int, study_class:StudyClass, classroom:Classroom):
        if study_class.teacher.preferences.times and \
                week_time not in study_class.teacher.preferences.times:
            self.cur_count += 1

    def temp_count(self, week_time: int, study_class: StudyClass, classroom: Classroom) -> int:
        if study_class.teacher.preferences.times and \
                week_time not in study_class.teacher.preferences.times:
            return self.cur_count + 1
        return self.cur_count


class TeacherPrefClassroomFeature(ErrorsCounter):
    def count(self, week_time:int, study_class:StudyClass, classroom:Classroom):
        self.cur_count += len(
            study_class.teacher.preferences.classroom_features - classroom.features
        )
    
    def temp_count(self, week_time: int, study_class: StudyClass, classroom: Classroom) -> int:
        return self.cur_count + len(
            study_class.teacher.preferences.classroom_features - classroom.features
        )


class SCPrefClassroom(ErrorsCounter):
    def count(self, week_time:int, study_class:StudyClass, classroom:Classroom):
        if study_class.preferences.classrooms and \
                classroom.id not in study_class.preferences.classrooms:
            self.cur_count += 1
    
    def temp_count(self, week_time: int, study_class: StudyClass, classroom: Classroom) -> int:
        if study_class.preferences.classrooms and \
                classroom.id not in study_class.preferences.classrooms:
            return self.cur_count + 1
        return self.cur_count


class SCPrefTime(ErrorsCounter):
    def count(self, week_time:int, study_class:StudyClass, classroom:Classroom):
        if study_class.preferences.times and \
                week_time not in study_class.preferences.times:
            self.cur_count += 1

    def temp_count(self, week_time: int, study_class: StudyClass, classroom: Classroom) -> int:
        if study_class.preferences.times and \
                week_time not in study_class.preferences.times:
            return self.cur_count + 1
        return self.cur_count


class SCPrefClassroomFeature(ErrorsCounter):
    def count(self, week_time:int, study_class:StudyClass, classroom:Classroom):
        self.cur_count += len(
            study_class.preferences.classroom_features - classroom.features
        )
    
    def temp_count(self, week_time: int, study_class: StudyClass, classroom: Classroom) -> int:
        return self.cur_count + len(
            study_class.preferences.classroom_features - classroom.features
        )
