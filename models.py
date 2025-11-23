"""
Database models for the workflow application.
"""
from datetime import datetime
from database import db


class PromptTemplate(db.Model):
    __tablename__ = "prompt_templates"

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)  # e.g., character, scene
    title = db.Column(db.String(120), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("category", "title", name="uq_prompt_category_title"),
    )

    def __repr__(self):
        return f"<PromptTemplate {self.category}:{self.title}>"


class Character(db.Model):
    __tablename__ = "characters"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    original_image_path = db.Column(db.String(255), nullable=False)
    processed_image_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    scenes = db.relationship("Scene", backref="character", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Character {self.name}>"


class Scene(db.Model):
    __tablename__ = "scenes"

    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey("characters.id"), nullable=False)
    theme = db.Column(db.String(80), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    videos = db.relationship("Video", backref="scene", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Scene {self.theme} ({self.character.name})>"


class Video(db.Model):
    __tablename__ = "videos"

    id = db.Column(db.Integer, primary_key=True)
    scene_id = db.Column(db.Integer, db.ForeignKey("scenes.id"), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    job_id = db.Column(db.String(100), nullable=True)
    video_url = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), default="submitted")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Video {self.scene.character.name} status={self.status}>"

