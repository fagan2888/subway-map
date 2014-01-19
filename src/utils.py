import numpy as np
import fiona
from shapely.geometry import MultiPolygon, Polygon
from pyproj import transform, Proj

def corr(x,y,k=0):
    if k > 0:
        x = x[:-k]
        y = y[k:]
    elif k < 0:
        k = np.abs(k)
        x = x[k:]
        y = y[:-k]

    xbar = np.mean(x)
    ybar = np.mean(y)
    r = np.sum( (x-xbar)*(y-ybar) ) / np.sqrt(sum( (x-xbar)**2 ) * sum(
        (y-ybar)**2 ))
    
    return r

def nyc_boundary():
    boroughs = {}
    # maps BoroCode to categorical
    borough_names = {5:'SI',4:'Q',3:'BK',1:'M',2:'BX'}
    
    with fiona.open('../data/indata/nybb_13a/nybb.shp','r') as source:
        # set up three projection types: boundary data start; google-standard
        # lat/lon, using WGS84; Albers Equal Area
        p1 = Proj(source.crs,preserve_units=True)
        p2 = Proj({'proj':'longlat', 'datum':'WGS84'})
        p3 = Proj({'proj':'aea', 'datum':'WGS84', 'lon_0':'-96'})
    
        # for each shape, convert its coordinates to AEA
        nyc = MultiPolygon()
        for borough in source:
            borough_shapes = MultiPolygon()
            borocode = borough['properties']['BoroCode']
            for shape in borough['geometry']['coordinates']:
                p1_points = np.array(shape[0])
    
                p2_points = transform(p1, p2, p1_points[:,0], p1_points[:,1])
                p3_points = transform(p2, p3, p2_points[0], p2_points[1])
                p3_points = np.vstack([p3_points[0], p3_points[1]]).T
    
                new = Polygon(p3_points)
                nyc = nyc.union(new)
                borough_shapes = borough_shapes.union(new)
            boroughs[borocode] = borough_shapes
    
    # i = 0
    # for shape in nyc:
        # x,y = shape.exterior.xy
        # plt.plot(x,y)
    
        # bounds = np.array(shape.bounds)
        # bounds = bounds.reshape([2,2])
        # cx = np.mean(bounds[:,0])
        # cy = np.mean(bounds[:,1])
    
        # plt.text(cx,cy,str(i))
        # i = i+1
    # By running the above, we identify the following islands that contain subway stations:
    #        i  borough            name
    #   1.   3  staten island      staten island
    #   2.  39  manhattan          manhattan
    #   3.  36  manhattan          roosevelt island
    #   4.  40  bronx              bronx
    #   5.  10  brooklyn / queens  rockaways
    #   6.  14  brooklyn / queens  jamaica bay wildlife refuge / broad channel
    #   7.  15  brooklyn / queens  brooklyn / queens
    # indices = [3, 39, 36, 40, 10, 14, 15]
    indices = [39, 36, 40, 10, 14, 15]
    boundary = []
    for i in indices:
        boundary.append(nyc[i])
    nyc = MultiPolygon(boundary)

    return nyc, boroughs, borough_names
