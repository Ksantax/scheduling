import numpy as np

from enums import ClassroomSpecialization
from task import SchedulingTask, StudyClass
from evaluation import Evaluator
from individual import Individual
from json_schemas import FitnessWeights


class IndividualCreator:
    task:SchedulingTask
    weights:FitnessWeights

    def __init__(self, weights:FitnessWeights, task:SchedulingTask):
        self.weights = weights
        self.task = task

    def create_randomly(self) -> Individual:
        return Individual({spec: np.random.permutation(n)
                    for spec, n in self.task.spec_to_n.items()})
    
    def create(self) -> Individual:
        evaluator = Evaluator(self.weights, self.task)
        ind = Individual({spec: np.array([-1]*n)
                for spec, n in self.task.spec_to_n.items()})
        for spec in self.task.spec_to_n:
            for class_num in np.random.permutation(len(self.task.classes[spec])):
                study_class = self.task.classes[spec][class_num]
                pos = self.__find_best_pos(ind, evaluator, study_class)
                ind[spec][pos] = class_num
                classroom, week_time = self.task.get_cl_wt(spec, pos)
                evaluator.count_class(study_class, classroom, week_time)
        return self.__fill_ind(ind)
    
    def __find_best_pos(self, ind:Individual, evaluator:Evaluator,
                study_class:StudyClass):
        best_poses = list()
        best_fitness = np.inf
        for pos in range(len(ind[study_class.cl_spec])):
            if ind[study_class.cl_spec][pos] > 0:
                continue
            classroom, week_time = self.task.get_cl_wt(study_class.cl_spec, pos)
            fitness = evaluator.count_class_without_saving(study_class, classroom, week_time)
            if not best_poses or fitness == best_fitness:
                best_poses.append(pos)
            elif fitness < best_fitness:
                best_poses = [pos]
                best_fitness = fitness
        return np.random.choice(best_poses)
    
    def __fill_ind(self, ind:Individual) -> Individual:
        for spec in self.task.spec_to_n:
            if len(ind[spec]) <= 0:
                continue
            idx = len(self.task.classes[spec])
            for ptr in range(len(ind[spec])):
                if ind[spec][ptr] > 0:
                    continue
                ind[spec][ptr] = idx
                idx += 1
        return ind