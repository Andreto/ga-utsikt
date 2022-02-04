import shapefile

shape = shapefile.Reader("calcData/swedenBorders/ne_10m_admin_0_countries_swe.shp") #250 polygons

feature = shape.shapeRecords()[50]  #Sweden = 50
sweden = feature.shape.__geo_interface__  

sweden = sweden["coordinates"] #Revoves unnecessary info

print(sweden)