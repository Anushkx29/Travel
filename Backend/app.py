from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import os
import random


app = Flask(__name__)  

app.secret_key = os.urandom(24)
# ---------------- BASE CONFIG ---------------- #
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, '../templates'),
    static_folder=os.path.join(BASE_DIR, '../static')
)

app.secret_key = "mysecret123"

# ---------------- LOAD DATASET ---------------- #
try:
    data_path = os.path.join(BASE_DIR, '../dataset/merged_dataset.csv')
    data = pd.read_csv(data_path)
    print("✅ Dataset Loaded Successfully")
except Exception as e:
    print("❌ Error loading dataset:", e)
    data = pd.DataFrame()

# ---------------- ROUTES ---------------- #

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/wishlist')
def wishlist():
    return render_template('wishlist.html')


# ---------- DESTINATIONS ---------- #
@app.route('/destinations')
def destinations():
    if 'Type' in data.columns:
        places = data[data['Type'] == 'Place'].to_dict(orient='records')
    else:
        places = []
    return render_template('destination.html', places=places)


# ---------- STAYS ---------- #
@app.route('/stays')
def stays():
    if 'Type' in data.columns:
        hotels = data[data['Type'] == 'Hotel'].to_dict(orient='records')
    else:
        hotels = []
    return render_template('stays.html', hotels=hotels)


# ---------- TOURS ---------- #
@app.route('/tours')
def tours():
    if 'Type' in data.columns:
        buses = data[data['Type'] == 'Bus'].to_dict(orient='records')
    else:
        buses = []
    return render_template('tours.html', buses=buses)


# ---------- CONTACT ---------- #
from db import get_db_connection

@app.route('/contact')
def contact():
    return render_template('contact.html')


from flask import flash

