from django.shortcuts import render

from climatechanges import models

# Create your views here.
def index(request):
    return render(request, "climatechanges/index.html")


def about(request):
    return render(request, "climatechanges/about.html")

def contact(request):
    return render(request, "climatechanges/contact.html")
#________login_________#

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render


def login_view(request):
  
  if request.method == 'POST':
    username = request.POST.get('username')
    password = request.POST.get('password')

    # Authenticate user using Django's built-in User model/backend
    user = authenticate(request, username=username, password=password)

    if user is not None:
      login(request,user)
      #auth_login(request, user)
      messages.success(request, 'Successfully logged in!')
      # Redirect to your home page or dashboard URL name
      return redirect('index')
    else:
      # Pass form data back to retain the username input on error
      context = {
          'form_errors': ['Invalid username or password.'],
          'form_data': {'username': username},
      }
      return render(request, 'climatechanges/login.html', context)

  return render(request, 'climatechanges/login.html')

#________loin end_________#


#----- SignUp-----#

from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from .models import Customer


def signup(request):

    if request.method == 'POST':

        username = request.POST.get('username')
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        password = request.POST.get('pwd')
        password_confirm = request.POST.get('pwd_2')
        address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        country = request.POST.get('country')
        zip_code = request.POST.get('zip_code')

        # 1. Check password confirmation
        if password != password_confirm:
            return render(request, 'climatechanges/signup.html', {
                'error': 'Passwords do not match'
            })

        # 2. Check username in Django User table
        if User.objects.filter(username=username).exists():
            return render(request, 'climatechanges/signup.html', {
                'error': 'Username already taken. Please choose another.'
            })

        # 3. Check username in Customer table
        if Customer.objects.filter(username=username).exists():
            return render(request, 'climatechanges/signup.html', {
                'error': 'Username already taken.'
            })

        # 4. Create Django user
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=full_name
        )

        # 5. Create Customer profile
        Customer.objects.create(
            username=username,
            full_name=full_name,
            email=email,
            password=make_password(password),
            address=address,
            city=city,
            state=state,
            country=country,
            zip_code=zip_code,
            user=user
        )

        # 6. Success message
        messages.success(
            request,
            'Account created successfully! Please log in.'
        )

        # 7. Redirect to login page
        return redirect('login')

    return render(request, 'climatechanges/signup.html')


#__________signup end__________#

import os
import math
import logging

import numpy as np
import pandas as pd
import plotly.offline as opy
import plotly.graph_objs as go

from pathlib import Path

from sklearn.ensemble import IsolationForest
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score, mean_squared_error

from django.conf import settings
from django.shortcuts import render


logger = logging.getLogger(__name__)


