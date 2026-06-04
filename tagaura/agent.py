import litellm
import questionary
import os
import sqlite3
import json
import platform
import subprocess
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.live import Live
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from tagaura.config import get_memory, add_to_memory
import getpass
import warnings

# İstenmeyen soket/kaynak uyarılarını gizle
warnings.simplefilter("ignore", ResourceWarning)

console = Console()
session = PromptSession()

TAGAURA_LOGO = """[bold cyan]
████████╗ █████╗  ██████╗  █████╗ ██╗   ██╗██████╗  █████╗ 
╚══██╔══╝██╔══██╗██╔════╝ ██╔══██╗██║   ██║██╔══██╗██╔══██╗
   ██║   ███████║██║  ███╗███████║██║   ██║██████╔╝███████║
   ██║   ██╔══██║██║   ██║██╔══██║██║   ██║██╔══██╗██╔══██║
   ██║   ██║  ██║╚██████╔╝██║  ██║╚██████╔╝██║  ██║██║  ██║
   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝
[/bold cyan]"""

def start_chat(provider, model, api_key):
    # API key ortam değişkenlerini (ENV) ayarlama
    provider_lower = provider.split()[0].lower()
    if "open" in provider_lower and "router" not in provider_lower:
        os.environ["OPENAI_API_KEY"] = api_key
    elif "anthropic" in provider_lower:
        os.environ["ANTHROPIC_API_KEY"] = api_key
    elif "google" in provider_lower or "gemini" in provider_lower:
        os.environ["GEMINI_API_KEY"] = api_key
    elif "mistral" in provider_lower:
        os.environ["MISTRAL_API_KEY"] = api_key
    elif "deepseek" in provider_lower:
        os.environ["DEEPSEEK_API_KEY"] = api_key
    elif "openrouter" in provider_lower:
        os.environ["OPENROUTER_API_KEY"] = api_key
    elif "z.ai" in provider_lower or "zhipu" in provider_lower:
        os.environ["ZHIPUAI_API_KEY"] = api_key
    elif "groq" in provider_lower:
        os.environ["GROQ_API_KEY"] = api_key
    else:
        os.environ[f"{provider_lower.upper()}_API_KEY"] = api_key

    # Plugin yükleme (Hot Reload için artık while döngüsü içinde yapılacak)

    # Sistem Bilgilerini Çekme
    os_name = platform.system()
    os_release = platform.release()
    username = getpass.getuser()
    cwd = os.getcwd()
    
    system_prompt = f"""You are TagAura, a powerful CLI AI Agent and System Administrator.
You operate via the terminal, assisting the user with system administration, coding, and automation.

- Current OS: {os_name} {os_release}
- Username: {username}
- Current Working Directory: {cwd}
- Current Provider: {provider}
- Current Model: {model}

CRITICAL RULES:
1. COMMUNICATION STYLE: Be concise, friendly, and natural. Do NOT write long essays.
2. ADAPT TO USER LANGUAGE: Always respond to the user in the EXACT language they use to speak with you (e.g., if they write in Turkish, reply in fluent Turkish).
3. NO UNASKED EXPLANATIONS: Do NOT list your capabilities or give examples unless explicitly requested. Focus directly on the task.
4. ABSOLUTE PROHIBITION ON CODE BLOCKS: NEVER give the user code or scripts to run manually. If the user asks you to write code or create a plugin, YOU MUST CALL THE `write_file` TOOL to save it directly to a file. Your conversational response MUST NOT contain ANY markdown code blocks (e.g., ```python, ```powershell, ```bash, or ```). Write code ONLY through your file tools, and keep the chat clean.
5. AUTONOMOUS EXECUTION: You MUST execute ALL system operations (like file creation, network scanning) YOURSELF by strictly using the `run_terminal_command` tool.
6. SELF-CORRECTION (DO NOT GIVE UP): If a tool command fails (e.g., folder not found, permission denied), DO NOT tell the user to fix it. Analyze the error and call the tool AGAIN to solve it yourself (e.g., create the missing folder first). Keep trying until you succeed.
7. SILENT SUCCESS: When an operation succeeds, just give a short one-sentence confirmation in the user's language. Do NOT show the long scripts or execution steps to the user.
8. IGNORE PAST TASKS: Do not bring up or summarize past completed tasks from the conversation history when the user just says hello or starts a new session. Focus only on their current message.
9. PERMANENT MEMORY: When the user tells you personal information (their name, age, preferences) or explicitly asks you to remember something, you MUST call the `memorize` tool to save it. Do not just say "I noted it", you must actually call the tool!
10. FILE OPERATIONS: You have native tools (`read_file`, `write_file`, `replace_in_file`) to create projects or fix code. ALWAYS use them instead of bash/powershell to write files!
11. WEB SEARCH: You have access to the internet. If you need documentation or a solution to an error, use `search_web` to find it, then `read_url` to read the page content.
12. GUI AUTOMATION: You have the `control_gui` tool to physically control the mouse and keyboard using PyAutoGUI python scripts. You can use it to open apps, click buttons, or type text if the user requests it.
13. BACKGROUND TASKS: You can use `run_background_task` to start daemon threads. Use this for scheduled cron jobs (using time.sleep or schedule module) or heavy processing that shouldn't block the chat interface.
14. MULTI-AGENT SWARM: You have the `delegate_task` tool. If a task is very complex, requires critical review (like writing a big algorithm), or requires a second opinion, SPAWN A SUB-AGENT to do it for you. The sub-agent will do the heavy lifting and report back to you.
15. CLIPBOARD MANAGEMENT: Use `read_clipboard` and `write_clipboard` to interact with the user's copy-paste clipboard.
16. SYSTEM NOTIFICATIONS: Use `send_notification` to show a desktop toast notification to the user when a long background task finishes.
17. FOLDER WATCHER: Use `watch_folder` to monitor a folder for new files and run a python script when a new file appears.
18. INTERNET TUNNELING: Use `expose_localhost` to expose a local port to the internet via Ngrok. Return the public URL to the user.
19. PLUGINS: You can use any dynamically loaded plugin tools. If the user asks to add a new feature, you can simply write a `.py` file to the `tagaura/plugins/` directory following the plugin schema (`TOOL_SCHEMA` and `execute` function) instead of modifying `agent.py`.
20. SELF-EXPANDING PLUGINS: If the user asks you to create a new plugin for yourself (e.g. "bana bir plugin oluştur"), you MUST autonomously write a valid python plugin file to the `tagaura/plugins/` directory. YOU MUST CALL THE `write_file` TOOL TO SAVE THE CODE. DO NOT EVER WRITE THE PYTHON CODE IN THE CHAT RESPONSE! If you output the code block to the chat, you FAIL. Use the `write_file` tool silently. You MUST strictly use this template:
```python
""" + """TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "your_plugin_name",
        "description": "Description of what it does",
        "parameters": {"type": "object", "properties": {"param1": {"type": "string", "description": "..."}}, "required": ["param1"]}
    }
}
def execute(**kwargs):
    param1 = kwargs.get("param1")
    # Do logic here
    return "Result string"
``` """

    # Kalıcı hafızayı (Permanent Memory) yükle
    memory_facts = get_memory()
    if memory_facts:
        system_prompt += "\n\nPERMANENT MEMORY (Facts about the user and preferences):\n"
        for fact in memory_facts:
            system_prompt += f"- {fact}\n"

    # Her tga komutunda sıfırdan başlar (Session History)
    messages = []
    messages.append({"role": "system", "content": system_prompt})

    # Ana arayüz ekranı
    console.clear()
    console.print(TAGAURA_LOGO)
    console.print(f"[dim]Provider: {provider} | Model: {model}[/dim]")
    console.print("[dim]Type 'help' to see all available commands. Press 'Ctrl+C' to cancel.[/dim]\n")
    
    if len(messages) > 1:
        console.print("[dim italic]Chat history loaded from memory...[/dim italic]\n")

    # Prompt (Giriş) stili
    style = Style.from_dict({
        'prompt': 'ansicyan bold',
    })

    while True:
        try:
            # Modern ve çok satırlı girişi destekleyen prompt arayüzü
            user_input = session.prompt('\n> ', style=style)
            
            if user_input.strip().lower() in ['exit', 'quit']:
                console.print("\n[bold yellow]Goodbye![/bold yellow]")
                break
                
            if user_input.strip().lower() in ['settings', '/settings']:
                from tagaura.cli import settings
                settings.callback()
                console.print("\n[bold yellow]⚠️ Please restart TagAura for the new settings to take effect (type 'exit' and then run 'tga' again).[/bold yellow]")
                continue
                
            if user_input.strip().lower() == 'help':
                console.print("\n[bold cyan]🛠️ TagAura Commands:[/bold cyan]")
                console.print("  [green]help[/green]       : Shows this help menu")
                console.print("  [green]exit[/green]       : Quits the TagAura session")
                console.print("  [green]settings[/green]   : Change the default AI provider and model")
                console.print("  [green]/voice[/green]     : Activates the microphone for Voice Command")
                console.print("  [green](Enter)[/green]    : Pressing Enter with empty input also activates Voice Command")
                console.print("")
                continue

            if not user_input.strip() or user_input.strip().lower() == '/voice':
                try:
                    import speech_recognition as sr
                    recognizer = sr.Recognizer()
                    with sr.Microphone() as source:
                        console.print("\n[bold cyan]🎙️ Dinleniyor... (Konuşun)[/bold cyan]")
                        recognizer.adjust_for_ambient_noise(source)
                        audio = recognizer.listen(source, timeout=5, phrase_time_limit=15)
                    console.print("[dim]🔄 Ses yazıya çevriliyor...[/dim]")
                    user_input = recognizer.recognize_google(audio, language="tr-TR")
                    console.print(f"[bold green]Sen (Sesli):[/bold green] {user_input}")
                except ImportError:
                    console.print("[red]Ses modülü eksik. Lütfen 'pip install SpeechRecognition pyaudio' komutunu çalıştırın.[/red]")
                    continue
                except sr.UnknownValueError:
                    console.print("[red]Ses anlaşılamadı. Lütfen tekrar deneyin.[/red]")
                    continue
                except sr.WaitTimeoutError:
                    console.print("[dim]Ses duyulmadı, dinleme iptal edildi.[/dim]")
                    continue
                except Exception as e:
                    console.print(f"[red]Mikrofon hatası: {e}[/red]")
                    continue

            # ÖNEMLİ İŞLEMLERDE ONAY KISMI (Human-in-the-loop)
            dangerous_keywords = ["sil", "kaldır", "format", "rm ", "delete"]
            if any(word in user_input.lower() for word in dangerous_keywords):
                confirm = questionary.confirm("This operation could be dangerous. Do you want to continue?", default=False).ask()
                if not confirm:
                    console.print("[red]Operation cancelled.[/red]")
                    continue

            messages.append({"role": "user", "content": user_input})

            # Modelden yanıt al
            
            # Eklentileri (Plugins) Dinamik (Hot-Reload) Yükle
            import importlib.util
            plugins_dir = os.path.join(os.path.dirname(__file__), "plugins")
            if not os.path.exists(plugins_dir):
                os.makedirs(plugins_dir)

            plugin_tools = []
            plugin_funcs = {}

            for filename in os.listdir(plugins_dir):
                if filename.endswith(".py"):
                    try:
                        filepath = os.path.join(plugins_dir, filename)
                        spec = importlib.util.spec_from_file_location(filename[:-3], filepath)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        
                        if hasattr(module, "TOOL_SCHEMA") and hasattr(module, "execute"):
                            plugin_tools.append(module.TOOL_SCHEMA)
                            plugin_funcs[module.TOOL_SCHEMA["function"]["name"]] = module.execute
                    except Exception as e:
                        console.print(f"[dim red]Plugin {filename} yüklenirken hata: {e}[/dim red]")
            
            # API'lerin desteklediği asıl model isimleriyle eşleme (Mistral vb.)
            api_model_name = model
            model_mappings = {
                "mistral-large-3": "mistral-large-latest",
                "mistral-large-2": "mistral-large-2407",
                "mistral-small-3": "mistral-small-latest",
                "mistral-medium-3": "mistral-medium-latest",
            }
            if model in model_mappings:
                api_model_name = model_mappings[model]

            litellm_model = api_model_name
            if "mistral" in provider_lower:
                litellm_model = f"mistral/{api_model_name}"
            elif "google" in provider_lower or "gemini" in provider_lower:
                litellm_model = f"gemini/{model}"
            elif "anthropic" in provider_lower or "claude" in provider_lower:
                litellm_model = f"anthropic/{model}"
            elif "deepseek" in provider_lower:
                litellm_model = f"deepseek/{model}"
            elif "openrouter" in provider_lower and not model.startswith("openrouter/"):
                litellm_model = f"openrouter/{model}"
            elif "z.ai" in provider_lower or "zhipu" in provider_lower:
                litellm_model = f"zhipu/{model}"
            elif "groq" in provider_lower:
                litellm_model = f"groq/{model}"
                
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "run_terminal_command",
                        "description": "Kullanıcının sisteminde (terminalde) bir komut çalıştırır. Dosya oluşturmak, disk, ağ veya port taraması yapmak için kullanıcıya kodu vermek yerine doğrudan bu aracı çağırarak komutu çalıştır.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "command": {
                                    "type": "string",
                                    "description": "Çalıştırılacak olan işletim sistemine uygun tam komut. (Örn: Get-Process)"
                                }
                            },
                            "required": ["command"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "memorize",
                        "description": "Kullanıcı hakkında önemli bir bilgi öğrenildiğinde (isim, yaş, işletim sistemi tercihleri, projeler, vb.) bu bilgiyi kalıcı hafızaya kaydeder.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "fact": {
                                    "type": "string",
                                    "description": "Kaydedilecek bilgi (Örn: 'Kullanıcının adı Ahmet' veya 'Kullanıcı Python kullanmayı sever')"
                                }
                            },
                            "required": ["fact"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "read_file",
                        "description": "Belirtilen dosyanın içeriğini okur.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "path": {
                                    "type": "string",
                                    "description": "Okunacak dosyanın tam yolu."
                                }
                            },
                            "required": ["path"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "write_file",
                        "description": "Belirtilen yola yeni bir dosya oluşturur ve içine metin yazar. Dosya zaten varsa üzerine yazar. Klasör yoksa otomatik oluşturulur.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "path": {
                                    "type": "string",
                                    "description": "Oluşturulacak dosyanın tam yolu."
                                },
                                "content": {
                                    "type": "string",
                                    "description": "Dosyanın içine yazılacak tam içerik."
                                }
                            },
                            "required": ["path", "content"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "replace_in_file",
                        "description": "Mevcut bir dosyadaki belirli bir metni bulur ve yenisiyle değiştirir. Sadece küçük düzeltmeler (healing) için kullanın.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "path": {
                                    "type": "string",
                                    "description": "Değiştirilecek dosyanın tam yolu."
                                },
                                "old_text": {
                                    "type": "string",
                                    "description": "Değiştirilmek istenen tam metin kısmı."
                                },
                                "new_text": {
                                    "type": "string",
                                    "description": "Yerine yazılacak yeni metin."
                                }
                            },
                            "required": ["path", "old_text", "new_text"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "search_web",
                        "description": "DuckDuckGo üzerinden web araması yapar ve en iyi sonuçların başlık, özet ve URL bilgilerini döndürür.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Arama sorgusu (Örn: 'React 19 yeni özellikler' veya 'Python ValueError çözümü')"
                                },
                                "max_results": {
                                    "type": "integer",
                                    "description": "Döndürülecek maksimum sonuç sayısı (Varsayılan: 5)"
                                }
                            },
                            "required": ["query"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "read_url",
                        "description": "Verilen bir URL adresine gidip web sayfasının içindeki tüm metin içeriğini (HTML etiketlerinden arındırılmış saf metni) okur.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "url": {
                                    "type": "string",
                                    "description": "Okunacak web sayfasının tam adresi (URL)"
                                }
                            },
                            "required": ["url"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "control_gui",
                        "description": "Bilgisayarın faresi ve klavyesi üzerinde fiziksel kontrol sağlar. Ekranda tıklama yapmak, yazı yazmak veya kısayol tuşlarına basmak için Python PyAutoGUI kodlarını (script) çalıştırır.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "action_script": {
                                    "type": "string",
                                    "description": "Çalıştırılacak PyAutoGUI python kodu. Örn: 'import pyautogui; pyautogui.click(100, 200); pyautogui.write(\"Hello\")'"
                                }
                            },
                            "required": ["action_script"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "run_background_task",
                        "description": "Belirli bir Python kodunu arka planda yeni bir işlem (Thread) olarak çalıştırır. Terminaldeki sohbeti dondurmadan arka planda sürekli çalışması gereken görevler, sunucular veya zamanlanmış (schedule) işlemler için kullanılır.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "task_name": {
                                    "type": "string",
                                    "description": "Görevin adı (Örn: 'HavaDurumu_Kontrol')"
                                },
                                "script": {
                                    "type": "string",
                                    "description": "Arka planda çalıştırılacak Python kodu. Sürekli çalışması için while döngüsü içerebilir veya 'schedule' modülü kullanabilir."
                                }
                            },
                            "required": ["task_name", "script"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "delegate_task",
                        "description": "Karmaşık bir problemi çözmek, kod incelemesi yaptırmak veya paralel bir araştırma yaptırmak için başka bir (Alt / Sub) Yapay Zeka ajanı yaratır ve ona görev verir. Bu ajan çalışıp sana sonuçları döndürür.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "agent_role": {
                                    "type": "string",
                                    "description": "Alt ajanın rolü (Örn: 'Senior Code Reviewer', 'Security Expert', 'Data Analyst')"
                                },
                                "task_description": {
                                    "type": "string",
                                    "description": "Alt ajanın yapması gereken görevin detaylı açıklaması."
                                }
                            },
                            "required": ["agent_role", "task_description"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "read_clipboard",
                        "description": "Kullanıcının panosundaki (kopyaladığı) metni okur.",
                        "parameters": {
                            "type": "object",
                            "properties": {}
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "write_clipboard",
                        "description": "Kullanıcının panosuna (kopyalama alanına) metin yazar.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "text": {"type": "string", "description": "Panoya kopyalanacak metin."}
                            },
                            "required": ["text"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "send_notification",
                        "description": "İşletim sisteminde sağ altta çıkan bir masaüstü bildirimi (Toast) gönderir.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string", "description": "Bildirim başlığı."},
                                "message": {"type": "string", "description": "Bildirim içeriği."}
                            },
                            "required": ["title", "message"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "watch_folder",
                        "description": "Bir klasörü izler. Klasöre yeni bir dosya eklendiğinde verilen Python kodunu çalıştırır.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "folder_path": {"type": "string", "description": "İzlenecek klasörün tam yolu."},
                                "script": {"type": "string", "description": "Yeni dosya eklendiğinde çalışacak Python kodu."}
                            },
                            "required": ["folder_path", "script"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "expose_localhost",
                        "description": "Yerel bilgisayardaki bir portu ngrok aracılığıyla tüm dünyaya açar ve genel bir internet adresi (URL) döndürür.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "port": {"type": "integer", "description": "İnternete açılacak yerel port numarası (Örn: 8000, 3000)"}
                            },
                            "required": ["port"]
                        }
                    }
                }
            ]

            # Yüklenen Plugin araçlarını listeye ekle
            try:
                tools.extend(plugin_tools)
            except:
                pass

            console.print("\n[dim cyan]Senin için buradayım. (Çıkmak için 'exit' veya 'quit' yazın)[/dim cyan]")

            MAX_ITERATIONS = 5
            for iteration in range(MAX_ITERATIONS):
                reply = ""
                tool_calls_buffer = {}
                
                with Live(Panel(Markdown(reply if reply else "Thinking..."), title="[bold green]✨ TagAura[/bold green]", title_align="left", border_style="green", padding=(1, 2)), refresh_per_second=15, console=console) as live:
                    try:
                        import time
                        
                        response = None
                        for attempt in range(3):
                            try:
                                if "openrouter" in provider_lower:
                                    from openai import OpenAI
                                    client = OpenAI(
                                        base_url="https://openrouter.ai/api/v1",
                                        api_key=os.environ.get("OPENROUTER_API_KEY", "")
                                    )
                                    # OpenRouter'a kendi model ismiyle direkt istek at (Örn: openai/gpt-oss-120b:free)
                                    response = client.chat.completions.create(
                                        model=model,
                                        messages=messages,
                                        stream=True,
                                        tools=tools,
                                        extra_headers={
                                            "HTTP-Referer": "https://tagaura.app",
                                            "X-Title": "TagAura"
                                        }
                                    )
                                else:
                                    response = litellm.completion(
                                        model=litellm_model,
                                        messages=messages,
                                        stream=True,
                                        tools=tools
                                    )
                                break
                            except Exception as e:
                                if "rate limit" in str(e).lower() or "429" in str(e):
                                    if attempt < 2:
                                        live.update(Panel(Markdown(f"⏳ API Rate Limit exceeded. Waiting 4 seconds before retrying... (Attempt {attempt+1}/3)"), title="[bold yellow]⚠️ Warning[/bold yellow]", border_style="yellow"))
                                        time.sleep(4)
                                        continue
                                raise e
                                
                        for chunk in response:
                            delta = chunk.choices[0].delta
                            
                            # Normal metin cevabı akıyorsa
                            if getattr(delta, 'content', None):
                                reply += delta.content
                                live.update(Panel(Markdown(reply), title="[bold green]✨ TagAura[/bold green]", title_align="left", border_style="green", padding=(1, 2)))
                            
                            # Eğer Tool Call (Fonksiyon çağrısı) geliyorsa
                            if getattr(delta, 'tool_calls', None):
                                for tc in delta.tool_calls:
                                    idx = getattr(tc, 'index', 0)
                                    if idx not in tool_calls_buffer:
                                        tool_calls_buffer[idx] = {
                                            "id": getattr(tc, 'id', None) or f"call_{idx}",
                                            "type": "function",
                                            "function": {"name": "", "arguments": ""}
                                        }
                                    if getattr(tc.function, 'name', None):
                                        if tc.function.name not in tool_calls_buffer[idx]["function"]["name"]:
                                            tool_calls_buffer[idx]["function"]["name"] += tc.function.name
                                    if getattr(tc.function, 'arguments', None):
                                        tool_calls_buffer[idx]["function"]["arguments"] += tc.function.arguments
                                        
                    except Exception as e:
                        reply = f"**Error occurred:** {str(e)}\n\nPlease check your API key or model name."
                        live.update(Panel(Markdown(reply), title="[bold red]❌ Error[/bold red]", border_style="red"))
                        break
                
                # Eğer Tool çağrısı yoksa döngüden çık
                if not tool_calls_buffer:
                    if reply:
                        messages.append({"role": "assistant", "content": reply})
                    break
                else:
                    # Tool çağrısı var!
                    tool_calls_list = []
                    for idx, tc in sorted(tool_calls_buffer.items()):
                        tool_calls_list.append({
                            "id": tc["id"],
                            "type": tc["type"],
                            "function": {
                                "name": tc["function"]["name"],
                                "arguments": tc["function"]["arguments"]
                            }
                        })
                    
                    messages.append({
                        "role": "assistant",
                        "content": reply if reply else None,
                        "tool_calls": tool_calls_list
                    })
                    
                    for tc in tool_calls_list:
                        func_name = tc["function"]["name"]
                        func_args_str = tc["function"]["arguments"]
                        
                        import json
                        try:
                            args = json.loads(func_args_str)
                        except:
                            args = {}
                        
                        if func_name == "run_terminal_command":
                            command = args.get("command", "")
                            
                            # Tehlikeli komut kontrolü (Regex ile tam kelime eşleşmesi)
                            import re
                            dangerous_keywords = [r"\brm\b", r"\brmdir\b", r"\bdel\b", r"\bremove-item\b", r"\bformat\b", r"\bdrop\b", r"\bkill\b", r"\bstop-process\b", r"\bclear-content\b", r"\brd\b"]
                            is_dangerous = any(re.search(kw, command, re.IGNORECASE) for kw in dangerous_keywords)
                            
                            if is_dangerous:
                                # Kullanıcıdan onay iste
                                console.print(f"\n[bold red]⚠️  WARNING: TagAura wants to run a potentially dangerous command:[/bold red]")
                                console.print(f"[cyan]{command}[/cyan]\n")
                                confirm = questionary.confirm("Do you want to run this command?").ask()
                            else:
                                confirm = True
                                console.print(f"\n[dim cyan]⚡ Running: {command}[/dim cyan]")
                            
                            if confirm:
                                try:
                                    if platform.system().lower() == "windows":
                                        import tempfile
                                        # Hata ve emoji (UTF-8) sorunlarını aşmak için geçici bir .ps1 dosyası kullanalım
                                        fd, temp_path = tempfile.mkstemp(suffix=".ps1")
                                        with open(temp_path, "w", encoding="utf-8-sig") as f:
                                            # Çıktının da UTF-8 olmasını zorla
                                            f.write("[Console]::OutputEncoding = [System.Text.Encoding]::UTF8\n" + command)
                                        os.close(fd)
                                        
                                        result = subprocess.run(
                                            ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", temp_path],
                                            capture_output=True,
                                            text=True,
                                            encoding="utf-8"
                                        )
                                        os.remove(temp_path)
                                    else:
                                        result = subprocess.run(command, shell=True, capture_output=True, text=True)
                                        
                                    output = result.stdout
                                    if result.stderr:
                                        output += "\n[STDERR]:\n" + result.stderr
                                        
                                    if result.returncode != 0:
                                        output += f"\n[ÇIKIŞ KODU]: {result.returncode} (HATA!)"
                                        
                                    if not output.strip():
                                        output = "Command executed successfully (No output)."
                                        
                                    if len(output) > 3000:
                                        output = output[:3000] + "\n\n... [OUTPUT TRUNCATED - Only showing the first 3000 characters]"
                                        
                                except Exception as e:
                                    output = f"Critical error while executing command: {str(e)}"
                            else:
                                output = "User denied command execution."
                                console.print("[dim red]Command cancelled.[/dim red]")
                                
                        elif func_name == "memorize":
                            fact = args.get("fact", "")
                            if fact:
                                add_to_memory(fact)
                                console.print(f"\n[dim yellow]🧠 New fact saved to permanent memory: {fact}[/dim yellow]")
                                output = "Fact successfully added to permanent memory."
                            else:
                                output = "Error: 'fact' parameter is empty."
                                
                        elif func_name == "read_file":
                            path = args.get("path", "")
                            try:
                                with open(path, "r", encoding="utf-8") as f:
                                    output = f.read()
                                console.print(f"\n[dim cyan]📄 File read: {path}[/dim cyan]")
                            except Exception as e:
                                output = f"Error: {str(e)}"
                                
                        elif func_name == "write_file":
                            path = args.get("path", "")
                            content = args.get("content", "")
                            try:
                                os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
                                with open(path, "w", encoding="utf-8") as f:
                                    f.write(content)
                                console.print(f"\n[dim green]📝 File created: {path}[/dim green]")
                                output = "File written successfully."
                            except Exception as e:
                                output = f"Error: {str(e)}"
                                
                        elif func_name == "replace_in_file":
                            path = args.get("path", "")
                            old_text = args.get("old_text", "")
                            new_text = args.get("new_text", "")
                            try:
                                with open(path, "r", encoding="utf-8") as f:
                                    content = f.read()
                                if old_text in content:
                                    content = content.replace(old_text, new_text)
                                    with open(path, "w", encoding="utf-8") as f:
                                        f.write(content)
                                    console.print(f"\n[dim yellow]🛠️ File edited (Auto-heal): {path}[/dim yellow]")
                                    output = "Replacement successful."
                                else:
                                    output = "Error: Target 'old_text' not found in file."
                            except Exception as e:
                                output = f"Error: {str(e)}"
                                
                        elif func_name == "search_web":
                            query = args.get("query", "")
                            max_results = args.get("max_results", 5)
                            try:
                                from ddgs import DDGS
                                console.print(f"\n[dim cyan]🔍 Webde aranıyor: {query}[/dim cyan]")
                                results = DDGS().text(query, max_results=max_results)
                                output = json.dumps(list(results), indent=2, ensure_ascii=False)
                            except Exception as e:
                                output = f"Arama hatası: {str(e)}"
                                
                        elif func_name == "read_url":
                            url = args.get("url", "")
                            try:
                                import requests
                                from bs4 import BeautifulSoup
                                console.print(f"\n[dim cyan]🌐 Sayfa okunuyor: {url}[/dim cyan]")
                                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                                resp = requests.get(url, headers=headers, timeout=10)
                                resp.raise_for_status()
                                soup = BeautifulSoup(resp.text, "html.parser")
                                # Sadece metin içeren kısımları al
                                output = soup.get_text(separator=' ', strip=True)
                                if len(output) > 15000:
                                    output = output[:15000] + "\n\n... [SAYFA ÇOK UZUN, KESİLDİ]"
                            except Exception as e:
                                output = f"Sayfa okuma hatası: {str(e)}"
                                
                        elif func_name == "control_gui":
                            action_script = args.get("action_script", "")
                            try:
                                import pyautogui
                                console.print("\n[dim magenta]🖱️  GUI Automating...[/dim magenta]")
                                local_env = {"pyautogui": pyautogui}
                                exec(action_script, globals(), local_env)
                                output = "GUI action executed successfully."
                            except Exception as e:
                                output = f"GUI error: {str(e)}"
                                
                        elif func_name == "run_background_task":
                            task_name = args.get("task_name", "Unknown_Task")
                            script = args.get("script", "")
                            try:
                                import threading
                                def bg_job(name, code):
                                    try:
                                        exec(code, globals())
                                    except Exception as e:
                                        with open(f"tagaura_bg_{name}_error.log", "w", encoding="utf-8") as f:
                                            f.write(str(e))
                                            
                                t = threading.Thread(target=bg_job, args=(task_name, script), daemon=True)
                                t.start()
                                console.print(f"\n[dim magenta]⏳ Background Task Started: {task_name}[/dim magenta]")
                                output = f"Task '{task_name}' successfully started in the background."
                            except Exception as e:
                                output = f"Failed to start background task: {str(e)}"
                                
                        elif func_name == "delegate_task":
                            agent_role = args.get("agent_role", "Assistant")
                            task_description = args.get("task_description", "")
                            try:
                                console.print(f"\n[dim magenta]🤖 Spawning Sub-Agent [{agent_role}]...[/dim magenta]")
                                sub_messages = [
                                    {"role": "system", "content": f"You are a specialized AI Sub-Agent. Your role is: {agent_role}. Solve the task efficiently and strictly provide the requested output. Do NOT use markdown code blocks if the user prohibits it, follow the prompt."},
                                    {"role": "user", "content": task_description}
                                ]
                                
                                if "openrouter" in provider_lower:
                                    sub_resp = client.chat.completions.create(
                                        model=model,
                                        messages=sub_messages,
                                        extra_headers={"HTTP-Referer": "https://tagaura.app", "X-Title": "TagAura"}
                                    )
                                    sub_output = sub_resp.choices[0].message.content
                                else:
                                    sub_resp = litellm.completion(
                                        model=litellm_model,
                                        messages=sub_messages
                                    )
                                    sub_output = sub_resp.choices[0].message.content
                                    
                                output = f"Sub-Agent '{agent_role}' completed the task. Result:\n{sub_output}"
                                console.print(f"[dim green]✅ Sub-Agent [{agent_role}] finished successfully.[/dim green]")
                            except Exception as e:
                                output = f"Failed to delegate task: {str(e)}"
                                
                        elif func_name == "read_clipboard":
                            try:
                                import pyperclip
                                output = pyperclip.paste()
                                console.print(f"\n[dim cyan]📋 Clipboard Read: {len(output)} chars[/dim cyan]")
                            except Exception as e:
                                output = f"Error reading clipboard: {str(e)}"
                                
                        elif func_name == "write_clipboard":
                            text = args.get("text", "")
                            try:
                                import pyperclip
                                pyperclip.copy(text)
                                console.print("\n[dim cyan]📋 Clipboard Written.[/dim cyan]")
                                output = "Text copied to clipboard successfully."
                            except Exception as e:
                                output = f"Error writing to clipboard: {str(e)}"
                                
                        elif func_name == "send_notification":
                            title = args.get("title", "TagAura")
                            message = args.get("message", "")
                            try:
                                from plyer import notification
                                notification.notify(
                                    title=title,
                                    message=message,
                                    app_name="TagAura",
                                    timeout=10
                                )
                                console.print(f"\n[dim yellow]🔔 Notification Sent: {title}[/dim yellow]")
                                output = "Notification sent successfully."
                            except Exception as e:
                                output = f"Error sending notification: {str(e)}"
                                
                        elif func_name == "watch_folder":
                            folder_path = args.get("folder_path", "")
                            script = args.get("script", "")
                            try:
                                import threading
                                import time
                                from watchdog.observers import Observer
                                from watchdog.events import FileSystemEventHandler
                                
                                class CustomHandler(FileSystemEventHandler):
                                    def on_created(self, event):
                                        if not event.is_directory:
                                            local_env = {"event": event}
                                            try:
                                                exec(script, globals(), local_env)
                                            except Exception as e:
                                                with open("tagaura_watchdog_error.log", "a", encoding="utf-8") as f:
                                                    f.write(f"Error processing {event.src_path}: {str(e)}\n")
                                                    
                                def start_watching(path, handler):
                                    observer = Observer()
                                    observer.schedule(handler, path, recursive=False)
                                    observer.start()
                                    try:
                                        while True:
                                            time.sleep(1)
                                    except:
                                        observer.stop()
                                    observer.join()
                                    
                                handler = CustomHandler()
                                t = threading.Thread(target=start_watching, args=(folder_path, handler), daemon=True)
                                t.start()
                                console.print(f"\n[dim magenta]👁️ Started watching folder: {folder_path}[/dim magenta]")
                                output = f"Started watching '{folder_path}' successfully in background."
                            except Exception as e:
                                output = f"Error starting folder watch: {str(e)}"
                                
                        elif func_name == "expose_localhost":
                            port = args.get("port", 80)
                            try:
                                from pyngrok import ngrok
                                public_url = ngrok.connect(port)
                                console.print(f"\n[dim green]🌍 Localhost exposed: {public_url.public_url}[/dim green]")
                                output = f"Successfully exposed port {port}. Public URL: {public_url.public_url}"
                            except Exception as e:
                                output = f"Error exposing localhost: {str(e)}\n(Note: You may need to authenticate ngrok first using 'tga run_terminal_command ngrok config add-authtoken <token>')"
                                
                        elif func_name in plugin_funcs:
                            try:
                                console.print(f"\n[dim magenta]🧩 Running Plugin: {func_name}[/dim magenta]")
                                output = str(plugin_funcs[func_name](**args))
                            except Exception as e:
                                output = f"Plugin execution error: {str(e)}"
                            
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "name": func_name,
                            "content": output
                        })
                    # Tool çağrısı bittikten sonra döngü başa döner ve LLM'e tekrar istek atılır (sonucu yorumlaması için)

        except KeyboardInterrupt:
            continue
        except EOFError:
            break
