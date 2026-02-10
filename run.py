from app import app, db
from waitress import serve

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("Baza podataka i tabele su provjerene/kreirane!")

    print("----------------------------------------------------------------")
    print("POKRETANJE PRODUKCIJSKOG SERVERA (WAITRESS)...")
    print("Aplikacija je dostupna na: http://127.0.0.1:8080")
    print("----------------------------------------------------------------")
    
    serve(app, host='0.0.0.0', port=8080)