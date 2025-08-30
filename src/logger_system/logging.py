import os
import sys
import traceback
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import inspect

class ErrorTracker:
    @staticmethod
    def capture_error(error: Exception) -> Dict[str, Any]:
        error_dict = {
            'type': type(error).__name__,
            'message': str(error),
            'args': error.args,
            'traceback': traceback.format_exception(type(error), error, error.__traceback__),
            'timestamp': datetime.now().isoformat()
        }
        return error_dict


class AutoTracker:
    @staticmethod
    def get_execution_info():
        frame = inspect.currentframe().f_back.f_back.f_back  # Go back two frames to get the caller's info
        return {
            'function': frame.f_code.co_name,
            'lineno': frame.f_lineno,
            'module': frame.f_globals.get('__name__')
        }

class Logger:
    def __init__(self, log_file: str=None, name: Optional[str] = None):
        self.log_file = log_file
        self.name = name
        self._setup_logger()

    def _setup_logger(self):
        self.logger = logging.getLogger(self.name or __name__)
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s -> %(custom_module)s - %(custom_function)s - %(custom_lineno)d')
        
        #File handler
        if self.log_file:
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        #Console handeler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def set_name(self, new_name: str):
        self.name = new_name
        self._setup_logger()
    
    def _log(self, level: int, message: str, *args, **kwargs):
        exec_info = AutoTracker.get_execution_info()
        
        # Create a custom record factory to include execution info
        old_factory = logging.getLogRecordFactory()
        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            record.custom_function = exec_info['function']
            record.custom_lineno = exec_info['lineno']
            record.custom_module = exec_info['module']
            return record
        
        logging.setLogRecordFactory(record_factory)
        
        try:
            self.logger.log(level, message, *args, **kwargs)
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
        self._log(logging.ERROR, f"Error: {message}", exc_info=True, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        self._log(logging.CRITICAL, f"Critical: {message}", exc_info=True, *args, **kwargs)
    
    def __del__(self):
        # Clean up handlers when the logger is destroyed
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)


class CustomException(Exception):
    def __init__(self, message: str, logger: Logger):
        super().__init__(message)
        logger.error(message)
        ErrorTracker.capture_error(self)


class DetailedTracker:
    def get_execution_info(self):
        frame = inspect.currentframe().f_back
        return {
            'class': self.__class__.__name__,
            'func': frame.f_code.co_name,
            'line': frame.f_lineno,
            'file': frame.f_code.co_filename,
            'module': frame.f_globals.get('__name__'),
            'python_version': sys.version,
            'os': os.name,
            'platform': sys.platform,
            'caller': frame.f_back.f_code.co_name if frame.f_back else None,
            'args': inspect.getargvalues(frame).args,
            'varargs': inspect.getargvalues(frame).varargs,
            'keywords': inspect.getargvalues(frame).keywords,
        }