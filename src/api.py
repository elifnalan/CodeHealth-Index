from fastapi import FastAPI
import pandas as pd
import os
import joblib

app = FastAPI()

# Retrieve the trained model and scaler from the saved files
model = joblib.load("risk_model.pkl")
scaler = joblib.load("scaler.pkl")

@app.get("/")
def read_root():
    return {"status": "running"}


@app.get("/risk-scores")
def get_risk_scores():
    df = pd.read_csv("raw_metrics.csv")
    df = df[df["filepath"].str.endswith(".py")].copy()
    df["exists"] = df["filepath"].apply(lambda fp: os.path.exists(f"../requests/{fp}"))
    df = df[df["exists"]].copy()

    features = ["churn", "num_commits", "num_authors"]
    X = df[features]
    X_scaled = scaler.transform(X)

    df["risk_score"] = model.predict_proba(X_scaled)[:, 1]

    return df[["filepath", "risk_score"]].to_dict(orient="records")