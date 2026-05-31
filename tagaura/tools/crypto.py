import os
import shutil
import base64
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from rich.console import Console

console = Console()

def generate_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key

def encrypt_file(file_path: str, password: str):
    try:
        # Rastgele salt oluştur
        salt = os.urandom(16)
        key = generate_key(password, salt)
        fernet = Fernet(key)
        
        with open(file_path, "rb") as f:
            data = f.read()
            
        encrypted_data = fernet.encrypt(data)
        
        # Salt'ı dosyanın başına ekle ki çözerken bilelim
        with open(file_path + ".tga", "wb") as f:
            f.write(salt + encrypted_data)
            
        return True
    except Exception as e:
        console.print(f"[red]Şifreleme hatası ({file_path}): {e}[/red]")
        return False

def backup_folder(source: str, destination: str, password: str):
    console.print(f"[bold cyan]{source} klasörü {destination} hedefine şifrelenerek yedekleniyor...[/bold cyan]")
    
    src_path = Path(source)
    dest_path = Path(destination)
    
    if not src_path.exists():
        console.print("[red]Kaynak klasör bulunamadı![/red]")
        return
        
    dest_path.mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    fail_count = 0
    
    # Tüm dosyaları gez ve şifreleyerek hedefe kopyala
    for root, dirs, files in os.walk(src_path):
        # Hedefteki alt klasör yapısını koru
        rel_path = Path(root).relative_to(src_path)
        current_dest_dir = dest_path / rel_path
        current_dest_dir.mkdir(parents=True, exist_ok=True)
        
        for file in files:
            src_file = os.path.join(root, file)
            # Geçici kopyalama ve şifreleme
            dest_file = os.path.join(current_dest_dir, file)
            shutil.copy2(src_file, dest_file)
            
            if encrypt_file(dest_file, password):
                os.remove(dest_file) # Orijinal şifresiz kopyayı sil, .tga uzantılısı kaldı
                success_count += 1
            else:
                fail_count += 1
                
    console.print(f"[bold green]Yedekleme Tamamlandı! Başarılı: {success_count}, Başarısız: {fail_count}[/bold green]")