@app.route('/submit_review', methods=['POST'])
def submit_review():
    name = request.form.get('name')
    email = request.form.get('email')
    subject = request.form.get('subject')
    message = request.form.get('message')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO reviews (name, email, subject, message)
        VALUES (%s, %s, %s, %s)
    """, (name, email, subject, message))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('thankyou'))


# ---------- BROWSE STAYS ---------- #

# ---------------- HELPER FUNCTION ---------------- #
def get_rating_desc(rating):
    try:
        rating = float(rating)
        if rating >= 4.5:
            return "Excellent"
        elif rating >= 4.0:
            return "Very Good"
        elif rating >= 3.5:
            return "Good"
        elif rating >= 3.0:
            return "Average"
        else:
            return "Poor"
    except:
        return "Not Rated"


# ---------------- ROUTE ---------------- #
@app.route('/browse_stays', methods=['GET'])
def browse_stays():

    city = request.args.get('city', '').strip().lower()
    price = request.args.get('price', '')

    hotels = []

    if city == "":
        return render_template("browse_stays.html", hotels=[], city="", price="")

    try:
        # =========================
        # LOAD DATASET (28 columns)
        # =========================
        df = pd.read_csv(
            r"C:\Users\verma\Travel&Tourism\dataset\hotels_dataset.csv",
            low_memory=False
        )

        # =========================
        # SELECT REQUIRED COLUMNS BY NAME
        # =========================
        df = df[[
        "Category",
        "Hotel Name",
        "Rating",
        "Reviews",
        "Star Rating",
        "Location",
        "Nearest Landmark",
        "Distance to Landmark",
        "Price",
        "Tax"
        ]].copy()
        # =========================
        # RENAME COLUMNS
        # =========================
        df.columns = [
        "type",   # now mapped from Category
        "hotel_name",
        "rating",
        "review",
        "stars",
        "location",
        "landmark",
        "distance",
        "price",
        "tax"
        ]

        # =========================
        # CLEAN DATA
        # =========================
        df = df.dropna(subset=["hotel_name"])

        df["type"] = df["type"].astype(str).str.lower()
        df["location"] = df["location"].astype(str).str.lower().str.strip()
        df["hotel_name"] = df["hotel_name"].astype(str).str.lower().str.strip()
        df["landmark"] = df["landmark"].astype(str).str.lower().str.strip()

        # ONLY HOTELS
        df = df[df["type"] == "hotel"]

        # =========================
        # CITY FILTER
        # =========================
        city_map = {
            "bangalore": "bengaluru",
            "bengaluru": "bangalore"
        }

        search_terms = [city]
        if city in city_map:
            search_terms.append(city_map[city])

        pattern = "|".join(search_terms)

        filtered = df[
            df["location"].str.contains(pattern, na=False) |
            df["hotel_name"].str.contains(pattern, na=False)
        ].copy()

        print("After city filter:", len(filtered))

        # =========================
        # PRICE FILTER
        # =========================
        if price:

            print("Selected price:", price)

            # Clean price column
            filtered["price_num"] = (
                filtered["price"]
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.replace(r"[^\d]", "", regex=True)
            )

            filtered["price_num"] = pd.to_numeric(
                filtered["price_num"], errors="coerce"
            )

            filtered = filtered.dropna(subset=["price_num"])

            print("MAX PRICE:", filtered["price_num"].max())

            # Apply price filter
            if price == "₹0 - ₹1500":
                filtered = filtered[filtered["price_num"] <= 1500]

            elif price == "₹1500 - ₹3000":
                filtered = filtered[
                    (filtered["price_num"] > 1500) &
                    (filtered["price_num"] <= 3000)
                ]

            elif price == "₹3000 - ₹5000":
                filtered = filtered[
                    (filtered["price_num"] > 3000) &
                    (filtered["price_num"] <= 5000)
                ]

            elif price == "₹5000+":
                filtered = filtered[filtered["price_num"] > 5000]

            print("After price filter:", len(filtered))

        # =========================
        # FORMAT DATA
        # =========================
        filtered["hotel_name"] = filtered["hotel_name"].str.title()
        filtered["location"] = filtered["location"].str.title()

        filtered["stars"] = pd.to_numeric(filtered["stars"], errors="coerce").fillna(0).astype(int)
        filtered["rating"] = pd.to_numeric(filtered["rating"], errors="coerce")

        filtered = filtered.sort_values(by="rating", ascending=False)

        # =========================
        # IMAGES
        # =========================
        import random
        images = [
            "images/hotel_default.jpg",
            "images/hotel_default1.jpg",
            "images/hotel_default2.jpg",
            "images/hotel_default3.jpg"
        ]

        # =========================
        # CONVERT TO LIST
        # =========================
        for _, row in filtered.iterrows():
            hotels.append({
                "name": row["hotel_name"],
                "rating": "NA" if pd.isna(row["rating"]) else round(row["rating"], 1),
                "rating_description": get_rating_desc(row["rating"]),
                "location": row["location"],
                "price": row["price"],
                "reviews": int(float(row["review"])) if pd.notna(row["review"]) else 0,
                "star_rating": row["stars"],
                "nearest_landmark": row["landmark"] if pd.notna(row["landmark"]) else "",
                "distance": "" if pd.isna(row["distance"]) or str(row["distance"]).strip().lower() == "nan" else row["distance"],
                "image": random.choice(images)
            })

        return render_template(
            "browse_stays.html",
            hotels=hotels,
            city=city,
            price=price
        )

    except Exception as e:
        return f"ERROR: {str(e)}"
    

    #----------WISHLIST--------------#

import os
import pandas as pd
import re
from flask import request, render_template

@app.route('/place_details')
def place_details():

    name = request.args.get('name', '').strip().lower()
    image = request.args.get('image', '')

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(BASE_DIR, "..", "dataset", "places_dataset.csv")

    # ✅ READ CSV PROPERLY
    df = pd.read_csv(file_path, encoding="utf-8", engine="python")

    # -----------------------------
    # ✅ CLEAN DATA
    # -----------------------------
    df["Place"] = df["Place"].astype(str).str.lower().str.strip()
    df["City"] = df["City"].astype(str).str.lower().str.strip()

    # 🚀 REMOVE NUMBERING (IMPORTANT)
    df["Place"] = df["Place"].apply(lambda x: re.sub(r'^\d+\.\s*', '', x))

    # clean input
    name = " ".join(name.split())

    # -----------------------------
    # 🔹 CASE 1: EXACT PLACE MATCH
    # -----------------------------
    place_match = df[df["Place"] == name]

    if not place_match.empty:
        data = place_match.to_dict(orient="records")

    else:
        # -----------------------------
        # 🔹 CASE 2: CITY MATCH
        # -----------------------------
        city_match = df[df["City"] == name]

        if not city_match.empty:
            data = city_match.to_dict(orient="records")
        else:
            return "Place not found"

    # -----------------------------
    # ✅ REMOVE DUPLICATES
    # -----------------------------
    data = pd.DataFrame(data).drop_duplicates(subset=["Place"]).to_dict(orient="records")

    # -----------------------------
    # ✅ IMAGE FIX
    # -----------------------------
    for row in data:
        row["image"] = image if image else "/static/images/default_place.jpg"
        row["Place"] = str(row["Place"]).title()
        row["City"] = str(row["City"]).upper()

    return render_template("place_details.html", places=data)

    # ---------- BROWSE BUSES ---------- #

@app.route('/browse_buses', methods=['GET']) 
def browse_buses():

    source = request.args.get('from', '').strip().lower()
    destination = request.args.get('to', '').strip().lower()

    buses = []

    if source == "" or destination == "":
        return render_template(
            "browse_buses.html",
            buses=[],
            source="",
            destination=""
        )

    try:
        # =========================
        # LOAD DATA
        # =========================
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

        file_path = os.path.join(BASE_DIR, "..", "dataset", "merged_dataset.csv")

        df = pd.read_csv(file_path, low_memory=False)
       

        # =========================
        # CLEAN DATA
        # =========================
        df["From"] = df["From"].astype(str).str.lower().str.strip()
        df["To"] = df["To"].astype(str).str.lower().str.strip()

        # =========================
        # FILTER BUSES
        # =========================
        filtered = df[
            (df["From"].str.contains(source)) &
            (df["To"].str.contains(destination))
        ].copy()

        print("After filter:", len(filtered))

        # =========================
        # FORMAT DATA
        # =========================
        images = [
            "images/bus_default.jpg",
            "images/bus_default1.jpg",
            "images/bus_default2.jpg",
            "images/bus_default3.jpg"
]

        for _, row in filtered.iterrows():

            # Distance → base
            if pd.notna(row["Distance"]):
                try:
                   base = int(float(row["Distance"]))
                except:
                   base = 100
            else:
                base = 100

            # Price calculation
            price = int(base * 2 + random.randint(100, 500))

            buses.append({
                "operator": row.get("Operator", "Unknown"),
                "from": row.get("From", ""),
                "to": row.get("To", ""),
                "distance": str(row["Distance"]) + " km" if pd.notna(row["Distance"]) else "N/A",
                "bus_type": row.get("Bus Type", "Standard"),
                "departure": row.get("Departure", "N/A"),
                "arrival": row.get("Arrival", "N/A"),
                "price": price,
                "image": random.choice(images)
            })

        return render_template(
            "browse_buses.html",
            buses=buses,
            source=source.title(),
            destination=destination.title()
        )

    except Exception as e:
        return f"ERROR: {str(e)}"

# ---------- BROWSE TRAINS ---------- #

import ast
import random

@app.route('/browse_trains', methods=['GET'])
def browse_trains():

    from_city = request.args.get('from', '').strip().lower()
    to_city = request.args.get('to', '').strip().lower()

    trains = []

    if from_city == "" or to_city == "":
        return render_template(
            "browse_trains.html",
            trains=[],
            from_city="",
            to_city=""
        )

    try:
        df = pd.read_csv(
            r"C:\Users\verma\Travel&Tourism\dataset\merged_dataset.csv",
            low_memory=False
        )

        df = df[[
            "trainNumber", "trainName", "route",
            "runningDays", "trainRoute"
        ]].copy()

        # CLEAN
        df["route"] = df["route"].astype(str).str.lower()
        df["trainName"] = df["trainName"].astype(str).str.title()

        # FILTER
        filtered = df[
            df["route"].str.contains(from_city, na=False) &
            df["route"].str.contains(to_city, na=False)
        ].copy()

        print("Filtered trains:", len(filtered))

        # IMAGES
        images = [
            "images/train_default.jpg",
            "images/train_default1.jpg",
            "images/train_default2.jpg",
            "images/train_default3.jpg"
        ]

        for _, row in filtered.iterrows():

            # =========================
            # ✅ PARSE RUNNING DAYS
            # =========================
            try:
                days_dict = ast.literal_eval(str(row["runningDays"]))
                running_days = [day for day, val in days_dict.items() if val]

                running_days = ", ".join([d.capitalize()[:3] for d in running_days]) if running_days else "Not Available"

            except:
                running_days = "Not Available"

            # =========================
            # ✅ PARSE TRAIN ROUTE
            # =========================
            try:
                route_list = ast.literal_eval(str(row["trainRoute"]))

                # FIRST station → departure
                departure = route_list[0].get("departs", "N/A")

                # LAST station → arrival
                arrival = route_list[-1].get("arrives", "N/A")

            except:
                departure = "N/A"
                arrival = "N/A"

            # =========================
            # 💰 RANDOM PRICE
            # =========================
            price = random.randint(300, 1500)

            trains.append({
                "number": row.get("trainNumber", "N/A"),
                "name": row.get("trainName", "Unknown Train"),
                "route": row.get("route", "").title(),
                "days": running_days,
                "departure": departure,
                "arrival": arrival,
                "price": price,
                "image": random.choice(images)
            })

        return render_template(
            "browse_trains.html",
            trains=trains,
            from_city=from_city,
            to_city=to_city
        )

    except Exception as e:
        return f"ERROR: {str(e)}"
    
# ---------- LOAD PLACES DATASET ---------- #
places_data = pd.read_csv("../dataset/places_dataset.csv", low_memory=False)

# ----------------- DESTINATION BROWSE --------------------#

@app.route('/destination_browse')
def destination_browse():

    city = request.args.get('city', '').strip().lower()
    selected_type = request.args.get('type', '').strip()

    df = places_data.copy()

    # CLEAN DATA
    df['City'] = df['City'].astype(str).str.strip().str.lower()
    df['Type'] = df['Type'].astype(str).str.strip()

    # FILTER BY CITY
    if city:
        df = df[df['City'].str.contains(city, na=False)]

    # FILTER BY TYPE
    if selected_type:
        df = df[df['Type'] == selected_type]

    # FIRST LOAD
    if not city and not selected_type:
        places = []
    else:
        places = df.to_dict(orient='records')

    # 👉 CATEGORY PAGE
    if selected_type:
        return render_template(
            "destination_type.html",
            places=places,
            selected_type=selected_type
        )

    # 👉 SEARCH PAGE
    return render_template(
        "destination_browse.html",
        places=places
    )

# ---------- LOGIN ---------- #
from db import get_db_connection

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM users WHERE email=%s AND password=%s
        """, (email, password))

        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user:
            session['username'] = user[1]   # assuming name is 2nd column in users table
            return redirect(url_for('home'))
        else:
            return "❌ Invalid Credentials"

    return render_template('login.html')




# ---------- REGISTER ---------- #
from db import get_db_connection

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        password = request.form.get('password')

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO users (name, phone, email, password)
                VALUES (%s, %s, %s, %s)
            """, (name, phone, email, password))

            conn.commit()
        except Exception as e:
            return f"❌ Error: {str(e)}"
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('login'))

    return render_template('register.html')

# ---------- STATIC PAGES ---------- #
@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/thankyou')
def thankyou():
    return render_template('thankyou.html')

@app.route('/test')
def test():
    return "Working"

# ---------- LOGOUT ---------- #
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

# ---------------- RUN APP ---------------- #
if __name__ == '__main__':
    app.run(debug=True)