#!/usr/bin/python

# Filename: kml_lookup.py
# Version: v5.0
# Author: Philippe Tang
# Email: ptang@splunk.com
# Date: 10/17/2017
# Description: Get Placemarks for specific Lat, Lon
# Script usage: kml_lookup.py -l <lat> -L <lon>

# Imports
from pykml import parser
from pykml.factory import nsmap
from shapely.geometry import Point, MultiPoint
from shapely.geometry.polygon import Polygon
from zipfile import ZipFile
import os, sys, getopt, time

# Environment variables
#SPLUNK_HOME = "/opt/splunk"
#KML_PATH = "etc/apps/TA-KML_Lookup/appserver/static/kml"
#FULLPATH = os.path.join(SPLUNK_HOME, KML_PATH)
FULLPATH = "/home/l00py/kml_lookup/kmz"

# List of KML files
files = []
for file in os.listdir(FULLPATH):
    if file.endswith(".kml") or file.endswith(".kmz"):
        files.append(file)

# OpenKMZ
def openKMZ(filename):
    fstring = ""
    zip = ZipFile(filename)
    for z in zip.filelist:
        if z.filename[-4:] == '.kml':
            fstring = zip.read(z)
            break
    else:
        raise Exception("Could not find kml file in %s" % filename)
    return fstring

# OpenKML
def openKML(filename):
    fstring = ""
    if filename.endswith(".kmz"):
        fstring = openKMZ(filename)
    elif filename.endswith(".kml"):
        fstring = open(filename,'r').read()
    else:
        raise Exception("Could not find kml file in %s" % filename)
    return fstring

# Function: Iterate through dictionary and find placemarks
def getPlacemarks(lat, lon):
    # Parse KML and build Dictionary [Placemark:coordinates]
    pmCoordDict = {}
    for file in files:
        f = openKML(FULLPATH+"/"+file)
        root = parser.fromstring(f)
        folder = root.Document.Folder
        for pm in folder.Placemark:
            # Determine if Multigeometry or Single Geom
            if hasattr(pm, 'MultiGeometry'):
                #print pm.name.text, pm.description.text.encode('utf-8'), "multigeom"
                #print "multigeom"
                outPoints = []
                inPoints = []
                # outerBoundaryIs
                if hasattr(pm.MultiGeometry.Polygon, 'outerBoundaryIs'):
                    outPoints = []
                    coordinates = pm.MultiGeometry.Polygon.outerBoundaryIs.LinearRing.coordinates.text.split()
                    for point in coordinates:
                        xy = point.split(",")
                        latitude = float(xy[1])
                        longitude = float(xy[0])
                        outPoints.append(tuple([latitude,longitude]))
                # innerBoundaryIs
                elif hasattr(pm.MultiGeometry.Polygon, 'innerBoundaryIs'):
                    inPoints = []
                    coordinates = pm.MultiGeometry.Polygon.innerBoundaryIs.LinearRing.coordinates.text.split()
                    for point in coordinates:
                        xy = point.split(",")
                        latitude = float(xy[1])
                        longitude = float(xy[0])
                        inPoints.append(tuple([latitude,longitude]))
                # MultiGeom Polygon
                # If there are innerBoundaryIs
                if len(inPoints) > 0:
                    multiGeomPoly = Polygon(outPoints,[inPoints])
                else:
                    multiGeomPoly = Polygon(outPoints)
                pmCoordDict[pm.name+" : \""+pm.description+"\""] = multiGeomPoly
            # Determine if Single geometry
            elif hasattr(pm, 'Polygon'):
                #print pm.name.text, pm.description.text.encode('utf-8'), "singlegeom"
                # outerBoundaryIs
                outPoints = []
                coordinates = pm.Polygon.outerBoundaryIs.LinearRing.coordinates.text.split()
                for point in coordinates:
                    xy = point.split(",")
                    latitude = float(xy[1])
                    longitude = float(xy[0])
                    outPoints.append(tuple([latitude,longitude]))
                singleGeomPoly = Polygon(outPoints)
                pmCoordDict[pm.name+" : \""+pm.description+"\""] = singleGeomPoly
    # Get Placemarks list
    pmList = []
    for key, value in pmCoordDict.iteritems():
        poly = Polygon(value)
        lat = float(lat)
        lon = float(lon)
        if poly.contains(Point(lat,lon)):
            pmList.append(key)
    return pmList

# Main
def main(argv):
   # Get Start time
   start_time = time.time()
   # Declare lat, lon
   lat = 0.0
   lon = 0.0
   # Get passing arguments
   try:
      opts, args = getopt.getopt(argv,"hl:L:",["lat=","lon="])
   except getopt.GetoptError:
      print 'kml_lookup.py -l <lat> -L <lon>'
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print 'kml_lookup.py -l <lat> -L <lon>'
         sys.exit()
      elif opt in ("-l", "--lat"):
         lat = arg
      elif opt in ("-L", "--lon"):
         lon = arg
   print 'Lat: ', lat
   print 'Lon: ', lon
   # Run getPlacemarks
   pmList = getPlacemarks(lat, lon)
   print '[%s]' % ', '.join(map(str, pmList))
   # Get elapased time
   elapsed_time = time.time() - start_time
   print "Elapsed Time: %.3f" % elapsed_time

if __name__ == "__main__":
   main(sys.argv[1:])
