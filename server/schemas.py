from marshmallow import (
    Schema, ValidationError, fields, pre_load, validate, validates, validates_schema,
)

from models import EXERCISE_CATEGORIES


class ExerciseSchema(Schema):
    id = fields.Integer(dump_only=True)
    name = fields.String(required=True, validate=validate.Length(max=100))
    category = fields.String(required=True, validate=validate.OneOf(EXERCISE_CATEGORIES))
    equipment_needed = fields.Boolean(load_default=False)

    @pre_load
    def normalize(self, data, **kwargs):
        data = dict(data)
        if isinstance(data.get("name"), str):
            data["name"] = data["name"].strip()
        if isinstance(data.get("category"), str):
            data["category"] = data["category"].strip().lower()
        return data

    @validates("name")
    def validate_name(self, value):
        if not value:
            raise ValidationError("Name cannot be blank.")


class WorkoutSchema(Schema):
    id = fields.Integer(dump_only=True)
    date = fields.Date(required=True)
    duration_minutes = fields.Integer(
        required=True, strict=True, validate=validate.Range(min=1, max=1440)
    )
    notes = fields.String(
        load_default=None, allow_none=True, validate=validate.Length(max=1000)
    )


class WorkoutExerciseSchema(Schema):
    id = fields.Integer(dump_only=True)
    workout_id = fields.Integer(dump_only=True)
    exercise_id = fields.Integer(dump_only=True)
    reps = fields.Integer(
        load_default=None, allow_none=True, strict=True, validate=validate.Range(min=1)
    )
    sets = fields.Integer(
        load_default=None, allow_none=True, strict=True, validate=validate.Range(min=1)
    )
    duration_seconds = fields.Integer(
        load_default=None, allow_none=True, strict=True, validate=validate.Range(min=1)
    )
    exercise = fields.Nested(ExerciseSchema, dump_only=True)
    workout = fields.Nested(WorkoutSchema, dump_only=True)

    @validates_schema
    def require_measure(self, data, **kwargs):
        has_reps_and_sets = data.get("reps") is not None and data.get("sets") is not None
        if not (has_reps_and_sets or data.get("duration_seconds") is not None):
            raise ValidationError(
                "Provide both reps and sets, or duration_seconds.", "_schema"
            )


class WorkoutDetailSchema(WorkoutSchema):
    """Workout plus its exercises, including reps/sets/duration."""
    workout_exercises = fields.Nested(
        WorkoutExerciseSchema, many=True, exclude=("workout",), dump_only=True
    )


class ExerciseDetailSchema(ExerciseSchema):
    """Exercise plus the workouts it appears in."""
    workout_exercises = fields.Nested(
        WorkoutExerciseSchema, many=True, exclude=("exercise",), dump_only=True
    )
