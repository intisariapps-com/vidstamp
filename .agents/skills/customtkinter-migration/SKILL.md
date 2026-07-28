---
name: customtkinter-migration
description: Panduan migrasi aman widget GUI Tkinter klasik ke CustomTkinter modern untuk VidStamp.
---

# Panduan Migrasi CustomTkinter (VidStamp)

Dokumen ini berisi standar migrasi antarmuka pengguna (GUI) dari Tkinter klasik bawaan ke library CustomTkinter (`ctk`) untuk mencapai estetika UI modern (Dark Mode premium, sudut melengkung, dan komponen bergaya).

## 1. Persiapan Lingkungan & Impor
Pastikan `customtkinter` terpasang di virtual environment. Gunakan alias `ctk` secara konsisten.

```python
import customtkinter as ctk
```

## 2. Inisialisasi Tema & Jendela Utama
Konfigurasikan tema gelap/terang global sebelum menginisialisasi jendela utama:

```python
ctk.set_appearance_mode("Dark")  # Pilihan: "System", "Dark", "Light"
ctk.set_default_color_theme("blue")  # Pilihan tema bawaan: "blue", "green", "dark-blue"
```

Ubah kelas jendela utama untuk mewarisi `ctk.CTk` alih-alih `tk.Tk`:

```python
class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("VidStamp - Video Timestamp & Marker")
        self.geometry("1200x800")
```

## 3. Pemetaan Komponen (Widget Mapping)
Ganti widget Tkinter bawaan dengan widget CustomTkinter yang setara:

| Widget Klasik (`tk`/`ttk`) | Widget CustomTkinter (`ctk`) | Catatan Penting |
| :--- | :--- | :--- |
| `tk.Frame` / `ttk.Frame` | `ctk.CTkFrame` | Mendukung `corner_radius` dan `fg_color`. |
| `tk.Label` / `ttk.Label` | `ctk.CTkLabel` | Gunakan parameter `text_color` untuk warna kustom. |
| `tk.Button` / `ttk.Button` | `ctk.CTkButton` | Mendukung `hover_color`, `corner_radius`, dan `image`. |
| `tk.Entry` / `ttk.Entry` | `ctk.CTkEntry` | Mendukung placeholder teks. |
| `tk.Text` | `ctk.CTkTextbox` | Komponen teks multiline CustomTkinter yang dapat discroll. |
| `ttk.Scale` / `tk.Scale` | `ctk.CTkSlider` | Slider interaktif yang sangat halus. |
| `ttk.Progressbar` | `ctk.CTkProgressBar` | Indikator progres modern. |

## 4. Sinkronisasi Thread Pemutaran Video OpenCV
Salah satu tantangan terbesar adalah memperbarui canvas frame OpenCV di CustomTkinter tanpa memblokir thread UI.
* **Canvas Rendering**: Jangan gunakan `tk.Canvas` biasa jika ingin performa terbaik. Tetap gunakan `tk.Canvas` (atau `ctk.CTkCanvas`) untuk me-render array gambar OpenCV via `PIL.ImageTk.PhotoImage`.
* **Threading**: Loop rendering video OpenCV harus tetap berjalan di thread terpisah atau dipicu menggunakan metode `.after()` Tkinter agar UI tetap responsif.
* **Anti-Blocking**: Hindari pemanggilan `update_idletasks()` yang berulang-ulang di loop pemutaran video karena dapat menyebabkan stuttering (patah-patah) di CustomTkinter.

## 5. Contoh Implementasi Frame Kontrol Pemutar

```python
class PlayerControls(ctk.CTkFrame):
    def __init__(self, parent, play_callback):
        super().__init__(parent, corner_radius=10)
        
        # Tombol Play dengan ikon unicode minimalis
        self.btn_play = ctk.CTkButton(
            self, 
            text="▶", 
            width=40, 
            height=30,
            corner_radius=6,
            command=play_callback
        )
        self.btn_play.pack(side="left", padx=5, pady=5)
        
        # Slider Posisi Video
        self.slider = ctk.CTkSlider(
            self, 
            from_=0, 
            to=100, 
            number_of_steps=1000
        )
        self.slider.pack(side="fill", expand=True, padx=10)
```
