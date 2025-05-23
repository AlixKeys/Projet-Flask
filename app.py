from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import joblib
import os

# Initialisation de l'application Flask
app = Flask(__name__)
app.secret_key = 'secret-key'

# Configuration de la base de données
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///spam_detector.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialisation de SQLAlchemy
db = SQLAlchemy(app)

# Initialisation de Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# Chargement du modèle ML
model = joblib.load('spam_model.pkl')


# Modèle utilisateur
class AppUser(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Modèle email
class Email(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    prediction = db.Column(db.String(10), nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

# Fonction de chargement utilisateur
@login_manager.user_loader
def load_user(user_id):
    return AppUser.query.get(int(user_id))

# Page d'enregistrement
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        existing_user = AppUser.query.filter_by(email=email).first()
        if existing_user:
            return "Utilisateur déjà existant.", 409
        new_user = AppUser(email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

# Page de connexion
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = AppUser.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('home'))
        return "Identifiants invalides", 401
    return render_template('login.html')

# Déconnexion
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Accueil (compose)
@app.route('/compose', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        message = request.form['message']
        prediction = model.predict([message])[0]
        result = "SPAM" if prediction == 1 else "NON-SPAM"
        return render_template('compose.html', prediction=result)
    return render_template('compose.html')

# Inbox
@app.route('/inbox')
@login_required
def inbox():
    emails = Email.query.filter_by(prediction="NON-SPAM").order_by(Email.timestamp.desc()).all()
    return render_template('listing.html', emails=emails)

# Brouillons
@app.route('/draft')
@login_required
def draft():
    return render_template('draft.html')

# Messages envoyés
@app.route('/message_sent')
@login_required
def message_sent():
    return render_template('message_sent.html')

# Spam
@app.route('/spam')
@login_required
def spam():
    emails = Email.query.filter_by(prediction="SPAM").order_by(Email.timestamp.desc()).all()
    return render_template('spam.html', emails=emails)

# Enregistrement + prédiction
@app.route('/predict', methods=['POST'])
@login_required
def predict():
    message = request.form['message']
    prediction = model.predict([message])[0]
    result = "SPAM" if prediction == 1 else "NON-SPAM"

    new_email = Email(content=message, prediction=result)
    db.session.add(new_email)
    db.session.commit()

    return render_template('compose.html', prediction=result)

# Lancer le serveur
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
