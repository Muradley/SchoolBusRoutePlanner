import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
import requests
import numpy as np
from sklearn.cluster import KMeans
import time


st.markdown("""
    # Bus Route Planner
    Upload a CSV file containing the names and addresses of all students as per the following example:

    | Full Name | Address |
    | ------ | ----------- |
    | Mark Fullman | 2490 Corina Way, Mountain View, CA, 92012, USA |     

    An address should contain the following, Street, City, State, Zipcode, Country, in the respective order.
""")

uploaded_file = st.file_uploader("Input csv file of addresses", type=['csv'])
school_address = st.text_input("Address of the school")
num_of_buses = st.number_input("How many buses do you have?", min_value=1, value=1)
bus_capacity = st.number_input("What is the capacity of each bus?", min_value=1, value=1)
clicked = st.button("Generate Routes")

if clicked:
    if uploaded_file is None:
        st.write("Please upload a CSV containing the names and addresses of all students")
    else:
        df = pd.read_csv(uploaded_file)

        if (num_of_buses * bus_capacity) < len(df):
            st.write("There aren't enough buses to accomodate for this many students")
        else:
     
            st.dataframe(df)
            geolocator = Nominatim(user_agent="myGeocoder", timeout=100)

            school_loc = geolocator.geocode(school_address)
            school_lon = school_loc.longitude
            school_lat = school_loc.latitude

            longitudes = []
            latitudes = []

            with st.spinner('Wait for it... generating routes may take a while...'):
                for i in range(len(df)):
                    location = geolocator.geocode(df["Address"][i])
                    longitudes.append(location.longitude)
                    latitudes.append(location.latitude)

                df['Longitude'] = longitudes
                df['Latitude'] = latitudes

                vehicles = []
                for i in range(1, num_of_buses + 1):
                    vehicles.append({
                        "vehicle_id": f"Bus {i}",
                        "type_id": "bus",
                        "start_address": {
                            "location_id": "school",
                            "lon": school_lon,
                            "lat": school_lat
                        },
                        "end_address": {
                            "location_id": "school",
                            "lon": school_lon,
                            "lat": school_lat
                        }
                    })

                vehicle_types = [{
                    "type_id": "bus",
                    "profile": "car_delivery",
                    "capacity": [bus_capacity]
                    }]

                services = []
                for i, row in df.iterrows():
                    services.append({
                        "id": row["Full Name"],
                        "address": {
                            "location_id": row["Address"],
                            "lon": row["Longitude"],
                            "lat": row["Latitude"]
                        },
                        "size": [1]
                    })

                query = {"key": "ecd7cc39-6f78-4356-adc9-c28724240329"}

                payload = {
                "vehicles": vehicles,
                "vehicle_types": vehicle_types,
                "services": services
                }

                headers = {"Content-Type": "application/json"}
                url = "https://graphhopper.com/api/1/vrp"

                response = requests.post(url, json=payload, headers=headers, params=query)
                data = response.json()

                results_df = pd.DataFrame()
                
                for route in data["solution"]["routes"]:
                    addresses = []

                    for activity in route["activities"]:
                        addresses.append(activity["location_id"])

                    result = pd.DataFrame(addresses, columns=[f'{route["vehicle_id"]}'])

                    results_df = pd.concat([results_df, result], axis=1)
                    
            st.success('Done!')

            st.download_button(label="Download Routes", data=results_df.to_csv().encode('utf-8'), file_name="routes.csv", mime="csv")