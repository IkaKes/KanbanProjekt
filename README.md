# Sistem za upravljanje skladišča (Kanban)

Programska rešitev za vodenje skladiščnega poslovanja po metodologiji Kanban. Sistem sestavljata spletna administrativna plošča (Flask) in namizni klient (Tkinter) za skladiščnike.

## Uporabljene tehnologije

* **Backend:** Python (Flask, SQLAlchemy, PyMySQL), Flask-Login (avtentikacija), Flask-CORS, Waitress (produkcijski WSGI strežnik).
* **Podatkovna baza:** MySQL (XAMPP/WAMP)
* **Frontend (Splet):** HTML5, Bootstrap 5, Jinja2, FontAwesome (ikone).
* **Frontend (Namizje):** Tkinter, Ttkbootstrap, Requests (HTTP klici), Pillow (obdelava slik).
* **Orodja:** ReportLab (generiranje PDF), QRCode
* **Arhitektura:** REST API (JSON komunikacija med klientom in strežnikom).

## Namestitev in zagon

### 1. Priprava podatkovne baze
Sistem zahteva delujoč MySQL strežnik.
1.  Zaženite Apache in MySQL v XAMPP nadzorni plošči.
2.  Odprite phpMyAdmin.
3.  Ustvarite novo, prazno bazo z imenom: `kanban_db` (Collation: `utf8_general_ci`).

### 2. Namestitev knjižnic
V terminalu, v mapi projekta, zaženite ukaz:

    pip install -r requirements.txt

### 3. Inicializacija sistema
Zaženite skripto za pripravo baze in ustvarjanje uporabnikov:

    python setup.py

### 4. Zagon strežnika (Backend)
Za zagon spletne aplikacije in API vmesnika uporabite:

    python run.py

Strežnik bo dostopen na naslovu: `http://127.0.0.1:8080`

### 5. Zagon terminala (Namizna aplikacija)
Za zagon aplikacije izberite eno od možnosti:

* **Možnost A:** Dvokliknite na datoteko **`START_APP.bat`**.
* **Možnost B (Terminal):** V terminalu ročno zaženite ukaz:
    ```bash
    python magacin_terminal.py
    ```

## Dostopni podatki (Prijava)

| Vloga | Uporabniško ime | Geslo |
| :--- | :--- | :--- |
| **Administrator** (Splet) | `admin` | `admin` |
| **Skladiščnik** (Namizje) | `marko` | `marko123` |
