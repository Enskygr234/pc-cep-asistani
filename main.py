import os
import platform
import socket
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

import psutil

APP_NAME = "PC Cep Asistanı"

def bytes_gb(value):
    return f"{value / (1024 ** 3):.1f} GB"

def get_gpu_name():
    if platform.system() == "Windows":
        try:
            result = subprocess.run(
                ["wmic", "path", "win32_VideoController", "get", "name"],
                capture_output=True, text=True, timeout=4
            )
            names = [x.strip() for x in result.stdout.splitlines()
                     if x.strip() and x.strip().lower() != "name"]
            return ", ".join(names) if names else "Bilgi alınamadı"
        except Exception:
            return "Bilgi alınamadı"
    return "Windows için GPU bilgisi"

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
        "Bilgisayar": socket.gethostname(),
        "İşletim sistemi": f"{platform.system()} {platform.release()} ({platform.version()})",
        "İşlemci": platform.processor() or "Bilinmiyor",
        "Çekirdek": f"{psutil.cpu_count(logical=False) or '?'} fiziksel / {psutil.cpu_count(logical=True) or '?'} mantıksal",
        "İşlemci hızı": cpu_speed,
        "RAM": f"{bytes_gb(vm.used)} kullanılıyor / {bytes_gb(vm.total)} toplam ({vm.percent:.0f}%)",
        "Disk": f"{bytes_gb(disk.used)} kullanılıyor / {bytes_gb(disk.total)} toplam ({disk.percent:.0f}%)",
        "Ekran kartı": get_gpu_name(),
        "Pil": (f"%{battery.percent:.0f}" + (" - Şarj oluyor" if battery.power_plugged else " - Pilde"))
               if battery else "Masaüstü bilgisayar veya pil bilgisi yok",
        "Ağ adı": socket.gethostname(),
    }

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("760x620")
        self.minsize(650, 540)
        self.configure(bg="#101827")
        self.info = {}
        self._style()
        self._build()
        self.refresh()

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
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), padding=9)
        style.map("Accent.TButton", background=[("active", "#2563eb")])

    def _build(self):
        root = ttk.Frame(self, padding=22)
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
                                 "Ekran kartı", "Pil", "Ağ adı"]):
            card = ttk.Frame(self.cards, style="Card.TFrame", padding=13)
            card.grid(row=i // 2, column=i % 2, sticky="nsew",
                      padx=(0, 8) if i % 2 == 0 else (8, 0), pady=7)
            ttk.Label(card, text=key.upper(), style="CardTitle.TLabel").pack(anchor="w")
            value = ttk.Label(card, text="—", style="CardValue.TLabel",
                              wraplength=290, justify="left")
            value.pack(anchor="w", pady=(7, 0))
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
        try:
            self.info = collect_info()
            for key, value in self.info.items():
                self.labels[key].configure(text=value)
            self.status.configure(text=f"Son güncelleme: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        except Exception as exc:
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
        lines = [f"{APP_NAME} - Sistem Raporu",
                 f"Oluşturulma: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}", ""]
        lines.extend(f"{key}: {value}" for key, value in self.info.items())
        try:
            with open(path, "w", encoding="utf-8") as file:
                file.write("\n".join(lines))
            messagebox.showinfo("Tamamlandı", "Sistem raporu kaydedildi.")
        except OSError as exc:
            messagebox.showerror("Kayıt hatası", str(exc))

if __name__ == "__main__":
    App().mainloop()
