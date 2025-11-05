import json

# Input and output file paths
input_file = "../results/TBO_users_with_relationships.json"
output_file = "../results/ordered_users_with_relationships.json"

# Load JSON data
with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# Sort the users by identifier
if "users" in data:
    data["users"].sort(key=lambda x: x.get("identifier", float("inf")))

    # For each user, sort relationships and relationships_expected by key
    for user in data["users"]:
        if "relationships" in user and isinstance(user["relationships"], dict):
            user["relationships"] = {
                k: user["relationships"][k]
                for k in sorted(user["relationships"], key=lambda x: int(x))
            }

        if "relationships_expected" in user and isinstance(user["relationships_expected"], dict):
            user["relationships_expected"] = {
                k: user["relationships_expected"][k]
                for k in sorted(user["relationships_expected"], key=lambda x: int(x))
            }

# Write back to a new JSON file
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Users and their relationships have been ordered and saved to {output_file}")
