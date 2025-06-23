import pandas as pd
import json

# Load the dataset
df = pd.read_csv("Food Ingredients and Recipe Dataset with Image Name Mapping.csv")

# Prepare recipe data
recipes = []
for _, row in df.iterrows():
    recipe = {
        "title": row["Title"],
        "ingredients": str(row["Cleaned_Ingredients"]).lower().split(", "),
        "instructions": row["Instructions"]
    }
    recipes.append(recipe)

# Save to JSON
with open("recipes.json", "w") as f:
    json.dump(recipes, f, indent=4)

print("recipes.json created successfully!")
