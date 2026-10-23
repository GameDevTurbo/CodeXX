"""Read the original App location without changing Gatekeeper/quarantine state."""
import ctypes
import os
from pathlib import Path
import sys


def original_app_path(path):
    path = Path(path)
    if sys.platform != "darwin" or "AppTranslocation" not in path.parts:
        return path
    references = []
    cf = None
    try:
        cf = ctypes.CDLL("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")
        security = ctypes.CDLL("/System/Library/Frameworks/Security.framework/Security")
        cf.CFURLCreateFromFileSystemRepresentation.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_long, ctypes.c_ubyte]
        cf.CFURLCreateFromFileSystemRepresentation.restype = ctypes.c_void_p
        cf.CFURLGetFileSystemRepresentation.argtypes = [ctypes.c_void_p, ctypes.c_ubyte, ctypes.c_void_p, ctypes.c_long]
        cf.CFURLGetFileSystemRepresentation.restype = ctypes.c_ubyte
        cf.CFRelease.argtypes = [ctypes.c_void_p]
        cf.CFRelease.restype = None
        security.SecTranslocateCreateOriginalPathForURL.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
        security.SecTranslocateCreateOriginalPathForURL.restype = ctypes.c_void_p
        raw = os.fsencode(path)
        url = cf.CFURLCreateFromFileSystemRepresentation(None, raw, len(raw), True)
        if not url:
            return None
        references.append(url)
        error = ctypes.c_void_p()
        original = security.SecTranslocateCreateOriginalPathForURL(url, ctypes.byref(error))
        if error.value:
            references.append(error.value)
        if not original:
            return None
        references.append(original)
        buffer = ctypes.create_string_buffer(32768)
        if cf.CFURLGetFileSystemRepresentation(original, True, buffer, len(buffer)):
            result = Path(os.fsdecode(buffer.value))
            return result if result.is_dir() else None
    except (OSError, AttributeError):
        return None
    finally:
        if cf:
            for reference in references:
                cf.CFRelease(reference)
    return None
