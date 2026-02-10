import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import requests
from PIL import Image, ImageTk
import io  
import qrcode
import os


SERVER_URL = "http://127.0.0.1:8080"

class MagacinApp:
    def __init__(self, root):
        self.root = root
        self.root.title("KANBAN WORKSTATION PRO")
        self.root.geometry("1200x800")
        
        self.trenutni_radnik = None
        self.svi_artikli_cache = []
        self.aktivni_artikal = None
        self.tk_product_img = None 

        
        self.container = ttk.Frame(root, padding=20)
        self.container.pack(fill=BOTH, expand=YES)
        
        self.prikazi_login()

    def ocisti_prozor(self):
        for w in self.container.winfo_children(): w.destroy()

    
    def prikazi_login(self):
        self.ocisti_prozor()
        
        frame = ttk.Frame(self.container, padding=40, bootstyle="secondary")
        frame.place(relx=0.5, rely=0.5, anchor="center")
        
        ttk.Label(frame, text="🏭 MAGACIN TERMINAL", font=("Helvetica", 24, "bold"), bootstyle="inverse-secondary").pack(pady=(0, 30))
        
        ttk.Label(frame, text="Korisničko ime", bootstyle="inverse-secondary").pack(anchor="w")
        eu = ttk.Entry(frame, font=("Helvetica", 12), width=25)
        eu.pack(pady=(0, 15))
        
        ttk.Label(frame, text="Lozinka", bootstyle="inverse-secondary").pack(anchor="w")
        ep = ttk.Entry(frame, font=("Helvetica", 12), width=25, show="*")
        ep.pack(pady=(0, 20))
        
        def login(e=None):
            try:
                
                if requests.post(f"{SERVER_URL}/api/login", json={"username": eu.get(), "password": ep.get()}).status_code == 200:
                    self.trenutni_radnik = eu.get()
                    self.ucitaj_artikle()
                    self.prikazi_meni()
                else: messagebox.showerror("Greška", "Pogrešni podaci")
            except: messagebox.showerror("Greška", "Nema konekcije sa serverom!\nProveri da li je run.py pokrenut.")
            
        ttk.Button(frame, text="PRIJAVA ➜", command=login, bootstyle="success", width=20).pack(pady=10)
        self.root.bind('<Return>', login)

    def ucitaj_artikle(self):
        try: self.svi_artikli_cache = requests.get(f"{SERVER_URL}/api/svi_artikli").json()['data']
        except: pass

    
    def prikazi_meni(self):
        self.ocisti_prozor(); self.root.unbind('<Return>')
        
        
        header = ttk.Frame(self.container, padding=10, bootstyle="primary")
        header.pack(fill=X, pady=(0, 20))
        ttk.Label(header, text=f"👤 Prijavljen: {self.trenutni_radnik}", font=("Helvetica", 14, "bold"), bootstyle="inverse-primary").pack(side=LEFT)
        ttk.Button(header, text="ODJAVA", command=self.prikazi_login, bootstyle="danger-outline").pack(side=RIGHT)

        
        nb = ttk.Notebook(self.container, bootstyle="primary")
        nb.pack(fill=BOTH, expand=YES)
        
        self.tab_scan = ttk.Frame(nb, padding=20); nb.add(self.tab_scan, text=" 📥 SKENIRANJE ")
        self.setup_scan()
        
        self.tab_create = ttk.Frame(nb, padding=20); nb.add(self.tab_create, text=" 🛠️ KREIRANJE ")
        self.setup_create()
        
        self.tab_history = ttk.Frame(nb, padding=20); nb.add(self.tab_history, text=" 🕒 ISTORIJA ")
        self.setup_history()

    
    def setup_scan(self):
        left_col = ttk.Frame(self.tab_scan); left_col.pack(side=LEFT, fill=BOTH, expand=YES)
        
        ttk.Label(left_col, text="Skeniraj QR kod artikla:", font=("Helvetica", 16)).pack(pady=40)
        self.ent_scan = ttk.Entry(left_col, font=("Helvetica", 28), justify='center', bootstyle="info")
        self.ent_scan.pack(pady=10, ipady=10, fill=X, padx=100)
        self.ent_scan.bind('<Return>', self.proveri_karticu)
        
        self.lbl_info = ttk.Label(left_col, text="Skeniraj karticu za detalje...", font=("Helvetica", 18), bootstyle="secondary")
        self.lbl_info.pack(pady=30)
        
        self.btn_naruci = ttk.Button(left_col, text="📥 POŠALJI NARUDŽBU", state="disabled", command=self.naruci, bootstyle="warning", width=30)
        self.btn_naruci.pack(pady=20, ipady=10)

    def proveri_karticu(self, e):
        try:
            r = requests.get(f"{SERVER_URL}/api/artikal/{self.ent_scan.get()}")
            if r.status_code == 200:
                self.aktivni_artikal = r.json()['data']
                stanje = self.aktivni_artikal['stanje']
                self.lbl_info.config(text=f"📦 {self.aktivni_artikal['naziv']}\nTrenutno na stanju: {stanje}", bootstyle="success" if stanje > 0 else "danger")
                self.btn_naruci.config(state="normal", bootstyle="success")
            else:
                self.lbl_info.config(text="❌ Nepoznat artikal", bootstyle="danger")
        except: pass

    def naruci(self):
        requests.post(f"{SERVER_URL}/api/naruci", json={"sifra": self.aktivni_artikal['sifra'], "radnik": self.trenutni_radnik})
        messagebox.showinfo("Uspeh", "Zahtev za nabavku je poslat šefu!"); self.ent_scan.delete(0, tk.END); self.btn_naruci.config(state="disabled")

    
    def setup_create(self):
        cols = ttk.Frame(self.tab_create)
        cols.pack(fill=BOTH, expand=YES)
        
        left = ttk.Labelframe(cols, text=" Podaci o artiklu ", padding=20, bootstyle="info")
        left.pack(side=LEFT, fill=BOTH, expand=YES, padx=(0, 10))
        
        right = ttk.Labelframe(cols, text=" Live Preview (Izgled Štampe) ", padding=20, bootstyle="secondary")
        right.pack(side=RIGHT, fill=BOTH, expand=YES, padx=(10, 0))

        self.vars = {k: tk.StringVar() for k in ['sifra','naziv','dobavljac','lokacija','kolicina','pakovanje']}
        self.vars['kolicina'].set("1 Kutija"); self.vars['pakovanje'].set("200 kom")
        
        ttk.Label(left, text="Izaberi postojeći ili unesi novi:", bootstyle="info").pack(anchor=W)
        cb = ttk.Combobox(left, values=[f"{a['naziv']} ({a['sifra']})" for a in self.svi_artikli_cache], font=("Helvetica", 11))
        cb.pack(fill=X, pady=(5, 20)); cb.bind("<<ComboboxSelected>>", self.popuni)
        
        for k, v in self.vars.items(): 
            ttk.Label(left, text=k.replace('_', ' ').title(), font=("Helvetica", 10, "bold")).pack(anchor=W, pady=(5,0))
            ttk.Entry(left, textvariable=v, font=("Helvetica", 11)).pack(fill=X, pady=(0, 5))
            
        ttk.Label(left, text="Tip zone (Boja):", font=("Helvetica", 10, "bold")).pack(anchor=W, pady=(10,0))
        self.cmb_boja = ttk.Combobox(left, values=["blue", "red"], state="readonly", font=("Helvetica", 11))
        self.cmb_boja.set("blue"); self.cmb_boja.pack(fill=X, pady=5); self.cmb_boja.bind("<<ComboboxSelected>>", self.preview)
        
        ttk.Button(left, text="🖨️ SAČUVAJ I ŠTAMPAJ", command=self.stampaj, bootstyle="success", width=100).pack(side=BOTTOM, pady=20, ipady=5)
        
        
        self.canvas = tk.Canvas(right, width=320, height=450, bg="white", highlightthickness=0)
        self.canvas.pack(pady=20, anchor="center") 
        
        for v in self.vars.values(): v.trace("w", self.preview)
        self.preview()

    def popuni(self, e):
        
        s = e.widget.get().split('(')[-1].replace(')', '')
        a = next((x for x in self.svi_artikli_cache if x['sifra'] == s), None)
        if a:
            self.vars['sifra'].set(a['sifra'])
            self.vars['naziv'].set(a['naziv'])
            if 'dobavljac' in a: self.vars['dobavljac'].set(a['dobavljac'])
            if 'lokacija' in a: self.vars['lokacija'].set(a['lokacija'])
            if 'tip' in a: self.cmb_boja.set(a['tip'])

    def preview(self, *args):
        if not hasattr(self, 'canvas'): return
        self.canvas.delete("all")
        
        
        self.canvas.create_rectangle(0, 0, 320, 450, fill="white", outline="gray")
        
        tip = self.cmb_boja.get()
        color = "#0055a5" if tip=="blue" else "#d63031"
        
        
        self.canvas.create_rectangle(0, 0, 320, 50, fill=color, width=0)
        self.canvas.create_text(15, 25, text="KANBAN", fill="white", font=("Arial", 18, "bold"), anchor="w")
        
        if tip == "red": 
            self.canvas.create_rectangle(260, 0, 320, 50, fill="#f1c40f", width=0)
            self.canvas.create_text(290, 25, text="K4", font=("Arial", 14, "bold"), fill="black")
        
        
        self.canvas.create_line(160, 50, 160, 450, fill="#bdc3c7", width=2)
        for y in [180, 230, 280, 330]: 
            self.canvas.create_line(0, y, 320, y, fill="#bdc3c7", width=2)
            
        
        labels = ["Naručiti kad", "Količina za", "Lokacija"]
        ys = [195, 245, 295]
        for i, l in enumerate(labels):
            self.canvas.create_text(10, ys[i], text=l, font=("Arial", 10), fill="black", anchor="w")
            
        self.canvas.create_text(240, 65, text="Naziv", font=("Arial", 9), fill="gray")
        self.canvas.create_text(240, 135, text="Dobavljač", font=("Arial", 9), fill="gray")

        
        self.canvas.create_text(240, 95, text=self.vars['naziv'].get(), width=150, justify="center", font=("Arial", 12, "bold"), fill="black")
        self.canvas.create_text(240, 155, text=self.vars['dobavljac'].get(), width=150, justify="center", font=("Arial", 11), fill="black")
        self.canvas.create_text(240, 205, text=self.vars['kolicina'].get(), fill="#c0392b", font=("Arial", 16, "bold"))
        self.canvas.create_text(240, 255, text=self.vars['pakovanje'].get(), fill="#2980b9", font=("Arial", 16, "bold"))
        self.canvas.create_text(240, 305, text=self.vars['lokacija'].get(), font=("Arial", 14, "bold"), fill="black")
        
        
        sifra = self.vars['sifra'].get()
        if sifra:
            
            image_url = f"{SERVER_URL}/static/{sifra}.jpg"
            print(f"Tražim sliku: {image_url}") 

            try:
                
                response = requests.get(image_url, timeout=0.5)
                
                if response.status_code == 200:
                    
                    img_data = response.content
                    pil_img = Image.open(io.BytesIO(img_data))
                    pil_img.thumbnail((140, 110))
                    self.tk_product_img = ImageTk.PhotoImage(pil_img)
                    self.canvas.create_image(80, 115, image=self.tk_product_img)
                else:
                    
                    fallback_url = f"{SERVER_URL}/static/vijak.jpg"
                    resp2 = requests.get(fallback_url, timeout=0.5)
                    if resp2.status_code == 200:
                        pil_img = Image.open(io.BytesIO(resp2.content))
                        pil_img.thumbnail((140, 110))
                        self.tk_product_img = ImageTk.PhotoImage(pil_img)
                        self.canvas.create_image(80, 115, image=self.tk_product_img)
                    else:
                        raise Exception("Nema slike")
            except:
                
                self.canvas.create_rectangle(10, 60, 150, 170, outline="lightgray")
                self.canvas.create_text(80, 115, text="(NEMA SLIKE)", fill="gray")

        
        if tip == "blue" and sifra:
            try: 
                self.img = ImageTk.PhotoImage(qrcode.make(sifra).resize((100, 100)))
                self.canvas.create_image(240, 390, image=self.img)
                self.canvas.create_text(240, 445, text=f"ID: {sifra}", font=("Arial", 8), fill="black")
            except: pass
            
        if tip == "red":
            self.canvas.create_text(160, 400, text="Tok nabavke: Kanban B1 -> Nabavka", font=("Arial", 10, "italic"), fill="gray")

    def stampaj(self):
        data = {k: v.get() for k, v in self.vars.items()}; data['radnik'] = self.trenutni_radnik; data['tip'] = self.cmb_boja.get()
        if requests.post(f"{SERVER_URL}/api/kreiraj_karticu", json=data).status_code == 200:
            r = requests.get(f"{SERVER_URL}/api/pdf/{data['sifra']}")
            if r.status_code == 200:
                with open(f"Kartica_{data['sifra']}.pdf", 'wb') as f: f.write(r.content)
                try: os.startfile(f"Kartica_{data['sifra']}.pdf")
                except: pass
                messagebox.showinfo("Uspeh", "Kartica je kreirana i otvorena!")

   
    def setup_history(self):
        cols = ("Artikal", "Količina", "Status", "Datum")
        self.tree = ttk.Treeview(self.tab_history, columns=cols, show='headings', bootstyle="info")
        for c in cols: self.tree.heading(c, text=c)
        self.tree.pack(fill=BOTH, expand=YES, pady=10)
        ttk.Button(self.tab_history, text="🔄 OSVEŽI LISTU", command=self.osvezi_istoriju, bootstyle="secondary-outline").pack(fill=X)
        self.osvezi_istoriju()

    def osvezi_istoriju(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        try:
            r = requests.get(f"{SERVER_URL}/api/moje_narudzbe/{self.trenutni_radnik}")
            if r.status_code == 200:
                for n in r.json()['data']:
                    self.tree.insert("", "end", values=(n['artikal'], n['kolicina'], n['status'].upper(), n['datum']))
        except: pass

if __name__ == "__main__":
    app = ttk.Window(themename="superhero") 
    MagacinApp(app)
    app.mainloop()