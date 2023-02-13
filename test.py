from geopy.geocoders import Nominatim

locator = Nominatim(user_agent="myGeocoder")

print(locator.geocode("3551 Middlefield Road, Menlo Park, CA, 94025, USA").latitude)