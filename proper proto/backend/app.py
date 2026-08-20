from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import traceback
import joblib
import pandas as pd

# ============================================================
# SPORTFIT PATHFINDER - FLASK BACKEND
# Existing ML model + recommendation layer
# ============================================================

app = Flask(__name__)
CORS(app)

# ------------------------------------------------------------
# PATHS
# ------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

MODEL_PATH = os.path.join(BACKEND_DIR, "sports_model.pkl")
USERS_PATH = os.path.join(BACKEND_DIR, "users.json")

print("=" * 70)
print("SPORTFIT PATHFINDER BACKEND")
print("=" * 70)
print("Base directory:")
print(BASE_DIR)
print()
print("Frontend directory:")
print(FRONTEND_DIR)
print()
print("Model path:")
print(MODEL_PATH)
print()

# ------------------------------------------------------------
# EXISTING MODEL
# ------------------------------------------------------------

model = None
model_error = None

try:
    if not os.path.exists(MODEL_PATH):
        model_error = "sports_model.pkl was not found"
        print("ERROR:", model_error)
    else:
        print("Trying joblib.load()...")
        model = joblib.load(MODEL_PATH)

        print("=" * 70)
        print("EXISTING SPORTS MODEL LOADED")
        print("=" * 70)

except Exception as e:
    model_error = f"{type(e).__name__}: {str(e)}"

    print("=" * 70)
    print("ERROR: COULD NOT LOAD sports_model.pkl")
    print("=" * 70)
    print(model_error)
    print()
    print("The Flask server will still start.")
    print("The recommendation layer can still provide recommendations.")
    print()

# ------------------------------------------------------------
# MODEL FEATURES
# These are the SAME features used by your existing model.
# DO NOT change these.
# ------------------------------------------------------------

MODEL_FEATURES = [
    "age",
    "height_cm",
    "weight_kg",
    "resting_heart_rate",
    "max_heart_rate",
    "VO2_max",
    "training_hours_per_week",
    "reaction_time_sec",
    "agility_score",
    "strength_score",
    "endurance_score",
    "speed_index",
    "fatigue_score",
    "recovery_time_hr",
    "fitness_score"
]

# ------------------------------------------------------------
# DEFAULT VALUES
# These are the training medians from your existing project.
# We are NOT retraining the model.
# ------------------------------------------------------------

DEFAULT_VALUES = {
    "resting_heart_rate": 75.0,
    "max_heart_rate": 185.0,
    "VO2_max": 52.132797,
    "training_hours_per_week": 11.0,
    "reaction_time_sec": 0.582641,
    "agility_score": 46.816035,
    "strength_score": 49.781293,
    "endurance_score": 49.439077,
    "speed_index": 49.008530,
    "fatigue_score": 48.718687,
    "recovery_time_hr": 26.039966,
    "fitness_score": 49.790946
}

# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------

def first_value(data, keys, default=None):
    """
    Return the first available value from a list of possible keys.
    This makes the backend compatible with slightly different
    frontend field names.
    """
    for key in keys:
        if key in data:
            value = data.get(key)

            if value is not None and value != "":
                return value

    return default


def to_float(value, default=None):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


def to_int(value, default=None):
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (ValueError, TypeError):
        return default


def normalize_gender(value):
    if value is None:
        return "Not specified"

    text = str(value).strip().lower()

    if text in ["male", "m", "man"]:
        return "Male"

    if text in ["female", "f", "woman"]:
        return "Female"

    if text in [
        "third gender",
        "third_gender",
        "third-gender",
        "other",
        "non-binary",
        "nonbinary"
    ]:
        return "Third Gender"

    return str(value).strip()


def normalize_para(value):
    if isinstance(value, bool):
        return value

    if value is None:
        return False

    text = str(value).strip().lower()

    return text in [
        "true",
        "yes",
        "1",
        "para athlete",
        "para",
        "disabled",
        "disability",
        "athlete with disability"
    ]


def normalize_activity(value):
    if value is None:
        return ""

    return str(value).strip().lower()


def normalize_goal(value):
    if value is None:
        return ""

    return str(value).strip().lower()


