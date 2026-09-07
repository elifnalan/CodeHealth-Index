# This script is used to mine the repository and extract the file statistics such as churn, 
# number of commits, and number of authors for each file in the repository. 
# Additionally, it calculates the complexity of each file using the radon library and stores the data in a CSV file.
# For risk data, regex is used to identify bugfix commits based on commit messages. 
# The script also handles file renames/moves by merging the old history into the new path.


from pydriller import Repository
from collections import defaultdict
import pandas as pd
from radon.complexity import cc_visit
import re

# The keywords used to identify bugfix commits in the commit messages.
BUGFIX_PATTERN = re.compile(
    r"\b(fix(e[sd])?|bug|defect|error|crash|fail(s|ed|ure)?|issue\s*#?\d+|closes?\s*#\d+|resolves?\s*#\d+)\b",
    re.IGNORECASE
)

# Storing the file statistics in a dictionary with default values
file_stats = defaultdict(lambda: {

    #churn: number of lines added + number of lines deleted
    "churn": 0,

    "num_commits": 0,

    # number of commits that are identified as bugfix commits based on the commit message
    "bugfix_commits": 0,

    # will be using the modifcation date to for training 
    "last_modified": None,

    "authors": set(),
})


# Repo used for this project:
repo = Repository("../requests")


# A function to calculate the complexity of a file using radon library
def get_file_complexity(filepath):
    """Sum all function/class complexity scores in a file into one total."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            source = f.read()
        blocks = cc_visit(source)
        return sum(block.complexity for block in blocks)
    except Exception:
        return None  # file might not exist, might not be valid Python, etc.

    

# Traversing through the commits in the repository
for commit in repo.traverse_commits():

    # For every modified file in the commmit, storing the path, churn 
    for mod in commit.modified_files:

       
        # file renamed/moved, so merge its old history into the new path
        if mod.change_type.name == "RENAME":
            old_path = mod.old_path
            new_path = mod.new_path

            file_stats[new_path]["churn"] += file_stats[old_path]["churn"]
            file_stats[new_path]["num_commits"] += file_stats[old_path]["num_commits"]
            file_stats[new_path]["authors"].update(file_stats[old_path]["authors"])
            file_stats[new_path]["bugfix_commits"] += file_stats[old_path]["bugfix_commits"]
            file_stats[new_path]["last_modified"] = file_stats[old_path]["last_modified"]

            file_stats[old_path] = {"churn": 0, "num_commits": 0, "authors": set(), "bugfix_commits": 0, "last_modified": None}  # Reset old path stats
            
            #print(f"RENAME detected: {old_path} -> {new_path}")
        if not mod.new_path:
            continue

        
        file_stats[mod.new_path]["churn"] += mod.added_lines + mod.deleted_lines
        file_stats[mod.new_path]["num_commits"] += 1
        # becasue the username can change, storing the email of the author instead of the username
        file_stats[mod.new_path]["authors"].add(commit.author.email)
        file_stats[mod.new_path]["last_modified"] = commit.author_date

        # identifying if the commit is a bugfix based on the commit message using regex
        is_bugfix = bool(BUGFIX_PATTERN.search(commit.msg))
        
        # if the commit is identified as a bugfix, increment the bugfix commit count for the file
        # since the commit message doesnt change for modification, the increase in bugfix commit 
        # count is done before the churn and num_commits are updated for the file
        if(is_bugfix):
            file_stats[mod.new_path]["bugfix_commits"] += 1
        
        

   
for filepath in file_stats:
    if "models.py" in filepath and file_stats[filepath]["num_commits"] > 0:
        print(filepath, file_stats[filepath])

print(f"\nTotal files tracked: {len(file_stats)}")


#to insert the data into a database, we need to convert the data into a list of dictionaries
rows = []
for filepath, stats in file_stats.items():
    if stats["num_commits"] > 0:

        rows.append({
            "filepath" : filepath,
            "churn" : stats["churn"],
            "num_commits" : stats["num_commits"],
            "num_authors" : len(stats["authors"]),
            "bugfix_commits" : stats["bugfix_commits"],
            "last_modified" : stats["last_modified"],

            #calculating the complexity once, for each file that is inserted into the databse 
            "complexity" : get_file_complexity(f"../requests/{filepath}")
        })

        # print(f"File: {filepath}, Churn: {stats['churn']}, Commits: {stats['num_commits']}, Authors: {len(stats['authors'])}")


#inserting the data into a csv file
df = pd.DataFrame(rows)
df.to_csv("raw_metrics.csv", index=False)