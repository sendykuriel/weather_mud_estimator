# Weather Forecast Dashboard 🚜🌦️

An interactive Streamlit app to visualize weather forecasts and estimate dirt road conditions.

## 🧠 Features

- Retrieves weather data from [Open-Meteo](https://open-meteo.com/).
- Visualizations include:
  - Hourly forecast: temperature, humidity, rain.
  - Daily summary with multi-axis plots.
  - Calendar view showing whether the road was dry or muddy.
- Displays a message indicating whether the dirt road is currently passable.
- Estimates the **next day** the road will likely be dry again.
- Supports predefined locations and manual coordinate input.

## 📸 Screenshots

| Road Status | Road Calendar | Hourly Weather |
|-------------|----------------|----------------|
| ✅ or 🚫     | 🗓️ Green/red per day | 📈 With shading and rain markers |

## 🚀 How to Run Locally

### 1. Clone the repository


### 2. Set up the environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Launch the app

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

## 📁 Project Structure

```
weather-app/
│
├── app.py                  # Main Streamlit application
├── requirements.txt
├── README.md
└── src/
    ├── weather_data.py     # Weather API logic
    ├── plotting.py         # Custom Matplotlib/Plotly charts
    └── utils.py            # Road condition logic
```

## ⚙️ Technologies Used

- Python 3.11+
- Streamlit
- Pandas
- Matplotlib
- Plotly
- Open-Meteo API

## 🙌 Author

Developed by [Uriel Sendyk](https://github.com/sendykuriel)  
Built with love for dirt roads and automation 🛤️✨
