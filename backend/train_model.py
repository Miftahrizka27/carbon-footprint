import pandas as pd
from sklearn.tree import DecisionTreeRegressor, export_text
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import pickle

df = pd.read_csv("dataset_carbon.csv")
print(df.head())
print(f"\nJumlah data: {len(df)} baris")
print(f"Statistik Potensi Hemat (kg):\n{df['potensi_hemat_kg'].describe()}\n")

X = df[["listrik_kwh", "air_liter", "transportasi_km", "sampah_kg"]]
y = df["potensi_hemat_kg"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
print(f"Data training: {len(X_train)} baris")
print(f"Data testing : {len(X_test)} baris\n")


print("Training model Decision Tree Regressor...")
model = DecisionTreeRegressor(
    max_depth=5,        
    random_state=42
)
model.fit(X_train, y_train)


y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"R^2 (Kecocokan model): {r2 * 100:.1f}%")
print(f"MAE (Rata-rata prediksi meleset sebesar): {mae:.2f} kg\n")

print("Struktur Decision Tree:")
tree_rules = export_text(
    model,
    feature_names=["listrik_kwh", "air_liter", "transportasi_km", "sampah_kg"]
)
print(tree_rules)

with open("carbon_model.pkl", "wb") as f:
    pickle.dump(model, f)

print("Model berhasil disimpan sebagai carbon_model.pkl")
print("Sekarang calculator.py bisa load model ini!")
