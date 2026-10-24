# Workout Tracker API

## Description
A Flask REST API for a workout tracking app used by personal trainers. Trainers can create, view and delete **workouts** and reusable **exercises**, and attach exercises to workouts with reps, sets or duration. Built with Flask, Flask-SQLAlchemy, Flask-Migrate and Marshmallow, with validation at three levels: database table constraints, model validations and schema validations.

## Data model
- **Exercise**: `id`, `name` (unique), `category`, `equipment_needed`
- **Workout**: `id`, `date`, `duration_minutes`, `notes`
- **WorkoutExercise** (join table): `id`, `workout_id`, `exercise_id`, `reps`, `sets`, `duration_seconds`

A workout has many exercises through `WorkoutExercise`, and an exercise has many workouts through `WorkoutExercise`.

## Installation
```bash
git clone <your-repo-url>
cd <your-repo-folder>
pipenv install
pipenv shell
cd server
flask db upgrade head      # create the database from the included migrations
python seed.py             # load example data (safe to rerun; it resets the data)
```

If you ever need to regenerate migrations from scratch:
```bash
rm -rf migrations instance
flask db init
flask db migrate -m "initial tables"
flask db upgrade head
```

## Run
```bash
cd server
flask run -p 5555
```
The API is then available at `http://localhost:5555`. (`python app.py` also works.)
Set `FLASK_APP=app.py` if Flask can't find the app.

## Tests
```bash
pipenv install --dev
cd server
pytest
```

## Endpoints

| Method | Path | Description | Success |
|--------|------|-------------|---------|
| GET | `/workouts` | List all workouts | 200 |
| GET | `/workouts/<id>` | Show one workout with its exercises, including reps/sets/duration | 200 |
| POST | `/workouts` | Create a workout (`date`, `duration_minutes`, optional `notes`) | 201 |
| DELETE | `/workouts/<id>` | Delete a workout and its associated WorkoutExercises | 204 |
| GET | `/exercises` | List all exercises | 200 |
| GET | `/exercises/<id>` | Show one exercise with the workouts it appears in | 200 |
| POST | `/exercises` | Create an exercise (`name`, `category`, optional `equipment_needed`) | 201 |
| DELETE | `/exercises/<id>` | Delete an exercise and its associated WorkoutExercises | 204 |
| POST | `/workouts/<workout_id>/exercises/<exercise_id>/workout_exercises` | Add an exercise to a workout. Send `reps` + `sets`, or `duration_seconds` | 201 |

Errors return JSON: `400` for invalid data, `404` for unknown ids, `409` for duplicates (e.g. a repeated exercise name, or the same exercise added twice to one workout).

### Example requests
```bash
curl -X POST localhost:5555/exercises -H 'Content-Type: application/json' \
  -d '{"name": "Deadlift", "category": "strength", "equipment_needed": true}'

curl -X POST localhost:5555/workouts -H 'Content-Type: application/json' \
  -d '{"date": "2026-10-25", "duration_minutes": 50, "notes": "Pull day"}'

curl -X POST localhost:5555/workouts/1/exercises/1/workout_exercises \
  -H 'Content-Type: application/json' -d '{"reps": 5, "sets": 5}'
```

## Validations
- **Table constraints**: unique exercise name, non-blank name/category, `duration_minutes > 0`, positive reps/sets/duration, each WorkoutExercise needs (reps and sets) or duration, unique workout/exercise pair.
- **Model validations**: exercise name and category (`strength`, `cardio`, `flexibility`, `balance`, `mobility`, `other`), `equipment_needed` is a boolean, workout `date` is a date, positive integers for duration/reps/sets.
- **Schema validations**: required fields and types, category must be allowed, name cannot be blank, duration between 1 and 1440 minutes, reps/sets/duration at least 1, and WorkoutExercise must include a measure.

## Project structure
```
server/
  app.py        # app config, error handlers, routes
  models.py     # SQLAlchemy models, relationships, constraints, validations
  schemas.py    # Marshmallow schemas and schema validations
  seed.py       # example data
  migrations/   # Alembic migrations
  tests/        # pytest suite
```
