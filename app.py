"""
Flask application orchestrating the AI workflow.
"""
import mimetypes
import os
from pathlib import Path

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_from_directory,
    abort,
)
from werkzeug.utils import secure_filename

from typing import Optional

import config
from config import (
    CHARACTER_DIR,
    SCENE_DIR,
    VIDEO_DIR,
    SECRET_KEY,
    DATABASE_URL,
    MAX_CONTENT_LENGTH,
)
from database import init_db, db
from models import Character, Scene, Video, PromptTemplate
from services.character_service import CharacterImageProcessor
from services.video_service import generate_video as call_video_api


DEFAULT_CHARACTER_PROMPTS = [
    (
        "Influencer Portrait",
        "Portrait of a stylish Mexican influencer with shoulder-length blonde hair, soft makeup, "
        "bright natural lighting, contemporary background, friendly confident expression."
    ),
    (
        "News Anchor Transform",
        "Transform this portrait into a professional news anchor sitting at a modern news desk. "
        "Keep the person's identity intact, add studio lighting, and subtle JobSite Sentry branding in the background."
    ),
    (
        "Podcast Host",
        "Style this person as a charismatic podcast host speaking into a microphone inside a cozy studio with warm lighting."
    ),
    (
        "Safety Supervisor",
        "Show this individual wearing a smart high-visibility vest and helmet, smiling confidently at a construction site."
    ),
]

DEFAULT_SCENE_PROMPTS = [
    (
        "Newsroom Overview",
        "Transform the character into a charismatic news anchor sitting at a modern news desk with "
        "JobSite Sentry branding on digital screens behind them."
    ),
    (
        "Podcast Set",
        "Place the character in a professional podcast studio with microphones, sound panels, and soft lighting."
    ),
    (
        "Boardroom Briefing",
        "Depict the character leading a corporate meeting with JobSite Sentry analytics displayed on large monitors."
    ),
]


DATA_ROOT = config.DATA_DIR.resolve()


def relative_to_data(path: Path) -> str:
    """
    Convert an absolute path under DATA_ROOT to a POSIX-style relative path for storage.
    """
    resolved = path.resolve()
    try:
        rel = resolved.relative_to(DATA_ROOT)
    except ValueError as exc:
        raise ValueError(f"Path {resolved} is outside data directory") from exc
    return rel.as_posix()


def resolve_data_path(rel_path: str) -> Path:
    """
    Resolve a stored relative path back to an absolute path under DATA_ROOT.
    """
    candidate = Path(rel_path)
    if not candidate.is_absolute():
        candidate = DATA_ROOT / candidate
    candidate = candidate.resolve()
    if not candidate.is_relative_to(DATA_ROOT):
        raise ValueError("Invalid path outside data directory")
    return candidate


def delete_file(rel_path: Optional[str]) -> None:
    """Remove a stored file if it exists."""
    if not rel_path:
        return
    try:
        path = resolve_data_path(rel_path)
    except ValueError:
        return
    if path.exists():
        path.unlink()


def ensure_relative_path(path_str: Optional[str]) -> Optional[str]:
    if not path_str:
        return None
    path = Path(path_str)
    if path.is_absolute():
        return relative_to_data(path)
    return path.as_posix()


