from typing import Literal, Optional
from .loggers import Logger 


class LoggerManager:
    _loggers = {}

    @classmethod
    def get_logger(
        cls,
        log_file: str,
        formatter_type: Optional[Literal["local", "dev", "test", "prod"]] = "local",
        name: Optional[str] = None,
    ):
        if log_file not in cls._loggers:
            cls._loggers[log_file] = Logger(formatter_type, log_file, name)
        else:
            cls._loggers[log_file].set_name(name)
        return cls._loggers[log_file]

    @classmethod
    def close_all_loggers(cls):
        for logger in cls._loggers.values():
            for handler in logger.logger.handlers[:]:
                handler.close()
                logger.logger.removeHandler(handler)
        cls._loggers.clear()

    @classmethod
    def close_logger(cls, log_file: str):
        if log_file in cls._loggers:
            logger = cls._loggers[log_file]
            for handler in logger.logger.handlers[:]:
                handler.close()
                logger.logger.removeHandler(handler)
            del cls._loggers[log_file]