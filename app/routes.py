import os
import io
import qrcode
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A6, portrait
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader

from app import app, db
from app.models import User, Artikal, Dobavljac, Lokacija, Narudzba, Log

UPLOAD_FOLDER = 'app/static'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            if user.role == 'admin':
                login_user(user)
                return redirect(url_for('admin_panel'))
            else:
                flash('Pristup dozvoljen samo administratorima.')
        else:
            flash('Pogrešno korisničko ime ili lozinka.')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/admin')
@login_required
def admin_panel():
    pending = Narudzba.query.filter_by(status='pending').all()
    ordered = Narudzba.query.filter_by(status='approved').all()
    history = Narudzba.query.filter(Narudzba.status.in_(['delivered', 'rejected'])).order_by(Narudzba.datum_kreiranja.desc()).limit(50).all()
    svi_artikli = Artikal.query.all()
    svi_radnici = User.query.all()
    return render_template('admin.html', user=current_user, pending=pending, ordered=ordered, history=history, artikli=svi_artikli, radnici=svi_radnici)

@app.route('/api/admin/obrisi_radnika/<int:id>', methods=['DELETE'])
@login_required
def api_obrisi_radnika(id):
    u = User.query.get(id)
    if u:
        if u.role == 'admin' and u.id == current_user.id:
            return jsonify({'status': 'error', 'message': 'Ne možete obrisati sopstveni nalog!'})
        
        db.session.delete(u)
        db.session.add(Log(radnik=current_user.username, akcija="BRISANJE_RADNIKA", opis=f"Obrisao korisnika {u.username}"))
        db.session.commit()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Korisnik nije nađen'})

@app.route('/api/admin/obrisi_artikal/<sifra>', methods=['DELETE'])
@login_required
def api_obrisi_artikal(sifra):
    a = Artikal.query.get(sifra)
    if a:
        Narudzba.query.filter_by(artikal_sifra=sifra).delete()
        db.session.delete(a)
        db.session.add(Log(radnik=current_user.username, akcija="BRISANJE_ARTIKLA", opis=f"Obrisao artikal {a.naziv} ({sifra})"))
        db.session.commit()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Artikal nije nađen'})

@app.route('/api/admin/obrisi_narudzbu/<int:id>', methods=['DELETE'])
@login_required
def api_obrisi_narudzbu(id):
    if current_user.role != 'admin':
        return jsonify({'status': 'error', 'message': 'Nemaš pravo pristupa'})
        
    n = Narudzba.query.get(id)
    if n:
        opis = f"Obrisao zapis iz istorije (Artikal: {n.artikal_sifra}, Količina: {n.kolicina})"
        db.session.delete(n)
        db.session.add(Log(radnik=current_user.username, akcija="BRISANJE_ISTORIJE", opis=opis))
        db.session.commit()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Nije nađeno'})

@app.route('/api/admin/koriguj_stanje', methods=['POST'])
@login_required
def api_koriguj_stanje():
    data = request.json
    a = Artikal.query.get(data.get('sifra'))
    novo_stanje = data.get('stanje')
    if a and novo_stanje is not None:
        try:
            val = int(novo_stanje)
            staro = a.stanje
            a.stanje = val
            db.session.add(Log(radnik=current_user.username, akcija="KOREKCIJA_STANJA", opis=f"Artikal {a.naziv}: {staro} -> {val}"))
            db.session.commit()
            return jsonify({'status': 'success'})
        except:
            return jsonify({'status': 'error', 'message': 'Mora biti broj'})
    return jsonify({'status': 'error'})

@app.route('/api/admin/reset_radnika', methods=['POST'])
@login_required
def api_reset_radnika():
    if current_user.role != 'admin': return jsonify({'status': 'error'})

    data = request.json
    u = User.query.get(data.get('id'))
    nova_sifra = data.get('nova_sifra')
    
    if u and nova_sifra:
        u.password_hash = generate_password_hash(nova_sifra)
        db.session.add(Log(radnik=current_user.username, akcija="RESET_SIFRE", opis=f"Promenio šifru za korisnika: {u.username}"))
        db.session.commit()
        return jsonify({'status': 'success', 'message': f'Šifra za {u.username} je uspešno promenjena!'})
    return jsonify({'status': 'error', 'message': 'Greška u podacima'})

