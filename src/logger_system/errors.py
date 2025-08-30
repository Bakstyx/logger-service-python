

class DBRecordsErrors(Exception):
    def __init__(self, message, code, record):
        super().__init__(message)
        self.message = message
        self.code = code
        self.record = record.__dict__

    def __str__(self):
        if self.code:
            return f"[Error code {self.code}]: {self.message}. \n {self.record}"
        return self.message