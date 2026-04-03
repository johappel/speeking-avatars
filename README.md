# TTS Avatar - Sprechender Avatar

Erstelle einen sprechenden Avatar aus einem beliebigen Portrait-Bild mit Text-to-Speech und Lip-Sync.

## Architektur

```
┌─────────────────────────────────────────────────┐
│                  Web Frontend                    │
│         (HTML/CSS/JS - index.html)               │
│  - Bild-Upload (Drag & Drop)                     │
│  - Texteingabe                                   │
│  - Engine-Auswahl (Wav2Lip / SadTalker)          │
│  - Video-Player für Ergebnisse                   │
└──────────────────────┬──────────────────────────┘
                       │ HTTP/JSON
┌──────────────────────▼──────────────────────────┐
│               Flask Backend (Port 5000)          │
│              (backend/app.py)                    │
│  - Bild-Upload Handler                           │
│  - TTS Audio-Generierung (edge-tts)              │
│  - Routing zu Lip-Sync Engine                    │
│  - Video-Serving                                 │
└──────────┬────────────────────┬──────────────────┘
           │                    │
┌──────────▼──────────┐  ┌──────▼──────────────────┐
│     Wav2Lip          │  │   SadTalker Service     │
│ (nur Lippen-Sync)    │  │ (mit Kopfpose/Gestik)   │
│ subprocess           │  │ HTTP auf Port 5001      │
└─────────────────────┘  └─────────────────────────┘
```

## Voraussetzungen

### Option A: Docker (empfohlen)

- Docker + Docker Compose
- NVIDIA Container Toolkit (für CUDA)

### Option B: Manuell

- Python 3.12
- FFmpeg (für Video-Verarbeitung)
- CUDA-fähige GPU (empfohlen)

## Docker Setup (empfohlen)

### 1. Submodule initialisieren

```bash
git submodule update --init --recursive
```

### 2. Checkpoints herunterladen

SadTalker Checkpoints müssen manuell in `sadtalker/checkpoints/` gespeichert werden:

```bash
cd sadtalker
python download_checkpoints.py
```

### 3. Docker starten

```bash
docker compose up --build
```

Das startet:
- **Backend** → http://localhost:5000
- **SadTalker Service** → http://localhost:5001 (mit CUDA)

### 4. Stoppen

```bash
docker compose down
```

## Manuelle Installation

### 1. Submodule initialisieren

```bash
git submodule update --init --recursive
```

### 2. Backend Dependencies

```bash
pip install -r backend/requirements.txt
```

### 3. FFmpeg installieren

```bash
winget install Gyan.FFmpeg
```

### 4. SadTalker Checkpoints herunterladen

```bash
cd sadtalker
python download_checkpoints.py
```

