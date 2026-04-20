import pandas as pd
import zipfile
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
dataset_path = os.path.join(BASE_DIR, "..", "dataset")
dataset_path = os.path.abspath(dataset_path)

print("📁 Dataset Path:", dataset_path)

# -------------------------------
# STEP 1: EXTRACT ZIP FILES
# -------------------------------
for file in os.listdir(dataset_path):
    if file.endswith(".zip"):
        with zipfile.ZipFile(os.path.join(dataset_path, file), 'r') as zip_ref:
            zip_ref.extractall(dataset_path)
        print(f"✅ Extracted: {file}")

print("✅ Extraction complete!\n")

# -------------------------------
# STEP 2: COLLECT FILES (IMPORTANT FIX)
# -------------------------------
bus_files = []
hotel_files = []
place_files = []
train_files = []

for root, dirs, files in os.walk(dataset_path):
    for file in files:
        file_lower = file.lower()
        full_path = os.path.join(root, file)

        print("🔍 Found:", file)

        if "bus" in file_lower and file.endswith(".csv"):
            bus_files.append(full_path)

        elif "place" in file_lower and file.endswith(".csv"):
            place_files.append(full_path)

        elif "train" in file_lower:
            train_files.append(full_path)

        elif file.endswith(".csv") and any(city in file_lower for city in [
        "bangalore", "chennai", "delhi", "hyderabad", "kolkata", "mumbai"
]):
         hotel_files.append(full_path)


print("\n📄 Bus Files:", bus_files)
print("📄 Hotel Files:", hotel_files)
print("📄 Place Files:", place_files)
print("📄 Train Files:", train_files)

# -------------------------------
# STEP 3: LOAD ALL FILES
# -------------------------------
all_dfs = []

# BUS
for file in bus_files:
    df = pd.read_csv(file)
    df["Type"] = "Bus"
    all_dfs.append(df)

# HOTEL (THIS FIXES YOUR ISSUE)
for file in hotel_files:
    df = pd.read_csv(file)
    df["Type"] = "Hotel"
    all_dfs.append(df)

# PLACE
for file in place_files:
    df = pd.read_csv(file)
    df["Type"] = "Place"
    all_dfs.append(df)

# TRAIN (THIS FIXES YOUR TRAIN ISSUE)
for file in train_files:
    try:
        if file.endswith(".json"):
            df = pd.read_json(file)
        else:
            df = pd.read_csv(file)

        df["Type"] = "Train"
        all_dfs.append(df)

    except Exception as e:
        print(f"⚠️ Skipping {file} due to error:", e)


# -------------------------------
# STEP 4: MERGE
# -------------------------------
merged_df = pd.concat(all_dfs, ignore_index=True)

# -------------------------------
# STEP 5: SAVE
# -------------------------------
output_path = os.path.join(dataset_path, "merged_dataset.csv")
merged_df.to_csv(output_path, index=False)

print("\n🎉 SUCCESS: ALL DATA MERGED CORRECTLY!")
print("📁 Saved at:", output_path)