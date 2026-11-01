PRAGMA foreign_keys = ON;

CREATE TABLE patients (
    patient_id      INTEGER PRIMARY KEY,
    age_group       TEXT NOT NULL,
    sex             TEXT NOT NULL CHECK (sex IN ('男性', '女性')),
    diagnosis       TEXT NOT NULL,
    registered_date DATE NOT NULL
);

CREATE TABLE therapists (
    therapist_id INTEGER PRIMARY KEY,
    display_name TEXT NOT NULL
);

CREATE TABLE exercises (
    exercise_id INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    category    TEXT NOT NULL CHECK (category IN
                ('ストレッチ', '筋力強化', '可動域運動', 'バランス・協調性運動', '有酸素運動')),
    purpose     TEXT NOT NULL,
    description TEXT,
    reps        INTEGER NOT NULL CHECK (reps > 0),
    sets        INTEGER NOT NULL CHECK (sets > 0)
);

CREATE TABLE prescriptions (
    prescription_id INTEGER PRIMARY KEY,
    patient_id      INTEGER NOT NULL REFERENCES patients(patient_id),
    exercise_id     INTEGER NOT NULL REFERENCES exercises(exercise_id),
    therapist_id    INTEGER NOT NULL REFERENCES therapists(therapist_id),
    days_per_week   INTEGER NOT NULL CHECK (days_per_week BETWEEN 1 AND 7),
    start_date      DATE NOT NULL
);

CREATE TABLE exercise_logs (
    log_id          INTEGER PRIMARY KEY,
    prescription_id INTEGER NOT NULL REFERENCES prescriptions(prescription_id),
    log_date        DATE NOT NULL,
    done_flag       INTEGER NOT NULL CHECK (done_flag IN (0, 1)),
    nrs             INTEGER CHECK (nrs BETWEEN 0 AND 10),
    UNIQUE (prescription_id, log_date)
);