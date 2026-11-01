from datetime import date


def validate_log(log_date: date, today: date, start_date: date, nrs: int) -> list[str]:
    """実施記録の入力値を検証し、エラーメッセージのリストを返す（空なら問題なし）"""
    errors = []
    if log_date > today:
        errors.append("未来の日付は入力できません")
    if log_date < start_date:
        errors.append("処方開始日より前の日付は入力できません")
    if not isinstance(nrs, int) or not 0 <= nrs <= 10:
        errors.append("痛み（NRS）は0〜10の整数で入力してください")
    return errors
