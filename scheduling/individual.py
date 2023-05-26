import numpy as np

from enums import ClassroomSpecialization

class Individual(dict[ClassroomSpecialization, np.ndarray[int]]):
    fitness:float
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fitness = np.nan
    
    def __eq__(self, __value: object) -> bool:
        return self.fitness.__eq__(__value.fitness)
    
    def __ne__(self, __value: object) -> bool:
        return self.fitness.__ne__(__value.fitness)

    def __le__(self, __value: object) -> bool:
        return self.fitness.__le__(__value.fitness)
    
    def __ge__(self, __value: object) -> bool:
        return self.fitness.__ge__(__value.fitness)
    
    def __lt__(self, __value: object) -> bool:
        return self.fitness.__lt__(__value.fitness)
    
    def __ge__(self, __value: object) -> bool:
        return self.fitness.__ge__(__value.fitness)
    
