from datetime import datetime
import matplotlib.pyplot as plt
from meteostat import Point, Daily

# Set time period
start = datetime(2024, 3, 1)
end = datetime(2024, 4, 4)

location = Point(52.409538, 16.931992)
# Get daily data for 2023
data = Daily(location, start, end)
data = data.fetch()
# Plot line chart including average, minimum and maximum temperature

data.plot(y=["tavg", "tmin", "tmax"])
plt.show()