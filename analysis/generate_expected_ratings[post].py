from typing import List, Dict, Any
from openai import OpenAI
import os, json, time, itertools
from dotenv import load_dotenv
#TODO Parallelise
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

JSON_PATH   = "../results/on_repost_bio_other_partisan_info_1.json"
OUTPUT_PATH = "../results/TBO_users_with_relationships.json"

SYSTEM_MSG = """You are an impartial, terse classifier.
Your task: Given two users' personas, output EXACTLY ONE TOKEN from this set: -1, 0, 1

Generally, if you would expect the two users to be friendly/agreeable/aligned or generally like each other, output 1.
If you would expect them to be antagonistic/opposed/hostile or not like each other, output -1.
Otherwise, if you believe they would be neutral towards each other output 0.

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

def post_brief(posts: List[Dict[str, Any]], user_id: int) -> str:
    """Summarize posts for LLM context."""

    brief_posts = []
    for post in posts:
        if post.get("user_id") == user_id:
            brief_posts.append({
                "content" : post.get("post_content").get("content")
            })
    return json.dumps(brief_posts, ensure_ascii=False)

def judge_relationship_llm(user_a: Dict[str, Any], user_b: Dict[str, Any], posts: List[Dict[str, Any]],
                           *, max_retries: int = 3, sleep_s: float = 0.6) -> int:
    """
    Returns -1, 0, or 1 using the LLM.
    """
    ua = persona_brief(user_a["persona"])
    uaposts = post_brief(posts, user_a["identifier"]) #SWAP FILES
    ub = persona_brief(user_b["persona"])
    ubposts = post_brief(posts, user_b["identifier"])

    user_msg = f"""USER_A {user_a['identifier']} persona: {ua}
USER_A {user_a['identifier']} posts: {uaposts}
USER_B {user_b['identifier']} persona: {ub}
USER_B {user_b['identifier']} posts: {ubposts}
Return only one of: -1, 0, 1
"""
    print(user_msg)

    for attempt in range(1, max_retries + 1):
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0,
                max_tokens=2,  
                messages=[
                    {"role": "system", "content": SYSTEM_MSG},
                    {"role": "user", "content": user_msg},
                ],
            )
            raw = (resp.choices[0].message.content or "").strip()
            if raw in {"-1", "0", "1"}:
                return int(raw)
        
            for tok in ("-1", "0", "1"):
                if tok in raw:
                    return int(tok)
        except Exception:
            if attempt == max_retries:
                return 0  
            time.sleep(sleep_s * attempt)

    return 0

def load_data(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def compute_and_attach_relationships(data: Dict[str, Any]) -> Dict[str, Any]:
    users: List[Dict[str, Any]] = data["users"]
    posts: List[Dict[str, Any]] = data["posts"]
    n = len(users)


    for u in users:
        u.setdefault("relationships_expected_post", {})
   
    for u in users:
        u["relationships_expected_post"][u["identifier"]] = 1
        u["relationships"][u["identifier"]] = 1

    # Compute for each unordered pair once, mirror both directions
    for i, j in itertools.combinations(range(n), 2):
        ui, uj = users[i], users[j]
        label = judge_relationship_llm(ui, uj, posts)
        ui["relationships_expected_post"][uj["identifier"]] = label
        uj["relationships_expected_post"][ui["identifier"]] = label

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
