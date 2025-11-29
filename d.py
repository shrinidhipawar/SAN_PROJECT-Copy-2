import pandas as pd

df = pd.read_csv("sim_results.csv")
print("Columns in CSV:")
print(df.columns)

print("\nFirst 5 rows:")
print(df.head())

# Check if time_s exists
if "time_s" in df.columns:
    print("\nYES: time_s column exists")
else:
    print("\nNO: time_s column missing")

# Check if timestamp exists
if "timestamp" in df.columns:
    print("YES: timestamp column exists")
else:
    print("NO: timestamp column missing")
