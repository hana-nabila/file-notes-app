import customtkinter as ctk
import os
from tkinter import filedialog, messagebox
from datetime import datetime
from fpdf import FPDF
import shutil

# Set tema visual
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class FileNotesPro(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("FileNotes Pro - Aplikasi Catatan Digital")
        self.geometry("1150x750")
        
        # Inisialisasi folder penyimpanan
        self.notes_dir = "my_notes"
        if not os.path.exists(self.notes_dir):
            os.makedirs(self.notes_dir)
            
        self.current_file = None
        self.empty_label = None 
        self.configure(fg_color="#FFFFFF")

        # Layout Utama
        self.grid_columnconfigure(0, weight=0) 
        self.grid_columnconfigure(1, weight=1) 
        self.grid_columnconfigure(2, weight=3) 
        self.grid_rowconfigure(0, weight=1)

        self.setup_sidebar()
        self.setup_list_panel()
        self.setup_editor_panel()
        
        self.after(100, self.refresh_notes_list)

    # --- 1. SIDEBAR ---
    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#F8F9FA", border_width=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="MENU UTAMA", font=("Inter", 12, "bold"), text_color="#718096").pack(pady=(30,10), padx=25, anchor="w")
        
        self.menu_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.menu_container.pack(fill="x", padx=10)

    def sidebar_item(self, text, count, icon=""):
        frame = ctk.CTkFrame(self.menu_container, fg_color="transparent", height=40)
        frame.pack(fill="x", pady=2)
        
        btn = ctk.CTkButton(frame, text=f"{icon}  {text}", anchor="w", fg_color="transparent", 
                            text_color="#2D3748", font=("Inter", 13), hover_color="#EDF2F7", height=40)
        btn.pack(side="left", fill="x", expand=True)
        
        ctk.CTkLabel(frame, text=str(count), font=("Inter", 11, "bold"), text_color="#A0AEC0").pack(side="right", padx=15)

    def refresh_sidebar_menus(self):
        for widget in self.menu_container.winfo_children(): widget.destroy()
        all_files = [f for f in os.listdir(self.notes_dir) if f.endswith(".txt")]
        starred_count = len([f for f in all_files if f.startswith("starred_")])
        
        self.sidebar_item("Semua Catatan", len(all_files), "📝")
        self.sidebar_item("Ditandai", starred_count, "⭐")
        self.sidebar_item("Sampah", 0, "🗑️")

    # --- 2. LIST PANEL ---
    def setup_list_panel(self):
        self.list_panel = ctk.CTkFrame(self, width=320, corner_radius=0, fg_color="white", border_width=1, border_color="#EDF2F7")
        self.list_panel.grid(row=0, column=1, sticky="nsew")
        
        header = ctk.CTkFrame(self.list_panel, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(25, 10))
        ctk.CTkLabel(header, text="Daftar Catatan", font=("Inter", 20, "bold"), text_color="#1A202C").pack(side="left")
        
        ctk.CTkButton(header, text="📥 Impor", width=70, height=30, font=("Inter", 11), 
                      fg_color="#E2E8F0", text_color="#2D3748", command=self.import_file).pack(side="right")

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.refresh_notes_list())
        ctk.CTkEntry(self.list_panel, placeholder_text="Cari judul...", 
                                    textvariable=self.search_var, height=40, border_color="#E2E8F0").pack(fill="x", padx=20, pady=(5, 15))

        self.scroll_notes = ctk.CTkScrollableFrame(self.list_panel, fg_color="transparent")
        self.scroll_notes.pack(fill="both", expand=True, padx=5)

        self.fab = ctk.CTkButton(self, text="+ Baru", width=100, height=45, corner_radius=25, 
                                 font=("Inter", 14, "bold"), fg_color="#3182CE", command=self.create_note)
        self.fab.place(relx=0.25, rely=0.92, anchor="center")

    # --- 3. EDITOR PANEL ---
    def setup_editor_panel(self):
        self.editor_panel = ctk.CTkFrame(self, corner_radius=0, fg_color="white")
        self.editor_panel.grid(row=0, column=2, sticky="nsew")
        
        toolbar = ctk.CTkFrame(self.editor_panel, fg_color="transparent", height=80)
        toolbar.pack(fill="x", padx=40, pady=(20, 0))
        
        self.title_entry = ctk.CTkEntry(toolbar, font=("Inter", 28, "bold"), placeholder_text="Ketik Judul...",
                                        fg_color="transparent", border_width=0, width=450, text_color="#1A202C")
        self.title_entry.pack(side="left")
        self.title_entry.bind("<FocusOut>", self.rename_note)

        # Tombol ⭐ Bintang (BARU)
        self.star_btn = ctk.CTkButton(toolbar, text="⭐", width=40, height=32, fg_color="transparent", 
                                      text_color="#CBD5E0", font=("Inter", 18), command=self.toggle_star)
        self.star_btn.pack(side="left", padx=5)

        ctk.CTkButton(toolbar, text="🗑️ Hapus", width=80, height=32, fg_color="#FFF5F5", 
                      text_color="#E53E3E", command=self.delete_note).pack(side="right")
        
        ctk.CTkButton(toolbar, text="📄 Ekspor ke PDF", width=120, height=32, fg_color="#EBF8FF", 
                      text_color="#3182CE", command=self.export_pdf).pack(side="right", padx=15)

        self.textbox = ctk.CTkTextbox(self.editor_panel, font=("Inter", 16), fg_color="white", border_width=0, wrap="word")
        self.textbox.pack(fill="both", expand=True, padx=60, pady=(20, 20))
        self.textbox.bind("<KeyRelease>", self.auto_save)
        
        self.status_label = ctk.CTkLabel(self.editor_panel, text="Pilih atau buat catatan untuk mulai", font=("Inter", 12), text_color="#CBD5E0")
        self.status_label.pack(side="bottom", anchor="w", padx=60, pady=10)

    # --- LOGIKA FITUR ---
    def toggle_star(self):
        if not self.current_file: return
        
        old_path = os.path.join(self.notes_dir, self.current_file)
        if self.current_file.startswith("starred_"):
            new_filename = self.current_file.replace("starred_", "", 1)
            self.star_btn.configure(text_color="#CBD5E0") # Abu-abu
        else:
            new_filename = "starred_" + self.current_file
            self.star_btn.configure(text_color="#F6AD55") # Orange emas
            
        new_path = os.path.join(self.notes_dir, new_filename)
        os.rename(old_path, new_path)
        self.current_file = new_filename
        self.refresh_notes_list()

    def refresh_notes_list(self):
        for widget in self.scroll_notes.winfo_children(): widget.destroy()
        if self.empty_label:
            self.empty_label.destroy()
            self.empty_label = None

        query = self.search_var.get().lower()
        files = sorted([f for f in os.listdir(self.notes_dir) if f.endswith(".txt")], 
                       key=lambda x: os.path.getmtime(os.path.join(self.notes_dir, x)), reverse=True)
        
        if not files:
            self.empty_label = ctk.CTkLabel(self.scroll_notes, text="Klik + untuk membuat\ncatatan baru", font=("Inter", 12), text_color="#A0AEC0")
            self.empty_label.pack(pady=50)
        else:
            for f in files:
                if query in f.lower(): self.add_note_item(f)
        self.refresh_sidebar_menus()

    def add_note_item(self, filename):
        path = os.path.join(self.notes_dir, filename)
        mtime = datetime.fromtimestamp(os.path.getmtime(path)).strftime("%d %b %Y")
        
        is_starred = filename.startswith("starred_")
        display_name = filename.replace("starred_", "", 1).replace(".txt", "")
        
        card = ctk.CTkFrame(self.scroll_notes, fg_color="transparent", height=70, cursor="hand2")
        card.pack(fill="x", pady=2, padx=5)
        
        title_text = f"⭐ {display_name}" if is_starred else display_name
        lbl_title = ctk.CTkLabel(card, text=title_text, font=("Inter", 14, "bold"), 
                                 text_color="#F6AD55" if is_starred else "#2D3748")
        lbl_title.pack(anchor="w", padx=15, pady=(10, 0))
        
        ctk.CTkLabel(card, text=f"Diubah: {mtime}", font=("Inter", 11), text_color="#A0AEC0").pack(anchor="w", padx=15, pady=(0, 10))

        for widget in [card, lbl_title]:
            widget.bind("<Button-1>", lambda e, f=filename: self.load_note(f))

    def load_note(self, filename):
        self.current_file = filename
        clean_name = filename.replace("starred_", "", 1).replace(".txt","")
        
        self.title_entry.delete(0, "end")
        self.title_entry.insert(0, clean_name)
        
        # Update warna bintang di toolbar
        if filename.startswith("starred_"):
            self.star_btn.configure(text_color="#F6AD55")
        else:
            self.star_btn.configure(text_color="#CBD5E0")
            
        with open(os.path.join(self.notes_dir, filename), "r", encoding="utf-8") as f:
            self.textbox.delete("1.0", "end")
            self.textbox.insert("1.0", f.read())
        self.status_label.configure(text="Catatan dimuat")

    def create_note(self):
        name = f"Catatan_{datetime.now().strftime('%H%M%S')}.txt"
        with open(os.path.join(self.notes_dir, name), "w", encoding="utf-8") as f: f.write("")
        self.refresh_notes_list()
        self.load_note(name)

    def auto_save(self, event=None):
        if self.current_file:
            content = self.textbox.get("1.0", "end-1c")
            with open(os.path.join(self.notes_dir, self.current_file), "w", encoding="utf-8") as f: f.write(content)
            self.status_label.configure(text=f"Tersimpan otomatis • {datetime.now().strftime('%H:%M:%S')}")

    def rename_note(self, event=None):
        if not self.current_file: return
        new_title = self.title_entry.get().strip()
        prefix = "starred_" if self.current_file.startswith("starred_") else ""
        new_filename = prefix + new_title + ".txt"
        
        if not new_title or new_filename == self.current_file: return
        
        try:
            os.rename(os.path.join(self.notes_dir, self.current_file), os.path.join(self.notes_dir, new_filename))
            self.current_file = new_filename
            self.refresh_notes_list()
        except Exception:
            messagebox.showerror("Error", "Gagal mengganti nama.")

    def import_file(self):
        path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if path:
            shutil.copy(path, self.notes_dir)
            self.refresh_notes_list()

    def export_pdf(self):
        if not self.current_file: return
        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Documents", "*.pdf")])
        if path:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Helvetica", size=12)
            pdf.multi_cell(0, 10, txt=self.textbox.get("1.0", "end-1c").encode('latin-1', 'replace').decode('latin-1'))
            pdf.output(path)
            messagebox.showinfo("Berhasil", "PDF disimpan!")

    def delete_note(self):
        if self.current_file and messagebox.askyesno("Konfirmasi", "Hapus catatan ini?"):
            os.remove(os.path.join(self.notes_dir, self.current_file))
            self.current_file = None
            self.textbox.delete("1.0", "end")
            self.title_entry.delete(0, "end")
            self.refresh_notes_list()

if __name__ == "__main__":
    app = FileNotesPro()
    app.mainloop()