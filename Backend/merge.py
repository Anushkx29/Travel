import pandas as pd
import zipfile
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
dataset_path = os.path.join(BASE_DIR, "..", "dataset")
dataset_path = os.path.abspath(dataset_path)

print("📁 Dataset Path:", dataset_path)

# -------------------------------
# STEP 0: CLASSIFICATION FUNCTION
# -------------------------------
def classify_place(row):
    text = str(row.get('Place', '')) + " " + str(row.get('Place_desc', ''))
    text = text.lower()

    # 🛕 Holy Places (priority first)
    if any(word in text for word in [
        'temple', 'mandir', 'mosque', 'church', 'gurudwara',
        'shrine', 'dham', 'ashram', 'math',
        'vaishno devi', 'amarnath', 'tirupati'
    ]):
        return 'Holy Places'

    # 🏰 Monuments
    elif any(word in text for word in [
        'fort', 'palace', 'monument', 'tomb',
        'museum', 'tower', 'gate', 'caves', 'arch'
    ]):
        return 'Monuments'

    # 🏖️ Beaches
    elif any(word in text for word in [
        'beach', 'sea', 'coast', 'shore', 'island'
    ]):
        return 'Beaches'

    # 🏔️ Mountains / Nature
    elif any(word in text for word in [
        'mountain', 'hill', 'valley', 'peak',
        'waterfall', 'lake', 'river', 'trek', 'forest'
    ]):
        return 'Mountains'

    return None  # fallback later


# -------------------------------
# STEP 0B: CITY FALLBACK MAPPING
# -------------------------------
city_map = {
    # Mountains
    "MANALI": "Mountains", "LEH LADAKH": "Mountains", "COORG": "Mountains",
    "SRINAGAR": "Mountains", "GANGTOK": "Mountains", "MUNNAR": "Mountains",
    "MCLEODGANJ": "Mountains", "DARJEELING": "Mountains", "NANITAL": "Mountains",
    "SHIMLA": "Mountains", "OOTY": "Mountains", "LONAVALA": "Mountains",
    "MUSSOORIE": "Mountains", "KODAIKANAL": "Mountains", "DALHOUSIE": "Mountains",
    "PACHMARHI": "Mountains", "MOUNT ABU": "Mountains", "WAYANAD": "Mountains",
    "AULI": "Mountains", "KASOL": "Mountains", "ALMORA": "Mountains",
    "KALIMPONG": "Mountains", "SHIMOGA": "Mountains", "KASAULI": "Mountains",
    "NAHAN": "Mountains", "DEHRADUN": "Mountains",

    # Beaches
    "GOA": "Beaches", "ANDAMAN": "Beaches", "LAKSHADWEEP": "Beaches",
    "VARKALA": "Beaches", "ALLEPPEY": "Beaches", "MUMBAI": "Beaches",
    "PONDICHERRY": "Beaches", "KANYAKUMARI": "Beaches", "KOCHI": "Beaches",
    "VISAKHAPATNAM": "Beaches", "DIGHA": "Beaches", "KOVALAM": "Beaches",
    "ALIBAUG": "Beaches", "POOVAR": "Beaches",

    # Holy Places
    "VARANASI": "Holy Places", "RISHIKESH": "Holy Places", "HARIDWAR": "Holy Places",
    "VAISHNO DEVI": "Holy Places", "AMARNATH": "Holy Places", "BODH GAYA": "Holy Places",
    "TIRUPATI": "Holy Places", "UJJAIN": "Holy Places", "MATHURA": "Holy Places",
    "VRINDAVAN": "Holy Places", "RAMESHWARAM": "Holy Places", "SHIRDI": "Holy Places",
    "MADURAI": "Holy Places", "PURI": "Holy Places", "AJMER": "Holy Places",

    # Monuments
    "JAIPUR": "Monuments", "UDAIPUR": "Monuments", "AGRA": "Monuments",
    "KOLKATA": "Monuments", "JODHPUR": "Monuments", "DELHI": "Monuments",
    "JAISALMER": "Monuments", "HYDERABAD": "Monuments", "KHAJURAHO": "Monuments",
    "CHENNAI": "Monuments", "AHMEDABAD": "Monuments", "MYSORE": "Monuments",
    "HAMPI": "Monuments", "GWALIOR": "Monuments", "LUCKNOW": "Monuments",
    "THANJAVUR": "Monuments", "BHUBANESHWAR": "Monuments",
    "AURANGABAD": "Monuments", "CHITTORGARH": "Monuments",
    "BIKANER": "Monuments"
}

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
hotel_only = []

# -------- BUS --------
for file in bus_files:
    df = pd.read_csv(file)
    df["Category"] = "bus"
    all_dfs.append(df)

# -------- HOTEL --------
for file in hotel_files:
    df = pd.read_csv(file)

    df["Category"] = "hotel"

    all_dfs.append(df)     # for merged dataset
    hotel_only.append(df)  # for hotel dataset

# -------- PLACE --------
for file in place_files:
    df = pd.read_csv(file)

    df["Category"] = "place"

    # Clean city names
    if "City" in df.columns:
        df["City"] = df["City"].astype(str).str.strip().str.upper()

    # STEP 1: classify by place
    df["Type"] = df.apply(classify_place, axis=1)

    # STEP 2: fallback to city mapping
    if "City" in df.columns:
        df["Type"] = df["Type"].fillna(df["City"].map(city_map))

    # STEP 3: final fallback
    df["Type"] = df["Type"].fillna("Other")

    all_dfs.append(df)
    places_only.append(df)

# -------- TRAIN --------
for root, dirs, files in os.walk(dataset_path):
    for file in files:
        if "train" in file.lower() and (file.endswith(".json") or file.endswith(".csv")):

            full_path = os.path.join(root, file)

            try:
                if file.endswith(".json"):
                    df = pd.read_json(full_path)
                else:
                    df = pd.read_csv(full_path)

                df["Category"] = "train"
                all_dfs.append(df)

            except Exception as e:
                print(f"⚠️ Skipping {file}: {e}")

# -------------------------------
# STEP 4: SAVE MERGED DATASET
# -------------------------------
if all_dfs:
    merged_df = pd.concat(all_dfs, ignore_index=True)
    merged_path = os.path.join(dataset_path, "merged_dataset.csv")
    merged_df.to_csv(merged_path, index=False)
    print("🎉 merged_dataset.csv created")

# -------------------------------
# STEP 5: SAVE PLACES DATASET
# -------------------------------
if places_only:
    places_df = pd.concat(places_only, ignore_index=True)
    places_path = os.path.join(dataset_path, "places_dataset.csv")
    places_df.to_csv(places_path, index=False)
    print("🎉 places_dataset.csv created")

    # -------------------------------
# STEP 6: SAVE HOTELS DATASET
# -------------------------------
if hotel_only:
    hotels_df = pd.concat(hotel_only, ignore_index=True)
    hotels_path = os.path.join(dataset_path, "hotels_dataset.csv")
    hotels_df.to_csv(hotels_path, index=False)
    print("🎉 hotels_dataset.csv created")

print("✅ ALL DONE SUCCESSFULLY") 