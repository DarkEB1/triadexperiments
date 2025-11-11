from typing import List, Dict, Any
import os, json, time, itertools

INPUT_PATH = "../results/ordered_users_with_relationships.json"

def load_data(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
    
def analyze_triad(relationships, data) -> List[int]:
    results = [0,0,0] # balanced, unbalanced, incomplete
    for i in range(1, len(data["users"])-1):
        Arelations = data["users"][i-1][relationships]
        for j in range(i+1, len(data["users"])):
            if Arelations[str(j)] != 0:
                Brelations = data["users"][j-1][relationships]
                if Brelations[str(i)] != 0 and Brelations[str(i)] == Arelations[str(j)]:
                    for k in range(j+1, len(data["users"])+1):
                        if Arelations[str(k)] != 0 and Brelations[str(k)] != 0:
                            Crelations = data["users"][k-1][relationships]
                            if Crelations[str(i)] != 0 and Crelations[str(j)] != 0 and Crelations[str(i)] == Arelations[str(k)] and Crelations[str(j)] == Brelations[str(k)]:
                                if (Arelations[str(j)] * Brelations[str(k)] * Crelations[str(i)] == 1):
                                    results[0] += 1
                                else:
                                    results[1] += 1
                            else:
                                results[2] += 1
                        else:
                            results[2] += 1
                else:
                    results[2] += 1
            else:
                results[2] += 1

    return results

def main():
    
    data = load_data(INPUT_PATH)
    expected_post = analyze_triad("relationships_expected_post", data)
    expected_pre = analyze_triad("relationships_expected_pre", data)
    actual_post = analyze_triad("relationships_post", data)
    actual_pre = analyze_triad("relationships_pre", data)

    print(f"Balanced triads expected pre: {expected_pre[0]}")
    print(f"Unbalanced triads expected pre: {expected_pre[1]}")
    print(f"Incomplete triads expected pre: {expected_pre[2]}")

    print(f"Balanced triads expected post: {expected_post[0]}")
    print(f"Unbalanced triads expected post: {expected_post[1]}")
    print(f"Incomplete triads expected post: {expected_post[2]}")

    print(f"Balanced triads actual pre: {actual_pre[0]}")
    print(f"Unbalanced triads actual pre: {actual_pre[1]}")
    print(f"Incomplete triads actual pre: {actual_pre[2]}")

    print(f"Balanced triads actual post: {actual_post[0]}")
    print(f"Unbalanced triads actual post: {actual_post[1]}")
    print(f"Incomplete triads actual post: {actual_post[2]}")

if __name__ == "__main__":
    main()

# It can happen that A likes B, but B dislikes A. We treat this as neutral (0).
# In order to run this, we need to have an ordered json file which we get by running generate_expected_ratings.py and order_json.py first.