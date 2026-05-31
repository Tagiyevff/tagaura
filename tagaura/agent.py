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
    else:
        os.environ[f"{provider_lower.upper()}_API_KEY"] = api_key

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
4. ABSOLUTE PROHIBITION ON CODE BLOCKS: NEVER give the user code or scripts to run manually. Your conversational response MUST NOT contain ANY markdown code blocks (e.g., ```powershell, ```bash, or ```).
5. AUTONOMOUS EXECUTION: You MUST execute ALL system operations (like file creation, network scanning) YOURSELF by strictly using the `run_terminal_command` tool.
6. SELF-CORRECTION (DO NOT GIVE UP): If a tool command fails (e.g., folder not found, permission denied), DO NOT tell the user to fix it. Analyze the error and call the tool AGAIN to solve it yourself (e.g., create the missing folder first). Keep trying until you succeed.
7. SILENT SUCCESS: When an operation succeeds, just give a short one-sentence confirmation in the user's language. Do NOT show the long scripts or execution steps to the user.
8. IGNORE PAST TASKS: Do not bring up or summarize past completed tasks from the conversation history when the user just says hello or starts a new session. Focus only on their current message.
9. PERMANENT MEMORY: When the user tells you personal information (their name, age, preferences) or explicitly asks you to remember something, you MUST call the `memorize` tool to save it. Do not just say "I noted it", you must actually call the tool!
10. FILE OPERATIONS: You have native tools (`read_file`, `write_file`, `replace_in_file`) to create projects or fix code. ALWAYS use them instead of bash/powershell to write files!"""

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
    console.print("[dim]Type 'exit' or 'quit' to quit. Type 'settings' to change model. Press 'Ctrl+C' to cancel.[/dim]\n")
    
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
                
            if not user_input.strip():
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
                }
            ]

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