def calculate_bmi(height_cm, weight_kg):
    try:
        if height_cm is None or weight_kg is None:
            return None

        height_m = float(height_cm) / 100.0

        if height_m <= 0:
            return None

        return round(float(weight_kg) / (height_m * height_m), 1)

    except Exception:
        return None


# ------------------------------------------------------------
# BUILD MODEL INPUT
# ------------------------------------------------------------

def build_model_input(data):
    age = to_int(
        first_value(
            data,
            ["age", "user_age"],
            22
        ),
        22
    )

    height_cm = to_float(
        first_value(
            data,
            ["height_cm", "height", "heightCm"],
            175
        ),
        175
    )

    weight_kg = to_float(
        first_value(
            data,
            ["weight_kg", "weight", "weightKg"],
            70
        ),
        70
    )

    values = {
        "age": age,
        "height_cm": height_cm,
        "weight_kg": weight_kg
    }

    # Fill the remaining existing model features
    # with the original training medians.

    for feature in MODEL_FEATURES:
        if feature not in values:
            values[feature] = DEFAULT_VALUES[feature]

    # Make absolutely sure the column order is identical
    # to the original model.

    model_input = pd.DataFrame(
        [[values[feature] for feature in MODEL_FEATURES]],
        columns=MODEL_FEATURES
    )

    return model_input


# ------------------------------------------------------------
# ML PREDICTION
# ------------------------------------------------------------

def get_ml_prediction(data):
    """
    Run the EXISTING trained model.

    If it fails, return None instead of crashing the website.
    """

    if model is None:
        return None

    try:
        model_input = build_model_input(data)

        prediction = model.predict(model_input)[0]

        return str(prediction)

    except Exception as e:
        print("ML prediction error:")
        print(type(e).__name__, str(e))
        traceback.print_exc()

        return None


# ------------------------------------------------------------
# RECOMMENDATION LAYER
#
# IMPORTANT:
# This does NOT retrain the model.
#
# The existing model gives one prediction.
# This layer makes the website recommendation more useful
# based on the profile information supplied by the user.
# ------------------------------------------------------------

