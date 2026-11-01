-- 直近7日間の実施率が50%未満の患者を抽出（基準日：2026-10-31）
WITH recent AS (
    -- 処方ごとに「予定日数」と「実施日数」を出す
    SELECT pr.patient_id,
           pr.prescription_id,
           pr.days_per_week AS planned,
           COALESCE(SUM(l.done_flag), 0) AS done
    FROM prescriptions pr
    LEFT JOIN exercise_logs l
           ON l.prescription_id = pr.prescription_id
          AND l.log_date BETWEEN DATE('2026-10-31', '-6 day') AND '2026-10-31'
    GROUP BY pr.prescription_id
)
-- 患者ごとに合計して実施率を出す
SELECT patient_id,
       SUM(MIN(done, planned)) AS done_days,
       SUM(planned)            AS planned_days,
       ROUND(100.0 * SUM(MIN(done, planned)) / SUM(planned), 1) AS adherence_rate
FROM recent
GROUP BY patient_id
HAVING adherence_rate < 50
ORDER BY adherence_rate;