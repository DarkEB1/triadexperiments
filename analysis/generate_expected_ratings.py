from typing import List, Dict, Any
from openai import OpenAI
import os, json, time, itertools
from dotenv import load_dotenv
#TODO IN ORDER, TODO ISNT CATCHING ALL
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

JSON_PATH   = "../results/on_repost_bio_other_partisan_info_1.json"
OUTPUT_PATH = "../results/on_repost_bio_with_relationships.json"

SYSTEM_MSG = """You are an impartial, terse classifier.
Your task: Given two users' personas, output EXACTLY ONE TOKEN from this set: -1, 0, 1

Semantics:
-1 = users are ideologically/socially opposed, or likely antagonistic.
  (e.g., directly conflicting loves/hates; strong opposing partisanship; hostile stances.)
  Prefer -1 when clear conflict is present.
  If one user hates a group/person the other loves, that is strong evidence for -1.
  If partisan scores strongly diverge, that is evidence toward -1.

 0 = unclear, mixed, or insufficient evidence to call alignment vs antagonism.
   (weak/unknown overlap; not enough signal; contradictory but weak signals.)

 1 = users are aligned or likely friendly.
   (shared “loveList” items; similar partisan/ideology; compatible issue priorities.)

Do not explain. Do not add whitespace. Output only -1 or 0 or 1.
"""

def persona_brief(p: Dict[str, Any]) -> str:
    """Keep the LLM context small but informative."""
    keys = [
        "party", "liberalConservative", "partisan", "loveList", "hateList",
        "importantProblems", "voted2020_for", "state", "religion", "gender", "age"
    ]
    brief = {k: p.get(k, None) for k in keys}
    return json.dumps(brief, ensure_ascii=False)

def judge_relationship_llm(user_a: Dict[str, Any], user_b: Dict[str, Any],
                           *, max_retries: int = 3, sleep_s: float = 0.6) -> int:
    """
    Returns -1, 0, or 1 using the LLM.
    """
    ua = persona_brief(user_a["persona"])
    ub = persona_brief(user_b["persona"])

    user_msg = f"""USER_A {user_a['identifier']} persona: {ua}
USER_B {user_b['identifier']} persona: {ub}

Return only one of: -1, 0, 1
"""

    for attempt in range(1, max_retries + 1):
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0,
                max_tokens=1,  # single token expected
                messages=[
                    {"role": "system", "content": SYSTEM_MSG},
                    {"role": "user", "content": user_msg},
                ],
            )
            raw = (resp.choices[0].message.content or "").strip()
            if raw in {"-1", "0", "1"}:
                return int(raw)
            # Last-chance sanitize
            for tok in ("-1", "0", "1"):
                if tok in raw:
                    return int(tok)
        except Exception:
            if attempt == max_retries:
                return 0  # neutral fallback on persistent failure
            time.sleep(sleep_s * attempt)

    return 0

def load_data(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def compute_and_attach_relationships(data: Dict[str, Any]) -> Dict[str, Any]:
    users: List[Dict[str, Any]] = data["users"]
    n = len(users)

    # Ensure each user has a relationships dict
    for u in users:
        u.setdefault("relationships_expected", {})

    # Self-relationship convention: 1
    for u in users:
        u["relationships_expected"][u["identifier"]] = 1
        u["relationships"][u["identifier"]] = 1

    # Compute for each unordered pair once, mirror both directions
    for i, j in itertools.combinations(range(n), 2):
        ui, uj = users[i], users[j]
        label = judge_relationship_llm(ui, uj)
        ui["relationships_expected"][uj["identifier"]] = label
        uj["relationships_expected"][ui["identifier"]] = label

    return data

def save_json(data: Dict[str, Any], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    data = load_data(JSON_PATH)
    data = compute_and_attach_relationships(data)
    save_json(data, OUTPUT_PATH)
    print(f"Wrote JSON with relationships to: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
