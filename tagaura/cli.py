import click
import questionary
from rich.console import Console
from tagaura.config import get_config, set_config
from tagaura.constants import PROVIDERS
from tagaura.agent import start_chat
from tagaura.tools.network import network_scan
from tagaura.tools.system import clean_system, process_monitor
from tagaura.tools.crypto import backup_folder

console = Console()

def setup_wizard():
    pass # Artık kullanılmıyor, main içerisinde sorulacak.

@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    # Eğer alt komut girilmediyse sohbeti başlat
    if ctx.invoked_subcommand is None:
        console.print("[bold green]Welcome to TagAura![/bold green]")
        
        provider = get_config("default_provider")
        model = get_config("default_model")
        
        if not provider or not model:
            provider = questionary.select(
                "Please select a model provider (This will be saved):",
                choices=list(PROVIDERS.keys())
            ).ask()
            
            if not provider:
                return

            model = questionary.select(
                f"Select a model for {provider}:",
                choices=PROVIDERS[provider]
            ).ask()
            
            if not model:
                return
                
            set_config("default_provider", provider)
            set_config("default_model", model)

        # API Key kontrolü
        provider_lower = provider.split()[0].lower()
        api_key = get_config(f"{provider_lower}_api_key")
        
        if not api_key:
            api_key = questionary.password(f"Please enter your {provider} API key:").ask()
            if api_key:
                set_config(f"{provider_lower}_api_key", api_key)
                
        if not api_key:
            console.print("[red]API key not provided. Exiting.[/red]")
            return
            
        start_chat(provider, model, api_key)

@main.command()
def settings():
    """Resets/changes default model and provider settings."""
    console.print("[bold yellow]Settings Menu[/bold yellow]")
    provider = questionary.select(
        "Please select your new default model provider:",
        choices=list(PROVIDERS.keys())
    ).ask()
    if not provider: return
    
    model = questionary.select(
        f"Select the new model for {provider}:",
        choices=PROVIDERS[provider]
    ).ask()
    if not model: return
    
    set_config("default_provider", provider)
    set_config("default_model", model)
    
    provider_lower = provider.split()[0].lower()
    api_key = get_config(f"{provider_lower}_api_key")
    if api_key:
        change_key = questionary.confirm(f"There is already a saved API key for {provider}. Do you want to change it?", default=False).ask()
        if change_key:
            new_key = questionary.password("Enter new API key:").ask()
            if new_key: set_config(f"{provider_lower}_api_key", new_key)
    else:
        new_key = questionary.password(f"Please enter your {provider} API key:").ask()
        if new_key: set_config(f"{provider_lower}_api_key", new_key)
        
    console.print("[bold green]Settings saved successfully! Type 'tga' to start chatting.[/bold green]")

# Sistem Araçları Komutları
@main.command()
def scan_network():
    """Ağ bağlantılarını ve açık portları tarar."""
    network_scan()

@main.command()
def clean():
    """Sistemdeki gereksiz dosyaları (temp) temizler."""
    clean_system()

@main.command()
def processes():
    """Şüpheli veya aktif süreçleri listeler."""
    process_monitor()

@main.command()
@click.argument('source')
@click.argument('destination')
@click.option('--password', prompt=True, hide_input=True)
def backup(source, destination, password):
    """Bir klasörü şifreler ve yedekler."""
    backup_folder(source, destination, password)

if __name__ == '__main__':
    main()
