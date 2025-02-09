import streamlit as st
import firebase_admin
from firebase_admin import auth, firestore, credentials
import random
import json

# Convert Streamlit secrets AttrDict to a dictionary
firebase_secrets = dict(st.secrets["firebase"])

# Initialize Firebase with the correct format
cred = credentials.Certificate(firebase_secrets)
firebase_admin.initialize_app(cred)

# Connect to Firestore
db = firestore.client()

def authenticate_user():
    st.title("Login with Google")
    user = st.experimental_user_auth("google")
    if user:
        st.session_state["user"] = user
        save_user_to_firebase(user)
        st.experimental_rerun()

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
