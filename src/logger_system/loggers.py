import inspect
import logging
import os
import traceback
from logging import Handler, StreamHandler, Formatter
from typing import Literal, Optional

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

#Loki handelers
from loki_logger_handler.loki_logger_handler import LokiLoggerHandler

from .log_models import Log

Base = declarative_base()

class ErrorTracker:
    @staticmethod
    def capture_error(error:Exception):
        error_dict = {
            "error_type" : type(error).__name__,
            "error_message" : str(error),
            "error_args" : error.args,
            "error_traceback" : traceback.format_exception(type(error), error, error.__traceback__)
        }
        return error_dict

class AutoTracker:
    @staticmethod
    def get_execution_info():
        """
        Retrieves execution context information from the call stack.
        Returns:
            dict: A dictionary containing the following keys:
                - 'function': The name of the function from which this method was called.
                - 'lineno': The line number in the source code where the call was made.
                - 'module': The name of the module where the call was made.
        """
        frame = inspect.currentframe()
        last_available_frame = frame
        # Traverse up to 3 frames, keeping track of the last available frame
        for _ in range(3):
            if frame is not None and hasattr(frame, "f_back"):
                frame = frame.f_back
                if frame is not None:
                    last_available_frame = frame
            else:
                break
        if last_available_frame is not None:
            return {
                "function": last_available_frame.f_code.co_name,
                "lineno": last_available_frame.f_lineno,
                "module": last_available_frame.f_globals.get("__name__"),
                "class": last_available_frame.f_locals.get("self").__class__.__name__
                    if "self" in last_available_frame.f_locals
                    else None,
            }
        else:
            return {
                "function": None,
                "lineno": None,
                "module": None,
                "class": None,
            }


class Logger:
    def __init__(
        self,
        formatter_type:Optional[Literal["local", "dev", "test", "prod"]] = "local",
        log_file:Optional[str] = None,
        name: Optional[str] = None
        ) -> None:
        self.log_file = log_file
        self.name = name
        self.formatter_type = formatter_type
        self._setup_logger()

    def _setup_logger(self):
        self._logger = logging.getLogger(self.name or __name__)
        self._logger.setLevel(logging.DEBUG)

        # Remove existing handlers
        for handler in self._logger.handlers[:]:
            self._logger.removeHandler(handler)

        if self.formatter_type == "local":
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s -> %(custom_module)s - %(custom_function)s - %(custom_lineno)d"
            )
        else:
            formatter = logging.Formatter(
                "%(name)s - %(levelname)s - %(message)s -> %(custom_module)s - %(custom_function)s - %(custom_lineno)d"
            )

        # File handler
        if self.log_file:
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self._logger.addHandler(file_handler)

        # Console handeler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)

    def set_name(self, new_name: str):
        self.name = new_name
        self._setup_logger()

    def _log(self, level: int, message: str, *args, **kwargs):
        exec_info = AutoTracker.get_execution_info()

        # Create a custom record factory to include execution info
        old_factory = logging.getLogRecordFactory()

        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            record.custom_function = exec_info["function"]
            record.custom_lineno = exec_info["lineno"]
            record.custom_module = exec_info["module"]
            return record

        logging.setLogRecordFactory(record_factory)

        try:
            self._logger.log(level, message, *args, **kwargs)
        finally:
            # Restore the original record factory
            logging.setLogRecordFactory(old_factory)

    def debug(self, message: str, *args, **kwargs):
        self._log(logging.DEBUG, f"Debug: {message}", *args, **kwargs)

    def info(self, message: str, *args, **kwargs):
        self._log(logging.INFO, f"Info: {message}", *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        self._log(logging.WARNING, f"Warning: {message}", *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        self._log(logging.ERROR, f"Error: {message}", *args, exc_info=True, **kwargs)

    def critical(self, message: str, *args, **kwargs):
        self._log(
            logging.CRITICAL, f"Critical: {message}", *args, exc_info=True, **kwargs
        )

    def _close_logger(self):
        # Clean up handlers when the logger is destroyed
        for handler in self._logger.handlers[:]:
            handler.close()
            self._logger.removeHandler(handler)



class SQLAlchemyLogHandler(Handler):
    def __init__(self, base):
        super().__init__()
        self.engine = base._create_engine()
        # Ensure the logs table is created if it doesn't exist
        Base.metadata.create_all(self.engine, tables=[Log.__table__])
        self.Session = sessionmaker(bind=self.engine)

    def store_log(self, name_logger:str, level:str, message:str, module:str,
                    classname:str, func_name:str, lineno:int, error_type:str,
                    error_message:str, error_args:str, error_traceback:str):
        session = self.Session()
        log = Log(name_logger=name_logger, level=level, message=message, module=module,
                    classname=classname, func_name=func_name, lineno=lineno, error_type=error_type,
                    error_message=error_message, error_args=error_args, error_traceback=error_traceback)
        session.add(log)
        session.commit()
        session.close()

    def emit(self, record):
        log_entry = self.format(record)
        self.store_log(
            name_logger=record.name,
            level=record.levelname,
            message=log_entry,
            module=getattr(record, "custom_module", "NA"),
            classname=getattr(record, "custom_class", "NA"),
            func_name=getattr(record, "custom_function", "NA"),
            lineno=getattr(record, "custom_lineno", -1),
            error_type=getattr(record, "error_type", "NA"),
            error_message=getattr(record, "error_message", "NA"),
            error_args=getattr(record, "error_args", "NA"),
            error_traceback=getattr(record, "error_traceback", "NA"),
        )


class PostgreSQLLogger(Logger):
    def __init__(
        self,
        sqlalchemy_base,
        name: Optional[str] = None,
        formatter_type: Optional[Literal["local", "dev", "test", "prod"]] = "local",
    ):
        self.base = sqlalchemy_base
        super().__init__(
            formatter_type=formatter_type,
            log_file=None,  # No file handler
            name=name
        )

    def _setup_logger(self):
        self._logger = logging.getLogger(self.name or __name__)
        self._logger.setLevel(logging.DEBUG)

        # Remove all handlers
        for handler in self._logger.handlers[:]:
            self._logger.removeHandler(handler)

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s -> %(custom_module)s - %(custom_function)s - %(custom_lineno)d"
        )

        # Use SQLAlchemyLogHandler for DB storage
        db_handler = SQLAlchemyLogHandler(self.base)
        db_handler.setLevel(logging.DEBUG)
        db_handler.setFormatter(formatter)
        self._logger.addHandler(db_handler)

        # Console handler for debugging
        console_handler = StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)

    def error(self, message: str, error_info: Optional[dict] = None, *args, **kwargs):
        self._log(logging.ERROR, f"Error: {message}", *args, exc_info=True, extra=error_info or {}, **kwargs)

    def critical(self, message: str, error_info: Optional[dict] = None, *args, **kwargs):
        self._log(logging.CRITICAL, f"Critical: {message}", *args, exc_info=True, extra=error_info or {}, **kwargs)



