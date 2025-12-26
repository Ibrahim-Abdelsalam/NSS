import pandas as pd

# Test how app.py reads the nurses CSV
print("="*60)
print("Testing how app.py reads analysis_nurses.csv")
print("="*60)

# App uses header=None (line 324 in app.py)
nurses_df = pd.read_csv('data/analysis_nurses.csv', header=None)
nurses_list = nurses_df.iloc[:, 0].astype(str).tolist()

print(f"\nWith header=None (as app.py does):")
print(f"  Total rows: {len(nurses_df)}")
print(f"  nurses_list length: {len(nurses_list)}")
print(f"\nNurses list:")
for i, nurse in enumerate(nurses_list, 1):
    print(f"  {i}. {nurse}")

print("\n" + "="*60)
print("FINDING: The app reads the 'Nurse' header as a nurse!")
print("="*60)
print(f"\nThe app counts: {len(nurses_list)} nurses")
print("  - 1st entry: 'Nurse' (the header)")
print("  - 2nd-9th entries: Nurse_1 through Nurse_8")
print("\nThis explains why you see 9 nurses in the app!")
print("="*60)
