from flask import Flask, request, render_template, jsonify
import base64
import requests
import os
import re

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "uploads"
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
api_key = os.getenv("GROQ_API_KEY")

HEADERS = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

def clean_text(text: str) -> str:
    text = re.sub(r"[*#`>]+", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    question = request.form.get('question', '')
    image_file = request.files.get('image', None)

    img_base64 = None
    if image_file and image_file.filename != '':
        img_path = os.path.join(app.config['UPLOAD_FOLDER'], image_file.filename)
        image_file.save(img_path)
        with open(img_path, "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode("utf-8")
        os.remove(img_path)

    content = []
    if question.strip():
        content.append({"type": "text", "text": question})
    if img_base64:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}
        })

    if not content:
        return jsonify({"error": "Please provide a question or an image."}), 400

    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [{"role": "user", "content": content}],
        "max_tokens": 300
    }

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json=payload,
            headers=HEADERS
        )
        if response.status_code != 200:
            return jsonify({"error": response.text}), 500

        data = response.json()
        answer = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        cleaned_answer = clean_text(answer)
        return jsonify({"answer": cleaned_answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
