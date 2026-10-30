import os
import sys
import platform
import socket
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

import psutil

APP_NAME = "PC Cep Asistanı"
APP_VERSION = "1.1.3"
IS_WINDOWS = platform.system() == "Windows"

# Pencereli (--windowed) EXE'de alt süreçlerin siyah konsol penceresi açmaması için
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def tr_upper(text):
    """Türkçe büyük harf: i→İ, ı→I (str.upper() 'BILGISAYAR' üretir)."""
    return text.replace("i", "İ").replace("ı", "I").upper()


def bytes_gb(value):
    return f"{value / (1024 ** 3):.1f} GB"


def _run(cmd, timeout=6):
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                            creationflags=_NO_WINDOW, errors="replace")
    return [x.strip() for x in result.stdout.splitlines() if x.strip()]


_gpu_cache = None


def get_gpu_name():
    """Ekran kartı adı değişmez; PowerShell'i her yenilemede çalıştırmamak için önbelleğe al."""
    global _gpu_cache
    if _gpu_cache is None:
        _gpu_cache = _query_gpu_name()
    return _gpu_cache


def _query_gpu_name():
    if not IS_WINDOWS:
        return "Yalnızca Windows'ta gösterilir"
    # wmic, Windows 11 24H2 ve sonrasında varsayılan olarak kaldırıldı; önce PowerShell/CIM dene.
    commands = [
        ["powershell", "-NoProfile", "-NonInteractive", "-Command",
         "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name"],
        ["wmic", "path", "win32_VideoController", "get", "name"],
    ]
    for cmd in commands:
        try:
            names = [x for x in _run(cmd) if x.lower() != "name"]
            if names:
                return ", ".join(dict.fromkeys(names))
        except Exception:
            continue
    return "Bilgi alınamadı"


def get_cpu_name():
    if IS_WINDOWS:
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as key:
                return winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
        except Exception:
            pass
    return platform.processor() or platform.machine() or "Bilinmiyor"


def get_os_name():
    if IS_WINDOWS:
        version = platform.version()  # ör. 10.0.22631
        try:
            build = int(version.split(".")[2])
        except (IndexError, ValueError):
            build = 0
        release = "11" if build >= 22000 else platform.release()
        edition = ""
        try:
            edition = platform.win32_edition() or ""
        except Exception:
            pass
        if "server" in edition.lower():
            name = "Windows Server"
            edition = edition.replace("Server", "").strip()
        else:
            name = f"Windows {release}"
        return f"{name} {edition} (derleme {build or version})".replace("  ", " ")
    return f"{platform.system()} {platform.release()}"


def get_local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))  # paket gönderilmez, yalnızca yerel arayüz seçilir
            return s.getsockname()[0]
    except OSError:
        return "Ağ bağlantısı yok"


def get_uptime():
    seconds = int(datetime.now().timestamp() - psutil.boot_time())
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    return f"{days} gün {hours} saat {rem // 60} dk" if days else f"{hours} saat {rem // 60} dk"


