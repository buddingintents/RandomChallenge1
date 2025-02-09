import streamlit as st
import firebase_admin
from firebase_admin import auth, firestore, credentials
import random
import json
import pyrebase

# Firebase configuration (replace with your values)
firebase_config = {
    "apiKey": st.secrets["firebase"].get("apiKey", ""),
    "authDomain": st.secrets["firebase"].get("authDomain", ""),
    "projectId": st.secrets["firebase"].get("projectId", ""),
    "storageBucket": st.secrets["firebase"].get("storageBucket", ""),
    "messagingSenderId": st.secrets["firebase"].get("messagingSenderId", ""),
    "appId": st.secrets["firebase"].get("appId", ""),
    "measurementId": st.secrets["firebase"].get("measurementId", ""),
    "databaseURL": st.secrets["firebase"].get("databaseURL", "")
}

if not firebase_config["databaseURL"]:
    st.warning("Firebase databaseURL is missing in secrets. If using Firestore, remove it from pyrebase config.")
    firebase_config.pop("databaseURL", None)

firebase = pyrebase.initialize_app(firebase_config)
auth_firebase = firebase.auth()

# Streamlit UI
st.title("Login with Google")

def authenticate_user():
    try:
        # Use Firebase Authentication to sign in with Google
        provider = auth_firebase.GoogleAuthProvider()
        result = auth_firebase.sign_in_with_popup(provider)
        user = result.user
        st.session_state["user"] = {
            "name": user.display_name,
            "email": user.email,
            "image": user.photo_url
        }
        save_user_to_firebase(st.session_state["user"])
        st.experimental_rerun()
    except Exception as e:
        st.error(f"Authentication failed: {e}")

def save_user_to_firebase(user):
    users_ref = db.collection("users").document(user["email"])
    user_data = users_ref.get()
    if not user_data.exists:
        users_ref.set({
            "name": user["name"],
            "email": user["email"],
            "image": user["image"],
            "score": 0,
            "level": 1,
            "consecutive_bonus": 0
        })

if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(json.dumps(dict(st.secrets["firebase"]))))
    firebase_admin.initialize_app(cred)

db = firestore.client()

def generate_challenge(level):
    challenges = ["Sudoku", "Kakuro", "Reasoning", "Math Puzzle"]
    return random.choice(challenges)

def display_leaderboard():
    st.title("Leaderboard")
    users_ref = db.collection("users").order_by("score", direction=firestore.Query.DESCENDING).limit(100)
    users = users_ref.stream()
    for user in users:
        data = user.to_dict()
        st.image(data["image"], width=50)
        st.write(f"{data['name']} - Score: {data['score']}")

def game():
    user = st.session_state.get("user")
    if not user:
        authenticate_user()
        return
    
    users_ref = db.collection("users").document(user["email"])
    user_data = users_ref.get().to_dict()
    level = user_data["level"]
    consecutive_bonus = user_data["consecutive_bonus"]
    
    st.title(f"Level {level}")
    challenge = generate_challenge(level)
    st.write(f"Challenge: {challenge}")
    
    if st.button("Submit Correct Answer"):
        score = level + consecutive_bonus
        users_ref.update({
            "score": firestore.Increment(score),
            "level": firestore.Increment(1),
            "consecutive_bonus": firestore.Increment(1)
        })
        st.experimental_rerun()
    
    if st.button("Retry"):
        users_ref.update({"consecutive_bonus": 0})
        st.experimental_rerun()

def main():
    st.sidebar.title("Menu")
    menu = st.sidebar.radio("Navigate", ["Game", "Leaderboard"])
    if menu == "Game":
        game()
    elif menu == "Leaderboard":
        display_leaderboard()

if __name__ == "__main__":
    main()