def recommendation_layer(data, ml_prediction):
    age = to_int(
        first_value(data, ["age", "user_age"], 22),
        22
    )

    height_cm = to_float(
        first_value(data, ["height_cm", "height", "heightCm"], 175),
        175
    )

    weight_kg = to_float(
        first_value(data, ["weight_kg", "weight", "weightKg"], 70),
        70
    )

    gender = normalize_gender(
        first_value(
            data,
            ["gender", "sex"],
            "Not specified"
        )
    )

    para = normalize_para(
        first_value(
            data,
            [
                "para_athlete",
                "paraAthlete",
                "athlete_type",
                "disability",
                "disability_status"
            ],
            False
        )
    )

    goal = normalize_goal(
        first_value(
            data,
            [
                "primary_goal",
                "goal",
                "fitness_goal"
            ],
            ""
        )
    )

    activity = normalize_activity(
        first_value(
            data,
            [
                "preferred_activity_level",
                "activity_level",
                "activity"
            ],
            ""
        )
    )

    accessibility = normalize_activity(
        first_value(
            data,
            [
                "accessibility_needs",
                "accessibility"
            ],
            ""
        )
    )

    bmi = calculate_bmi(height_cm, weight_kg)

    # --------------------------------------------------------
    # PARA ATHLETE RECOMMENDATIONS
    # --------------------------------------------------------

    if para:

        # Accessibility / para-sport recommendations.
        if any(word in accessibility for word in [
            "wheelchair",
            "mobility",
            "physical"
        ]):
            primary = "Wheelchair Tennis"
            alternatives = [
                "Para Table Tennis",
                "Para Archery",
                "Sitting Volleyball"
            ]

        elif "vision" in accessibility or "visual" in accessibility:
            primary = "Para Swimming"
            alternatives = [
                "Blind Football",
                "Goalball",
                "Para Athletics"
            ]

        elif "low impact" in activity:
            primary = "Para Swimming"
            alternatives = [
                "Para Table Tennis",
                "Para Archery",
                "Para Rowing"
            ]

        elif "strength" in goal or "muscle" in goal:
            primary = "Para Powerlifting"
            alternatives = [
                "Para Athletics",
                "Para Rowing",
                "Para Swimming"
            ]

        elif "speed" in goal:
            primary = "Para Athletics"
            alternatives = [
                "Para Cycling Track",
                "Para Cycling Road",
                "Para Swimming"
            ]

        else:
            primary = "Para Badminton"
            alternatives = [
                "Para Table Tennis",
                "Para Archery",
                "Para Swimming"
            ]

        return {
            "recommended_sport": primary,
            "alternatives": alternatives,
            "reason": (
                "The recommendation prioritizes inclusive para-sport "
                "pathways based on the athlete profile."
            ),
            "type": "para",
            "bmi": bmi
        }

    # --------------------------------------------------------
    # NON-PARA RECOMMENDATIONS
    # --------------------------------------------------------

    # First use the existing model when it produces a
    # meaningful sport.

    if ml_prediction:
        prediction_lower = ml_prediction.strip().lower()

        meaningful_predictions = {
            "running": "Running",
            "badminton": "Badminton",
            "table tennis": "Table Tennis",
            "athletics": "Athletics",
            "weightlifting": "Weightlifting"
        }

        for key, sport_name in meaningful_predictions.items():
            if key in prediction_lower:
                primary = sport_name

                alternatives_map = {
                    "Running": [
                        "Athletics",
                        "Badminton",
                        "Table Tennis"
                    ],
                    "Badminton": [
                        "Table Tennis",
                        "Running",
                        "Athletics"
                    ],
                    "Table Tennis": [
                        "Badminton",
                        "Athletics",
                        "Running"
                    ],
                    "Athletics": [
                        "Running",
                        "Badminton",
                        "Table Tennis"
                    ],
                    "Weightlifting": [
                        "Athletics",
                        "Running",
                        "Badminton"
                    ]
                }

                return {
                    "recommended_sport": primary,
                    "alternatives": alternatives_map[primary],
                    "reason": (
                        "The existing trained sports model identified "
                        "this sport as the strongest match."
                    ),
                    "type": "ml",
                    "bmi": bmi
                }

    # --------------------------------------------------------
    # FALLBACK RECOMMENDATION
    #
    # This is the important part for your current problem.
    # If the old model returns General Fitness because its
    # hidden inputs are medians, we do NOT blindly show
    # General Fitness every time.
    # --------------------------------------------------------

    # Goal-based rules

    if any(word in goal for word in [
        "strength",
        "muscle",
        "strength training",
        "build muscle"
    ]):
        primary = "Weightlifting"
        alternatives = [
            "Athletics",
            "Running",
            "Badminton"
        ]

    elif any(word in goal for word in [
        "endurance",
        "stamina",
        "cardio",
        "fitness"
    ]):
        primary = "Running"
        alternatives = [
            "Athletics",
            "Swimming",
            "Badminton"
        ]

    elif any(word in goal for word in [
        "speed",
        "agility",
        "performance"
    ]):
        primary = "Athletics"
        alternatives = [
            "Badminton",
            "Running",
            "Table Tennis"
        ]

    elif any(word in goal for word in [
        "fun",
        "recreation",
        "social"
    ]):
        primary = "Badminton"
        alternatives = [
            "Table Tennis",
            "Running",
            "Athletics"
        ]

    # Activity-based rules

    elif "high" in activity:
        primary = "Athletics"
        alternatives = [
            "Running",
            "Badminton",
            "Weightlifting"
        ]

    elif "moderate" in activity:
        primary = "Badminton"
        alternatives = [
            "Running",
            "Table Tennis",
            "Athletics"
        ]

    elif "low" in activity:
        primary = "Table Tennis"
        alternatives = [
            "Badminton",
            "Swimming",
            "Running"
        ]

    # BMI can help differentiate the fallback.
    elif bmi is not None and bmi < 18.5:
        primary = "Swimming"
        alternatives = [
            "Badminton",
            "Table Tennis",
            "Running"
        ]

    elif bmi is not None and bmi >= 27:
        primary = "Swimming"
        alternatives = [
            "Walking / Running",
            "Badminton",
            "Table Tennis"
        ]

    # Height can provide another simple differentiation.
    elif height_cm >= 185:
        primary = "Athletics"
        alternatives = [
            "Running",
            "Badminton",
            "Swimming"
        ]

    elif height_cm <= 165:
        primary = "Table Tennis"
        alternatives = [
            "Badminton",
            "Running",
            "Athletics"
        ]

    else:
        primary = "Badminton"
        alternatives = [
            "Table Tennis",
            "Running",
            "Athletics"
        ]

    return {
        "recommended_sport": primary,
        "alternatives": alternatives,
        "reason": (
            "The existing ML model returned a general fitness category, "
            "so the recommendation layer used the available profile "
            "information to provide a more specific sport pathway."
        ),
        "type": "profile",
        "bmi": bmi
    }