def climateTempPrediction(request):

    context = {
        'country_list': [],
        'selected_country': '',
        'trend_chart_div': None,
        'impact_chart_div': None,
        'corr_matrix_html': None,
        'r2_score': 'N/A',
        'rmse': 'N/A',
        'total_countries': 0,
        'anomaly_count': 0,
        'forecast_summary': [],
        'recent_10yr_avg': 'N/A',
        'error_message': None,
    }

    try:

        # =====================================================
        # 1. LOAD EXCEL DATASET
        # =====================================================

        excel_file = Path(settings.BASE_DIR) / 'media' / 'Temperature.xls'

        if not excel_file.exists():
            excel_file = Path(settings.BASE_DIR) / 'Temperature.xls'

        if not excel_file.exists():
            raise FileNotFoundError(
                "Temperature.xls was not found in media/ or project root."
            )

        data = pd.read_excel(excel_file, engine='xlrd')

        if data.empty:
            raise ValueError("The Excel dataset is empty.")

        # =====================================================
        # 2. DATA CLEANING
        # =====================================================

        if 'Country' not in data.columns:
            raise ValueError("Missing required column: Country")

        data['Country'] = data['Country'].astype(str).str.strip()

        data = data[
            (data['Country'] != '') &
            (data['Country'].str.lower() != 'nan')
        ].copy()

        # Extract historical year columns

        year_cols = sorted(
            [
                col for col in data.columns
                if str(col).strip().isdigit()
                and 1961 <= int(str(col).strip()) <= 2023
            ],
            key=lambda x: int(str(x).strip())
        )

        if len(year_cols) < 2:
            raise ValueError(
                "At least two historical year columns between 1961 and 2023 are required."
            )

        # Convert year columns to numeric

        for col in year_cols:
            data[col] = pd.to_numeric(
                data[col],
                errors='coerce'
            )

        # Remove records with too many missing values

        minimum_values = max(2, math.ceil(len(year_cols) * 0.8))

        data = data.dropna(
            subset=year_cols,
            thresh=minimum_values
        ).copy()

        if data.empty:
            raise ValueError("No valid climate records found.")

        # Fill small gaps within each country's time series

        data[year_cols] = data[year_cols].apply(
            lambda row: row.interpolate(
                method='linear',
                limit_direction='both'
            ),
            axis=1
        )

        data = data.dropna(subset=year_cols).copy()

        if data.empty:
            raise ValueError("Unable to clean the historical temperature records.")

        # =====================================================
        # 3. CLIMATE SUMMARY METRICS
        # =====================================================

        year_numbers = [int(str(col).strip()) for col in year_cols]

        data['Avg_Temp_Change'] = data[year_cols].mean(axis=1)

        latest_10_years = year_cols[-10:]

        data['Recent_10Yr_Avg'] = data[latest_10_years].mean(axis=1)

        data['Temp_Volatility'] = data[year_cols].std(axis=1)

        # =====================================================
        # 4. COUNTRY FILTER
        # =====================================================

        country_list = sorted(data['Country'].unique().tolist())

        selected_country = request.GET.get(
            'country',
            country_list[0]
        )

        if selected_country not in country_list:
            selected_country = country_list[0]

        country_data = data[
            data['Country'] == selected_country
        ].iloc[0]

        context['country_list'] = country_list
        context['selected_country'] = selected_country

        # =====================================================
        # 5. ANOMALY DETECTION
        # =====================================================

        if len(data) >= 10:

            iso_forest = IsolationForest(
                n_estimators=100,
                contamination=0.05,
                random_state=42
            )

            data['Anomaly_Score'] = iso_forest.fit_predict(
                data[year_cols]
            )

        else:
            data['Anomaly_Score'] = 1

        anomalous_countries = data[
            data['Anomaly_Score'] == -1
        ]

        anomaly_count = len(anomalous_countries)

        # =====================================================
        # 6. RIDGE REGRESSION MODEL
        # =====================================================

        years = np.array(year_numbers).reshape(-1, 1)

        temp_values = country_data[year_cols].values.astype(float)

        future_years = np.arange(
            2024,
            2036
        ).reshape(-1, 1)

        # Chronological train/test evaluation

        split_index = int(len(years) * 0.8)

        if split_index >= 2 and len(years) - split_index >= 2:

            evaluation_model = Ridge(alpha=1.0)

            evaluation_model.fit(
                years[:split_index],
                temp_values[:split_index]
            )

            test_predictions = evaluation_model.predict(
                years[split_index:]
            )

            r2 = r2_score(
                temp_values[split_index:],
                test_predictions
            )

            rmse = np.sqrt(
                mean_squared_error(
                    temp_values[split_index:],
                    test_predictions
                )
            )

            context['r2_score'] = round(float(r2), 3)
            context['rmse'] = round(float(rmse), 3)

        # Train final model using all historical observations

        trend_model = Ridge(alpha=1.0)

        trend_model.fit(
            years,
            temp_values
        )

        # Historical fitted values

        hist_pred = trend_model.predict(years)

        # Future temperature predictions

        future_pred = trend_model.predict(future_years)

        # =====================================================
        # 7. FORECAST SUMMARY
        # =====================================================

        forecast_summary = []

        for year, prediction in zip(
            future_years.flatten(),
            future_pred
        ):

            forecast_summary.append({
                'year': int(year),
                'predicted_anomaly': round(
                    float(prediction), 3
                )
            })

        context['forecast_summary'] = forecast_summary

        # =====================================================
        # 8. DECADAL TEMPERATURE CORRELATION
        # =====================================================

        decade_columns = []

        for decade_start in range(1960, 2030, 10):

            decade_end = decade_start + 9

            cols = [
                col for col in year_cols
                if decade_start <= int(str(col).strip()) <= decade_end
            ]

            if cols:

                decade_name = f'{decade_start}s'

                data[decade_name] = data[cols].mean(axis=1)

                decade_columns.append(decade_name)

        correlation_columns = (
            decade_columns + ['Avg_Temp_Change']
        )

        corr_matrix = data[
            correlation_columns
        ].corr().round(2)

        corr_html = corr_matrix.to_html(
            classes='table table-bordered table-striped table-hover text-center mb-0',
            border=0,
            float_format=lambda x: f'{x:.2f}'
        )

        context['corr_matrix_html'] = corr_html

        # =====================================================
        # 9. PLOTLY CHART 1: TEMPERATURE TREND
        # =====================================================

        fig_trend = go.Figure()

        fig_trend.add_trace(
            go.Scatter(
                x=years.flatten(),
                y=temp_values,
                mode='markers+lines',
                name='Historical Temperature',
                line=dict(
                    color='#e74c3c',
                    width=2
                ),
                marker=dict(size=5)
            )
        )

        fig_trend.add_trace(
            go.Scatter(
                x=years.flatten(),
                y=hist_pred,
                mode='lines',
                name='Historical Model Fit',
                line=dict(
                    color='#27ae60',
                    dash='dot',
                    width=2
                )
            )
        )

        fig_trend.add_trace(
            go.Scatter(
                x=future_years.flatten(),
                y=future_pred,
                mode='lines+markers',
                name='2024–2035 Forecast',
                line=dict(
                    color='#2980b9',
                    dash='dash',
                    width=3
                ),
                marker=dict(size=7)
            )
        )

        fig_trend.update_layout(
            title=f'Temperature Trend & Prediction: {selected_country}',
            xaxis_title='Year',
            yaxis_title='Temperature (°C)',
            template='plotly_white',
            hovermode='x unified',
            legend=dict(
                orientation='h',
                y=-0.25
            ),
            margin=dict(
                l=40,
                r=30,
                t=60,
                b=80
            ),
            height=450
        )

        trend_chart_div = opy.plot(
            fig_trend,
            auto_open=False,
            output_type='div',
            include_plotlyjs=False
        )

        context['trend_chart_div'] = trend_chart_div

        # =====================================================
        # 10. PLOTLY CHART 2: TOP 10 WARMING REGIONS
        # =====================================================

        recent_decade_cols = [
            col for col in year_cols
            if 2020 <= int(str(col).strip()) <= 2023
        ]

        if recent_decade_cols:

            data['2020s_Avg'] = data[
                recent_decade_cols
            ].mean(axis=1)

        else:

            data['2020s_Avg'] = data[
                latest_10_years
            ].mean(axis=1)

        top_warming = (
            data.groupby('Country', as_index=False)['2020s_Avg']
            .mean()
            .sort_values(
                by='2020s_Avg',
                ascending=False
            )
            .head(10)
        )

        fig_impact = go.Figure()

        fig_impact.add_trace(
            go.Bar(
                x=top_warming['Country'],
                y=top_warming['2020s_Avg'],
                marker_color='#e67e22',
                name='Average Temperature'
            )
        )

        fig_impact.update_layout(
            title='Top 10 Highest Temperature Regions',
            xaxis_title='Country / Region',
            yaxis_title='Mean Temperature (°C)',
            template='plotly_white',
            height=400,
            margin=dict(
                l=40,
                r=20,
                t=60,
                b=100
            )
        )

        impact_chart_div = opy.plot(
            fig_impact,
            auto_open=False,
            output_type='div',
            include_plotlyjs=False
        )

        context['impact_chart_div'] = impact_chart_div

        # =====================================================
        # 11. FINAL DASHBOARD METRICS
        # =====================================================

        context.update({

            'total_countries': data['Country'].nunique(),

            'anomaly_count': anomaly_count,

            'recent_10yr_avg': round(
                float(country_data['Recent_10Yr_Avg']),
                3
            ),

        })

        # =====================================================
        # 12. RENDER TEMPLATE
        # =====================================================

        return render(
            request,
            'climatechanges/tempprediction.html',
            context
        )

    except Exception as e:

        logger.exception(
            "Climate temperature prediction error"
        )

        context['error_message'] = str(e)

        return render(
            request,
            'climatechanges/tempprediction.html',
            context
        )


