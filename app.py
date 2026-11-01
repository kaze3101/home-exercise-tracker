import sqlite3
from datetime import date

import pandas as pd
import streamlit as st

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

page = st.sidebar.radio("画面を選択", ["患者一覧", "実施率低下アラート"])

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

else:
    st.header("実施率低下アラート")
    threshold = st.slider("アラートの閾値（%）", 10, 100, 50, step=5)
    df = query(ALERT_SQL, {"today": TODAY.isoformat(), "threshold": threshold})
    st.write(f"直近7日間（〜{TODAY}）の実施率が {threshold}% 未満：**{len(df)} 名**")
    st.dataframe(df, width="stretch", hide_index=True)