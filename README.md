# PC Cep Asistanı

Windows için hafif bir bilgisayar bilgi ve tanılama aracı.

## Özellikler
- İşlemci, çekirdek ve hız bilgisi
- RAM kullanımını görüntüleme
- Sistem diskinin doluluk durumunu görüntüleme
- Ekran kartı adını gösterme
- Pil yüzdesi ve şarj durumunu gösterme (destekleniyorsa)
- Bilgileri TXT raporu olarak dışa aktarma
- Tek tıkla yenileme

Uygulama salt okunurdur; dosya silmez, kayıt defterini değiştirmez ve sistem ayarlarına dokunmaz.

## Çalıştırma (Python ile)
```bash
py -m pip install -r requirements.txt
py main.py
```

## EXE oluşturma
```bash
py -m pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --onefile --windowed --name PCCepAsistani main.py
```
EXE dosyası `dist/PCCepAsistani.exe` içine çıkar.

## GitHub Actions
`main` dalına kod gönderildiğinde Windows üzerinde EXE otomatik derlenir. Çıktıyı Actions sekmesindeki başarılı çalışmanın **Artifacts** bölümünden indirebilirsin.