# =============================================================
# CLIMATE TEMPERATURE PREDICTION END
# =============================================================


# =============================================================
# CLIMATE DISASTER PREDICTION START
# =============================================================

import logging
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objs as go
import plotly.offline as opy

from sklearn.ensemble import IsolationForest
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error, r2_score

from django.conf import settings
from django.shortcuts import render


logger = logging.getLogger(__name__)


def disasterPrediction(request):

    """
    Climate Disaster Frequency Prediction Dashboard.

    Dataset:
        Disaster.xls

    Expected columns:
        Country
        Indicator
        Year columns (1980, 1981, ... 2024)

    Features:
        1. Country selection
        2. Disaster type selection
        3. Historical disaster trend
        4. Future disaster prediction
        5. Model evaluation (R2 and RMSE)
        6. Anomaly detection
        7. Top 10 countries by disaster frequency
    """

    # ---------------------------------------------------------
    # INITIALIZE DASHBOARD CONTEXT
    # ---------------------------------------------------------

    context = {
        "country_list": [],
        "disaster_types": [],
        "selected_country": "",
        "selected_disaster": "TOTAL",

        "trend_chart_div": None,
        "impact_chart_div": None,

        "r2_score": "N/A",
        "rmse": "N/A",

        "total_countries": 0,
        "anomaly_count": 0,

        "forecast_summary": [],

        "recent_avg": "N/A",
        "latest_year": "N/A",
        "latest_total": "N/A",

        "error_message": None,
    }

    try:

        # -----------------------------------------------------
        # 1. FIND DISASTER EXCEL FILE
        # -----------------------------------------------------

        possible_paths = [

            # App media folder
            Path(__file__).resolve().parent / "media" / "Disaster.xls",

            # Project climatechanges/media folder
            Path(settings.BASE_DIR) / "climatechanges" / "media" / "Disaster.xls",

            # Django MEDIA_ROOT
            Path(settings.MEDIA_ROOT) / "Disaster.xls"
            if settings.MEDIA_ROOT else None,

            # Project media folder
            Path(settings.BASE_DIR) / "media" / "Disaster.xls",

            # Project root
            Path(settings.BASE_DIR) / "Disaster.xls",
        ]

        excel_file = next(
            (
                path.resolve()
                for path in possible_paths
                if path is not None and path.exists()
            ),
            None
        )

        if excel_file is None:

            raise FileNotFoundError(
                "Disaster.xls was not found. Checked locations: "
                + ", ".join(
                    str(path)
                    for path in possible_paths
                    if path is not None
                )
            )

        print("DISASTER DATASET FOUND:", excel_file)

        # -----------------------------------------------------
        # 2. LOAD EXCEL DATASET
        # -----------------------------------------------------

        data = pd.read_excel(
            excel_file,
            engine="xlrd"
        )

        if data.empty:
            raise ValueError("The disaster dataset is empty.")

        # -----------------------------------------------------
        # 3. VALIDATE REQUIRED COLUMNS
        # -----------------------------------------------------

        required_columns = {
            "Country",
            "Indicator"
        }

        missing = required_columns.difference(data.columns)

        if missing:

            raise ValueError(
                "Missing required dataset columns: "
                + ", ".join(sorted(missing))
            )

        data["Country"] = (
            data["Country"]
            .astype(str)
            .str.strip()
        )

        data["Indicator"] = (
            data["Indicator"]
            .astype(str)
            .str.strip()
        )

        data = data[
            data["Country"].ne("")
            & data["Country"].str.lower().ne("nan")
        ].copy()

        # -----------------------------------------------------
        # 4. DETECT YEAR COLUMNS
        # -----------------------------------------------------

        year_cols = sorted(
            [
                col
                for col in data.columns
                if str(col).strip().isdigit()
                and 1900 <= int(str(col).strip()) <= 2100
            ],
            key=lambda col: int(str(col).strip())
        )

        if len(year_cols) < 3:

            raise ValueError(
                "At least three yearly columns are required."
            )

        for col in year_cols:

            data[col] = pd.to_numeric(
                data[col],
                errors="coerce"
            )

        # -----------------------------------------------------
        # 5. FILTER DISASTER FREQUENCY DATA
        # -----------------------------------------------------

        prefix = (
            "Climate related disasters frequency, "
            "Number of Disasters: "
        )

        frequency_data = data[
            data["Indicator"].str.startswith(
                prefix,
                na=False
            )
        ].copy()

        if frequency_data.empty:

            raise ValueError(
                "No 'Number of Disasters' records were found "
                "in Disaster.xls. Check the Indicator column."
            )

        frequency_data["Disaster_Type"] = (
            frequency_data["Indicator"]
            .str.replace(prefix, "", regex=False)
            .str.strip()
        )

        disaster_types = sorted(
            frequency_data["Disaster_Type"]
            .dropna()
            .unique()
        )

        if not disaster_types:

            raise ValueError(
                "No disaster types were found in the dataset."
            )

        # -----------------------------------------------------
        # 6. DISASTER TYPE SELECTION
        # -----------------------------------------------------

        selected_disaster = request.GET.get(
            "disaster",
            "TOTAL"
        )

        if selected_disaster not in disaster_types:

            selected_disaster = (
                "TOTAL"
                if "TOTAL" in disaster_types
                else disaster_types[0]
            )

        selected_data = frequency_data[
            frequency_data["Disaster_Type"].eq(
                selected_disaster
            )
        ].copy()

        # -----------------------------------------------------
        # 7. HANDLE DUPLICATE COUNTRY RECORDS
        # -----------------------------------------------------

        selected_data = (
            selected_data
            .groupby("Country", as_index=False)[year_cols]
            .mean()
        )

        # -----------------------------------------------------
        # 8. HANDLE MISSING VALUES
        # -----------------------------------------------------

        selected_data[year_cols] = selected_data[
            year_cols
        ].apply(
            lambda row: row.interpolate(
                method="linear",
                limit_direction="both"
            ),
            axis=1
        )

        selected_data = selected_data.dropna(
            subset=year_cols,
            how="all"
        ).copy()

        if selected_data.empty:

            raise ValueError(
                "No usable records exist for this disaster type."
            )

        # -----------------------------------------------------
        # 9. COUNTRY SELECTION
        # -----------------------------------------------------

        country_list = sorted(
            selected_data["Country"].unique().tolist()
        )

        selected_country = request.GET.get(
            "country",
            country_list[0]
        )

        if selected_country not in country_list:

            selected_country = country_list[0]

        country_row = selected_data.loc[
            selected_data["Country"].eq(selected_country),
            year_cols
        ].iloc[0]

        # -----------------------------------------------------
        # 10. PREPARE HISTORICAL DATA
        # -----------------------------------------------------

        years = np.array(
            [
                int(str(col).strip())
                for col in year_cols
            ],
            dtype=int
        )

        values = country_row.to_numpy(
            dtype=float
        )

        valid = np.isfinite(values)

        years = years[valid]
        values = values[valid]

        if len(values) < 3:

            raise ValueError(
                "Not enough historical values to train "
                "the prediction model."
            )

        # -----------------------------------------------------
        # 11. TRAIN / TEST MODEL EVALUATION
        # -----------------------------------------------------

        split_index = int(len(years) * 0.8)

        if (
            split_index >= 2
            and len(years) - split_index >= 2
        ):

            evaluation_model = Ridge(
                alpha=1.0
            )

            evaluation_model.fit(
                years[:split_index].reshape(-1, 1),
                values[:split_index]
            )

            test_predictions = (
                evaluation_model.predict(
                    years[split_index:].reshape(-1, 1)
                )
            )

            context["r2_score"] = round(
                float(
                    r2_score(
                        values[split_index:],
                        test_predictions
                    )
                ),
                3
            )

            context["rmse"] = round(
                float(
                    np.sqrt(
                        mean_squared_error(
                            values[split_index:],
                            test_predictions
                        )
                    )
                ),
                3
            )

        # -----------------------------------------------------
        # 12. TRAIN FINAL PREDICTION MODEL
        # -----------------------------------------------------

        model = Ridge(
            alpha=1.0
        )

        model.fit(
            years.reshape(-1, 1),
            values
        )

        historical_fit = np.maximum(
            model.predict(
                years.reshape(-1, 1)
            ),
            0
        )

        # -----------------------------------------------------
        # 13. PREDICT NEXT 10 YEARS
        # -----------------------------------------------------

        future_years = np.arange(
            int(years.max()) + 1,
            int(years.max()) + 11
        )

        future_predictions = np.maximum(
            model.predict(
                future_years.reshape(-1, 1)
            ),
            0
        )

        context["forecast_summary"] = [

            {
                "year": int(year),

                "predicted_disasters": round(
                    float(prediction),
                    2
                )
            }

            for year, prediction in zip(
                future_years,
                future_predictions
            )
        ]

        # -----------------------------------------------------
        # 14. ANOMALY DETECTION
        # -----------------------------------------------------

        recent_year_cols = year_cols[-5:]

        anomaly_matrix = selected_data[
            recent_year_cols
        ].copy()

        anomaly_matrix = anomaly_matrix.apply(
            lambda row: row.interpolate(
                method="linear",
                limit_direction="both"
            ),
            axis=1
        ).fillna(0)

        if len(anomaly_matrix) >= 10:

            detector = IsolationForest(
                n_estimators=100,
                contamination=0.05,
                random_state=42
            )

            anomaly_labels = detector.fit_predict(
                anomaly_matrix
            )

            context["anomaly_count"] = int(
                (anomaly_labels == -1).sum()
            )

        # -----------------------------------------------------
        # 15. DASHBOARD METRICS
        # -----------------------------------------------------

        recent_values = values[
            -min(5, len(values)):
        ]

        recent_avg = float(
            np.mean(recent_values)
        )

        latest_year = int(
            years[-1]
        )

        latest_total = float(
            values[-1]
        )

        context.update({

            "country_list": country_list,

            "disaster_types": disaster_types,

            "selected_country": selected_country,

            "selected_disaster": selected_disaster,

            "total_countries": int(
                selected_data["Country"].nunique()
            ),

            "recent_avg": round(
                recent_avg,
                2
            ),

            "latest_year": latest_year,

            "latest_total": round(
                latest_total,
                2
            ),

        })

        # -----------------------------------------------------
        # 16. HISTORICAL TREND + FUTURE FORECAST CHART
        # -----------------------------------------------------

        fig_trend = go.Figure()

        # Historical disasters
        fig_trend.add_trace(
            go.Scatter(

                x=years,

                y=values,

                mode="lines+markers",

                name="Historical disasters",

                line=dict(
                    color="#e76f51",
                    width=2
                )
            )
        )

        # Model fit
        fig_trend.add_trace(
            go.Scatter(

                x=years,

                y=historical_fit,

                mode="lines",

                name="Model fit",

                line=dict(
                    color="#2a9d8f",
                    dash="dot",
                    width=2
                )
            )
        )

        # Future forecast
        fig_trend.add_trace(
            go.Scatter(

                x=future_years,

                y=future_predictions,

                mode="lines+markers",

                name="Forecast",

                line=dict(
                    color="#457b9d",
                    dash="dash",
                    width=3
                )
            )
        )

        fig_trend.update_layout(

            title=(
                f"{selected_disaster} Disaster Trend "
                f"— {selected_country}"
            ),

            xaxis_title="Year",

            yaxis_title="Number of disasters",

            template="plotly_white",

            hovermode="x unified",

            height=430,

            margin=dict(
                l=40,
                r=25,
                t=65,
                b=55
            )
        )

        context["trend_chart_div"] = opy.plot(

            fig_trend,

            auto_open=False,

            output_type="div",

            include_plotlyjs=False
        )

        # -----------------------------------------------------
        # 17. TOP 10 COUNTRIES BY DISASTER FREQUENCY
        # -----------------------------------------------------

        impact = selected_data[
            ["Country"] + recent_year_cols
        ].copy()

        impact["Recent_Average"] = (
            impact[recent_year_cols].mean(axis=1)
        )

        top_10 = (
            impact
            .nlargest(10, "Recent_Average")
            .sort_values("Recent_Average")
        )

        # -----------------------------------------------------
        # 18. COUNTRY IMPACT CHART
        # -----------------------------------------------------

        fig_impact = go.Figure()

        fig_impact.add_trace(
            go.Bar(

                x=top_10["Recent_Average"],

                y=top_10["Country"],

                orientation="h",

                marker_color="#e9a23b",

                name="Recent average"
            )
        )

        fig_impact.update_layout(

            title=(
                f"Top Countries — {selected_disaster} "
                "(latest 5-year average)"
            ),

            xaxis_title=(
                "Average number of disasters per year"
            ),

            yaxis_title="Country",

            template="plotly_white",

            height=430,

            margin=dict(
                l=130,
                r=25,
                t=65,
                b=50
            )
        )

        context["impact_chart_div"] = opy.plot(

            fig_impact,

            auto_open=False,

            output_type="div",

            include_plotlyjs=False
        )

        # -----------------------------------------------------
        # 19. RETURN DASHBOARD
        # -----------------------------------------------------

        return render(
            request,
            "climatechanges/disaster_prediction.html",
            context
        )

    # ---------------------------------------------------------
    # 20. ERROR HANDLING
    # ---------------------------------------------------------

    except Exception as exc:

        logger.exception(
            "Disaster prediction dashboard error"
        )

        context["error_message"] = str(exc)

        return render(
            request,
            "climatechanges/disaster_prediction.html",
            context
        )


