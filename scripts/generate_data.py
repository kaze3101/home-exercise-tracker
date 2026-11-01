"""架空データ生成スクリプト（実在の患者データは一切使用していません）"""
import random
import sqlite3
from datetime import date, timedelta

random.seed(42)  # 再現性のため固定
DB_PATH = "app.db"
TODAY = date(2026, 10, 31)   # 「今日」を固定（アラート判定の基準日）
PERIOD_DAYS = 28             # 記録期間（4週間）

AGE_GROUPS = {"20代": 0.80, "30代": 0.78, "40代": 0.78, "50代": 0.72,
              "60代": 0.65, "70代": 0.55, "80歳以上": 0.45}
DIAGNOSES = {  # 疾患: 実施率の補正（痛み主体の疾患は下げる）
    "筋筋膜性腰痛症": -0.10, "梨状筋症候群": -0.10, "腰部脊柱管狭窄症": -0.05,
    "変形性膝関節症": 0.0, "肩関節周囲炎": 0.0, "足関節捻挫": 0.0,
    "TKA術後": 0.10, "橈骨遠位端骨折": 0.10}
THERAPISTS = {"PT_A": 0.05, "PT_B": 0.0, "PT_C": -0.05, "PT_D": -0.08}
EXERCISES = [
    ("ハムストリングスのストレッチ", "ストレッチ", "太もも裏の柔軟性を高め、腰への負担を減らす", 30, 1),
    ("大殿筋ストレッチ", "ストレッチ", "お尻の筋肉の柔軟性を高める", 30, 2),
    ("スクワット", "筋力強化", "太もも・お尻の筋力を高める", 10, 3),
    ("ヒップリフト", "筋力強化", "お尻と体幹の筋力を高める", 10, 3),
    ("中殿筋トレーニング", "筋力強化", "骨盤の安定性を高める", 15, 2),
    ("膝の曲げ伸ばし", "可動域運動", "膝の動く範囲を広げる", 10, 2),
    ("肩のふりこ運動", "可動域運動", "肩の動きを保ち、痛みを和らげる", 20, 2),
    ("片脚立ち", "バランス・協調性運動", "バランス能力を高める", 30, 3),
    ("ウォーキング", "有酸素運動", "全身の持久力を高める", 1, 1)]


def clip(x, lo=0.05, hi=0.95):
    return max(lo, min(hi, x))


def clip_nrs(x):
    return int(max(0, min(10, round(x))))


def main():
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON;")
    cur = con.cursor()

    cur.executemany("INSERT INTO therapists(display_name) VALUES (?)",
                    [(n,) for n in THERAPISTS])
    cur.executemany(
        "INSERT INTO exercises(name, category, purpose, reps, sets) VALUES (?,?,?,?,?)",
        EXERCISES)

    start = TODAY - timedelta(days=PERIOD_DAYS - 1)
    for _ in range(150):  # 患者150名
        age = random.choice(list(AGE_GROUPS))
        dx = random.choice(list(DIAGNOSES))
        sex = random.choice(["男性", "女性"])
        cur.execute(
            "INSERT INTO patients(age_group, sex, diagnosis, registered_date) VALUES (?,?,?,?)",
            (age, sex, dx, start.isoformat()))
        pid = cur.lastrowid
        pt_name = random.choice(list(THERAPISTS))
        cur.execute("SELECT therapist_id FROM therapists WHERE display_name=?", (pt_name,))
        tid = cur.fetchone()[0]

        base = clip(AGE_GROUPS[age] + DIAGNOSES[dx] + THERAPISTS[pt_name])
        fading = random.random() < 0.30  # 約3割は徐々に実施率が下がる患者

        for ex_id in random.sample(range(1, len(EXERCISES) + 1), random.randint(1, 3)):
            days = random.choice([3, 4, 5, 7])
            cur.execute(
                "INSERT INTO prescriptions(patient_id, exercise_id, therapist_id, days_per_week, start_date) "
                "VALUES (?,?,?,?,?)", (pid, ex_id, tid, days, start.isoformat()))
            presc_id = cur.lastrowid

            for week in range(PERIOD_DAYS // 7):
                p = clip(base - (0.15 * week if fading else 0))
                week_start = start + timedelta(days=7 * week)
                for offset in sorted(random.sample(range(7), days)):  # 実施予定日
                    d = week_start + timedelta(days=offset)
                    done = 1 if random.random() < p else 0
                    nrs = clip_nrs(5 - 2 * p * week / 3 + random.gauss(0, 1.2))
                    cur.execute(
                        "INSERT INTO exercise_logs(prescription_id, log_date, done_flag, nrs) "
                        "VALUES (?,?,?,?)", (presc_id, d.isoformat(), done, nrs))
    con.commit()
    con.close()
    print("架空データの生成が完了しました")


if __name__ == "__main__":
    main()