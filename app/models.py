from app import db
from flask_login import UserMixin
from datetime import datetime

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='radnik') # 'admin' ili 'radnik'

class Dobavljac(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    naziv = db.Column(db.String(100), nullable=False)
    artikli = db.relationship('Artikal', backref='dobavljac_rel', lazy=True)

class Lokacija(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    oznaka = db.Column(db.String(50), nullable=False)
    artikli = db.relationship('Artikal', backref='lokacija_rel', lazy=True)

class Artikal(db.Model):
    sifra = db.Column(db.String(50), primary_key=True)
    naziv = db.Column(db.String(100), nullable=False)
    slika = db.Column(db.String(200))
    stanje = db.Column(db.Integer, default=0)
    limit_min = db.Column(db.Integer, default=10)
    tip = db.Column(db.String(20), default="blue") 
    url_proizvoda = db.Column(db.String(500))      
    
    dobavljac_id = db.Column(db.Integer, db.ForeignKey('dobavljac.id'))
    lokacija_id = db.Column(db.Integer, db.ForeignKey('lokacija.id'))

class Narudzba(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    artikal_sifra = db.Column(db.String(50), db.ForeignKey('artikal.sifra'))
    kolicina = db.Column(db.Integer, nullable=False)
    radnik = db.Column(db.String(100)) # Ime radnika koji je skenirao
    
    # STATUSI: 
    # 'pending' (čeka šefa), 'approved' (poručeno), 'delivered' (stiglo), 'rejected' (odbijeno)
    status = db.Column(db.String(20), default="pending") 
    
    datum_kreiranja = db.Column(db.DateTime, default=datetime.now)
    datum_isporuke = db.Column(db.DateTime)

    artikal = db.relationship('Artikal', backref='narudzbe')

class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    radnik = db.Column(db.String(100))
    akcija = db.Column(db.String(50))  # "KREIRANJE", "NARUDZBA", "ODOBRENJE"
    opis = db.Column(db.String(500))
    datum = db.Column(db.DateTime, default=datetime.now)