class LokiHandeler(Handler):
    # LokiLoggerHandler
    def __init__(
        self,
        loki_url: str,
        labels: Optional[dict] = None,
        label_keys: Optional[dict] = None,
        loki_metadata: Optional[dict] = None,
        ):
        super().__init__()
        self.loki_handler = LokiLoggerHandler(
            url=loki_url,
            labels=labels,
            label_keys=label_keys,
            timeout=5,
            enable_structured_loki_metadata=True,
            loki_metadata=loki_metadata,
        )
    def emit(self, record):
        self.loki_handler.emit(record)

class LokiLoggerService(Logger):
    def __init__(
        self,
        loki_config: dict,
        formatter_type: Optional[Literal["local", "dev", "test", "prod"]] = "local",
        name: Optional[str] = None,
    ) -> None:
        self.log_file = None
        self.name = name
        self.formatter_type = formatter_type
        self.loki_config = loki_config
        self._setup_logger()

    def __validate_config__ (self):
        # Validate loki_config here
        pass

    def _setup_logger(self):
        self._logger = logging.getLogger(self.name or __name__)
        self._logger.setLevel(logging.DEBUG)

        # Remove existing handlers
        for handler in self._logger.handlers[:]:
            self._logger.removeHandler(handler)

        if self.formatter_type == "local":
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s -> %(custom_module)s - %(custom_function)s - %(custom_lineno)d"
            )
        else:
            formatter = logging.Formatter(
                "%(name)s - %(levelname)s - %(message)s -> %(custom_module)s - %(custom_function)s - %(custom_lineno)d"
            )

        # Loki handler
        loki_handeler = LokiHandeler(
            loki_url=self.loki_config.get("loki_url", ""),
            labels=self.loki_config.get("labels", {}),
            label_keys=self.loki_config.get("label_keys", {}),
            loki_metadata=self.loki_config.get("loki_metadata", {}),
        )
        loki_handeler.setLevel(logging.DEBUG)
        loki_handeler.setFormatter(formatter)
        self._logger.addHandler(loki_handeler)

        # Console handeler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)


