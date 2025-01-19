from enum import Enum
from datetime import datetime
import sys

class LogLevel(Enum):
    DEBUG = '\033[94m'  # Blue
    INFO = '\033[92m'   # Green
    WARN = '\033[93m'   # Yellow
    ERROR = '\033[91m'  # Red
    END = '\033[0m'     # Reset color

def _log(level: LogLevel, message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{level.value}[{timestamp}] {level.name}: {message}{LogLevel.END.value}", file=sys.stderr)

def log_debug(message: str):
    _log(LogLevel.DEBUG, message)

def log_info(message: str):
    _log(LogLevel.INFO, message)

def log_warn(message: str):
    _log(LogLevel.WARN, message)

def log_err(message: str):
    _log(LogLevel.ERROR, message)

# Example usage:
if __name__ == "__main__":
    print_debug("This is a debug message")
    print_info("This is an info message")
    print_warn("This is a warning message")
    print_err("This is an error message")
