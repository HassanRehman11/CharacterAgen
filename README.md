# AI Video Workflow (Flask)

This application orchestrates a three-step workflow to generate promotional videos:

1. **Character Generation** – upload or transform a portrait and store it for reuse.
2. **Scene Creation** – apply themed prompts (newsroom, podcast, etc.) to the character image.
3. **Video Generation** – submit the scene image and prompt to an external API to obtain a video URL.

## Features

- SQLite persistence with SQLAlchemy models (Characters, Scenes, Videos).
- Uses OpenAI Image API to transform character portraits and build themed scenes.
- Built-in prompt template library saved in the database for both character and scene generation.
- Integrates with an external `/api/generate-video` endpoint using multipart form-data.
- Stores generated assets under the `data/` directory for later reuse.

## Requirements

```
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file with the following (and any overrides you need):

```
OPENAI_API_KEY=your_openai_api_key
VIDEO_API_URL=http://35.229.117.169:8000/api/generate-video
VIDEO_API_EMAIL=rehmanhassan@gmail.com
VIDEO_API_SECRET=hakuna_matata
VIDEO_API_NAME=anonymous
SECRET_KEY=change-this-secret
```

All generated files and the database live under `data/`.

## Running

```
flask --app app run
# or simply:
python app.py
```

The app starts on `http://127.0.0.1:5000/`. Follow the steps in the UI:

1. **Characters** – upload a portrait and optional prompt to transform it; the output is also resized to 1280×720.
2. **Scenes** – choose a character, pick a theme (or custom prompt), and generate a themed scene image.
3. **Videos** – select a scene, adjust the video prompt, and submit to the external video service. The response (including job ID / URL) is stored in the database and shown in the UI.

## Updating the Database

The app automatically creates the SQLite database on first run. To reset:

```
rm data/workflow.db
```

## Notes

- The OpenAI image edit step and the external video API both incur latency and require valid API credentials.
- The workflow stores media files under `data/characters`, `data/scenes`, and `data/videos`. Ensure sufficient disk space.
- To inspect JSON responses (e.g., for job status), check the saved Video entry in the UI or the database.

