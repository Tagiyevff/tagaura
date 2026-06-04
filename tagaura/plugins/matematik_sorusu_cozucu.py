# Bu eklenti, rastgele bir matematik sorusu üretir ve çözer.
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "matematik_sorusu_cozucu",
        "description": "Rastgele bir matematik sorusu (toplama, çıkarma, çarpma, bölme) üretir, çözer ve sonucu döndürür.",
        "parameters": {
            "type": "object", 
            "properties": {}
        }
    }
}

import random

def execute(**kwargs):
    # Rastgele işlem türü seç
    islemler = ['+', '-', '*', '/']
    islem = random.choice(islemler)
    
    # Rastgele sayılar üret (bölme için payda sıfır olmasın ve tam bölünebilir olsun)
    if islem == '/':
        payda = random.randint(1, 10)
        pay = payda * random.randint(1, 10)
        sayi1, sayi2 = pay, payda
    else:
        sayi1 = random.randint(1, 20)
        sayi2 = random.randint(1, 20)
    
    # Soruyu oluştur
    soru = f"{sayi1} {islem} {sayi2} kaçtır?"
    
    # Sonucu hesapla
    if islem == '+':
        sonuc = sayi1 + sayi2
    elif islem == '-':
        sonuc = sayi1 - sayi2
    elif islem == '*':
        sonuc = sayi1 * sayi2
    elif islem == '/':
        sonuc = sayi1 / sayi2
    
    # Sonucu döndür
    return f"Soru: {soru}\nCevap: {sonuc}"