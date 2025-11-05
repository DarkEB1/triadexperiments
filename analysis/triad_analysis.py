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
    expected = analyze_triad("relationships_expected", data)
    actual = analyze_triad("relationships", data)


    print(f"Balanced triads expected: {expected[0]}")
    print(f"Unbalanced triads expected: {expected[1]}")
    print(f"Incomplete triads expected: {expected[2]}")

    print(f"Balanced triads actual: {actual[0]}")
    print(f"Unbalanced triads actual: {actual[1]}")
    print(f"Incomplete triads actual: {actual[2]}")

if __name__ == "__main__":
    main()

# It can happen that A likes B, but B dislikes A. We treat this as neutral (0).
# In order to run this, we need to have an ordered json file which we get by running generate_expected_ratings.py and order_json.py first.