# =============================================================
# CLIMATE DISASTER PREDICTION END
# =============================================================


# =============================================================
# CARBON PREDICTION
# =============================================================
import os
import pandas as pd
import numpy as np
import plotly.offline as opy
import plotly.graph_objs as go
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score, mean_squared_error
from django.shortcuts import render
from django.http import JsonResponse

def climateCarbonPrediction(request):
    excel_file = os.path.join('media', 'Carbon.xls')
    if not os.path.exists(excel_file):
        excel_file = 'Carbon.xls'

    try:
        # ==========================================================
        # 1. READ & DATA WRANGLING
        # ==========================================================
        data = pd.read_excel(excel_file)
        
        # Dynamically extract historical year columns (F1992 to F2023)
        year_cols = [col for col in data.columns if str(col).startswith('F') and str(col)[1:].isdigit() and 1992 <= int(str(col)[1:]) <= 2023]
        
        if 'Country' not in data.columns or 'Indicator' not in data.columns:
            return JsonResponse({'error': 'Missing required columns: Country or Indicator'})

        # Clean string features
        data['Country'] = data['Country'].astype(str).str.strip()
        data['Indicator'] = data['Indicator'].astype(str).str.strip()
        
        # Filter for carbon/forest related indicators (e.g., 'Carbon stocks in forests')
        # You can change or make this dynamically selectable via request.GET
        indicator_list = sorted(data['Indicator'].unique().tolist())
        selected_indicator = request.GET.get('indicator', 'Carbon stocks in forests' if 'Carbon stocks in forests' in indicator_list else indicator_list[0])
        
        filtered_data = data[data['Indicator'] == selected_indicator].copy()

        # Convert time-series columns to float
        for col in year_cols:
            filtered_data[col] = pd.to_numeric(filtered_data[col], errors='coerce')
        
        # Drop rows missing complete temporal records
        filtered_data.dropna(subset=year_cols, inplace=True)
        if filtered_data.empty:
            return JsonResponse({'error': 'No valid carbon/climate records found for the selected indicator.'})

        # Calculate summary metrics
        filtered_data['Avg_Carbon_Value'] = filtered_data[year_cols].mean(axis=1)
        filtered_data['Recent_10Yr_Avg'] = filtered_data[[c for c in year_cols if int(c[1:]) >= 2014]].mean(axis=1)
        filtered_data['Carbon_Volatility'] = filtered_data[year_cols].std(axis=1)

        # Country Filter Setup
        country_list = sorted(filtered_data['Country'].unique().tolist())
        selected_country = request.GET.get('country', country_list[0] if country_list else '')
        if selected_country not in country_list and country_list:
            selected_country = country_list[0]

        country_row = filtered_data[filtered_data['Country'] == selected_country].iloc[0]

        # ==========================================================
        # 2. ANOMALY DETECTION (Isolation Forest)
        # ==========================================================
        iso_forest = IsolationForest(contamination=0.05, random_state=42)
        filtered_data['Anomaly_Score'] = iso_forest.fit_predict(filtered_data[year_cols])
        anomalous_countries = filtered_data[filtered_data['Anomaly_Score'] == -1]

        # ==========================================================
        # 3. TIME-SERIES TREND PREDICTION & FUTURE FORECASTING
        # ==========================================================
        years = np.array([int(c[1:]) for c in year_cols]).reshape(-1, 1)
        carbon_values = country_row[year_cols].values.astype(float)

        # Train Ridge Regression Model for stable linear trend forecasting
        trend_model = Ridge(alpha=1.0)
        trend_model.fit(years, carbon_values)

        # Forecast future years (2024–2035)
        future_years = np.arange(2024, 2036).reshape(-1, 1)
        all_years = np.vstack((years, future_years)).flatten()
        
        hist_pred = trend_model.predict(years)
        future_pred = trend_model.predict(future_years)
        all_pred = np.concatenate([hist_pred, future_pred])

        # Evaluate model accuracy on historical baseline
        r2 = r2_score(carbon_values, hist_pred)
        rmse = np.sqrt(mean_squared_error(carbon_values, hist_pred))

        # ==========================================================
        # 4. DECADAL CORRELATION ANALYSIS
        # ==========================================================
        decade_cols = {
            '1990s': [c for c in year_cols if 1992 <= int(c[1:]) <= 1999],
            '2000s': [c for c in year_cols if 2000 <= int(c[1:]) <= 2009],
            '2010s': [c for c in year_cols if 2010 <= int(c[1:]) <= 2019],
            '2020s': [c for c in year_cols if 2020 <= int(c[1:]) <= 2023],
        }
        for decade, cols in decade_cols.items():
            if cols:
                filtered_data[decade] = filtered_data[cols].mean(axis=1)

        available_decades = [d for d in ['1990s', '2000s', '2010s', '2020s'] if d in filtered_data.columns]
        corr_matrix = filtered_data[available_decades + ['Avg_Carbon_Value']].corr().round(2)
        corr_html = corr_matrix.to_html(classes='table table-bordered table-striped')

        # ==========================================================
        # 5. PLOTLY VISUALIZATIONS
        # ==========================================================
        # Chart 1: Historical Observations vs Future Carbon Forecast
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=years.flatten(), y=carbon_values,
            mode='markers+lines', name=f'Observed ({selected_indicator})',
            line=dict(color='#27ae60')
        ))
        fig_trend.add_trace(go.Scatter(
            x=all_years, y=all_pred,
            mode='lines', name='Predicted Trend (2024–2035)',
            line=dict(dash='dash', color='#2980b9')
        ))
        fig_trend.update_layout(
            title=f'{selected_indicator} Trend & Future Projection ({selected_country})',
            xaxis_title='Year', yaxis_title='Carbon Value',
            template='plotly_white'
        )
        trend_chart_div = opy.plot(fig_trend, auto_open=False, output_type='div')

        # Chart 2: Top 10 Regions with Highest Recent Carbon Values (2020s)
        if '2020s' in filtered_data.columns:
            top_regions = filtered_data.sort_values(by='2020s', ascending=False).head(10)
        else:
            top_regions = filtered_data.head(10)

        fig_impact = go.Figure()
        fig_impact.add_trace(go.Bar(
            x=top_regions['Country'], y=top_regions['2020s'] if '2020s' in top_regions.columns else top_regions[year_cols[-1]],
            marker_color='#16a085', name='Recent Average Value'
        ))
        fig_impact.update_layout(
            title=f'Top 10 Regions - {selected_indicator} (2020–2023)',
            xaxis_title='Country / Region', yaxis_title='Mean Value',
            template='plotly_white'
        )
        impact_chart_div = opy.plot(fig_impact, auto_open=False, output_type='div')

        # Forecast summary table data (2024–2035)
        forecast_summary = [
            {'year': int(y), 'predicted_value': round(float(p), 3)}
            for y, p in zip(future_years.flatten(), future_pred)
        ]

        # Context Payload for template rendering
        context = {
            'country_list': country_list,
            'selected_country': selected_country,
            'indicator_list': indicator_list,
            'selected_indicator': selected_indicator,
            'trend_chart_div': trend_chart_div,
            'impact_chart_div': impact_chart_div,
            'corr_matrix_html': corr_html,
            'r2_score': round(float(r2), 3),
            'rmse': round(float(rmse), 3),
            'total_countries': len(filtered_data),
            'anomaly_count': len(anomalous_countries),
            'forecast_summary': forecast_summary,
            'recent_10yr_avg': round(float(country_row['Recent_10Yr_Avg']), 2),
        }

        return render(request, 'climatechanges/carbonprediction.html', context)

    except Exception as e:
        return JsonResponse({'error': str(e)})

