from enum import Enum


class ClassroomFeature(Enum):
    '''
        Особенности аудиторий:
            PROJECTOR  - Наличие проектора в кабинете
            
    '''
    PROJECTOR = 'Projector'
    CHALK_DESK = 'Chalk desk'
    MARKER_DESK = 'Marker desk'


class Degree(Enum):
    '''
        Степень подготовки студентов в группе
            BACHELOR - Бакалавр
            MASTER   - Магистр
    '''
    BACHELOR = 'Bachelor'
    MASTER = 'Master'


class ClassroomSpecialization(Enum):
    '''
        Типы специализаций аудиториий
            DEFAULT    - Обычная аудитория
            COMPUTERS  - Наличие компьютеров в кабинете
            SPORTSROOM - Наличие спортивного оснащение, спортивный зал
    '''
    DEFAULT = 'Default'
    COMPUTERS = 'Computers'
    SPORTSROOM = 'Sportsroom'
