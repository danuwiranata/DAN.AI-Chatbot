import os
import openai
import pandas as pd
from flask import Flask, render_template, request, jsonify
from difflib import get_close_matches
import speech_recognition as sr
from werkzeug.utils import secure_filename

# ==== Konfigurasi API ====
openai.api_key = "YOUR_OPENAI_API_KEY"  # Atau gunakan Google Gemini API

# ==== Inisialisasi Flask ====
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# ==== Load FAQ Excel ====
faq_data = pd.read_excel("faq.xlsx")

# ==== Fungsi Cari Jawaban FAQ ====
def cari_jawaban(pertanyaan):
    pertanyaan_list = faq_data['pertanyaan'].tolist()
    match = get_close_matches(pertanyaan.lower(), pertanyaan_list, n=1, cutoff=0.5)
    if match:
        idx = faq_data[faq_data['pertanyaan'] == match[0]].index[0]
        return faq_data.loc[idx, 'jawaban']
    else:
        return None

# ==== Speech-to-Text dengan Whisper ====
def speech_to_text(audio_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio, language="id-ID")
    except sr.UnknownValueError:
        return "Maaf, saya tidak memahami suara Anda."

# ==== Generate Gambar ====
def generate_image(prompt):
    response = openai.Image.create(
        prompt=prompt,
        n=1,
        size="512x512"
    )
    return response['data'][0]['url']

# ==== ROUTES ====
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    user_input = request.form.get("question")
    img_prompt = request.form.get("image_prompt")
    is_audio = request.files.get("audio")

    # Jika ada audio, ubah ke teks
    if is_audio:
        audio_file = secure_filename(is_audio.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], audio_file)
        is_audio.save(path)
        user_input = speech_to_text(path)

    # Cek FAQ
    jawaban = cari_jawaban(user_input)
    if not jawaban:
        jawaban = "Maaf, saya tidak menemukan jawaban di FAQ."

    # Generate Gambar jika diminta
    img_url = None
    if img_prompt:
        img_url = generate_image(img_prompt)

    return jsonify({"jawaban": jawaban, "img_url": img_url})

if __name__ == '__main__':
    app.run(debug=True)
