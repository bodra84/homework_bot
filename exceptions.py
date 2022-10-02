class ResponseNotDict(TypeError):
    pass


class HomeworkNotList(TypeError):
    pass


class ResponseDictEmpty(ValueError):
    pass


class HomeworksNotInDict(KeyError):
    pass


class ResponseStatusNotOK(ValueError):
    pass


class HomeworkStatusesError(KeyError):
    pass


class HomeworkNameNotInDict(KeyError):
    pass


class StatusNotInDict(KeyError):
    pass
