
import sys
from datetime import datetime


class Logger:
    def __init__(self, verbose=True):
        self.verbose = verbose
    
    def info(self, message):
        print(message)
    
    def debug(self, message):
        if self.verbose:
            print(message)
    
    def success(self, message):
        print(f"{message}")
    
    def error(self, message):
        print(f"{message}", file=sys.stderr)
    
    def warning(self, message):
        print(f"{message}")
    
    def header(self, title, width=80):
        if self.verbose:
            print(f"\n{'='*width}")
            print(f"{title}")
            print(f"{'='*width}\n")
    
    def summary(self, stats):
        self.header("SUMMARY")
        for key, value in stats.items():
            print(f"{key}: {value}")
        print(f"{'='*80}\n")


_logger = None

def get_logger(verbose=True):
    global _logger
    if _logger is None:
        _logger = Logger(verbose)
    return _logger

def set_verbose(verbose):
    global _logger
    if _logger:
        _logger.verbose = verbose