def collect_info():
    vm = psutil.virtual_memory()
    disk = psutil.disk_usage(os.path.abspath(os.sep))
    battery = psutil.sensors_battery()
    try:
        freq = psutil.cpu_freq()
        cpu_speed = f"{freq.current / 1000:.2f} GHz" if freq else "Bilinmiyor"
    except Exception:
        cpu_speed = "Bilinmiyor"

    return {
        "Bilgisayar": f"{socket.gethostname()} — açık kalma: {get_uptime()}",
        "İşletim sistemi": get_os_name(),
        "İşlemci": get_cpu_name(),
        "Çekirdek": f"{psutil.cpu_count(logical=False) or '?'} fiziksel / {psutil.cpu_count(logical=True) or '?'} mantıksal",
        "İşlemci hızı": cpu_speed,
        "RAM": f"{bytes_gb(vm.used)} kullanılıyor / {bytes_gb(vm.total)} toplam ({vm.percent:.0f}%)",
        "Disk": f"{bytes_gb(disk.used)} kullanılıyor / {bytes_gb(disk.total)} toplam ({disk.percent:.0f}%)",
        "Ekran kartı": get_gpu_name(),
        "Pil": (f"%{battery.percent:.0f}" + (" - Şarj oluyor" if battery.power_plugged else " - Pilde"))
               if battery else "Masaüstü bilgisayar veya pil bilgisi yok",
        "Yerel IP": get_local_ip(),
    }

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw()  # içerik hazır olana kadar boş pencere gösterme
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.configure(bg="#101827")
        self.info = {}
        self._style()
        self._build()
        self.refresh()
        self._fit_window()

    def _fit_window(self):
        """Pencereyi içeriğin gerçek boyutuna göre aç ve ekranın ortasına yerleştir
        (sabit boyut, DPI ölçeklemede metinlerin kesilmesine yol açıyordu)."""
        self.update_idletasks()
        w = max(self.winfo_reqwidth(), 720)
        h = self.winfo_reqheight()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h = min(w, sw - 40), min(h, sh - 80)  # görev çubuğu payı
        x, y = max((sw - w) // 2, 0), max((sh - h - 40) // 2, 0)
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.minsize(min(w, 640), min(h, sh - 80))
        self.deiconify()

    def _style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#101827")
        style.configure("TLabel", background="#101827", foreground="#e5e7eb", font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 22, "bold"), foreground="#ffffff")
        style.configure("Sub.TLabel", foreground="#9ca3af", font=("Segoe UI", 10))
        style.configure("Card.TFrame", background="#1c293b")
        style.configure("CardTitle.TLabel", background="#1c293b", foreground="#93c5fd",
                        font=("Segoe UI", 10, "bold"))
        style.configure("CardValue.TLabel", background="#1c293b", foreground="#f9fafb",
                        font=("Segoe UI", 11))
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), padding=9,
                        background="#3b82f6", foreground="#ffffff",
                        bordercolor="#3b82f6", lightcolor="#3b82f6", darkcolor="#3b82f6",
                        focuscolor="#3b82f6")
        style.map("Accent.TButton",
                  background=[("pressed", "#1d4ed8"), ("active", "#2563eb")],
                  lightcolor=[("active", "#2563eb")], darkcolor=[("active", "#2563eb")])

    def _build(self):
        root = ttk.Frame(self, padding=18)
        root.pack(fill="both", expand=True)

        header = ttk.Frame(root)
        header.pack(fill="x", pady=(0, 18))
        ttk.Label(header, text="PC Cep Asistanı", style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, text="Bilgisayarının durumunu tek ekranda gör.",
                  style="Sub.TLabel").pack(anchor="w", pady=(4, 0))

        self.status = ttk.Label(root, text="Hazırlanıyor...", style="Sub.TLabel")
        self.status.pack(anchor="w", pady=(0, 12))

        self.cards = ttk.Frame(root)
        self.cards.pack(fill="both", expand=True)
        self.labels = {}
        for i, key in enumerate(["Bilgisayar", "İşletim sistemi", "İşlemci",
                                 "Çekirdek", "İşlemci hızı", "RAM", "Disk",
                                 "Ekran kartı", "Pil", "Yerel IP"]):
            card = ttk.Frame(self.cards, style="Card.TFrame", padding=(13, 10))
            card.grid(row=i // 2, column=i % 2, sticky="nsew",
                      padx=(0, 8) if i % 2 == 0 else (8, 0), pady=5)
            ttk.Label(card, text=tr_upper(key), style="CardTitle.TLabel").pack(anchor="w")
            value = ttk.Label(card, text="—", style="CardValue.TLabel",
                              wraplength=290, justify="left")
            value.pack(anchor="w", pady=(5, 0))
            self.labels[key] = value

        self.cards.columnconfigure(0, weight=1)
        self.cards.columnconfigure(1, weight=1)
        for row in range(5):
            self.cards.rowconfigure(row, weight=1)

        footer = ttk.Frame(root)
        footer.pack(fill="x", pady=(17, 0))
        ttk.Button(footer, text="↻ Yenile", style="Accent.TButton",
                   command=self.refresh).pack(side="left")
        ttk.Button(footer, text="Raporu dışa aktar", style="Accent.TButton",
                   command=self.export_report).pack(side="right")
        ttk.Label(root, text="Not: Bu uygulama yalnızca bilgi okur; sistem ayarlarını değiştirmez.",
                  style="Sub.TLabel").pack(anchor="w", pady=(14, 0))

    def refresh(self):
        self.status.configure(text="Bilgiler okunuyor...")
        self.update_idletasks()
        try:
            self.info = collect_info()
            for key, value in self.info.items():
                self.labels[key].configure(text=value)
            self.status.configure(text=f"Son güncelleme: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        except Exception as exc:
            self.status.configure(text="Bilgiler alınamadı.")
            messagebox.showerror("Hata", f"Sistem bilgileri alınamadı:\n{exc}")

    def export_report(self):
        if not self.info:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Metin dosyası", "*.txt")],
            initialfile="pc-raporu.txt"
        )
        if not path:
            return
        try:
            write_report(path, self.info)
            messagebox.showinfo("Tamamlandı", "Sistem raporu kaydedildi.")
        except OSError as exc:
            messagebox.showerror("Kayıt hatası", str(exc))


def write_report(path, info):
    lines = [f"{APP_NAME} v{APP_VERSION} - Sistem Raporu",
             f"Oluşturulma: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}", ""]
    lines.extend(f"{key}: {value}" for key, value in info.items())
    # utf-8-sig: Türkçe karakterler Windows Not Defteri'nde de doğru görünür
    with open(path, "w", encoding="utf-8-sig") as file:
        file.write("\n".join(lines) + "\n")


def enable_dpi_awareness():
    """Yüksek çözünürlüklü ekranlarda bulanık görüntüyü önler."""
    if not IS_WINDOWS:
        return
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


if __name__ == "__main__":
    # CI testi için: PCCepAsistani.exe --self-test rapor.txt  (pencere açmadan rapor yazar)
    if len(sys.argv) >= 3 and sys.argv[1] == "--self-test":
        write_report(sys.argv[2], collect_info())
        sys.exit(0)
    enable_dpi_awareness()
    App().mainloop()
