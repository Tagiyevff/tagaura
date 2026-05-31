import os
import tempfile
import psutil
from rich.console import Console
from rich.table import Table

console = Console()

def clean_system():
    console.print("[bold cyan]Sistem temizliği başlatılıyor...[/bold cyan]")
    temp_dir = tempfile.gettempdir()
    deleted_size = 0
    deleted_files = 0
    
    try:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    size = os.path.getsize(file_path)
                    os.remove(file_path)
                    deleted_size += size
                    deleted_files += 1
                except Exception:
                    pass # Bazı dosyalar kullanımda olabilir, atla.
                    
        mb_freed = deleted_size / (1024 * 1024)
        console.print(f"[bold green]Başarılı! {deleted_files} dosya silindi.[/bold green]")
        console.print(f"[bold green]Kazanılan alan: {mb_freed:.2f} MB[/bold green]")
    except Exception as e:
        console.print(f"[red]Temizlik sırasında hata oluştu: {e}[/red]")

def process_monitor():
    console.print("[bold cyan]Aktif Süreçler Taranıyor...[/bold cyan]")
    table = Table(title="Sistem Süreçleri (En Yüksek Bellek Kullanımı)")
    table.add_column("PID", style="cyan")
    table.add_column("İsim", style="green")
    table.add_column("Bellek (MB)", style="yellow")
    table.add_column("Durum", style="magenta")
    
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'status']):
            try:
                mem_mb = proc.info['memory_info'].rss / (1024 * 1024)
                processes.append((proc.info['pid'], proc.info['name'], mem_mb, proc.info['status']))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
                
        # Bellek kullanımına göre sırala ve ilk 10'u göster
        processes.sort(key=lambda x: x[2], reverse=True)
        
        for p in processes[:10]:
            table.add_row(str(p[0]), p[1], f"{p[2]:.2f}", p[3])
            
        console.print(table)
    except Exception as e:
        console.print(f"[red]Süreçler alınırken hata oluştu: {e}[/red]")
