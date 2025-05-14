import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
import joblib

# Chargement du fichier spam.csv
data = pd.read_csv("spam.csv", encoding="latin-1")[["v1", "v2"]]
data.columns = ['label', 'message']
data['label'] = data['label'].map({'ham': 0, 'spam': 1})

# Découpage train/test
X_train, X_test, y_train, y_test = train_test_split(data['message'], data['label'], test_size=0.2, random_state=42)

# Pipeline : vectorisation + modèle
pipeline = Pipeline([
    ('vectorizer', CountVectorizer()),
    ('classifier', MultinomialNB())
])

# Entraînement du modèle
pipeline.fit(X_train, y_train)

# Sauvegarde dans un fichier pickle
joblib.dump(pipeline, 'spam_model.pkl')
print("✅ Modèle entraîné et sauvegardé sous spam_model.pkl")



from sklearn.metrics import accuracy_score

# Prédictions sur les données de test
y_pred = pipeline.predict(X_test)

# Calcul de l'accuracy
accuracy = accuracy_score(y_test, y_pred)
print(f"🎯 Accuracy du modèle : {accuracy:.2%}")

