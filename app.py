from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "kunci_rahasia_anda"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///laporan.db'
db = SQLAlchemy(app)


# --- TABEL DATABASE ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'Guru' atau 'Siswa'


class Laporan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100))
    kelas = db.Column(db.String(20))
    isi = db.Column(db.Text)
    status = db.Column(db.String(50), default="Menunggu")
    balasan = db.Column(db.Text, default="")


# Inisialisasi Database & Akun Admin Default
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin", password=generate_password_hash("12345"), role="Guru")
        db.session.add(admin)
        db.session.commit()


# --- LOGIN & AUTH ---
@app.route('/')
def login_page():
    return render_template('login.html')


@app.route('/auth', methods=['POST'])
def auth():
    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password, password):
        session['user_id'] = user.id
        session['user_name'] = user.username
        session['user_role'] = user.role
        return redirect('/dashboard')
    return "Login Gagal! Akun tidak ditemukan atau PW salah. <a href='/'>Kembali</a>"


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# --- DASHBOARD & FITUR GURU ---
@app.route('/dashboard')
def dashboard():
    if 'user_role' not in session: return redirect('/')
    laporan = Laporan.query.all()
    return render_template('dashboard.html', laporan=laporan, role=session['user_role'], user=session['user_name'])


@app.route('/tambah_siswa', methods=['POST'])
def tambah_siswa():
    if session.get('user_role') != 'Guru': return "Akses Ditolak"
    user_baru = request.form.get('username')
    pw_baru = request.form.get('password')

    if User.query.filter_by(username=user_baru).first():
        return "Username sudah terdaftar! <a href='/dashboard'>Kembali</a>"

    baru = User(username=user_baru, password=generate_password_hash(pw_baru), role="Siswa")
    db.session.add(baru)
    db.session.commit()
    return redirect('/dashboard')


# --- FITUR LAPORAN ---
@app.route('/buat', methods=['GET', 'POST'])
def buat():
    if request.method == 'POST':
        db.session.add(Laporan(nama=session['user_name'], kelas=request.form.get('kelas'), isi=request.form.get('isi')))
        db.session.commit()
        return redirect('/dashboard')
    return render_template('buat.html')


@app.route('/update/<int:id>', methods=['POST'])
def update(id):
    l = Laporan.query.get(id)
    l.status = request.form.get('status_baru')
    l.balasan = request.form.get('balasan_guru')
    db.session.commit()
    return redirect('/dashboard')


if __name__ == '__main__':
    app.run(debug=True)