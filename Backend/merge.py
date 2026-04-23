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

print("✅ Extraction complete!")

# -------------------------------
# STEP 2: COLLECT FILES
# -------------------------------
bus_files = []
hotel_files = []
place_files = []
train_files = []

for root, dirs, files in os.walk(dataset_path):
    for file in files:

        file_lower = file.lower()
        full_path = os.path.join(root, file)

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

# -------------------------------
# STEP 3: LOAD FILES
# -------------------------------
all_dfs = []
places_only = []

# BUS
for file in bus_files:
    df = pd.read_csv(file)
    df["Type"] = "Bus"
    all_dfs.append(df)

# HOTEL
for file in hotel_files:
    df = pd.read_csv(file)
    df["Type"] = "Hotel"
    all_dfs.append(df)

# PLACE
for file in place_files:
    df = pd.read_csv(file)
    df["Type"] = "Place"
    all_dfs.append(df)
    places_only.append(df)   # separate save

# TRAIN
for file in train_files:
    try:
        if file.endswith(".json"):
            df = pd.read_json(file)
        else:
            df = pd.read_csv(file)

        df["Type"] = "Train"
        all_dfs.append(df)

    except:
        pass

# -------------------------------
# STEP 4: SAVE MERGED DATASET
# -------------------------------
merged_df = pd.concat(all_dfs, ignore_index=True)
merged_df.to_csv(os.path.join(dataset_path, "merged_dataset.csv"), index=False)

# -------------------------------
# STEP 5: SAVE PLACES DATASET
# -------------------------------
if places_only:
    places_df = pd.concat(places_only, ignore_index=True)
    places_df.to_csv(os.path.join(dataset_path, "places_dataset.csv"), index=False)

print("🎉 merged_dataset.csv created")
print("🎉 places_dataset.csv created")