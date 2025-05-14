from flask import Flask
import joblib

# Chargement du modèle sauvegardé
model = joblib.load('spam_model.pkl')

# Exemple d'utilisation
prediction = model.predict(["Hello, you've won a prize!"])
print(prediction)  # Affichera 1 (spam) ou 0 (non-spam)
