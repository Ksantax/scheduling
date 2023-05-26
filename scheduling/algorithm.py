'''
    Модуль для решения задачи составления расписания.
    --------

    Задача решается поиском по средствам генетического алгоритма (ГА).
    Особи в данном случае - это перестановки чисел о 1 до N, 
    где N = `кол-во аудиторий` * `кол-во дней в неделе` * `кол-во пар в дне`.

    Для ГА определены сделующие параметры:
        - Скрещивание - упорядоченный обмень участками генов особей (перестановок)
        - Мутация - обмен двух генов (чисел в перестановке)
        - Отбор - турнирный

    Так же используются элитизм и образование ниш
'''

import pickle
from copy import deepcopy

import numpy as np

from json_schemas import AlgorithmParams, TaskConfig, FitnessWeights
from task import SchedulingTask
from global_parameters import POPS_DIR
from individual import Individual
from individual_creator import IndividualCreator
from evaluation import Evaluator


class GeneticAlgorithm:
    '''
        Хранит данные о задаче составления расписания.
        Запускает алгоритм поиска.
    '''
    task:SchedulingTask

    weights:FitnessWeights
    params:AlgorithmParams
    population:np.ndarray[Individual] 
    hof:np.ndarray
    ind_creator:IndividualCreator
    evaluator:Evaluator  

    def __init__(self, config:TaskConfig):
        self.params = config.params
        self.weights = config.weights
        self.task = SchedulingTask(config.data)
        self.ind_creator = IndividualCreator(self.weights, self.task)
        self.evaluator = Evaluator(self.weights, self.task)
        self.hof = np.array([])

    def start_algorithm(self, generations:int, verbose_interval:bool=-1, 
            save_file_name:str=None):
        self.population = self.evaluation(self.population)
        self.population.sort()
        self.hof = deepcopy(self.population[:self.params.hof_size])
        for gen in range(1, generations+1):
            num = self.params.population_size - self.params.hof_size
            selected = self.selection(self.population, num)
            crossed = self.crossover(selected)
            muted = self.mutation(crossed)
            evaluated = self.evaluation(muted)
            self.population = np.append(evaluated, self.hof, axis=0)
            self.population.sort()
            self.hof = deepcopy(self.population[:self.params.hof_size])
            if verbose_interval > 0 and gen%verbose_interval == 0:
                print([ind.fitness for ind in self.hof])
                self.verbose_print(gen, generations)
            if save_file_name is not None:
                self.save_population(save_file_name)
        if verbose_interval > 0:
            self.verbose_print(gen, generations)
    
    def save_population(self, save_file_name:str):
        with open(POPS_DIR / save_file_name, 'wb+') as f:
            pickle.dump(self.population, f)

    def load_population(self, load_file_name:str):
        with open(POPS_DIR / load_file_name, 'rb') as f:
            self.population = pickle.load(f)
        self.population = self.extend_population(
                self.params.population_size, self.population)
    
    def verbose_print(self, gen:int, total:int):
        print(f'\n===Generation {gen}/{total}===')
        self.evaluator.print_errors(self.hof[0])
        print('='*20)

    def init_population(self):
        self.population = self.extend_population(self.params.population_size)

    def extend_population(self, size:int, init_pop:np.ndarray|list=None) ->np.ndarray[Individual]:
        if init_pop is None:
            init_pop = list()
        init_pop = list(init_pop)
        size -= len(init_pop)
        algorithm_size = int(size * self.params.proportion_by_algorithm)
        random_size = size - algorithm_size
        return np.array(init_pop + 
                [self.ind_creator.create() for _ in range(algorithm_size)] + 
                [self.ind_creator.create_randomly() for _ in range(random_size)])

    def evaluation(self, inds:np.ndarray[Individual]) -> np.ndarray[Individual]:
        for ind in inds:
            ind.fitness = self.evaluator.evaluate(ind)
        return inds

    def selection(self, inds:np.ndarray[Individual], size:int) -> np.ndarray[Individual]:
        return np.array([
            np.random.choice(inds, self.params.tour_size).min()
            for _ in range(size)
        ])

    def mutation(self, inds:np.ndarray[Individual]) -> np.ndarray[Individual]:
        for i in range(len(inds)):
            if np.random.random() < self.params.p_mutation:
                inds[i] = self.mut(inds[i])
        return inds

    def mut(self, ind:Individual) -> Individual:
        return Individual({spec: self.__mut(ind[spec]) for spec in ind})
    
    def __mut(self, arr:np.ndarray[int]) -> np.ndarray[int]:
        for i in range(len(arr)):
            if np.random.rand() < 10/len(arr):
                j = np.random.randint(0, len(arr))
                arr[i], arr[j] = arr[j], arr[i]
        return arr
    
    def crossover(self, inds:np.ndarray[Individual]) -> np.ndarray[Individual]:
        for i, j in np.random.randint(0, len(inds), size=(len(inds), 2)):
            if np.random.rand() < self.params.p_crossover:
                inds[i], inds[j] = self.cross(inds[i], inds[j])
        return inds

    def cross(self, ind1:Individual, ind2:Individual) -> \
            tuple[Individual, Individual]:
        ret1, ret2 = dict(), dict()
        for spec in ind1:
            ret1[spec], ret2[spec] = self.__cross(ind1[spec], ind2[spec])
        return Individual(ret1), Individual(ret2)

    def __cross(self, arr1:np.ndarray[int], arr2:np.ndarray[int]) ->\
            tuple[np.ndarray[int], np.ndarray[int]]:
        ret1, ret2 = arr1.copy(), arr2.copy()
        n = len(arr1)
        if n <= 0:
            return ret1, ret2
        l, r = np.random.randint(n, size=2)
        if l > r:
            l, r = r, l
        k1 = k2 = r
        ret1[l:r], ret2[l:r] = arr2[l:r], arr1[l:r]
        pocket1 = set(ret1[l:r])
        pocket2 = set(ret2[l:r])
        for i in range(r, n + r):
            if arr1[i%n] not in pocket1:
                ret1[k1%n] = arr1[i%n]
                k1 += 1
            if arr2[i%n] not in pocket2:
                ret2[k2%n] = arr2[i%n]
                k2 += 1
        return ret1, ret2
