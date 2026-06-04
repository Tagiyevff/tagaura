# 🧩 TagAura Plugin Development Guide

Welcome to the TagAura V5 Open Architecture! You can now extend TagAura's capabilities without modifying a single line of the core codebase (like `agent.py`). You can easily create your own Python scripts and introduce them to the system as new plugins.

## 🚀 How the Plugin System Works

Every time TagAura starts (via the `tga` command), it automatically scans the `tagaura/plugins/` directory. It reads every `.py` file inside. If the file matches the **TagAura Plugin Template**, it dynamically loads that file into its brain as a brand new "Tool".

## 📝 The Plugin Template

For a Python file to be recognized as a valid TagAura plugin, it **must** contain the following two components:
1. `TOOL_SCHEMA`: An OpenAI-compatible function schema dictionary that tells TagAura what this tool does and what parameters it requires.
2. `execute(**kwargs)`: The main Python function that is triggered when TagAura decides to use your tool.

---

### 💡 Example: Weather Plugin (`weather.py`)

If you save the following code as `tagaura/plugins/weather.py`, TagAura will instantly become an AI capable of checking the weather!

```python
# plugins/weather.py
import requests

# 1. TOOL SCHEMA: Tells TagAura how to use this tool
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_weather_plugin",
        "description": "Fetches the current weather for a specified city from the internet.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string", 
                    "description": "Name of the city to get the weather for (e.g., Istanbul, London)"
                }
            },
            "required": ["city"]
        }
    }
}

# 2. EXECUTE FUNCTION: The actual logic that runs
def execute(**kwargs):
    # Extract the parameter sent by TagAura
    city = kwargs.get("city", "Istanbul")
    
    try:
        # Request data from a public weather API (wttr.in)
        url = f"https://wttr.in/{city}?format=3"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            return f"Weather in {city}: {response.text}"
        else:
            return f"Failed to fetch weather. HTTP Status Code: {response.status_code}"
            
    except Exception as e:
        return f"An error occurred while executing the plugin: {str(e)}"
```

## ⚠️ Rules and Best Practices

1. **Dependencies:** If your plugin uses external libraries (like `requests`, `bs4`, `cv2`), make sure to remind users to install them via terminal (`pip install <library_name>`).
2. **Error Handling (Try-Catch):** We built the plugin system to be crash-proof; if your plugin throws an error, it won't crash TagAura. However, it is highly recommended to wrap your code in a `try-except` block and `return str(e)` on failure. This way, the AI can read the error message ("Oh, I passed the wrong parameter type!") and attempt to fix it automatically.
3. **Limitless Freedom:** From within a plugin, you can access the webcam, send signals to IoT devices (Arduino), query complex SQL databases, or send messages to a Discord channel. If Python can do it, TagAura can learn it!

You are now ready to build your own AI commands! The limit is not the sky, it's your imagination! 🌌
