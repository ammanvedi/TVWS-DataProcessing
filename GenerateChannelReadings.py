import json
from math import radians, cos, sin, asin, sqrt
from shapely.geometry import shape, Point


'''
	identify bands
'''

class RegionSelector:
	ITU_COUNTRIES = None
	WORLD_COUNTRIES = None
	ITU_REGIONS = None
	
	def __init__(self, ITUcountriesfile, Worldcountriesfile, ITUregionsfile):
		ITU_C_O = open(ITUcountriesfile)
		self.ITU_COUNTRIES = json.load(ITU_C_O)
		ITU_C_O.close()
		WORLD_C_F = open(Worldcountriesfile)
		self.WORLD_COUNTRIES = json.load(WORLD_C_F)
		WORLD_C_F.close()
		ITU_R_F = open(ITUregionsfile)
		self.ITU_REGION = json.load(ITU_R_F)
		ITU_R_F.close()
	
	def findCountry(self, lat, lng):
		testpoint = Point(lng, lat)
		for countrygeom in self.WORLD_COUNTRIES["features"]:
			geopoly = shape(countrygeom["geometry"])
			if geopoly.contains(testpoint):
				print "INFO : found measurement country of origin"
				return countrygeom["properties"]["name"]
		return None
	
	def findRegion(self, countryname):
		allcapsname = countryname.upper()
		for country in self.ITU_COUNTRIES:
			if country["Country"] == allcapsname:
				print "INFO : found ITU region for country"
				return country["ITURegion"]
		return None
		
	def getChannels(self, ITURegionNumber):
		print "INFO : found channel list for country"
		return [self.ITU_REGION[str(ITURegionNumber)]["subregions"][0]["Channels"],self.ITU_REGION[str(ITURegionNumber)]["BandWidth"]] 
		
'''
	combine powers over bands 
'''

class ReadingsParser:

	DATA_FILE = None
	MIN_POWER = 47
	BAND_LOWER_FREQ = None
	CHANNEL_IDS = None
	BAND_WIDTH = 0.3
	MIN_DISTANCE = 30
	RegionID = None
	
	def __init__(self, minimumpower, minimumdistance):
		self.MIN_POWER = minimumpower
		self.MIN_DISTANCE = minimumdistance
		self.RegionID = RegionSelector("ITURegionCountries.json", "countries.geo.json", "channelallocations.json")
	
	def determineBands(self, rawdatas):
		range = list()
		frequencies = list()
		BANDS = None
		for time, freqs in rawdatas[1]["Spectrum"].iteritems():
			range = freqs
			break
		for freq, power in range.iteritems():
			frequencies.append(float(freq))
		topend = max(frequencies)
		lowend = min(frequencies)
		for ts, loc in rawdatas[1]["Location"].iteritems():
			BANDS = self.RegionID.getChannels(self.RegionID.findRegion(self.RegionID.findCountry(loc[0], loc[1])))
			break
		filtered = [elem for elem in BANDS[0] if ((elem["LowEnd"] >= lowend) and (elem["UpEnd"] <= topend))]
		reduced = [elem["LowEnd"] for elem in filtered if 1]
		channels = [elem["ChannelNumber"] for elem in filtered if 1]
		print "INFO : selected valid bands"
		return reduced
		
	
	def Generate(self, filename):
		self.DATA_FILE = filename
		res = []
		json_file = open(self.DATA_FILE)
		data = json.load(json_file)
		self.BAND_LOWER_FREQ = self.determineBands(data)
		spectrum = data[1]["Spectrum"]
		print "INFO : combining readings for ", filename, " across valid bands..."
		for ts, loc in data[1]["Location"].iteritems():
			data_point = {'lat' : loc[0], 'lon' : loc[1], 'ts' : int(float(ts))}
			if self.farther_than(self.MIN_DISTANCE, res, data_point):
				data_point["Spectrum"] = self.get_ranges(spectrum[ts]) 
				res.append(data_point)
		print "INFO : finished compiling combined readings for ", filename
		return {'BANDS' : self.BAND_LOWER_FREQ, 'DATA' : res}
	
	def get_ranges(self, spectrum):
		res = []
		for lf in self.BAND_LOWER_FREQ:
			hf = lf + self.BAND_WIDTH
			freqsinrange = [k for k,v in spectrum.items() if (float(lf) <= float(k) <= float(hf))]
			combined = 0.0
			for val in freqsinrange:
				combined += self.MIN_POWER + spectrum[val] 
			res.append(combined)
		return res
	
	def haversine(self, lon1, lat1, lon2, lat2):
	    """
	    Calculate the great circle distance between two points 
	    on the earth (specified in decimal degrees)
	    """
	    # convert decimal degrees to radians 
	    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
	    # haversine formula 
	    dlon = lon2 - lon1 
	    dlat = lat2 - lat1 
	    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
	    c = 2 * asin(sqrt(a)) 
	    km = 6371 * c
	    return km*1000
	
	def printToJSON(self, filepath, rawdatas):
		f1 = open(filepath, "w+")
		f1.write(json.dumps(rawdatas, ensure_ascii=0))
		print "INFO : wrote file to ", filepath
	  
	def farther_than(self, meters, accepted, point):
		found = (x for x in accepted if self.haversine(x["lon"], x["lat"], point["lon"], point["lat"]) < meters)
		if len(list(found))  == 0:
			return 1
		if len(list(found)) > 0:
			return 0
	
def testgen():
	gen = ReadingsParser(47,30)
	gen.printToJSON("./results/OUT.json",gen.Generate("./inputs/manhattan-1.json"))
	
def testreg():
	reg = RegionSelector("./meta/ITURegionCountries.json", "./meta/countries.geo.json", "./meta/channelallocations.json")
	print reg.getChannels(reg.findRegion(reg.findCountry(52.05249, -1.757812)))
	
testgen()












