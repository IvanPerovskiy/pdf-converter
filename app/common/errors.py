from rest_framework.exceptions import ValidationError
from common.utils import get_logger


logger = get_logger('../logs/errors.log')


class ApiError(ValidationError):
    def __init(self, detail=None, code=None):
        super().__init__(detail, code)
        logger.info(detail)
