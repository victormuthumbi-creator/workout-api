import pytest

from models import Exercise, Workout, WorkoutExercise, db


def make_exercise(client, **overrides):
    payload = {"name": "Squat", "category": "strength", "equipment_needed": True}
    payload.update(overrides)
    return client.post("/exercises", json=payload)


def make_workout(client, **overrides):
    payload = {"date": "2026-10-23", "duration_minutes": 45, "notes": "Legs"}
    payload.update(overrides)
    return client.post("/workouts", json=payload)


# ----- Endpoints -----

def test_create_and_list_exercises(client):
    assert make_exercise(client).status_code == 201
    res = client.get("/exercises")
    assert res.status_code == 200
    assert res.get_json()[0]["name"] == "Squat"


def test_create_and_show_workout(client):
    wid = make_workout(client).get_json()["id"]
    res = client.get(f"/workouts/{wid}")
    assert res.status_code == 200
    assert res.get_json()["workout_exercises"] == []


def test_add_exercise_to_workout_and_show(client):
    wid = make_workout(client).get_json()["id"]
    eid = make_exercise(client).get_json()["id"]
    res = client.post(
        f"/workouts/{wid}/exercises/{eid}/workout_exercises",
        json={"reps": 10, "sets": 3},
    )
    assert res.status_code == 201
    workout = client.get(f"/workouts/{wid}").get_json()
    assert workout["workout_exercises"][0]["exercise"]["name"] == "Squat"
    assert workout["workout_exercises"][0]["reps"] == 10
    exercise = client.get(f"/exercises/{eid}").get_json()
    assert exercise["workout_exercises"][0]["workout"]["id"] == wid


def test_delete_workout_removes_join_rows(client):
    wid = make_workout(client).get_json()["id"]
    eid = make_exercise(client).get_json()["id"]
    client.post(f"/workouts/{wid}/exercises/{eid}/workout_exercises", json={"duration_seconds": 60})
    assert client.delete(f"/workouts/{wid}").status_code == 204
    assert WorkoutExercise.query.count() == 0
    assert Exercise.query.count() == 1


def test_delete_exercise_removes_join_rows(client):
    wid = make_workout(client).get_json()["id"]
    eid = make_exercise(client).get_json()["id"]
    client.post(f"/workouts/{wid}/exercises/{eid}/workout_exercises", json={"duration_seconds": 60})
    assert client.delete(f"/exercises/{eid}").status_code == 204
    assert WorkoutExercise.query.count() == 0
    assert Workout.query.count() == 1


def test_404s(client):
    assert client.get("/workouts/999").status_code == 404
    assert client.delete("/exercises/999").status_code == 404
    assert client.post("/workouts/1/exercises/1/workout_exercises", json={"reps": 1, "sets": 1}).status_code == 404


# ----- Schema validations -----

@pytest.mark.parametrize("payload", [
    {"name": "  ", "category": "strength"},
    {"name": "Curl", "category": "bogus"},
    {"category": "strength"},
    {"name": "Curl", "category": "strength", "extra": 1},
])
def test_exercise_schema_rejects_bad_data(client, payload):
    assert client.post("/exercises", json=payload).status_code == 400


@pytest.mark.parametrize("payload", [
    {"date": "not-a-date", "duration_minutes": 30},
    {"date": "2026-10-23", "duration_minutes": 0},
    {"date": "2026-10-23", "duration_minutes": "30"},
    {"duration_minutes": 30},
])
def test_workout_schema_rejects_bad_data(client, payload):
    assert client.post("/workouts", json=payload).status_code == 400


def test_workout_exercise_requires_a_measure(client):
    wid = make_workout(client).get_json()["id"]
    eid = make_exercise(client).get_json()["id"]
    url = f"/workouts/{wid}/exercises/{eid}/workout_exercises"
    assert client.post(url, json={}).status_code == 400
    assert client.post(url, json={"reps": 10}).status_code == 400


def test_duplicate_exercise_name_is_409(client):
    make_exercise(client)
    assert make_exercise(client).status_code == 409


def test_same_exercise_twice_in_workout_is_409(client):
    wid = make_workout(client).get_json()["id"]
    eid = make_exercise(client).get_json()["id"]
    url = f"/workouts/{wid}/exercises/{eid}/workout_exercises"
    assert client.post(url, json={"reps": 5, "sets": 5}).status_code == 201
    assert client.post(url, json={"reps": 5, "sets": 5}).status_code == 409


# ----- Model validations & table constraints -----

def test_model_validations(client):
    with pytest.raises(ValueError):
        Exercise(name="", category="strength")
    with pytest.raises(ValueError):
        Exercise(name="Row", category="nonsense")
    with pytest.raises(ValueError):
        Workout(date="2026-10-23", duration_minutes=30)  # str, not date
    with pytest.raises(ValueError):
        WorkoutExercise(reps=-1)


def test_table_constraint_blocks_bad_rows(client):
    from sqlalchemy.exc import IntegrityError
    db.session.add(Exercise(name="Dip", category="strength"))
    db.session.commit()
    # Bypass model validators with raw SQL to prove the DB itself enforces rules
    with pytest.raises(IntegrityError):
        db.session.execute(db.text("INSERT INTO workouts (date, duration_minutes) VALUES ('2026-10-23', -5)"))
    db.session.rollback()
