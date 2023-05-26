from collections import namedtuple

from global_parameters import CLASSES_PER_DAY as CPD


def get_wd_and_dt(week_time: int) -> tuple[int, int]:
    '''
        Получить номер дня недели и номер в рамках одного дня для времени,
        в которое проводится занятие в рамках недели.

        Get weekday and daytime of study class by its week time.
        args:
            week_time:int - number of study class in whole week.
        returns:
            (week_day:int, day_time:int) - weekday number of study class
                    and its number in day
    '''
    return week_time // CPD, week_time % CPD

