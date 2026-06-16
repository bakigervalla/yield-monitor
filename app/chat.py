import json
import re


async def openai_chat(
    question: str,
    stats_data: list[dict],
    daily_data: list[dict],
    api_key: str,
    history: list[dict] | None = None,
) -> str:
    try:
        import httpx

        system_prompt = (
            "You are a Yield Monitor assistant. "
            "Answer only using the provided application data. "
            "Do not invent numbers. Keep answers short and precise.\n\n"
            f"Current stats:\n{json.dumps(stats_data, indent=2)}\n\n"
            f"Daily data (last 7 days):\n{json.dumps(daily_data, indent=2)}"
        )

        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": question})

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": messages,
                    "max_tokens": 200,
                },
            )
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return rule_based_chat(question, stats_data, daily_data)


def rule_based_chat(
    question: str,
    stats_data: list[dict],
    daily_data: list[dict],
) -> str:
    q = question.lower()

    match = re.search(r"00[123]pn00[123]", q, re.IGNORECASE)
    if match:
        pn = match.group(0).upper()
        for row in stats_data:
            if row["part_number"] == pn:
                if row["total"] == 0:
                    return f"No tests recorded for {pn} yet."
                return (
                    f"Yield for {pn}: {row['yield_percent']}% "
                    f"({row['passed']} passed / {row['total']} tested)."
                )
        return f"No data found for {pn}."

    if "today" in q or "tested today" in q:
        today_entry = daily_data[-1] if daily_data else None
        if today_entry:
            return f"{today_entry['count']} units tested today ({today_entry['date']})."
        return "No data available for today."

    if "lowest" in q or "worst" in q:
        tested = [r for r in stats_data if r["total"] > 0]
        if not tested:
            return "No test data available yet."
        worst = min(tested, key=lambda r: r["yield_percent"])
        return (
            f"{worst['part_number']} has the lowest yield at "
            f"{worst['yield_percent']}% ({worst['passed']}/{worst['total']})."
        )

    if "total" in q or "how many" in q:
        total = sum(r["total"] for r in stats_data)
        return f"Total tests recorded across all part numbers: {total}."

    return (
        "I can answer questions about: yield for a specific part number "
        "(e.g. '001PN001'), units tested today, or which part has the lowest yield."
    )
