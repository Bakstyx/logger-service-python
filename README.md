# logger-service-python

A flexible and extensible Python logging service with support for multiple handlers including file logging, console output, SQL databases, and [Grafana Loki](https://grafana.com/oss/loki/). Perfect for applications requiring comprehensive logging with context awareness and error tracking.

## Features

- 🎯 **Multiple Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- 📁 **Multiple Handlers**: File, Console, SQLAlchemy Database, and Loki
- 🎨 **Flexible Formatters**: Local, Development, Testing, and Production formats
- 🔍 **Auto Context Tracking**: Automatically captures function name, module, line number, and class name
- ⚠️ **Error Capture**: Comprehensive error tracking with traceback information
- 💾 **Database Storage**: Optional logging to PostgreSQL or other SQLAlchemy-supported databases
- 📊 **Centralized Management**: LoggerManager for efficient logger lifecycle management
- 🔄 **Reusable Instances**: Singleton-like pattern with logger caching

## Installation

Install via pip:

```bash
pip install logger-service-python
```

Or with Poetry:

```bash
poetry add logger-service-python
```

### Dependencies

- Python >= 3.10
- SQLAlchemy >= 2.0.43
- loki-logger-handler >= 1.1.2
- python-dotenv >= 1.1.0
- requests >= 2.32.5

## Quick Start

### Basic File Logging

```python
from logger_system import LoggerManager

# Get a logger instance
logger = LoggerManager.get_logger(
    log_file="logs/app.log",
    formatter_type="local",
    name="app"
)

# Use the logger
logger.info("Application started")
logger.debug("Debugging information")
logger.warning("This is a warning")
logger.error("An error occurred")
logger.critical("Critical error!")

# Clean up
LoggerManager.close_logger("logs/app.log")
```

### Console Output

```python
from logger_system import LoggerManager

# Get a logger without specifying a log file (console only)
logger = LoggerManager.get_logger(
    log_file=None,
    formatter_type="dev",
    name="console_logger"
)

logger.info("This will appear in console")
```

### Error Tracking

```python
from logger_system import ErrorTracker

try:
    # Your code here
    result = 10 / 0
except Exception as e:
    error_info = ErrorTracker.capture_error(e)
    logger.error(f"Caught error: {error_info}")
```

## Configuration

### Formatter Types

The `formatter_type` parameter controls the output format:

- **`local`**: Includes timestamp, logger name, level, custom module, function, and line number
  ```
  2025-01-20 10:30:45,123 - app - INFO - Message -> module.name - func_name - 42
  ```

- **`dev`**: Development format without timestamp
  ```
  app - INFO - Message -> module.name - func_name - 42
  ```

- **`test`**: Testing format (same as dev)
  ```
  app - INFO - Message -> module.name - func_name - 42
  ```

- **`prod`**: Production format (same as dev)
  ```
  app - INFO - Message -> module.name - func_name - 42
  ```

## Core Components

### LoggerManager

Central manager for creating and managing logger instances:

```python
from logger_system import LoggerManager

# Get or create a logger
logger = LoggerManager.get_logger(
    log_file="logs/myapp.log",
    formatter_type="local",
    name="myapp"
)

# Close a specific logger
LoggerManager.close_logger("logs/myapp.log")

# Close all loggers
LoggerManager.close_all_loggers()
```

### Logger

Core logging class with context-aware logging:

```python
from logger_system import Logger

# Create logger directly
logger = Logger(
    formatter_type="local",
    log_file="logs/app.log",
    name="app"
)

# Log at different levels
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")
```

### AutoTracker

Automatically captures execution context:

```python
from logger_system import AutoTracker

context = AutoTracker.get_execution_info()
# Returns: {
#     'function': 'my_function',
#     'lineno': 42,
#     'module': '__main__',
#     'class': 'MyClass' or None
# }
```

### ErrorTracker

Captures comprehensive error information:

```python
from logger_system import ErrorTracker

try:
    raise ValueError("Something went wrong")
except Exception as e:
    error_dict = ErrorTracker.capture_error(e)
    # Returns error_type, error_message, error_args, error_traceback
```

## Advanced Usage

### Database Logging

Store logs in a PostgreSQL database:

```python
from logger_system import PostgreSQLLogger
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

# Setup your SQLAlchemy base
Base = declarative_base()

# Create logger with database support
logger = PostgreSQLLogger(
    sqlalchemy_base=Base,
    name="db_logger",
    formatter_type="prod",
    database_url="postgresql://user:password@localhost/logs"
)

logger.info("This will be stored in the database")
```

### Loki Integration

Send logs to Grafana Loki:

```python
from logger_system import Logger
from loki_logger_handler.loki_logger_handler import LokiLoggerHandler

logger = Logger(
    formatter_type="prod",
    log_file=None,
    name="loki_logger"
)

# Add Loki handler
loki_handler = LokiLoggerHandler(
    url="http://localhost:3100",
    tags={"app": "myapp", "env": "production"}
)
logger.logger.addHandler(loki_handler)

logger.info("Sent to Loki!")
```

## Project Structure

```
logger-service-python/
├── src/
│   └── logger_system/
│       ├── __init__.py           # Package exports
│       ├── logging_manager.py    # LoggerManager class
│       ├── loggers.py            # Logger, PostgreSQLLogger, and handler classes
│       ├── log_models.py         # SQLAlchemy Log model
│       └── errors.py             # Custom exceptions
├── test/                         # Test files
├── logs/                         # Log output directory
├── pyproject.toml               # Project configuration
└── README.md                    # This file
```

## Environment Variables

Configure logging via `.env` file (if using python-dotenv):

```env
LOG_LEVEL=DEBUG
LOG_FILE=logs/app.log
DATABASE_URL=postgresql://user:pass@localhost/logs
LOKI_URL=http://localhost:3100
```

## Error Handling

The package includes custom exceptions for database-related errors:

```python
from logger_system import DBRecordsErrors

try:
    # Database operation
    pass
except Exception as e:
    raise DBRecordsErrors(
        message="Failed to write log",
        code=500,
        record=log_record
    )
```

## Best Practices

1. **Use LoggerManager for consistency**: Centralize logger creation and lifecycle management
2. **Close loggers properly**: Call `LoggerManager.close_all_loggers()` on application shutdown
3. **Name your loggers**: Use descriptive names for better log filtering
4. **Use appropriate log levels**: DEBUG for development, INFO for production events
5. **Handle errors with AutoTracker**: Context information is automatically captured for all log calls

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Author

**Bakstyx** - [bakstyx.012@gmail.com](mailto:bakstyx.012@gmail.com)

## Version

Current version: **1.0.5**

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, questions, or feature requests, please open an issue on GitHub.