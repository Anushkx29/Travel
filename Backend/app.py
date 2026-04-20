from flask import Flask, render_template, request, redirect, url_for
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
            r"C:\Users\verma\Travel&Tourism\dataset\merged_dataset.csv",
            low_memory=False
        )

        # =========================
        # SELECT REQUIRED COLUMNS BY NAME
        # =========================
        df = df[[
            "Type",
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
            "type",
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
                "reviews": int(row["review"]) if str(row["review"]).isdigit() else 0,
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

# ---------------- RUN APP ---------------- #
if __name__ == '__main__':
    app.run(debug=True)