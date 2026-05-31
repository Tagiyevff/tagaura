import psutil
from rich.console import Console
from rich.table import Table

console = Console()

def network_scan():
    console.print("[bold cyan]Ağ Bağlantıları ve Açık Portlar Taranıyor...[/bold cyan]")
    
    table = Table(title="Aktif Ağ Bağlantıları")
    table.add_column("Protokol", style="magenta")
    table.add_column("Yerel Adres", style="green")
    table.add_column("Uzak Adres", style="yellow")
    table.add_column("Durum", style="blue")
    
    try:
        connections = psutil.net_connections(kind='inet')
        for conn in connections:
            if conn.status == 'ESTABLISHED' or conn.status == 'LISTEN':
                laddr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else ""
                raddr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else ""
                protocol = "TCP" if conn.type == 1 else "UDP"
                table.add_row(protocol, laddr, raddr, conn.status)
                
        console.print(table)
    except Exception as e:
        console.print(f"[red]Ağ bilgileri alınırken hata oluştu: {e}[/red]")
