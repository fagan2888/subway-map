import pickle
from numpy import array, vstack, mean, tile, nan, dot, log
from scipy.spatial import KDTree

stops = pickle.load(open('data/save/stops.p', 'rb'))
tracts = pickle.load(open('data/save/tracts.p', 'rb'))

xy = []
for i in range(len(stops)):
    xy.append(stops.iloc[i][['x', 'y']].values)
xy = array(xy)

tree = KDTree(xy)

new = ['v_area', 'v_larea', 'rolle_connectedness', 'graph_connectedness']
for n in new:
    tracts[n] = tile(nan, len(tracts))

# find subway station nearest to tract
for i in range(len(tracts)):
    tract = tracts.iloc[i]

    ch = tract['region'].convex_hull
    x1, y1, x2, y2 = ch.bounds

    x = mean([x1, x2])
    y = mean([y1, y2])

    k = 1
    d, ix = tree.query([x, y], k=k)

    # distance weights
    if k == 1:
        w = 1
    else:
        w = d / sum(d)

    neighbors = stops.iloc[ix]
    
    for n in new:
        tracts[n].iloc[i] = dot(w, neighbors[n])

pickle.dump(tracts, open('data/save/tracts.p', 'wb'))

# from src.utils import choropleth
# for measure in ['v_larea']:
    # if measure not in ['region', 'id']:
        # choropleth(tracts, measure, stops)
