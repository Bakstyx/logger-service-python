from sqlalchemy import Column, Integer, String, Text, func
from sqlalchemy import DateTime
from sqlalchemy.orm import declarative_base



Base_logs = declarative_base()

class Log(Base_logs):
    __tablename__ = "logs"
    __table_args__ = {"schema": "logs"}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name_logger = Column(String(255), nullable=False)
    level = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    module = Column(String(255), nullable=True)
    classname = Column(String(255), nullable=True)
    func_name = Column(String(255), nullable=True)
    lineno = Column(Integer, nullable=True)
    error_type = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)
    error_args = Column(Text, nullable=True)
    error_traceback = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