# =============================================================
# CARBON PREDICTION END
# =============================================================


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import SupportTicket, TicketMessage
from .forms import SupportForm, MessageForm


@login_required
def support(request):

    if request.method == 'POST':
        form = SupportForm(request.POST)

        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.save()

            return redirect('my_tickets')

    else:
        form = SupportForm()

    return render(request, 'climatechanges/support.html', {
        'form': form
    })


@login_required
def my_tickets(request):

    tickets = SupportTicket.objects.filter(
        user=request.user
    ).order_by('-created_at')

    return render(request, 'climatechanges/my_tickets.html', {
        'tickets': tickets
    })


@login_required
def ticket_detail(request, id):

    ticket = get_object_or_404(
        SupportTicket,
        id=id,
        user=request.user
    )

    messages = ticket.messages.all()

    if request.method == 'POST':
        form = MessageForm(request.POST)

        if form.is_valid():
            message = form.save(commit=False)
            message.ticket = ticket
            message.sender = request.user
            message.save()

            return redirect('ticket_detail', id=id)

    else:
        form = MessageForm()

    return render(request, 'climatechanges/ticket_detail.html', {
        'ticket': ticket,
        'messages': messages,
        'form': form
    })


#----------machine learning chat bot ----------------
import os
import json
import pandas as pd
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from google import genai