# ------------------------------------------------------------
# HOME PAGE
# ------------------------------------------------------------

@app.route("/")
def home():
    return send_from_directory(FRONTEND_DIR, "index.html")


# ------------------------------------------------------------
# SERVE FRONTEND FILES
# ------------------------------------------------------------

@app.route("/<path:filename>")
def frontend_files(filename):
    file_path = os.path.join(FRONTEND_DIR, filename)

    if os.path.isfile(file_path):
        return send_from_directory(FRONTEND_DIR, filename)

    return jsonify({
        "error": "Frontend file not found",
        "file": filename
    }), 404


# ------------------------------------------------------------
# HEALTH CHECK
# ------------------------------------------------------------

@app.route("/api/health", methods=["GET"])
def health():

    return jsonify({
        "status": "running",
        "backend": "Flask",
        "model_file_exists": os.path.exists(MODEL_PATH),
        "model_loaded": model is not None,
        "model_error": model_error
    })


# ------------------------------------------------------------
# RECOMMENDATION API
# ------------------------------------------------------------

@app.route("/api/recommend", methods=["POST"])
def recommend():

    try:

        data = request.get_json(silent=True)

        if data is None:
            data = {}

        print()
        print("=" * 70)
        print("NEW RECOMMENDATION REQUEST")
        print("=" * 70)
        print("Received profile:")
        print(json.dumps(data, indent=2, default=str))

        # ----------------------------------------------------
        # BASIC INPUT VALIDATION
        # ----------------------------------------------------

        age = to_int(
            first_value(data, ["age", "user_age"]),
            None
        )

        height = to_float(
            first_value(data, ["height_cm", "height", "heightCm"]),
            None
        )

        weight = to_float(
            first_value(data, ["weight_kg", "weight", "weightKg"]),
            None
        )

        if age is None:
            return jsonify({
                "success": False,
                "error": "Age is required."
            }), 400

        if height is None:
            return jsonify({
                "success": False,
                "error": "Height is required."
            }), 400

        if weight is None:
            return jsonify({
                "success": False,
                "error": "Weight is required."
            }), 400

        # ----------------------------------------------------
        # USER PROFILE
        # ----------------------------------------------------

        gender = normalize_gender(
            first_value(
                data,
                ["gender", "sex"],
                "Not specified"
            )
        )

        para = normalize_para(
            first_value(
                data,
                [
                    "para_athlete",
                    "paraAthlete",
                    "athlete_type",
                    "disability",
                    "disability_status"
                ],
                False
            )
        )

        # ----------------------------------------------------
        # EXISTING ML MODEL
        # ----------------------------------------------------

        ml_prediction = get_ml_prediction(data)

        print("Existing ML prediction:", ml_prediction)

        # ----------------------------------------------------
        # RECOMMENDATION LAYER
        # ----------------------------------------------------

        result = recommendation_layer(
            data,
            ml_prediction
        )

        print("Final recommendation:")
        print(result["recommended_sport"])

        print("Alternatives:")
        print(result["alternatives"])

        print("=" * 70)

        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        return jsonify({
            "success": True,

            "recommended_sport": result["recommended_sport"],

            # Multiple names included so your current JS can
            # easily use whichever one it expects.
            "sport": result["recommended_sport"],
            "recommendation": result["recommended_sport"],

            "alternatives": result["alternatives"],

            "reason": result["reason"],

            "recommendation_type": result["type"],

            "ml_prediction": ml_prediction,

            "profile": {
                "age": age,
                "height_cm": height,
                "weight_kg": weight,
                "gender": gender,
                "para_athlete": para
            },

            "bmi": result["bmi"]
        })

    except Exception as e:

        print("=" * 70)
        print("RECOMMENDATION ERROR")
        print("=" * 70)
        traceback.print_exc()

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ------------------------------------------------------------
# USERS FILE HELPERS
# ------------------------------------------------------------