@app.route('/api/admin/promeni_moju_sifru', methods=['POST'])
@login_required
def api_promeni_moju_sifru():
    data = request.json
    nova = data.get('nova_sifra')
    
    if nova:
        current_user.password_hash = generate_password_hash(nova)
        db.session.add(Log(radnik=current_user.username, akcija="PROMENA_SVOJE_SIFRE", opis="Admin je promenio svoju šifru"))
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Vaša šifra je promenjena!'})
    return jsonify({'status': 'error', 'message': 'Šifra ne sme biti prazna'})

@app.route('/api/admin/akcija', methods=['POST'])
@login_required
def api_admin_akcija():
    data = request.json
    n = Narudzba.query.get(data.get('id'))
    akcija = data.get('akcija')
    
    if not n: return jsonify({'status': 'error'}), 404
    a = Artikal.query.get(n.artikal_sifra)
    
    opis = ""
    if akcija == 'odobri':
        n.status = 'approved'
        opis = f"Odobrio narudžbu: {a.naziv} (kol: {n.kolicina})"
    elif akcija == 'odbij':
        n.status = 'rejected'
        opis = f"Odbio narudžbu: {a.naziv}"
    elif akcija == 'stiglo':
        n.status = 'delivered'
        n.datum_isporuke = datetime.now()
        a.stanje += n.kolicina 
        opis = f"Potvrdio prijem robe: {a.naziv} (+{n.kolicina})"

    db.session.add(Log(radnik=current_user.username, akcija=f"ADMIN_{akcija.upper()}", opis=opis))
    db.session.commit()
    return jsonify({'status': 'success'}), 200

@app.route('/admin/dodaj_radnika', methods=['POST'])
@login_required
def admin_dodaj_radnika():
    u = request.form.get('username')
    p = request.form.get('password')
    r = request.form.get('role')
    if not User.query.filter_by(username=u).first():
        db.session.add(User(username=u, password_hash=generate_password_hash(p), role=r))
        db.session.commit()
    return redirect(url_for('admin_panel'))

@app.route('/admin/dodaj_artikal', methods=['POST'])
@login_required
def admin_dodaj_artikal():
    sifra = request.form.get('sifra')
    if Artikal.query.get(sifra): return redirect(url_for('admin_panel'))
    
    dob_naziv = request.form.get('dobavljac')
    lok_oznaka = request.form.get('lokacija')
    
    dob = Dobavljac.query.filter_by(naziv=dob_naziv).first()
    if not dob and dob_naziv:
        dob = Dobavljac(naziv=dob_naziv)
        db.session.add(dob); db.session.commit()
        
    lok = Lokacija.query.filter_by(oznaka=lok_oznaka).first()
    if not lok and lok_oznaka:
        lok = Lokacija(oznaka=lok_oznaka)
        db.session.add(lok); db.session.commit()

    novi = Artikal(
        sifra=sifra, 
        naziv=request.form.get('naziv'), 
        dobavljac_id=dob.id if dob else None, 
        lokacija_id=lok.id if lok else None, 
        tip=request.form.get('tip'), 
        url_proizvoda=request.form.get('link'), 
        stanje=int(request.form.get('stanje', 0))
    )
    db.session.add(novi)
    db.session.commit()
    return redirect(url_for('admin_panel'))


@app.route('/admin/izmeni_artikal', methods=['POST'])
@login_required
def admin_izmeni_artikal():
    sifra = request.form.get('sifra')
    artikal = Artikal.query.get(sifra)
    
    if not artikal:
        return redirect(url_for('admin_panel'))
    
    dob_naziv = request.form.get('dobavljac')
    lok_oznaka = request.form.get('lokacija')
    
    if dob_naziv:
        dob = Dobavljac.query.filter_by(naziv=dob_naziv).first()
        if not dob:
            dob = Dobavljac(naziv=dob_naziv)
            db.session.add(dob); db.session.commit()
        artikal.dobavljac_id = dob.id
        
    if lok_oznaka:
        lok = Lokacija.query.filter_by(oznaka=lok_oznaka).first()
        if not lok:
            lok = Lokacija(oznaka=lok_oznaka)
            db.session.add(lok); db.session.commit()
        artikal.lokacija_id = lok.id

    artikal.naziv = request.form.get('naziv')
    artikal.tip = request.form.get('tip')
    
    db.session.add(Log(radnik=current_user.username, akcija="IZMENA_ARTIKLA", opis=f"Izmenio podatke za {artikal.naziv}"))
    db.session.commit()
    return redirect(url_for('admin_panel'))


@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    user = User.query.filter_by(username=data.get('username')).first()
    if user and check_password_hash(user.password_hash, data.get('password')):
        return jsonify({'status': 'success', 'user': user.username, 'role': user.role}), 200
    return jsonify({'status': 'error'}), 401

@app.route('/api/svi_artikli', methods=['GET'])
def api_svi_artikli():
    artikli = Artikal.query.all()
    lista = []
    for a in artikli:
        lista.append({
            'sifra': a.sifra, 
            'naziv': a.naziv, 
            'dobavljac': a.dobavljac_rel.naziv if a.dobavljac_rel else "", 
            'lokacija': a.lokacija_rel.oznaka if a.lokacija_rel else "", 
            'tip': a.tip,
            'stanje': a.stanje
        })
    return jsonify({'status': 'success', 'data': lista}), 200

@app.route('/api/artikal/<sifra>', methods=['GET'])
def api_get_artikal(sifra):
    a = Artikal.query.filter_by(sifra=sifra).first()
    if a:
        data = {
            'sifra': a.sifra, 
            'naziv': a.naziv, 
            'stanje': a.stanje, 
            'lokacija': a.lokacija_rel.oznaka if a.lokacija_rel else "", 
            'dobavljac': a.dobavljac_rel.naziv if a.dobavljac_rel else "", 
            'tip': a.tip
        }
        return jsonify({'status': 'success', 'data': data}), 200
    return jsonify({'status': 'error'}), 404

@app.route('/api/naruci', methods=['POST'])
def api_naruci():
    data = request.json
    db.session.add(Narudzba(artikal_sifra=data['sifra'], kolicina=50, radnik=data['radnik'], status="pending"))
    db.session.add(Log(radnik=data['radnik'], akcija="NARUDZBA", opis=f"Zahtev za artikal {data['sifra']}"))
    db.session.commit()
    return jsonify({'status': 'success'}), 200

@app.route('/api/moje_narudzbe/<username>', methods=['GET'])
def api_moje_narudzbe(username):
    narudzbe = Narudzba.query.filter_by(radnik=username).order_by(Narudzba.datum_kreiranja.desc()).limit(50).all()
    data = []
    for n in narudzbe:
        data.append({
            'id': n.id,
            'artikal': n.artikal.naziv,
            'kolicina': n.kolicina,
            'status': n.status,
            'datum': n.datum_kreiranja.strftime('%d.%m %H:%M')
        })
    return jsonify({'status': 'success', 'data': data}), 200

@app.route('/api/kreiraj_karticu', methods=['POST'])
def api_kreiraj():
    data = request.json
    sifra = data.get('sifra')
    
    dob_naziv = data.get('dobavljac')
    lok_oznaka = data.get('lokacija')
    
    dob = Dobavljac.query.filter_by(naziv=dob_naziv).first()
    if not dob and dob_naziv:
        dob = Dobavljac(naziv=dob_naziv)
        db.session.add(dob); db.session.commit()
        
    lok = Lokacija.query.filter_by(oznaka=lok_oznaka).first()
    if not lok and lok_oznaka:
        lok = Lokacija(oznaka=lok_oznaka)
        db.session.add(lok); db.session.commit()

    a = Artikal.query.filter_by(sifra=sifra).first()
    if not a:
        a = Artikal(sifra=sifra)
    
    a.naziv = data.get('naziv')
    a.dobavljac_id = dob.id if dob else None
    a.lokacija_id = lok.id if lok else None
    a.tip = data.get('tip')
    
    db.session.add(a)
    db.session.commit()
    return jsonify({'status': 'success'}), 200

@app.route('/api/pdf/<sifra>')
def api_pdf(sifra):
    a = Artikal.query.get(sifra)
    if not a: return "Artikal nije pronađen", 404
    
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=portrait(A6))
    w, h = portrait(A6)
    
    tip = a.tip
    boja = colors.HexColor("#0055a5") if tip == 'blue' else colors.HexColor("#d63031")

    c.setFillColor(boja)
    c.rect(0, h-50, w, 50, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(10, h-32, "KANBAN")
    
    if tip == 'red':
        c.setFillColor(colors.yellow)
        c.rect(w-50, h-50, 50, 50, fill=1, stroke=0)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(w-25, h-32, "K4")

    c.setStrokeColor(colors.black)
    c.line(w/2, h-50, w/2, 0) 
    for y in [h-50, h-150, h-200, h-250, h-300]: 
        c.line(0, y, w, y)

    c.setFillColor(colors.black)
    c.setFont("Helvetica", 10)
    labels = ["Naručiti kad", "Količina za", "Lokacija"]
    ys = [h-170, h-220, h-270]
    for i, l in enumerate(labels): 
        c.drawString(5, ys[i]+5, l)
    
    c.setFillColor(colors.lightgrey)
    c.rect(5, h-145, (w/2)-10, 90, fill=1, stroke=0)
    c.setFillColor(colors.black)
    c.drawCentredString((w/4), h-100, "(SLIKA)")

    c.setFillColor(colors.white)
    c.setFont("Helvetica", 9)
    c.setFillColor(boja)
    c.rect(w/2, h-70, w/2, 20, fill=1, stroke=1)
    c.rect(w/2, h-130, w/2, 20, fill=1, stroke=1)
    
    c.setFillColor(colors.white)
    c.drawCentredString(w*0.75, h-66, "Naziv")
    c.drawCentredString(w*0.75, h-126, "Dobavljač")
    
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(w*0.75, h-95, a.naziv[:18]) 
    
    c.setFont("Helvetica", 10)
    dob_naziv = a.dobavljac_rel.naziv if a.dobavljac_rel else "N/A"
    c.drawCentredString(w*0.75, h-145, dob_naziv[:20])
    
    c.setFillColor(colors.red)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(w*0.75, h-180, "1 Kutija") 
    
    c.setFillColor(colors.blue)
    c.drawCentredString(w*0.75, h-225, "200 kom") 
    
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 12)
    lok_oznaka = a.lokacija_rel.oznaka if a.lokacija_rel else "N/A"
    c.drawCentredString(w*0.75, h-275, lok_oznaka)

    if tip == 'blue':
        c.setFillColor(boja)
        c.rect(0, 0, w/2, h-300, fill=1, stroke=1)
        c.setFillColor(colors.white)
        c.drawString(5, h-320, "QR kod")
        
        qr_file = f"temp_{sifra}.png"
        qrcode.make(a.sifra).save(qr_file)
        try:
            c.drawImage(qr_file, w*0.55, 10, 100, 100)
        except:
            pass
        finally:
            if os.path.exists(qr_file):
                os.remove(qr_file)
                
        c.setFillColor(colors.black)
        c.drawString(10, 10, f"ID: {a.sifra}")
    else:
        c.setFillColor(colors.lightgrey)
        c.rect(0, h-320, w, 20, fill=1, stroke=1)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(5, h-316, "Tok nabavke")
        c.setFont("Helvetica", 8)
        c.drawString(5, h-335, "1. Kanban B1 -> Nabavka")

    c.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"k_{sifra}.pdf", mimetype='application/pdf')

@app.route('/admin/pdf/<sifra>')
@login_required
def admin_pdf(sifra):
    return api_pdf(sifra)