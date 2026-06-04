# Örnek Eklenti (Plugin) Dosyası
# Bu dosya TagAura başlarken otomatik olarak okunur ve sisteme yeni bir araç olarak eklenir.

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "say_hello_plugin",
        "description": "Örnek bir eklentidir. Kullanıcıya özel bir eklenti mesajı döndürür.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
}

def execute(**kwargs):
    # TagAura bu aracı çağırdığında bu fonksiyon çalışır.
    return "Merhaba! Ben senin 'plugins' klasörüne attığın ilk eklentiyim. Sistem başarıyla beni tanıdı ve çalıştırdı!"
