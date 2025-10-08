from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Float, Integer, ForeignKey, Boolean, Date, JSON, DateTime


class Base(DeclarativeBase):
    pass


class SceneModel(Base):
    __tablename__ = "scenes"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    upload_id: Mapped[str] = mapped_column(String, ForeignKey("script_uploads.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String)
    sequence_index: Mapped[int] = mapped_column(Integer, default=0)
    slugline: Mapped[str] = mapped_column(String)
    page_eighths: Mapped[int] = mapped_column(Integer)
    page_decimal: Mapped[float] = mapped_column(Float)
    estimated_minutes: Mapped[float] = mapped_column(Float)
    location: Mapped[str] = mapped_column(String)
    day_night: Mapped[str] = mapped_column(String(16))
    estimated_cost: Mapped[float] = mapped_column(Float)
    script_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    schedule_day_id: Mapped[str | None] = mapped_column(String, ForeignKey("day_plans.id"), nullable=True)

    cast_members: Mapped[list["SceneCastModel"]] = relationship(
        back_populates="scene", cascade="all, delete-orphan"
    )
    props_used: Mapped[list["ScenePropModel"]] = relationship(
        back_populates="scene", cascade="all, delete-orphan"
    )
    schedule_day: Mapped[DayPlanModel | None] = relationship(back_populates="scenes")
    day_positions: Mapped[list["DayPlanSceneModel"]] = relationship(
        back_populates="scene", cascade="all, delete-orphan"
    )


class SceneCastModel(Base):
    __tablename__ = "scene_cast"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scene_id: Mapped[str] = mapped_column(String, ForeignKey("scenes.id", ondelete="CASCADE"))
    performer_name: Mapped[str] = mapped_column(String)

    scene: Mapped[SceneModel] = relationship(back_populates="cast_members")


class ScenePropModel(Base):
    __tablename__ = "scene_props"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scene_id: Mapped[str] = mapped_column(String, ForeignKey("scenes.id", ondelete="CASCADE"))
    prop_name: Mapped[str] = mapped_column(String)

    scene: Mapped[SceneModel] = relationship(back_populates="props_used")


class DayPlanModel(Base):
    __tablename__ = "day_plans"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    upload_id: Mapped[str] = mapped_column(String, ForeignKey("script_uploads.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String)
    shooting_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    total_cost: Mapped[float] = mapped_column(Float, default=0.0)
    total_minutes: Mapped[float] = mapped_column(Float, default=0.0)
    total_pages_decimal: Mapped[float] = mapped_column(Float, default=0.0)
    location_summary: Mapped[list[str]] = mapped_column(JSON)
    cast_summary: Mapped[list[str]] = mapped_column(JSON)

    scenes: Mapped[list[SceneModel]] = relationship(back_populates="schedule_day")
    scene_positions: Mapped[list["DayPlanSceneModel"]] = relationship(
        back_populates="day_plan", cascade="all, delete-orphan"
    )


class RateCardModel(Base):
    __tablename__ = "rate_cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category: Mapped[str] = mapped_column(String)
    item_name: Mapped[str] = mapped_column(String)
    unit: Mapped[str] = mapped_column(String)
    base_rate: Mapped[float] = mapped_column(Float)
    overtime_rate: Mapped[float] = mapped_column(Float, default=0.0)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)


class ScriptUploadModel(Base):
    __tablename__ = "script_uploads"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    original_filename: Mapped[str] = mapped_column(String)
    mime_type: Mapped[str] = mapped_column(String)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    total_scenes: Mapped[int] = mapped_column(Integer, default=0)
    total_pages_decimal: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String, default="parsed")

    scenes: Mapped[list[SceneModel]] = relationship(backref="upload", cascade="all, delete-orphan")
    day_plans: Mapped[list[DayPlanModel]] = relationship(backref="upload", cascade="all, delete-orphan")


class DayPlanSceneModel(Base):
    __tablename__ = "day_plan_scenes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    day_plan_id: Mapped[str] = mapped_column(String, ForeignKey("day_plans.id", ondelete="CASCADE"))
    scene_id: Mapped[str] = mapped_column(String, ForeignKey("scenes.id", ondelete="CASCADE"))
    position: Mapped[int] = mapped_column(Integer, default=0)

    day_plan: Mapped[DayPlanModel] = relationship(back_populates="scene_positions")
    scene: Mapped[SceneModel] = relationship(back_populates="day_positions")
