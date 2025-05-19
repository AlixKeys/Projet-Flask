from flask import Flask, render_template, request, jsonify
import joblib

app = Flask(__name__)
model = joblib.load('spam_model.pkl')

@app.route('/')
def home():
    return render_template('compose.html')

@app.route('/predict', methods=['POST'])
def predict():
    message = request.form['message']  # récupère le message depuis le formulaire
    prediction = model.predict([message])[0]  # 0 ou 1
    result = "SPAM" if prediction == 1 else "NON-SPAM"
    return render_template('compose.html', prediction=result)

if __name__ == '__main__':
    app.run(debug=True)
