import numpy as np

from individual import Individual
from task import SchedulingTask, StudyClass
from enums import ClassroomSpecialization
from json_schemas import FitnessWeights, Classroom
from error_counters import (
        ErrorsCounter, 
        GroupWindow, 
        TeacherWindow,
        GroupParallel, 
        TeacherParallel, 
        ExcessClass, 
        StandardClassroomOverflow, 
        SpecialClassroomOverflow, 
        UnavailableGroupTime,
        TeacherPrefClassroom,
        TeacherPrefTime,
        TeacherPrefClassroomFeature,
        SCPrefClassroom,
        SCPrefTime,
        SCPrefClassroomFeature
)


# Weights To Error Counters
WTEC = {
        'g_window': GroupWindow,
        't_window': TeacherWindow,
        'g_parallel_class': GroupParallel,
        't_parallel_class': TeacherParallel,
        'g_excess_class': ExcessClass,
        'c_standard_overflow': StandardClassroomOverflow,
        'c_special_overflow': SpecialClassroomOverflow,
        'g_unavailable_time': UnavailableGroupTime,
        't_pref_classroom': TeacherPrefClassroom,
        't_pref_time': TeacherPrefTime,
        't_pref_classroom_feature': TeacherPrefClassroomFeature,
        'sc_pref_classroom': SCPrefClassroom,
        'sc_pref_time': SCPrefTime,
        'sc_pref_classroom_feature': SCPrefClassroomFeature,
}


class Evaluator:
    weights:np.ndarray
    error_counters:list[ErrorsCounter]
    task:SchedulingTask

    def __init__(self, weights:FitnessWeights, scheduling_task:SchedulingTask):
        self.weights = np.array(list(map(weights.__getattribute__, WTEC.keys())))
        self.error_counters = [e() for e in WTEC.values()]
        self.task = scheduling_task
        self.reset_counters()

    def evaluate(self, ind:Individual) -> float:
        self.reset_counters()
        self.count_individual(ind)
        result = self.weight_errors([ec.get_count() for ec in self.error_counters])
        self.reset_counters()
        return result
    
    def count_individual(self, ind:Individual):
        for spec in ind:
            n = len(self.task.classes[spec])
            for pos, class_num in filter(lambda x: x[1] < n, enumerate(ind[spec])):
                classroom, week_time = self.task.get_cl_wt(spec, pos)
                self.count_class(self.task.classes[spec][class_num], classroom, week_time)

    def count_class(self, study_class:StudyClass, classroom:Classroom, week_time:int):
        for error_counter in self.error_counters:
            error_counter.count(week_time, study_class, classroom)
    
    def count_class_without_saving(self, study_class:StudyClass, 
            classroom:Classroom, week_time:int) -> float:
        return self.weight_errors([
            ec.temp_count(week_time, study_class, classroom) 
            for ec in self.error_counters])
    
    def weight_errors(self, errors:list[int]) -> float:
        return float(np.dot(self.weights, np.array(errors)))
    
    def reset_counters(self):
        for error_counter in self.error_counters:
            error_counter.reset()
        for classroom_id, times in self.task.fixed.items():
            for time, classes in times.items():
                for study_class in classes:
                    self.count_class(
                            study_class, 
                            self.task.classrooms[classroom_id], 
                            time)
        
    def get_errors(self) -> dict[str, int]:
        return {err_name: ec.get_count() for err_name, ec in 
                zip(WTEC.keys, self.error_counters)}

    def print_errors(self, ind:Individual):
        self.reset_counters()
        self.count_individual(ind)
        print(*[f'{name} = {ec.get_count()}'
                for name, ec in zip(WTEC.keys(), self.error_counters)], sep='\n')
        self.reset_counters()