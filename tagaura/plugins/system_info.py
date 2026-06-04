# plugins/system_info.py

import platform
import psutil

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_system_info_plugin",
        "description": "Returns detailed information about the current computer system.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}

def execute(**kwargs):
    try:
        ram_gb = round(psutil.virtual_memory().total / (1024**3), 2)

        info = {
            "Operating System": platform.system(),
            "OS Version": platform.version(),
            "Computer Name": platform.node(),
            "Processor": platform.processor(),
            "Architecture": platform.machine(),
            "RAM (GB)": ram_gb,
            "Python Version": platform.python_version()
        }

        result = "\n".join(
            f"{key}: {value}" for key, value in info.items()
        )

        return result

    except Exception as e:
        return f"Plugin Error: {str(e)}"