# This file is for 


import pandas as pd

df = pd.read_csv("raw_metrics.csv")

df["bugfix_ratio"] = df["bugfix_commits"] / df["num_commits"]
bug_rate = df["bugfix_ratio"].median()

print(df[["filepath", "bugfix_commits", "num_commits", "bugfix_ratio"]].head(10))
threshold = df["bugfix_ratio"].quantile(0.75)
df["is_risky"] = (df["bugfix_ratio"] > threshold).astype(int)

print(f"Threshold (75th percentile): {threshold}")
print(df["is_risky"].value_counts())