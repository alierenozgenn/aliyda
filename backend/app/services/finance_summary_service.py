from datetime import date
from collections import defaultdict

def calculate_financial_summary(transactions: list, anomalies: list) -> dict:
    total_income  = sum(t["amount"] for t in transactions if t["direction"] == "income")
    total_expense = sum(t["amount"] for t in transactions if t["direction"] == "expense")
    net_balance   = total_income - total_expense

    cat_totals = defaultdict(float)
    for t in transactions:
        if t["direction"] == "expense":
            cat_totals[t.get("estimated_category", "Diger")] += t["amount"]

    categories = []
    for cat, amount in sorted(cat_totals.items(), key=lambda x: -x[1]):
        pct = round(amount / total_expense * 100, 1) if total_expense > 0 else 0
        categories.append({"name": cat, "amount": round(amount, 2), "percentage": pct})

    today          = date.today()
    days_passed    = today.day
    remaining_days = 30 - days_passed
    daily_expense  = total_expense / max(days_passed, 1)
    projected_end  = round(net_balance - (daily_expense * remaining_days), 2)

    return {
        "total_income":        round(total_income, 2),
        "total_expense":       round(total_expense, 2),
        "net_balance":         round(net_balance, 2),
        "categories":          categories,
        "top_category":        categories[0]["name"] if categories else None,
        "daily_expense_avg":   round(daily_expense, 2),
        "projected_month_end": projected_end,
        "anomalies":           anomalies,
        "health_score":        _health_score(total_income, total_expense, net_balance, categories),
    }

def _health_score(income, expense, net, categories) -> int:
    """
    Finansal Saglik Skoru (0-100):
      Gelir/Gider orani  : 40 puan
      Tasarruf orani     : 30 puan
      Kategori yogunlugu : 30 puan
    """
    score = 0
    if income > 0:
        score += min(40, int((net / income) * 80))
        score += min(30, int((max(0, net) / income) * 100))
    if categories and expense > 0:
        top_pct = categories[0]["percentage"]
        if top_pct < 30:   score += 30
        elif top_pct < 50: score += 20
        elif top_pct < 70: score += 10
    return max(0, min(100, score))
