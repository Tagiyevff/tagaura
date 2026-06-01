<div align="center">
  <h1>✨ TagAura</h1>
  <p><strong>A Next-Generation, Autonomous AI CLI Agent & System Administrator</strong></p>
</div>

TagAura is a powerful, autonomous CLI-based AI agent designed to run directly in your terminal. It goes beyond simple chat; it's a fully functional system administrator, developer, and automation tool. Powered by LiteLLM, it supports multiple top-tier models like Mistral, OpenAI, Anthropic, Gemini, and DeepSeek.

## 🚀 Features

* **🧠 Dual-Layer Memory Architecture:**
  * **Session Memory:** Keeps context during your current active session.
  * **Permanent Memory:** Learns facts about you, your projects, and your preferences, remembering them across restarts.
* **⚡ Autonomous System Execution:**
  TagAura executes commands directly on your system (with safety checks). You don't need to copy-paste scripts. It scans ports, checks active processes, and manages files on its own.
* **🛠️ Native File Operations (Scaffolding & Auto-Healing):**
  * **Scaffolding:** Can build full project directories (`index.html`, `style.css`, Python scripts) from scratch instantly without breaking shell encodings.
  * **Auto-Healing:** If a code it wrote crashes, it reads the error log, uses `replace_in_file` to fix the exact broken line, and reruns it autonomously.
* **🔐 Built-in System Tools (`tga` Commands):**
  * `tga scan_network`: Scan for active ports and network connections.
  * `tga clean`: Cleans up temporary system files to free space.
  * `tga processes`: Monitors and lists suspicious active processes.
  * `tga backup <source> <dest>`: Zips and AES-encrypts a folder securely.
* **⚙️ Smart Configuration & Settings:**
  Configures and caches your preferred AI model and API keys so you drop straight into the chat every time. Type `settings` to change them on the fly!
* **🌍 Multi-Language Support:**
  Adapts strictly to the language you speak. Ask in Turkish, it replies in Turkish. Ask in English, it switches instantly.

## 📦 Installation

**1. Clone the repository:**
```bash
git clone https://github.com/Tagiyevff/tagaura.git
cd tagaura
```

**2. Install via pip:**
```bash
pip install -e .
```

**3. Run the Agent:**
```bash
tga
```
*On first launch, it will guide you to select your preferred AI provider (Mistral, OpenAI, Gemini, etc.) and save your API key securely.*

## 💡 Usage Examples

**Inside the interactive TagAura terminal:**

* **Project Creation:**
  > "Create a folder named 'Portfolio' on my Desktop. Scaffold a fully working, dark-themed React application inside it."
* **Auto-Healing & Debugging:**
  > "Run the `app.py` script. If you get a SyntaxError, read the file, fix the line natively, and try running it again."
* **System Automation:**
  > "Show me all listening ports on my local machine and kill anything running on port 8080."
* **Memory Test:**
  > "My name is Ramin and I'm a developer. Remember this." (Later) -> "Who am I?"

## ⚙️ Commands

If you don't want to chat and just need a quick utility, TagAura acts as a CLI toolkit:
* `tga scan_network` - Network analysis
* `tga clean` - System temp cleaning
* `tga processes` - Process monitoring
* `tga settings` - Change your default LLM provider and model

## ⚠️ Security Warning

TagAura can execute real commands on your host operating system. While dangerous commands (like `rm`, `format`, `del`) are intercepted and require explicit human-in-the-loop (Y/N) confirmation, you should still supervise its actions carefully.
<img src="assets/logo.png" width="200" />

---
*Built with ❤️ for true autonomous terminal control.*
