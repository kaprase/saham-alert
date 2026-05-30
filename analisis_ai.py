"""
analisis_ai.py
Modul AI sederhana menggunakan Random Forest untuk prediksi arah harga
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings("ignore")


def buat_fitur(df: pd.DataFrame) -> pd.DataFrame | None:
    """
    Buat fitur untuk model ML dari data harga.
    """
    try:
        import pandas_ta as ta
        d = df.copy()
        close = d["Close"]

        d["RSI"] = ta.rsi(close, length=14)
        d["MA20"] = ta.sma(close, length=20)
        d["MA50"] = ta.sma(close, length=50)
        macd = ta.macd(close)
        if macd is not None:
            d["MACD_Hist"] = macd.get("MACDh_12_26_9", np.nan)

        # Return
        d["Return_1"] = close.pct_change(1)
        d["Return_5"] = close.pct_change(5)
        d["Return_10"] = close.pct_change(10)

        # Volatilitas
        d["Volatilitas"] = close.pct_change().rolling(10).std()

        # Posisi harga vs MA
        d["Rasio_MA20"] = close / d["MA20"]
        d["Rasio_MA50"] = close / d["MA50"]

        # Volume
        d["Vol_Ratio"] = d["Volume"] / d["Volume"].rolling(20).mean()

        # Target: apakah harga naik dalam 5 hari ke depan?
        d["Target"] = (close.shift(-5) > close).astype(int)

        kolom_fitur = [
            "RSI", "MACD_Hist", "Return_1", "Return_5", "Return_10",
            "Volatilitas", "Rasio_MA20", "Rasio_MA50", "Vol_Ratio"
        ]
        d = d[kolom_fitur + ["Target"]].dropna()
        return d
    except Exception as e:
        print(f"  [!] Gagal buat fitur AI: {e}")
        return None


def prediksi_ai(df: pd.DataFrame) -> dict:
    """
    Latih Random Forest dan prediksi probabilitas naik.
    """
    data_fitur = buat_fitur(df)
    if data_fitur is None or len(data_fitur) < 60:
        return {
            "skor": 50,
            "probabilitas_naik": 0.5,
            "label": "Data tidak cukup untuk AI ⚪",
        }

    try:
        kolom_fitur = [c for c in data_fitur.columns if c != "Target"]
        X = data_fitur[kolom_fitur].values
        y = data_fitur["Target"].values

        # Pisah data: 80% latih, 20% prediksi
        pisah = int(len(X) * 0.8)
        X_latih, X_test = X[:pisah], X[pisah:]
        y_latih = y[:pisah]

        # Normalisasi
        scaler = StandardScaler()
        X_latih = scaler.fit_transform(X_latih)
        X_test = scaler.transform(X_test)

        # Latih model
        model = RandomForestClassifier(
            n_estimators=100, max_depth=5, random_state=42, n_jobs=-1
        )
        model.fit(X_latih, y_latih)

        # Prediksi data terbaru
        prob_naik = model.predict_proba(X_test[-1].reshape(1, -1))[0][1]

        skor = int(prob_naik * 100)
        if prob_naik > 0.70:
            label = f"AI: Probabilitas naik {prob_naik*100:.0f}% — Bullish kuat 🟢"
        elif prob_naik > 0.55:
            label = f"AI: Probabilitas naik {prob_naik*100:.0f}% — Cenderung naik 🟡"
        elif prob_naik < 0.30:
            label = f"AI: Probabilitas naik {prob_naik*100:.0f}% — Bearish kuat 🔴"
        elif prob_naik < 0.45:
            label = f"AI: Probabilitas naik {prob_naik*100:.0f}% — Cenderung turun 🟡"
        else:
            label = f"AI: Probabilitas naik {prob_naik*100:.0f}% — Netral ⚪"

        return {
            "skor": skor,
            "probabilitas_naik": float(prob_naik),
            "label": label,
        }
    except Exception as e:
        print(f"  [!] Error model AI: {e}")
        return {"skor": 50, "probabilitas_naik": 0.5, "label": "AI error ⚪"}
