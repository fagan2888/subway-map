import numpy as np
from scipy.spatial import Voronoi, voronoi_plot_2d
import matplotlib.pyplot as plt

# raycasting adapted from http://geospatialpython.com/2011/01/point-in-polygon.html
# True if point is in poly; false if not
def raycast(p, poly):
    x,y = p[0],p[1]
    n = poly.shape[0]
    inside = False

    p1x,p1y = poly[0]
    for i in range(n+1):
        p2x,p2y = poly[i % n]
        if y > min(p1y,p2y):
            if y <= max(p1y,p2y):
                if x <= max(p1x,p2x):
                    if p1y != p2y:
                        xints = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                    if p1x == p2x or x <= xints:
                        inside = not inside
        p1x,p1y = p2x,p2y

    return inside

# p = (x1, y1, x2, y2, x3, y3, x4, y4)
# see http://en.wikipedia.org/wiki/Line-line_intersection
def intersection(p):
    # print p
    px = ( (p[:,0]*p[:,3] - p[:,1]*p[:,2])*(p[:,4] - p[:,6]) - (p[:,4]*p[:,7] - p[:,5]*p[:,6])*(p[:,0] - p[:,2]) )  /  ( (p[:,0] - p[:,2])*(p[:,5] - p[:,7]) - (p[:,1] - p[:,3])*(p[:,4] - p[:,6]) )
    py = ( (p[:,0]*p[:,3] - p[:,1]*p[:,2])*(p[:,5] - p[:,7]) - (p[:,4]*p[:,7] - p[:,5]*p[:,6])*(p[:,1] - p[:,3]) )  /  ( (p[:,0] - p[:,2])*(p[:,5] - p[:,7]) - (p[:,1] - p[:,3])*(p[:,4] - p[:,6]) )
    return np.vstack([px,py])

def CCW(a,b,c):
    n = np.shape(a)[0]
    a11 = np.ones(n)
    a21 = np.ones(n)
    a31 = np.ones(n)
    a12 = a[:,0]
    a13 = a[:,1]
    a22 = b[:,0]
    a23 = b[:,1]
    a32 = c[:,0]
    a33 = c[:,1]

    det = a11*(a22*a33 - a23*a32) - a12*(a21*a33 - a23*a31) + a13*(a21*a32 - a22*a31)
    return det > 0

def intersect(l1,l2):
    n = np.shape(l1)[0]
    result = np.ones(n)
    p11 = l1[:,0:2]
    p12 = l1[:,2:4]
    p21 = l2[:,0:2]
    p22 = l2[:,2:4]
    result[CCW(p11, p21, p22) == CCW(p12, p21, p22)] = 0
    result[CCW(p11, p12, p21) == CCW(p11, p12, p22)] = 0
    return result

# points will be both the points for which we calculate a Voronoi diagram, and the basis of our clipping region
points = np.array([[0, 0], [0, 1], [0, 2], [1, 0], [1, 1], [1, 2], [2, 0], [2, 1], [2, 2]])
vor = Voronoi(points)
# taken from voronoi.py
far_points = []
far_vertices = []
far_ridge_points = []
# adapted from scipy-0.13.0/scipy/spatial/_plotuitls.py
ptp_bound = vor.points.ptp(axis=0)
center = vor.points.mean(axis=0)
vor.ridge_vertices = np.array(vor.ridge_vertices)
for j in np.arange(np.shape(vor.ridge_points)[0]):
    pointidx = vor.ridge_points[j]
    simplex = vor.ridge_vertices[j]

    simplex = np.asarray(simplex)
    if np.any(simplex < 0):
        i = simplex[simplex >= 0][0]  # finite end Voronoi vertex

        t = vor.points[pointidx[1]] - vor.points[pointidx[0]]  # tangent
        t /= np.linalg.norm(t)
        n = np.array([-t[1], t[0]])  # normal

        midpoint = vor.points[pointidx].mean(axis=0)
        direction = np.sign(np.dot(midpoint - center, n)) * n
        far_point = vor.vertices[i] + direction * ptp_bound.max()

        # add new vertex (far_point) to vertices
        vor.vertices = np.vstack([vor.vertices, far_point])
        # reassign negative vertex index (negative value is always first) to newly added vertex
        vor.ridge_vertices[j][0] = np.shape(vor.vertices)[0] - 1

# NEED TO UPDATE VOR.REGIONS

# vertices in points to give clipping region points, in order
clipV = [0, 1, 2, 5, 8, 7, 6, 3, 0]
clips = points[clipV]
clips = np.hstack([clips[:-1],clips[1:]])

voronoi_lines = np.hstack([vor.vertices[vor.ridge_vertices][:,0], vor.vertices[vor.ridge_vertices][:,1]])

# combine all path lines with voronoi lines
# this would do it if a = np.array([1,2,3]): np.transpose([np.tile(a, len(b)), np.repeat(b, len(a))])
# we change this slightly for our two-dimensional arrays
lines = np.hstack([np.tile(clips.T,voronoi_lines.shape[0]).T, voronoi_lines.T.repeat(clips.shape[0],1).T])

result = intersect(lines[:,0:4], lines[:,4:8])
result = result.astype(bool)

intersection_pairs = lines[result] # lines that intersect
intersections = intersection(intersection_pairs)
intersections = intersections.T

# create list interior, containing all interior ridges--with intersecting segments replaced with a segment only to the intersection
interior = []
for ridge in vor.ridge_vertices:
    ridge_coords = vor.vertices[ridge]
    ridge_coords = np.hstack([ridge_coords[:,0], ridge_coords[:,1]])
    p1 = vor.vertices[ridge[0]]
    p2 = vor.vertices[ridge[1]]
    p1in = raycast(p1,points[clipV])
    p2in = raycast(p2,points[clipV])
    # print p1in, p2in
    if p1in or p2in:
        # print 'at least one'
        if p1in and p2in:
            interior.append([p1,p2])
        else:
            a = np.all(intersection_pairs[:,4:8] == np.hstack([p1,p2]), 1)
            b = np.all(intersection_pairs[:,4:8] == np.hstack([p2,p1]), 1)
            c = np.vstack([a,b]).T
            d = np.any(c,1)

            p_new = intersections[np.where(d)[0][0]]
            if p1in:
                interior.append([p1,p_new])
            else:
                interior.append([p2,p_new])
    print

interior = np.array(interior)
# np.all(np.hstack([np.all(intersection_pairs[:,4:8][:,[2,3,0,1]] == ridge_coords,1), np.alluintersection_pairs[:,4:8] == ridge_coords,1)], 1))
