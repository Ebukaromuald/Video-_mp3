import os
import uuid
import subprocess
import time
from flask import Flask, render_template, request, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB
UPLOAD_FOLDER = 'static/converted'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CONVERTED_FOLDER'] = UPLOAD_FOLDER  # Use same folder for converted files

# Create folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Auto-delete old files after 1 hour
def clean_old_files(folder, age_limit_seconds=3600):
    now = time.time()
    for filename in os.listdir(folder):
        filepath = os.path.join(folder, filename)
        if os.path.isfile(filepath):
            if now - os.path.getmtime(filepath) > age_limit_seconds:
                os.remove(filepath)

@app.route('/', methods=['GET', 'POST', 'HEAD'])
def index():
    clean_old_files(app.config['UPLOAD_FOLDER'])

    if request.method == 'POST':
        uploaded_files = request.files.getlist('videos')
        boost = 'boost_volume' in request.form
        download_links = []

        for file in uploaded_files:
            if file and file.filename.endswith('.mp4'):
                filename = secure_filename(file.filename)
                video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(video_path)

                mp3_filename = filename.rsplit('.', 1)[0] + '.mp3'
                mp3_path = os.path.join(app.config['CONVERTED_FOLDER'], mp3_filename)

                command = ['ffmpeg', '-i', video_path]
                if boost:
                    command += ['-filter:a', 'volume=1.5']
                command += [mp3_path, '-y']

                result = subprocess.run(command, capture_output=True, text=True)

                if result.returncode != 0:
                    print("FFmpeg Error:", result.stderr)
                else:
                    print("FFmpeg Success:", mp3_path)
                    download_links.append(f'/converted/{mp3_filename}')

        return render_template('result.html', links=download_links)

    return render_template('index.html')

@app.route('/converted/<filename>')
def download_file(filename):
    return send_from_directory(app.config['CONVERTED_FOLDER'], filename)

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/support')
def support():
    return render_template('support.html')

@app.errorhandler(413)
def file_too_large(e):
    return "Error: File too large. Maximum allowed size is 100MB.", 413

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
