from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import uuid
import subprocess
import tempfile
import threading
import requests
from pathlib import Path

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

UPLOAD_FOLDER = Path(__file__).parent.parent / 'uploads'
OUTPUT_FOLDER = Path(__file__).parent.parent / 'outputs'
UPLOAD_FOLDER.mkdir(exist_ok=True)
OUTPUT_FOLDER.mkdir(exist_ok=True)

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'bmp'}

SADTALKER_SERVICE_URL = os.environ.get('SADTALKER_URL', 'http://localhost:5001')

# Prevent concurrent generation
_generation_lock = threading.Lock()

# Prevent concurrent generation
_generation_lock = threading.Lock()


def generate_tts_audio(text: str, output_path: str, voice: str = 'en-US-GuyNeural', rate: str = '+0%') -> str:
    """Generate TTS audio from text using Microsoft Edge TTS and convert to WAV"""
    mp3_path = output_path.replace('.wav', '.mp3')

    import asyncio
    import edge_tts

    print(f"TTS params: voice={voice}, rate={rate}, text_len={len(text)}")
    print(f"Text preview: {text[:80]}...")

    async def _generate():
        try:
            communicate = edge_tts.Communicate(text, voice, rate=rate)
            await communicate.save(mp3_path)
        except Exception as e:
            raise RuntimeError(f"edge-tts error: {e}")

    asyncio.run(_generate())

    # Verify MP3 was created
    if not os.path.exists(mp3_path) or os.path.getsize(mp3_path) == 0:
        raise RuntimeError(f"TTS failed: MP3 file not created at {mp3_path}")
    print(f"MP3 created: {os.path.getsize(mp3_path)} bytes")

    # Convert MP3 to WAV using ffmpeg (Wav2Lip/SadTalker requires WAV)
    result = subprocess.run([
        'ffmpeg', '-y', '-i', mp3_path,
        '-ar', '16000', '-ac', '1',
        output_path
    ], capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg conversion failed: {result.stderr}")

    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        raise RuntimeError(f"TTS failed: WAV file not created at {output_path}")
    print(f"WAV created: {os.path.getsize(output_path)} bytes")

    return output_path


def run_wav2lip(image_path: str, audio_path: str, output_path: str) -> str:
    """Run Wav2Lip to generate lip-synced video (no head pose)"""
    wav2lip_dir = Path(__file__).parent.parent / 'wav2lip'
    inference_script = wav2lip_dir / 'inference.py'

    if not inference_script.exists():
        raise FileNotFoundError(
            "Wav2Lip inference.py not found. Please clone Wav2Lip into the wav2lip/ directory.\n"
            "Run: git clone https://github.com/Rudrabha/Wav2Lip.git wav2lip"
        )

    cmd = [
        'python', 'inference.py',
        '--checkpoint_path', str(wav2lip_dir / 'wav2lip.pth'),
        '--face', str(image_path),
        '--audio', str(audio_path),
        '--outfile', str(output_path),
        '--nosmooth',
    ]

    print(f"Running Wav2Lip: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(wav2lip_dir))

    if result.returncode != 0:
        raise RuntimeError(f"Wav2Lip failed: {result.stderr}")

    return output_path


def run_sadtalker(image_path: str, audio_path: str, output_path: str,
                  pose_style: int = 0, expression_scale: float = 1.0,
                  input_yaw: list = None, input_pitch: list = None,
                  input_roll: list = None) -> str:
    """Call SadTalker service via HTTP"""
    payload = {
        'image_path': str(image_path),
        'audio_path': str(audio_path),
        'pose_style': pose_style,
        'expression_scale': expression_scale,
    }
    if input_yaw:
        payload['input_yaw'] = input_yaw
    if input_pitch:
        payload['input_pitch'] = input_pitch
    if input_roll:
        payload['input_roll'] = input_roll

    print(f"Calling SadTalker service at {SADTALKER_SERVICE_URL}...")
    resp = requests.post(f"{SADTALKER_SERVICE_URL}/api/generate", json=payload, timeout=1200)

    if resp.status_code != 200:
        raise RuntimeError(f"SadTalker service error: {resp.text}")

    data = resp.json()
    if not data.get('success'):
        raise RuntimeError(f"SadTalker failed: {data.get('error')}")

    # Download the result from SadTalker service
    video_resp = requests.get(f"{SADTALKER_SERVICE_URL}{data['video_url']}")
    with open(output_path, 'wb') as f:
        f.write(video_resp.content)

    return str(output_path)


@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/upload-image', methods=['POST'])
def upload_image():
    """Upload avatar image"""
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'png'
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return jsonify({'error': f'Unsupported file type. Allowed: {ALLOWED_IMAGE_EXTENSIONS}'}), 400

    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = UPLOAD_FOLDER / filename
    file.save(str(filepath))

    return jsonify({
        'success': True,
        'image_id': filename,
        'image_url': f'/uploads/{filename}'
    })


@app.route('/api/generate', methods=['POST'])
def generate():
    """Generate talking avatar video from text and image"""
    # Prevent concurrent generation
    if not _generation_lock.acquire(blocking=False):
        return jsonify({'error': 'A generation is already in progress. Please wait.'}), 429

    try:
        return _generate()
    finally:
        _generation_lock.release()


def _generate():
    data = request.get_json()
    print(f"\n{'='*60}")
    print(f"RECEIVED REQUEST:")
    print(f"  job_id: {uuid.uuid4().hex[:8]}...")
    print(f"  text: {data.get('text', '')[:60]}...")
    print(f"  voice: {data.get('voice')}")
    print(f"  rate: {data.get('rate')}")
    print(f"  engine: {data.get('engine')}")
    print(f"{'='*60}\n")

    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400

    image_id = data.get('image_id')
    text = data['text']
    voice_name = data.get('voice', 'en-US-GuyNeural')
    rate = data.get('rate', '+0%')
    engine = data.get('engine', 'sadtalker')
    pose_style = data.get('pose_style', 0)
    expression_scale = data.get('expression_scale', 1.0)

    if not image_id:
        return jsonify({'error': 'No image_id provided. Upload an image first.'}), 400

    image_path = UPLOAD_FOLDER / image_id
    if not image_path.exists():
        return jsonify({'error': 'Image not found'}), 400

    job_id = uuid.uuid4().hex
    audio_path = OUTPUT_FOLDER / f"{job_id}_audio.wav"
    output_path = OUTPUT_FOLDER / f"{job_id}_output.mp4"

    try:
        # Step 1: Generate TTS audio
        print(f"Generating TTS audio for: {text[:50]}...")
        generate_tts_audio(text, str(audio_path), voice=voice_name, rate=rate)

        # Step 2: Run lip-sync engine
        if engine == 'sadtalker':
            print(f"Running SadTalker with pose_style={pose_style}, expression_scale={expression_scale}...")
            run_sadtalker(str(image_path), str(audio_path), str(output_path),
                         pose_style=pose_style, expression_scale=expression_scale)
        else:
            print("Running Wav2Lip lip-sync...")
            run_wav2lip(str(image_path), str(audio_path), str(output_path))

        return jsonify({
            'success': True,
            'job_id': job_id,
            'video_url': f'/outputs/{job_id}_output.mp4',
            'audio_url': f'/outputs/{job_id}_audio.wav'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/uploads/<filename>')
def serve_upload(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route('/outputs/<filename>')
def serve_output(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)


@app.route('/api/images')
def list_images():
    """List uploaded images"""
    images = []
    for f in UPLOAD_FOLDER.iterdir():
        if f.suffix.lower()[1:] in ALLOWED_IMAGE_EXTENSIONS:
            images.append({
                'id': f.name,
                'url': f'/uploads/{f.name}',
                'name': f.name
            })
    return jsonify({'images': images})


if __name__ == '__main__':
    print("Starting TTS Avatar server...")
    print(f"SadTalker service: {SADTALKER_SERVICE_URL}")
    print("Open http://localhost:5000 in your browser")
    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)