def load_users():

    if not os.path.exists(USERS_PATH):
        return []

    try:
        with open(
            USERS_PATH,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

            if isinstance(data, list):
                return data

            return []

    except Exception:
        return []


def save_users(users):

    with open(
        USERS_PATH,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            users,
            f,
            indent=2
        )


# ------------------------------------------------------------
# REGISTER
# ------------------------------------------------------------

@app.route("/api/register", methods=["POST"])
def register():

    try:

        data = request.get_json(silent=True) or {}

        name = str(
            first_value(
                data,
                ["name", "full_name", "fullName"],
                ""
            )
        ).strip()

        email = str(
            first_value(
                data,
                ["email"],
                ""
            )
        ).strip().lower()

        password = str(
            first_value(
                data,
                ["password"],
                ""
            )
        )

        if not name:
            return jsonify({
                "success": False,
                "error": "Full name is required."
            }), 400

        if not email:
            return jsonify({
                "success": False,
                "error": "Email is required."
            }), 400

        if len(password) < 6:
            return jsonify({
                "success": False,
                "error": "Password must contain at least 6 characters."
            }), 400

        users = load_users()

        for user in users:

            if str(user.get("email", "")).lower() == email:

                return jsonify({
                    "success": False,
                    "error": "An account with this email already exists."
                }), 409

        users.append({
            "name": name,
            "email": email,
            "password": password
        })

        save_users(users)

        print("New user registered:", email)

        return jsonify({
            "success": True,
            "message": "Account created successfully."
        })

    except Exception as e:

        print("REGISTER ERROR:")
        traceback.print_exc()

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ------------------------------------------------------------
# LOGIN
# ------------------------------------------------------------

@app.route("/api/login", methods=["POST"])
def login():

    try:

        data = request.get_json(silent=True) or {}

        email = str(
            first_value(
                data,
                ["email"],
                ""
            )
        ).strip().lower()

        password = str(
            first_value(
                data,
                ["password"],
                ""
            )
        )

        if not email or not password:

            return jsonify({
                "success": False,
                "error": "Email and password are required."
            }), 400

        users = load_users()

        for user in users:

            if (
                str(user.get("email", "")).lower() == email
                and str(user.get("password", "")) == password
            ):

                return jsonify({
                    "success": True,
                    "message": "Login successful.",
                    "user": {
                        "name": user.get("name", ""),
                        "email": user.get("email", "")
                    }
                })

        return jsonify({
            "success": False,
            "error": "Invalid email or password."
        }), 401

    except Exception as e:

        print("LOGIN ERROR:")
        traceback.print_exc()

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ------------------------------------------------------------
# OPTIONAL PROFILE API
# ------------------------------------------------------------

@app.route("/api/profile", methods=["POST"])
def save_profile():

    try:

        data = request.get_json(silent=True) or {}

        return jsonify({
            "success": True,
            "message": "Profile received.",
            "profile": data
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ------------------------------------------------------------
# SERVER START
# ------------------------------------------------------------

if __name__ == "__main__":

    print()
    print("=" * 70)
    print("STARTING SPORTFIT PATHFINDER SERVER")
    print("=" * 70)

    print("Frontend:")
    print(FRONTEND_DIR)

    print()

    print("Model:")
    print(MODEL_PATH)

    print()

    print("Model loaded:", model is not None)

    if model_error:
        print("Model error:", model_error)

    print()
    print("Open in browser:")
    print("http://127.0.0.1:5000")

    print("=" * 70)

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )