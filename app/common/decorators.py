import logging

from functools import wraps

request_logger = logging.getLogger(__name__)
request_logger.setLevel(logging.INFO)
request_logger_handler = logging.FileHandler("../logs/requests.log")
request_logger_handler.setLevel(logging.INFO)
request_logger_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(message)s")
)
request_logger.addHandler(request_logger_handler)


def read_only_admin_model(*non_display_fields):
    """
        Декоратор для класса отображения модели в админке, который делает модель доступной только для чтения
        В качестве аргумента принимает список полей, которые нужно скрыть в самой модели
        По умолчанию запрещает создавать и удалять объекты модели
    """

    class ClassWrapper:
        def __init__(self, cls):
            self.other_class = cls
            self.other_class.has_add_permission = lambda self, request: False
            self.other_class.has_delete_permission = lambda self, request, obj=None: False

            if non_display_fields:

                def get_fields(self, request, obj=None):
                    fields = super(cls, self).get_fields(request, obj)
                    for field in non_display_fields:
                        fields.remove(field)
                    return fields

                self.other_class.get_fields = get_fields

        def __call__(self, *cls_ars):
            other = self.other_class(*cls_ars)
            return other

    return ClassWrapper


def log_request(function):
    @wraps(function)
    def decorator(self, request, *args, **kwargs):
        if request.user.is_anonymous:
            user_id = 'anonymous'
        else:
            user_id = request.user.user.id
        message = f'USER_ID: {user_id} | METHOD: {request.method} | URL: {request.path} | '
        if request.method == "GET":
            message += f'ARGS: {dict(request.GET)}'
        elif self.action == 'create':
            # Не записываем в лог тело файла
            pass
        else:
            message += f'ARGS: {request.data}'
        request_logger.info(message)
        return function(self, request, *args, **kwargs)
    return decorator
