###########################

#getRouteMatrix()
#elevation = getElevationVector(37.788022,-122.399797,API_KEY)
#print(elevation)

origin = 'New York, NY'
destination = 'Los Angeles, CA'
num_intermediate_points = 5

num_intermediate_points = getDistance(origin, destination, API_KEY)

elv = []

lat, lng = getRouteMatrix(origin, destination, num_intermediate_points, API_KEY)
for i in range(0, len(lat)):
    elv.append(getElevationVector(lat[i], lng[i], API_KEY))
    
elv = [13.4994592666626,
 293.1217041015625,
 374.8125,
 1224.585327148438,
 2068.4765625]
print(getGradient(elv))
    
###########################

elvation = [13.4994592666626, 356.5942687988281, 231.8114929199219, 160.6178436279297, 378.9525451660156, 352.2007446289062, 1170.530151367188, 1706.24072265625, 1965.924926757812, 187.6017761230469]
gradient = [343.0948095321655, -124.78277587890622, -71.19364929199222, 218.33470153808594, -26.751800537109432, 818.3294067382817, 535.710571289062, 259.68420410156205, -1778.3231506347652]
None
