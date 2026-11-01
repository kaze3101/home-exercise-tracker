import sqlite3
from datetime import date

import pandas as pd
import streamlit as st

from logic import validate_log

DB_PATH = "app.db"
TODAY = date(2026, 10, 31)  # デモ用に基準日を固定（架空データの最終日）

ALERT_SQL = """
WITH recent AS (
    SELECT pr.patient_id,
           pr.prescription_id,
           pr.days_per_week AS planned,
           COALESCE(SUM(l.done_flag), 0) AS done
    FROM prescriptions pr
    LEFT JOIN exercise_logs l
           ON l.prescription_id = pr.prescription_id
          AND l.log_date BETWEEN DATE(:today, '-6 day') AND :today
    GROUP BY pr.prescription_id
)
SELECT r.patient_id      AS 患者ID,
       p.age_group       AS 年齢層,
       p.diagnosis       AS 疾患,
       SUM(MIN(r.done, r.planned)) AS 実施日数,
       SUM(r.planned)              AS 予定日数,
       ROUND(100.0 * SUM(MIN(r.done, r.planned)) / SUM(r.planned), 1) AS 実施率
FROM recent r
JOIN patients p ON p.patient_id = r.patient_id
GROUP BY r.patient_id
HAVING 実施率 < :threshold
ORDER BY 実施率
"""


@st.cache_data
def query(sql, params=()):
    con = sqlite3.connect(DB_PATH)
    try:
        return pd.read_sql_query(sql, con, params=params)
    finally:
        con.close()


st.set_page_config(page_title="自主トレ管理アプリ", layout="wide")
st.title("自主トレ処方・実施記録アプリ")
st.caption("※ 表示データはすべて架空です")

page = st.sidebar.radio("画面を選択", ["患者一覧", "実施記録の入力", "実施率低下アラート"])

if page == "患者一覧":
    st.header("患者一覧")
    df = query("""
        SELECT patient_id AS 患者ID, age_group AS 年齢層, sex AS 性別,
               diagnosis AS 疾患, registered_date AS 登録日
        FROM patients ORDER BY patient_id""")
    keyword = st.text_input("疾患で絞り込み（例：腰痛）")
    if keyword:
        df = df[df["疾患"].str.contains(keyword)]
    st.write(f"{len(df)} 件")
    st.dataframe(df, width="stretch", hide_index=True)

elif page == "実施記録の入力":
    st.header("実施記録の入力")
    patients = query("SELECT patient_id, age_group, diagnosis FROM patients ORDER BY patient_id")
    labels = {r.patient_id: f"ID {r.patient_id}｜{r.age_group}｜{r.diagnosis}"
              for r in patients.itertuples()}
    pid = st.selectbox("患者", list(labels), format_func=lambda x: labels[x])

    presc = query("""
        SELECT pr.prescription_id, e.name, e.category, e.purpose,
               pr.days_per_week, pr.start_date
        FROM prescriptions pr
        JOIN exercises e ON e.exercise_id = pr.exercise_id
        WHERE pr.patient_id = :pid
        ORDER BY pr.prescription_id""", {"pid": int(pid)})
    plabels = {r.prescription_id: f"{r.name}（{r.category}・週{r.days_per_week}日）"
               for r in presc.itertuples()}
    prescription_id = st.selectbox("処方された運動", list(plabels),
                                   format_func=lambda x: plabels[x])
    row = presc[presc["prescription_id"] == prescription_id].iloc[0]
    st.info(f"目的：{row['purpose']}　／　処方開始日：{row['start_date']}")

    log_date = st.date_input("実施日", value=date.today())
    done = st.checkbox("実施した", value=True)
    nrs = st.number_input("痛み（NRS 0〜10）", min_value=0, max_value=10, value=3, step=1)

    if st.button("保存"):
        errors = validate_log(log_date, date.today(),
                              date.fromisoformat(row["start_date"]), int(nrs))
        if errors:
            for msg in errors:
                st.error(msg)
        else:
            con = sqlite3.connect(DB_PATH)
            con.execute("PRAGMA foreign_keys = ON;")
            try:
                with con:
                    con.execute(
                        "INSERT INTO exercise_logs(prescription_id, log_date, done_flag, nrs) "
                        "VALUES (?,?,?,?)",
                        (int(prescription_id), log_date.isoformat(), int(done), int(nrs)))
                query.clear()  # 一覧の表示を最新にする
                st.success("保存しました")
            except sqlite3.IntegrityError:
                st.error("同じ処方・同じ日付の記録がすでにあります")
            finally:
                con.close()

else:
    st.header("実施率低下アラート")
    threshold = st.slider("アラートの閾値（%）", 10, 100, 50, step=5)
    df = query(ALERT_SQL, {"today": TODAY.isoformat(), "threshold": threshold})
    st.write(f"直近7日間（〜{TODAY}）の実施率が {threshold}% 未満：**{len(df)} 名**")
    st.dataframe(df, width="stretch", hide_index=True)