def ensure_default_prompts():
    """Insert default prompt templates if they are missing."""
    existing = {
        (template.category, template.title)
        for template in PromptTemplate.query.all()
    }

    for title, prompt in DEFAULT_CHARACTER_PROMPTS:
        key = ("character", title)
        if key not in existing:
            db.session.add(PromptTemplate(category="character", title=title, prompt=prompt))
    for title, prompt in DEFAULT_SCENE_PROMPTS:
        key = ("scene", title)
        if key not in existing:
            db.session.add(PromptTemplate(category="scene", title=title, prompt=prompt))
    db.session.commit()


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
    app.config["UPLOAD_FOLDER"] = CHARACTER_DIR

    init_db(app)

    with app.app_context():
        db.create_all()
        ensure_default_prompts()

    @app.route("/")
    def index():
        counts = {
            "characters": Character.query.count(),
            "scenes": Scene.query.count(),
            "videos": Video.query.count(),
        }
        return render_template("index.html", counts=counts)

    @app.route("/files/<path:rel_path>")
    def serve_file(rel_path):
        try:
            file_path = resolve_data_path(rel_path)
        except ValueError:
            abort(404)
        if not file_path.exists():
            abort(404)
        return send_from_directory(file_path.parent, file_path.name)

    @app.route("/characters/new", methods=["GET", "POST"])
    def new_character():
        characters = Character.query.order_by(Character.created_at.desc()).all()
        character_rows = []
        changed = False
        for character in characters:
            original_rel = ensure_relative_path(character.original_image_path)
            processed_rel = ensure_relative_path(character.processed_image_path)
            if original_rel != character.original_image_path:
                character.original_image_path = original_rel
                changed = True
            if processed_rel != character.processed_image_path:
                character.processed_image_path = processed_rel
                changed = True
            preview_rel = processed_rel or original_rel
            character_rows.append((character, preview_rel))
        if changed:
            db.session.commit()
        templates = PromptTemplate.query.filter_by(category="character").order_by(PromptTemplate.title).all()
        default_prompt = templates[0].prompt if templates else ""
        if request.method == "GET":
            return render_template(
                "characters/new.html",
                character_rows=character_rows,
                prompt_templates=templates,
                default_prompt=default_prompt,
            )

        name = request.form.get("name", "").strip()
        prompt = request.form.get("prompt", "").strip()
        file = request.files.get("image")

        if not name:
            flash("Character name is required.", "danger")
            return redirect(url_for("new_character"))

        processor = CharacterImageProcessor()
        final_path: Path
        original_path: Path

        try:
            if file and file.filename:
                filename = secure_filename(file.filename)
                original_path = CHARACTER_DIR / filename
                file.save(original_path)

                if prompt:
                    final_path = CHARACTER_DIR / f"{original_path.stem}_edited.png"
                    processor.edit_image(
                        image_path=original_path,
                        prompt=prompt,
                        output_path=final_path,
                        size="1536x1024",
                    )
                else:
                    final_path = original_path
            else:
                if not prompt:
                    flash("Provide a prompt to generate a new character portrait.", "danger")
                    return redirect(url_for("new_character"))
                safe_name = secure_filename(name) or "character"
                final_path = CHARACTER_DIR / f"{safe_name}_generated.png"
                processor.generate_character_face(
                    prompt=prompt,
                    output_path=final_path,
                    size="1024x1024",
                )
                original_path = final_path

            character = Character(
                name=name,
                description=prompt or None,
                original_image_path=relative_to_data(original_path),
                processed_image_path=relative_to_data(final_path),
            )
            db.session.add(character)
            db.session.commit()
            flash("Character saved successfully.", "success")
        except Exception as exc:
            db.session.rollback()
            flash(f"Failed to create character: {exc}", "danger")

        return redirect(url_for("new_character"))

    @app.post("/characters/<int:character_id>/delete")
    def delete_character(character_id):
        character = Character.query.get_or_404(character_id)

        scene_image_paths = [scene.image_path for scene in character.scenes]

        delete_file(character.original_image_path)
        if character.processed_image_path and character.processed_image_path != character.original_image_path:
            delete_file(character.processed_image_path)
        for rel_path in scene_image_paths:
            delete_file(rel_path)

        try:
            db.session.delete(character)
            db.session.commit()
            flash("Character deleted.", "info")
        except Exception as exc:
            db.session.rollback()
            flash(f"Failed to delete character: {exc}", "danger")

        return redirect(url_for("new_character"))

    @app.route("/scenes/new", methods=["GET", "POST"])
    def new_scene():
        characters = Character.query.order_by(Character.created_at.desc()).all()
        scenes = Scene.query.order_by(Scene.created_at.desc()).limit(10).all()
        scene_rows = []
        changed = False
        for scene in scenes:
            rel_path = ensure_relative_path(scene.image_path)
            if rel_path != scene.image_path:
                scene.image_path = rel_path
                changed = True
            scene_rows.append((scene, rel_path))
        if changed:
            db.session.commit()
        templates = PromptTemplate.query.filter_by(category="scene").order_by(PromptTemplate.title).all()
        default_prompt = templates[0].prompt if templates else ""

        if request.method == "GET":
            return render_template(
                "scenes/new.html",
                characters=characters,
                scene_rows=scene_rows,
                default_prompt=default_prompt,
                prompt_templates=templates,
            )

        character_id = request.form.get("character_id")
        theme = request.form.get("theme", "custom")
        prompt = request.form.get("prompt", "").strip()

        if not character_id or not prompt:
            flash("Character and prompt are required.", "danger")
            return redirect(url_for("new_scene"))

        character = Character.query.get(character_id)
        if not character:
            flash("Selected character not found.", "danger")
            return redirect(url_for("new_scene"))

        processor = CharacterImageProcessor()
        base_image_path = resolve_data_path(character.processed_image_path or character.original_image_path)
        scene_filename = f"scene_{character.id}_{len(character.scenes)+1}.png"
        scene_output_path = SCENE_DIR / scene_filename

        try:
            processor.generate_scene_image(
                base_image_path=base_image_path,
                theme_prompt=prompt,
                output_path=scene_output_path,
                size="1536x1024",
            )

            scene = Scene(
                character=character,
                theme=theme,
                prompt=prompt,
                image_path=relative_to_data(scene_output_path),
            )
            db.session.add(scene)
            db.session.commit()
            flash("Scene generated successfully.", "success")
        except Exception as exc:
            db.session.rollback()
            flash(f"Failed to generate scene: {exc}", "danger")

        return redirect(url_for("new_scene"))

    def build_video_prompt(dialogue: str) -> str:
        """
        Build the full video prompt by combining generic instructions with the dialogue.
        
        Args:
            dialogue: The dialogue text entered by the user.
            
        Returns:
            Combined prompt with generic instructions and dialogue.
        """
        generic_prompt = (
            "Maintain the same lighting, color palette, background, and overall visual style "
            "as shown in the reference image. Keep the character's appearance, clothing, and "
            "setting consistent with the image. Do not add any text overlays or captions. "
            "The character should speak naturally and expressively. "
        )
        return f"{generic_prompt}Dialogue: {dialogue}"

    @app.route("/videos/new", methods=["GET", "POST"])
    def new_video():
        scenes = Scene.query.order_by(Scene.created_at.desc()).all()
        scene_rows = []
        changed_scene = False
        for scene in scenes:
            rel_path = ensure_relative_path(scene.image_path)
            if rel_path != scene.image_path:
                scene.image_path = rel_path
                changed_scene = True
            scene_rows.append(scene)
        videos = Video.query.order_by(Video.created_at.desc()).limit(10).all()
        if changed_scene:
            db.session.commit()
        default_dialogue = (
            "Jobsite Sentry is an AI-powered platform that keeps your team safe, "
            "tracks site activity, and gives real-time alerts for any unusual events. "
            "It is like having a 24/7 smart safety assistant on site."
        )

        if request.method == "GET":
            return render_template(
                "videos/new.html",
                scenes=scene_rows,
                videos=videos,
                default_prompt=default_dialogue,
            )

        scene_id = request.form.get("scene_id")
        dialogue = request.form.get("prompt", "").strip()

        if not scene_id or not dialogue:
            flash("Scene and dialogue are required.", "danger")
            return redirect(url_for("new_video"))

        scene = Scene.query.get(scene_id)
        if not scene:
            flash("Selected scene not found.", "danger")
            return redirect(url_for("new_video"))

        try:
            image_path = resolve_data_path(scene.image_path)
        except ValueError:
            flash("Scene image file path is invalid.", "danger")
            return redirect(url_for("new_video"))

        if not image_path.exists():
            flash("Scene image file is missing.", "danger")
            return redirect(url_for("new_video"))

        try:
            # Build the full prompt with generic instructions + dialogue
            full_prompt = build_video_prompt(dialogue)
            response = call_video_api(prompt=full_prompt, image_path=image_path)
            video_url = response.get("video_url") or response.get("url")
            job_id = response.get("job_id") or response.get("id")
            status = response.get("status", "submitted")

            # Store the dialogue (what user entered) in the database
            video = Video(
                scene=scene,
                prompt=dialogue,
                job_id=job_id,
                video_url=video_url,
                status=status,
            )
            db.session.add(video)
            db.session.commit()

            if video_url:
                flash(f"Video generated! URL: {video_url}", "success")
            else:
                flash("Video request submitted. Check status later.", "info")
        except Exception as exc:
            db.session.rollback()
            flash(f"Failed to generate video: {exc}", "danger")

        return redirect(url_for("new_video"))

    return app


app = create_app()


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))

