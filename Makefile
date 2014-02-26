all: datadir data voronoi


data: nybb_13a google_transit ACS acs_geoids

datadir:
	mkdir -p data/indata/ data/save/


nybb_13a:
	src/indata/nybb_13a.sh

google_transit:
	src/indata/google_transit.sh

voronoi:
	python src/voronoi.py

choropleth:
	python src/choropleth.py


ACS:
	src/indata/ACS.sh

acs_geoids:
	src/indata/acs_geoids.sh

census:
	python src/census_request.py
