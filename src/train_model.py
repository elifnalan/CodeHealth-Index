# This file is for training the model using the mined data from the repository. 
# It reads the CSV file containing the file statistics and calculates the bugfix ratio for each file. 
# The bugfix ratio is defined as the number of bugfix commits divided by the total number of commits for a file. 
# The script then determines a threshold for riskiness based on the 75th percentile of the bugfix ratio and labels 
# files as risky or not based on this threshold.

# Due to some files having zero bugfix commits, teh threshold is calculated using the 75th percentile of the bugfix 
# ratio, which helps to identify files that are more likely to be risky based on their commit history.


import pandas as pd
import os
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler


# onyl keeping the files that are Python files
# filtering non-Python files and files
df = pd.read_csv("raw_metrics.csv")
df = df[df["filepath"].str.endswith(".py")].copy()

df["bugfix_ratio"] = df["bugfix_commits"] / df["num_commits"]
bug_rate = df["bugfix_ratio"].median()

threshold = df["bugfix_ratio"].quantile(0.75)
df["is_risky"] = (df["bugfix_ratio"] > threshold).astype(int)

#sorting the dataframe by modifcation date

#first, converting the last_modified column to datetime format
df["last_modified"] = pd.to_datetime(df["last_modified"], utc=True)

#then sorting the dataframe by last_modified in ascending order
#as a result, older records will be at the top and newer records will be at the bottom of the dataframe
df_sorted = df.sort_values(by="last_modified", ascending=True)

#creating the split for training and testing data, 80/20 split is used here
total_rows = len(df_sorted)
split_index = int(total_rows * 0.8) #split index for 80% of the data

#slicing the dataframe into training and testing dataframes based on the split index
train_df = df_sorted.iloc[:split_index]
test_df = df_sorted.iloc[split_index:]

# features used for training the model, these features are selected based on their relevance to the riskiness of a file
# label is the riskiness of a file, which is determined based on the bugfix ratio and the threshold calculated earlier
features = ["churn", "num_commits", "num_authors"]
#, "complexity"] complexity is eliminated from features as it shrinks the dataset significantly
X_train = train_df[features]
y_train = train_df["is_risky"]
X_test = test_df[features]
y_test = test_df["is_risky"]

#Standartizing the data to have each of the features to make meaningful contribution 
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)


#the model we will be using to train is a logistic regression model, which is suitable for binary classification tasks like this one
model = LogisticRegression()
model.fit(X_train_scaled, y_train)

#testing the model on the test data and calculating the AUC score to evaluate its performance
y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
auc = roc_auc_score(y_test, y_pred_proba)

print(f"AUC: {auc}")

for feature, coef in zip(features, model.coef_[0]):
    print(feature, coef)