Oder manuell von [SadTalker Releases](https://github.com/OpenTalker/SadTalker/releases/tag/v0.0.2-rc) und [HF Space](https://huggingface.co/spaces/John6666/SadTalkerGitHub/tree/main/checkpoints):

| Datei | Größe |
|-------|-------|
| `SadTalker_V0.0.2_256.safetensors` | ~645 MB |
| `SadTalker_V0.0.2_512.safetensors` | ~691 MB |
| `mapping_00109-model.pth.tar` | ~149 MB |
| `mapping_00229-model.pth.tar` | ~149 MB |
| `facevid2vid_00189-model.pth.tar` | ~2 GB |
| `epoch_20.pth` | ~275 MB |
| `shape_predictor_68_face_landmarks.dat` | ~95 MB |
| `hub.zip` → nach `hub/` entpacken | ~200 MB |

Alle Dateien in `sadtalker/checkpoints/` speichern.

### 5. Wav2Lip Checkpoint

Lade `wav2lip.pth` von [Nekochu/Wav2Lip](https://huggingface.co/Nekochu/Wav2Lip/resolve/main/wav2lip.pth) und speichere es in `wav2lip/`.

## Starten

### Option A: Nur Wav2Lip (einfacher)

```bash
python backend/app.py
```

→ http://localhost:5000 → Engine "Wav2Lip" wählen

### Option B: Mit SadTalker (Kopfpose + Gestik)

**Terminal 1 – SadTalker Service starten:**
```bash
cd sadtalker
python sadtalker_service.py
```

**Terminal 2 – Backend starten:**
```bash
python backend/app.py
```

→ http://localhost:5000 → Engine "SadTalker" wählen

## Verwendung

1. **Bild hochladen**: Drag & Drop oder klicken
2. **Text eingeben**: Was soll der Avatar sagen?
3. **Stimme wählen**: 30+ Microsoft Edge Neural Voices (Deutsch, Englisch, Französisch, Spanisch, Italienisch)
4. **Engine wählen**: Wav2Lip (nur Lippen) oder SadTalker (mit Kopfpose)
5. **Posen-Stil**: Natürlich → Expressiv
6. **Ausdrucksstärke**: Dezent → Übertrieben
7. **Generieren** und Video abspielen

## Projektstruktur

```
speeking/
├── backend/
│   ├── app.py              # Haupt-Flask-Server (Port 5000)
│   └── requirements.txt    # Python Dependencies
├── frontend/
│   └── index.html          # Web UI
├── wav2lip/                # Git Submodule
├── sadtalker/              # Git Submodule
│   ├── sadtalker_service.py  # SadTalker HTTP-Service (Port 5001)
│   ├── inference.py          # SadTalker Inference
│   ├── checkpoints/          # SadTalker Modelle
│   └── download_checkpoints.py
├── uploads/                # Hochgeladene Bilder
├── outputs/                # Generierte Videos
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.sadtalker
└── README.md
```

## API-Endpunkte

### Backend (Port 5000)

| Methode | Pfad | Beschreibung |
|---------|------|--------------|
| GET | `/` | Web UI |
| POST | `/api/upload-image` | Bild hochladen |
| POST | `/api/generate` | Video generieren |
| GET | `/api/images` | Liste der Bilder |

### SadTalker Service (Port 5001)

| Methode | Pfad | Beschreibung |
|---------|------|--------------|
| GET | `/health` | Health Check |
| POST | `/api/generate` | Video mit Kopfpose generieren |

## Troubleshooting

### "SadTalker service error"
Stelle sicher, dass der SadTalker Service läuft: `python sadtalker/sadtalker_service.py`

### "Checkpoint not found"
Lade die Checkpoints herunter und speichere sie in `sadtalker/checkpoints/`

### "CUDA out of memory"
Verwende `--size 256` statt 512 oder reduziere die Bildauflösung

### dlib Kompilierungsfehler
SadTalker benötigt dlib für die Gesichtserkennung. Unter Python 3.12 kann die Kompilierung fehlschlagen. Alternative:
- Conda verwenden: `conda install -c conda-forge dlib`
- Oder Python 3.10/3.11 nutzen

## Lizenz

Dieses Projekt ist unter der **MIT License** lizenziert – siehe [LICENSE](LICENSE).

## Danksagungen

Dieses Projekt basiert auf folgenden Open-Source-Projekten:

| Projekt | Lizenz | Beschreibung |
|---------|--------|--------------|
| [**SadTalker**](https://github.com/OpenTalker/SadTalker) | MIT | Audio-gesteuerte 3D-Gesichtsanimation mit Kopfpose |
| [**Wav2Lip**](https://github.com/Rudrabha/Wav2Lip) | MIT | Lip-Sync aus Bild und Audio |
| [**edge-tts**](https://github.com/rany2/edge-tts) | LGPL-3.0 | Microsoft Edge Text-to-Speech API |
| [**GFPGAN**](https://github.com/TencentARC/GFPGAN) | Apache-2.0 | Gesichtsverbesserung |
| [**face_alignment**](https://github.com/1adrianb/face-alignment) | BSD-3 | Gesichtserkennung und Landmark-Erkennung |
| [**Deep3DFaceRecon_pytorch**](https://github.com/sicxu/Deep3DFaceRecon_pytorch) | MIT | 3D-Gesichtsrekonstruktion |

Vielen Dank an alle Contributors dieser großartigen Projekte!
