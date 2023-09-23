from datetime import datetime
from pathlib import Path, PosixPath, WindowsPath


nested_text_converters = {
    datetime: str,
    PosixPath: str,
    WindowsPath: str,
    Path: str
}
