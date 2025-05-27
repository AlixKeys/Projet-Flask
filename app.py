from flask import Flask, render_template, request, redirect, url_for,flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import joblib
import os
from datetime import datetime
from flask_migrate import Migrate
from sqlalchemy import or_


# Initialisation de l'application Flask
app = Flask(__name__)
app.secret_key = 'secret-key'

# Configuration de la base de données
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///spam_detector.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialisation de SQLAlchemy
db = SQLAlchemy(app)
migrate = Migrate(app, db)


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
    emails = db.relationship('Email', backref='user', lazy=True)


# Modèle email
class Email(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    isRead= db.Column(db.Boolean)  
    isDelete= db.Column(db.Boolean)    
    content = db.Column(db.Text, nullable=False)
    objet = db.Column(db.String(200))               
    sender = db.Column(db.String(120)) 
    prediction = db.Column(db.String(10), nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', name='fk_email_user_id'), nullable=False)



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

# Page d'accueil (compose)
@app.route('/compose', methods=['GET', 'POST'])
@login_required
def home():
    email_count = Email.query.filter_by(sender=current_user.email,prediction="NON-SPAM", isDelete=False,isRead=False).count()
    draft_count= Email.query.filter(
    (
        (Email.user_id == current_user.id) |
        (Email.sender == current_user.email)
    ) &
    (Email.isDelete == True)
    ).count()
    sent_count = Email.query.filter_by(user_id=current_user.id,prediction="NON-SPAM",isDelete=False).count()

    spam_count = Email.query.filter_by(prediction="SPAM",user_id=current_user.id).count()
    if request.method == 'POST':
        message = request.form['message']
        prediction = model.predict([message])[0]
        result = "SPAM" if prediction == 1 else "NON-SPAM"
        return render_template('compose.html', prediction=result)
    return render_template('compose.html', email_count=email_count,spam_count=spam_count, draft_count=draft_count, sent_count=sent_count)

# Inbox
@app.route('/inbox')
@login_required
def inbox():
    emails = Email.query.filter_by(sender=current_user.email,prediction="NON-SPAM",isDelete=False).order_by(Email.timestamp.desc()).all()
    email_count = Email.query.filter_by(sender=current_user.email,prediction="NON-SPAM", isDelete=False,isRead=False).count()
    draft_count= Email.query.filter(
    (
        (Email.user_id == current_user.id) |
        (Email.sender == current_user.email)
    ) &
    (Email.isDelete == True)
    ).count()
    sent_count = Email.query.filter_by(user_id=current_user.id,prediction="NON-SPAM",isDelete=False).count()

    spam_count = Email.query.filter_by(prediction="SPAM",user_id=current_user.id).count()
    return render_template('listing.html', emails=emails,email_count=email_count,spam_count=spam_count, draft_count=draft_count, sent_count=sent_count)
    
# suppression de mail
@app.route('/delete_email/<int:email_id>', methods=['POST'])
@login_required
def delete_email(email_id):
    email = Email.query.filter_by(id=email_id, user_id=current_user.id).first()
    
    if email:
        email.isDelete = False  # on le marque comme supprimé
        db.session.commit()
        flash("Email supprimé avec succès.", "success")
    else:
        flash("Email introuvable ou non autorisé.", "danger")

    return redirect(url_for('inbox'))

@app.route('/delete_multiple_emails', methods=['POST'])
@login_required
def delete_multiple_emails():
    ids = request.form.getlist('email_ids')  # liste des ids cochés
    if ids:
        # Filtrer uniquement les emails de l'utilisateur connecté
        emails = Email.query.filter(Email.id.in_(ids), Email.user_id == current_user.id).all()

        for email in emails:
            if not email.isDelete:
                email.isDelete = True
                flash(f"{len(emails)} email(s) supprimé(s).", "success")
            else:
                email.isDelete = False
                flash(f"{len(emails)} email(s) restauré(s).", "success")

        db.session.commit()
        
    else:
        flash("Aucun email sélectionné.", "warning")

    return redirect(url_for('inbox'))


# Messages envoyés
@app.route('/message_sent')
@login_required
def message_sent():
    emails = Email.query.filter_by(user_id=current_user.id,prediction="NON-SPAM",isDelete=False).order_by(Email.timestamp.desc()).all()
    email_count = Email.query.filter_by(sender=current_user.email,prediction="NON-SPAM", isDelete=False,isRead=False).count()
    draft_count= Email.query.filter(
    (
        (Email.user_id == current_user.id) |
        (Email.sender == current_user.email)
    ) &
    (Email.isDelete == True)
    ).count()
    sent_count = Email.query.filter_by(user_id=current_user.id,prediction="NON-SPAM",isDelete=False).count()

    spam_count = Email.query.filter_by(prediction="SPAM",user_id=current_user.id).count()
    return render_template('message_sent.html', emails=emails,email_count=email_count,spam_count=spam_count, draft_count=draft_count, sent_count=sent_count)

@app.route('/reply/<int:email_id>')
@login_required
def reply(email_id):
    email = Email.query.filter_by(id=email_id, user_id=current_user.id).first_or_404()
    
    # Si non lu, on le marque comme lu
    if not email.isRead:
        email.isRead = True
        db.session.commit()
    email_count = Email.query.filter_by(sender=current_user.email,prediction="NON-SPAM", isDelete=False,isRead=False).count()
    draft_count= Email.query.filter(
    (
        (Email.user_id == current_user.id) |
        (Email.sender == current_user.email)
    ) &
    (Email.isDelete == True)
    ).count()
    sent_count = Email.query.filter_by(user_id=current_user.id,prediction="NON-SPAM",isDelete=False).count()

    spam_count = Email.query.filter_by(prediction="SPAM",user_id=current_user.id).count()
    return render_template('reply.html', email=email,email_count=email_count,spam_count=spam_count, draft_count=draft_count, sent_count=sent_count)

# Corbeille
@app.route('/draft')
@login_required
def draft():
    emails = Email.query.filter(
    (
        (Email.user_id == current_user.id) |
        (Email.sender == current_user.email)
    ) &
    (Email.isDelete == True)
).order_by(Email.timestamp.desc()).all()
    email_count = Email.query.filter_by(sender=current_user.email,prediction="NON-SPAM", isDelete=False,isRead=False).count()
    draft_count= Email.query.filter(
    (
        (Email.user_id == current_user.id) |
        (Email.sender == current_user.email)
    ) &
    (Email.isDelete == True)
    ).count()
    sent_count = Email.query.filter_by(user_id=current_user.id,prediction="NON-SPAM",isDelete=False).count()

    spam_count = Email.query.filter_by(prediction="SPAM",user_id=current_user.id).count()
    return render_template('draft.html', emails=emails,email_count=email_count,spam_count=spam_count, draft_count=draft_count, sent_count=sent_count)


# Spam
@app.route('/spam')
@login_required
def spam():
    emails = Email.query.filter_by(prediction="SPAM",user_id=current_user.id).order_by(Email.timestamp.desc()).all()
    email_count = Email.query.filter_by(sender=current_user.email,prediction="NON-SPAM", isDelete=False,isRead=False).count()
    draft_count= Email.query.filter(
    (
        (Email.user_id == current_user.id) |
        (Email.sender == current_user.email)
    ) &
    (Email.isDelete == True)
    ).count()
    sent_count = Email.query.filter_by(user_id=current_user.id,prediction="NON-SPAM",isDelete=False).count()

    spam_count = Email.query.filter_by(prediction="SPAM",user_id=current_user.id).count()
    return render_template('spam.html', emails=emails,email_count=email_count,spam_count=spam_count, draft_count=draft_count, sent_count=sent_count)

# Enregistrement + prédiction
@app.route('/predict', methods=['POST'])
@login_required
def predict():
    objet = request.form["objet"]
    sender = request.form["sender"]
    message = request.form['compose_message']
    prediction = model.predict([message])[0]
    result = "SPAM" if prediction == 1 else "NON-SPAM"
    emails = Email.query.filter_by(sender=current_user.email,prediction="NON-SPAM",isDelete=False).order_by(Email.timestamp.desc()).all()
    email_count = Email.query.filter_by(sender=current_user.email,prediction="NON-SPAM", isDelete=False,isRead=False).count()
    draft_count= Email.query.filter(
    (
        (Email.user_id == current_user.id) |
        (Email.sender == current_user.email)
    ) &
    (Email.isDelete == True)
    ).count()
    sent_count = Email.query.filter_by(user_id=current_user.id,prediction="NON-SPAM",isDelete=False).count()

    spam_count = Email.query.filter_by(prediction="SPAM",user_id=current_user.id).count()
    new_email = Email(
        content=message,
        isDelete=False,
        isRead=False,
        objet=objet,
        sender=sender,
        prediction=result,
        user_id=current_user.id  # <-- ajout du user_id
    )
    db.session.add(new_email)
    db.session.commit()

    return render_template('listing.html', prediction=result, emails=emails,email_count=email_count,spam_count=spam_count, draft_count=draft_count, sent_count=sent_count)


# Mot de passe oublié
@app.route('/forgot_password')
def forgot_password():
    return render_template('forgot_password.html')

@app.template_filter('smart_datetime')
def smart_datetime(value):
    """Affiche l'heure si la date est aujourd'hui, sinon la date."""
    if not isinstance(value, datetime):
        return value  # sécurité
    now = datetime.now()
    if value.date() == now.date():
        return value.strftime("%H:%M")
    else:
        return value.strftime("%d %B")  # ex: 26 mai 2025


# Lancer le serveur
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
