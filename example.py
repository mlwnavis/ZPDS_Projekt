import datetime
import matplotlib.pyplot as plt
from meteostat import Point, Daily

# Set time period

start = datetime.datetime.today() - datetime.timedelta(days=30)
end = datetime.datetime.today()
location = Point(52.409538, 16.931992)
# Get daily data for 2023
data = Daily(location, start, end)
data = data.fetch()
# Plot line chart including average, minimum and maximum temperature
print(data)
data.plot(y=["tavg", "tmin", "tmax"])
plt.show()
