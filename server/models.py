from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import validates

db = SQLAlchemy()

EXERCISE_CATEGORIES = (
    "strength", "cardio", "flexibility", "balance", "mobility", "other",
)


def _require_positive_int(field, value, allow_none=False):
    """Shared check: value must be a positive integer (bools are rejected)."""
    if value is None and allow_none:
        return value
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field} must be a positive integer.")
    return value


class Exercise(db.Model):
    __tablename__ = "exercises"
    __table_args__ = (
        db.CheckConstraint("length(trim(name)) > 0", name="ck_exercise_name_not_blank"),
        db.CheckConstraint("length(trim(category)) > 0", name="ck_exercise_category_not_blank"),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    category = db.Column(db.String, nullable=False)
    equipment_needed = db.Column(db.Boolean, nullable=False, default=False)

    workout_exercises = db.relationship(
        "WorkoutExercise", back_populates="exercise", cascade="all, delete-orphan"
    )
    workouts = association_proxy("workout_exercises", "workout")

    @validates("name")
    def validate_name(self, key, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Exercise name must be a non-empty string.")
        return value.strip()

    @validates("category")
    def validate_category(self, key, value):
        if not isinstance(value, str) or value.strip().lower() not in EXERCISE_CATEGORIES:
            raise ValueError(
                f"Category must be one of: {', '.join(EXERCISE_CATEGORIES)}."
            )
        return value.strip().lower()

    @validates("equipment_needed")
    def validate_equipment_needed(self, key, value):
        if not isinstance(value, bool):
            raise ValueError("equipment_needed must be a boolean.")
        return value

    def __repr__(self):
        return f"<Exercise {self.id} {self.name}>"


class Workout(db.Model):
    __tablename__ = "workouts"
    __table_args__ = (
        db.CheckConstraint("duration_minutes > 0", name="ck_workout_duration_positive"),
    )

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text)

    workout_exercises = db.relationship(
        "WorkoutExercise", back_populates="workout", cascade="all, delete-orphan"
    )
    exercises = association_proxy("workout_exercises", "exercise")

    @validates("duration_minutes")
    def validate_duration(self, key, value):
        return _require_positive_int("duration_minutes", value)

    @validates("date")
    def validate_date(self, key, value):
        # datetime is a subclass of date, so check for the exact type
        if type(value).__name__ != "date":
            raise ValueError("date must be a valid date.")
        return value

    def __repr__(self):
        return f"<Workout {self.id} {self.date}>"


class WorkoutExercise(db.Model):
    __tablename__ = "workout_exercises"
    __table_args__ = (
        db.UniqueConstraint("workout_id", "exercise_id", name="uq_workout_exercise_pair"),
        db.CheckConstraint("reps IS NULL OR reps > 0", name="ck_we_reps_positive"),
        db.CheckConstraint("sets IS NULL OR sets > 0", name="ck_we_sets_positive"),
        db.CheckConstraint(
            "duration_seconds IS NULL OR duration_seconds > 0",
            name="ck_we_duration_positive",
        ),
        db.CheckConstraint(
            "(reps IS NOT NULL AND sets IS NOT NULL) OR duration_seconds IS NOT NULL",
            name="ck_we_has_measure",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    workout_id = db.Column(
        db.Integer, db.ForeignKey("workouts.id", ondelete="CASCADE"), nullable=False
    )
    exercise_id = db.Column(
        db.Integer, db.ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False
    )
    reps = db.Column(db.Integer)
    sets = db.Column(db.Integer)
    duration_seconds = db.Column(db.Integer)

    workout = db.relationship("Workout", back_populates="workout_exercises")
    exercise = db.relationship("Exercise", back_populates="workout_exercises")

    @validates("reps", "sets", "duration_seconds")
    def validate_measure(self, key, value):
        return _require_positive_int(key, value, allow_none=True)

    def __repr__(self):
        return f"<WorkoutExercise {self.id} w={self.workout_id} e={self.exercise_id}>"
