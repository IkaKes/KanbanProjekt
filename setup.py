from app import app, db
from app.models import User, Artikal, Dobavljac, Lokacija
from werkzeug.security import generate_password_hash

def setup_system():
    print(" SYSTEM INITIALIZATION STARTED ")
    
    with app.app_context():
        # 1. Create all database tables based on models.py
        db.create_all()
        print("[OK] Database tables created or verified.")

        # 2. Create Administrator account
        if not User.query.filter_by(username="admin").first():
            admin = User(username="admin", password_hash=generate_password_hash("admin"), role="admin")
            db.session.add(admin)
            print("[OK] Admin account created: admin / admin")
        else:
            print("[INFO] Admin account already exists.")
        
        # 3. Create Warehouse Worker account
        if not User.query.filter_by(username="marko").first():
            marko = User(username="marko", password_hash=generate_password_hash("marko123"), role="radnik")
            db.session.add(marko)
            print("[OK] Worker account created: marko / marko123")
        else:
             print("[INFO] Worker account already exists.")

        # 4. Insert initial test data (Supplier, Location, Item)
        if not Dobavljac.query.first():
            supplier = Dobavljac(naziv="Wurth d.o.o.")
            location = Lokacija(oznaka="R-01")
            db.session.add(supplier)
            db.session.add(location)
            db.session.commit()
            
            # Add a test item
            item = Artikal(
                sifra="500", 
                naziv="Vijak M6", 
                dobavljac_id=supplier.id, 
                lokacija_id=location.id, 
                stanje=100, 
                tip="blue",
                slika="vijak.jpg" 
            )
            db.session.add(item)
            print("[OK] Test data inserted (Item: Vijak M6).")

        db.session.commit()
        print(" SYSTEM READY. PLEASE RUN 'run.py' ")

if __name__ == "__main__":
    setup_system()