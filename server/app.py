import os

from flask import Flask, jsonify, request
from flask_migrate import Migrate
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from models import db, Exercise, Workout, WorkoutExercise
from schemas import (
    ExerciseDetailSchema, ExerciseSchema, WorkoutDetailSchema,
    WorkoutExerciseSchema, WorkoutSchema,
)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URI", "sqlite:///app.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)
db.init_app(app)

exercise_schema = ExerciseSchema()
exercises_schema = ExerciseSchema(many=True)
exercise_detail_schema = ExerciseDetailSchema()
workout_schema = WorkoutSchema()
workouts_schema = WorkoutSchema(many=True)
workout_detail_schema = WorkoutDetailSchema()
workout_exercise_schema = WorkoutExerciseSchema()


def get_json_body():
    """Return the request's JSON object or raise a 400-style error."""
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        raise ValidationError({"_body": ["Request body must be a JSON object."]})
    return body


# ---------- Error handlers ----------

@app.errorhandler(ValidationError)
def handle_schema_error(err):
    return jsonify({"errors": err.messages}), 400


@app.errorhandler(ValueError)
def handle_model_error(err):
    return jsonify({"errors": [str(err)]}), 400


@app.errorhandler(IntegrityError)
def handle_integrity_error(err):
    db.session.rollback()
    return jsonify({"errors": ["Database constraint violated (e.g. duplicate record)."]}), 409


@app.errorhandler(404)
def handle_not_found(err):
    return jsonify({"errors": ["Resource not found."]}), 404


# ---------- Workouts ----------

@app.route("/workouts", methods=["GET"])
def list_workouts():
    return jsonify(workouts_schema.dump(Workout.query.order_by(Workout.date).all())), 200


@app.route("/workouts/<int:id>", methods=["GET"])
def show_workout(id):
    workout = db.get_or_404(Workout, id)
    return jsonify(workout_detail_schema.dump(workout)), 200


@app.route("/workouts", methods=["POST"])
def create_workout():
    data = workout_schema.load(get_json_body())
    workout = Workout(**data)
    db.session.add(workout)
    db.session.commit()
    return jsonify(workout_schema.dump(workout)), 201


@app.route("/workouts/<int:id>", methods=["DELETE"])
def delete_workout(id):
    workout = db.get_or_404(Workout, id)
    db.session.delete(workout)  # cascades to its WorkoutExercises
    db.session.commit()
    return "", 204


# ---------- Exercises ----------

@app.route("/exercises", methods=["GET"])
def list_exercises():
    return jsonify(exercises_schema.dump(Exercise.query.order_by(Exercise.name).all())), 200


@app.route("/exercises/<int:id>", methods=["GET"])
def show_exercise(id):
    exercise = db.get_or_404(Exercise, id)
    return jsonify(exercise_detail_schema.dump(exercise)), 200


@app.route("/exercises", methods=["POST"])
def create_exercise():
    data = exercise_schema.load(get_json_body())
    exercise = Exercise(**data)
    db.session.add(exercise)
    db.session.commit()
    return jsonify(exercise_schema.dump(exercise)), 201


@app.route("/exercises/<int:id>", methods=["DELETE"])
def delete_exercise(id):
    exercise = db.get_or_404(Exercise, id)
    db.session.delete(exercise)  # cascades to its WorkoutExercises
    db.session.commit()
    return "", 204


# ---------- Workout <-> Exercise ----------

@app.route(
    "/workouts/<int:workout_id>/exercises/<int:exercise_id>/workout_exercises",
    methods=["POST"],
)
def add_exercise_to_workout(workout_id, exercise_id):
    workout = db.get_or_404(Workout, workout_id)
    exercise = db.get_or_404(Exercise, exercise_id)
    data = workout_exercise_schema.load(get_json_body())

    workout_exercise = WorkoutExercise(workout=workout, exercise=exercise, **data)
    db.session.add(workout_exercise)
    db.session.commit()
    return jsonify(workout_exercise_schema.dump(workout_exercise)), 201


if __name__ == "__main__":
    app.run(port=5555, debug=True)