# ⚠️ Use environment variables in production
client = genai.Client(api_key="AIzaSyAlG_kfT6zBE0ajsqhjbOygK6hTgVx5-qA")

# ---- Temperature Formatter (°C) ----
def format_temp_change(value):
    try:
        val = float(value)
        if pd.isna(val):
            return "N/A"
        sign = "+" if val > 0 else ""
        return f"{sign}{val:.3f} °C"
    except (ValueError, TypeError):
        return "N/A"

@csrf_exempt
def chatbot(request):
    excel_file_path = os.path.join("media", "Temperature.xls")
    df = None

    # Load Excel dataset
    try:
        df = pd.read_excel(excel_file_path, sheet_name="Indicator_3_1_Climate_Indicator")
    except Exception as e:
        print(f"⚠️ Excel load failed: {e}")

    if request.method == "POST":
        try:
            if request.headers.get("Content-Type") == "application/json":
                data = json.loads(request.body)
                user_input = data.get("message", "")
            else:
                user_input = request.POST.get("message", "")
        except Exception:
            return JsonResponse({"response": "Invalid request format."}, status=400)

        matched_row = None
        temp_summary = ""

        # 🔎 Check if user input matches any Country in the dataset
        if df is not None and user_input:
            user_query_lower = user_input.lower()
            for _, row in df.iterrows():
                country_name = str(row.get("Country", "")).strip()
                if country_name and country_name.lower() in user_query_lower:
                    matched_row = row
                    break

            if matched_row is not None:
                country = matched_row["Country"]
                indicator = matched_row.get("Indicator", "Surface Temperature Change")
                latest_temp = format_temp_change(matched_row.get("Temp"))

                # Extract available year columns (1961 to 2023)
                year_cols = [col for col in df.columns if isinstance(col, int)]
                yearly_values = {
                    yr: matched_row[yr]
                    for yr in year_cols
                    if pd.notna(matched_row[yr])
                }

                # Recent 10 years breakdown
                recent_years = sorted(yearly_values.keys())[-10:]
                recent_details = [
                    f"  - {yr}: {format_temp_change(yearly_values[yr])}"
                    for yr in recent_years
                ]

                # Historical min & max years
                if yearly_values:
                    max_yr = max(yearly_values, key=yearly_values.get)
                    min_yr = min(yearly_values, key=yearly_values.get)
                    extremes = (
                        f"Warmest recorded year: {max_yr} ({format_temp_change(yearly_values[max_yr])})\n"
                        f"Coolest recorded year: {min_yr} ({format_temp_change(yearly_values[min_yr])})"
                    )
                else:
                    extremes = ""

                # Check if user asked about a specific year (e.g., 2015, 1998)
                specific_year_note = ""
                for yr, val in yearly_values.items():
                    if str(yr) in user_input:
                        specific_year_note += f"Requested Year {yr}: {format_temp_change(val)}\n"

                temp_summary = (
                    f"Country/Region: {country}\n"
                    f"Indicator: {indicator}\n"
                    f"Latest/Overall Temp Change ('Temp' column): {latest_temp}\n"
                    f"{specific_year_note}"
                    f"{extremes}\n"
                    f"Recent Years Trend:\n" + "\n".join(recent_details)
                )

        # 🟢 Build AI prompt with instructions for both dataset and live/current info
        if matched_row is not None and temp_summary:
            full_prompt = f"""
            You are an advanced climate and live weather assistant.

            Here is the official historical surface temperature change dataset info for the requested region:
            {temp_summary}

            User's question: {user_input}

            Instructions:
            - If the user is asking about historical temperature changes, trends, or past years, use the dataset details provided above.
            - If the user is asking about *live weather, current temperature right now, or today's forecast*, use your up-to-date knowledge to provide live/current weather information.
            - Answer clearly, concisely, and accurately.
            """
        else:
            full_prompt = f"""
            You are a knowledgeable climate and live weather assistant.
            The user's question did not match a specific country in the historical climate dataset. 
            If the user is asking for current live weather or general climate facts, provide an accurate, up-to-date response.

            User's question: {user_input}
            """

        # 🔗 Call Gemini API
        try:
            response = client.models.generate_content(
                model="gemini-3.5-flash",
                contents=full_prompt
            )
            bot_response = response.text
        except Exception as e:
            bot_response = f"⚠️ Error from Gemini API: {e}"

        return JsonResponse({"response": bot_response})

    return render(request, "climatechanges/chatbot.html")