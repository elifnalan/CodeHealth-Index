# This file is for training the model using the mined data from the repository. 
# It reads the CSV file containing the file statistics and calculates the bugfix ratio for each file. 
# The bugfix ratio is defined as the number of bugfix commits divided by the total number of commits for a file. 
# The script then determines a threshold for riskiness based on the 75th percentile of the bugfix ratio and labels 
# files as risky or not based on this threshold.

# Due to some files having zero bugfix commits, teh threshold is calculated using the 75th percentile of the bugfix 
# ratio, which helps to identify files that are more likely to be risky based on their commit history.


import pandas as pd

df = pd.read_csv("raw_metrics.csv")

df["bugfix_ratio"] = df["bugfix_commits"] / df["num_commits"]
bug_rate = df["bugfix_ratio"].median()

threshold = df["bugfix_ratio"].quantile(0.75)
df["is_risky"] = (df["bugfix_ratio"] > threshold).astype(int)

#sorting the dataframe by modifcation

#first, converting the last_modified column to datetime format
df["last_modified"] = pd.to_datetime(df["last_modified"], utc=True)

#then sorting the dataframe by last_modified in ascending order
#as a result, older records will be at the bottom and newer records will be at the top of the dataframe
df_sorted = df.sort_values(by="last_modified", ascending=True)

#creating the split for training and testing data, 80/20 split is used here
total_rows = len(df_sorted)
split_index = int(total_rows * 0.8) #split index for 80% of the data

#slicing the dataframe into training and testing dataframes based on the split index
train_df = df_sorted.iloc[:split_index]
test_df = df_sorted.iloc[split_index:]

print("Train rows:", len(train_df))
print("Test rows:", len(test_df))
print("Train date range:", train_df["last_modified"].min(), "to", train_df["last_modified"].max())
print("Test date range:", test_df["last_modified"].min(), "to", test_df["last_modified"].max())