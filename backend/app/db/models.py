from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Float, Integer, ForeignKey, Boolean, Date, JSON, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID


class Base(DeclarativeBase):
    pass


class SceneModel(Base):
    __tablename__ = "scenes"

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True)
    upload_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("script_uploads.id", ondelete="CASCADE"), index=True)
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
    schedule_day_id: Mapped[UUID | None] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("day_plans.id"), nullable=True)
    synopsis: Mapped[str | None] = mapped_column(Text, nullable=True)

    cast_members: Mapped[list["SceneCastModel"]] = relationship(
        back_populates="scene", cascade="all, delete-orphan"
    )
    props_used: Mapped[list["ScenePropModel"]] = relationship(
        back_populates="scene", cascade="all, delete-orphan"
    )
    schedule_day: Mapped["DayPlanModel | None"] = relationship(back_populates="scenes")
    day_positions: Mapped[list["DayPlanSceneModel"]] = relationship(
        back_populates="scene", cascade="all, delete-orphan"
    )
    tags: Mapped[list["SceneTagModel"]] = relationship(
        back_populates="scene", cascade="all, delete-orphan"
    )
    notes: Mapped[list["SceneNoteModel"]] = relationship(
        back_populates="scene", cascade="all, delete-orphan"
    )
    elements: Mapped[list["SceneElementModel"]] = relationship(
        back_populates="scene", cascade="all, delete-orphan"
    )


class SceneCastModel(Base):
    __tablename__ = "scene_cast"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scene_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("scenes.id", ondelete="CASCADE"))
    performer_name: Mapped[str] = mapped_column(String)

    scene: Mapped[SceneModel] = relationship(back_populates="cast_members")


class ScenePropModel(Base):
    __tablename__ = "scene_props"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scene_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("scenes.id", ondelete="CASCADE"))
    prop_name: Mapped[str] = mapped_column(String)

    scene: Mapped[SceneModel] = relationship(back_populates="props_used")


class DayPlanModel(Base):
    __tablename__ = "day_plans"

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True)
    upload_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("script_uploads.id", ondelete="CASCADE"), index=True)
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

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True)
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
    day_plan_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("day_plans.id", ondelete="CASCADE"))
    scene_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("scenes.id", ondelete="CASCADE"))
    position: Mapped[int] = mapped_column(Integer, default=0)

    day_plan: Mapped[DayPlanModel] = relationship(back_populates="scene_positions")
    scene: Mapped[SceneModel] = relationship(back_populates="day_positions")


class ActorCompensationModel(Base):
    __tablename__ = "actor_compensation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor_name: Mapped[str] = mapped_column(String, unique=True, index=True)
    daily_rate: Mapped[float] = mapped_column(Float, default=0.0)
    overtime_rate: Mapped[float] = mapped_column(Float, default=0.0)
    union_status: Mapped[str] = mapped_column(String, default="NON_SAG")
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LocationCompensationModel(Base):
    __tablename__ = "location_compensation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    location_name: Mapped[str] = mapped_column(String, unique=True, index=True)
    daily_fee: Mapped[float] = mapped_column(Float, default=0.0)
    permits_cost: Mapped[float] = mapped_column(Float, default=0.0)
    insurance_cost: Mapped[float] = mapped_column(Float, default=0.0)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CharacterAssignmentModel(Base):
    __tablename__ = "character_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    upload_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("script_uploads.id", ondelete="CASCADE"), index=True)
    character_name: Mapped[str] = mapped_column(String)
    actor_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("actor_compensation.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ScheduleDayOverrideModel(Base):
    __tablename__ = "schedule_day_overrides"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    upload_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("script_uploads.id", ondelete="CASCADE"), index=True)
    script_day: Mapped[int] = mapped_column(Integer)
    shooting_location: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SceneTagModel(Base):
    __tablename__ = "scene_tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scene_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("scenes.id", ondelete="CASCADE"), index=True)
    tag: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    scene: Mapped["SceneModel"] = relationship(back_populates="tags")


class SceneNoteModel(Base):
    __tablename__ = "scene_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scene_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("scenes.id", ondelete="CASCADE"), index=True)
    note_text: Mapped[str] = mapped_column(String)
    note_type: Mapped[str] = mapped_column(String, default="GENERAL")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    scene: Mapped["SceneModel"] = relationship(back_populates="notes")


class ElementCategoryModel(Base):
    __tablename__ = "element_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_name: Mapped[str] = mapped_column(String, unique=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    color: Mapped[str] = mapped_column(String, default="#808080")

    elements: Mapped[list["SceneElementModel"]] = relationship(back_populates="category")


class SceneElementModel(Base):
    __tablename__ = "scene_elements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scene_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("scenes.id", ondelete="CASCADE"), index=True)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("element_categories.id", ondelete="CASCADE"))
    element_name: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
    is_critical: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    scene: Mapped["SceneModel"] = relationship(back_populates="elements")
    category: Mapped[ElementCategoryModel] = relationship(back_populates="elements")


class MasterElementModel(Base):
    __tablename__ = "master_elements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    upload_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("script_uploads.id", ondelete="CASCADE"), index=True)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("element_categories.id", ondelete="CASCADE"))
    element_name: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    total_scenes: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
