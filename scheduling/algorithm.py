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
from math import floor

import numpy as np
from deap import base
from deap import creator
creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", dict, fitness=creator.FitnessMax)
from deap import tools

from json_schemas import AlgorithmParams, TaskConfig, FitnessWeights
from ga_functions import eaSimpleWithElitism, selTournamentWithSharing
from task import SchedulingTask
from global_parameters import WEIGHT_TO_ERROR, POPS_DIR


class GeneticAlgorithm:
    '''
        Хранит данные о задаче составления расписания.
        Запускает алгоритм поиска.
    '''
    task:SchedulingTask
    weights:FitnessWeights
    params:AlgorithmParams
    population:list[creator.Individual] 
    hof:tools.HallOfFame

    __toolbox:base.Toolbox    

    def __init__(self, config:TaskConfig):
        self.params = config.params
        self.weights = config.weights
        self.task = SchedulingTask(config.data)
        self.hof = tools.HallOfFame(self.params.hof_size)
        self.__init_toolbox()

    def calc_fitness(self, individ:creator.Individual) -> float:
        errors = self.task.evaluate(individ)
        return ( 100_000 - sum(
                getattr(self.weights, w) * getattr(errors, e)
                for w, e in WEIGHT_TO_ERROR
        ), )# one element tuple
        

    def start_algorithm(self, max_generations:int, 
            change_interval:int=100, verbose:bool=False, 
            save_file_name:str=None):
        stats = tools.Statistics(lambda ind: 100_000 - ind.fitness.values[0])
        stats.register('min', np.min)
        stats.register('mean', np.mean)
        iterations = floor(max_generations / change_interval)
        for i in range(iterations):
            ngen = change_interval if i < iterations - 1 else max_generations%change_interval
            self.population, _ = eaSimpleWithElitism(
                    self.population, self.__toolbox, 
                    cxpb=self.params.p_crossover, 
                    mutpb=self.params.p_mutation,
                    ngen=ngen,
                    stats=stats,
                    halloffame=self.hof,
                    verbose=verbose,
                    verbose_delay=change_interval)
            if verbose:
                print(f'\n===Iteration {i+1}/{iterations}===')
                self.__print_individ_errors(self.hof.items[0])
                print(f'===Iteration {i+1}/{iterations}===\n')
            if save_file_name is not None:
                self.save_population(save_file_name)
            
    
    def calc_distance(self, ind1:creator.Individual, ind2:creator.Individual) -> int:
        max_union = sum(len(classes) for classes in self.task.classes.values())
        return max_union - sum(i == j for spec in ind1 
                for i, j in zip(ind1[spec], ind2[spec]) if i < len(self.task.classes[spec]))
    
    def save_population(self, save_file_name:str):
        with open(POPS_DIR / save_file_name, 'wb+') as f:
            pickle.dump(self.population, f)

    def load_population(self, load_file_name:str):
        with open(POPS_DIR / load_file_name, 'rb') as f:
            self.population = pickle.load(f)
        self.population = self.extend_population(
                self.params.population_size, self.population)

    def init_population(self):
        self.population = self.extend_population(self.params.population_size)

    def extend_population(self, size:int, init_pop:list=None) -> list[creator.Individual]:

        if init_pop is None:
            init_pop = list()
        size -= len(init_pop)
        algorithm_size = int(size * 0.1)
        default_size = size - algorithm_size
        return (init_pop + 
                [self.create_individual(True) for _ in range(algorithm_size)] + 
                [self.create_individual() for _ in range(default_size)])
    
    def __print_individ_errors(self, individ:creator.Individual) -> None:
        print('='*20, self.task.evaluate(individ), '='*20, sep='\n')

    def __init_toolbox(self):
        toolbox = base.Toolbox()
        if self.params.sharing_extent == 1.0 and self.params.distance_trashold == 1.0:
            toolbox.register("select", tools.selTournament, tournsize=self.params.tourn_size)
        else:
            toolbox.register("select", selTournamentWithSharing,
                    tournsize=self.params.tourn_size,
                    dist_trashold=self.params.distance_trashold,
                    sharing_ext=self.params.sharing_extent,
                    dist_calculator=self.calc_distance)
        toolbox.register("mate", self.__crossover)
        toolbox.register("mutate", self.__mutation)
        toolbox.register('evaluate', self.calc_fitness)
        self.__toolbox = toolbox
    
    def create_individual(self, by_algorithm=False):
        ind = creator.Individual()
        dict_ind = self.task.create_individual(by_algorithm)
        for key, val in dict_ind.items():
            ind[key] = val
        return ind

    def __crossover(self, ind1:creator.Individual, 
            ind2:creator.Individual) -> tuple[creator.Individual, creator.Individual]:
        for key in ind1:
            if ind1[key] and ind2[key]:
                ind1[key], ind2[key] = tools.cxOrdered(ind1[key], ind2[key])
        return ind1, ind2
    
    def __mutation(self, ind:creator.Individual) -> creator.Individual:
        for key in ind:
            if ind[key]:
                ind[key], = tools.mutShuffleIndexes(ind[key], indpb=1/len(ind[key]))
        return ind,
