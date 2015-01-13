# convert rtl-sdr samples to google maps' heatmap
#
#

require 'json'
require 'rubygems'
require 'google_chart'

include Math

DATA_FILE='Scan.rfs'
OUT_FILE='peakpowernormalised.json'
OPEN_OUT=File.open(OUT_FILE, 'w')
MIN_POWER = 47
BAND_LOWER_FREQ=[ # MHz
  945.00,
  945.74,
  946.18,
  946.94,
  947.60,
  948.26,
  948.84,
  949.17
]
BAND_WIDTH=0.3 #300 KHz
MIN_DISTANCE=10 #meters, don't store points, closer than this distance to each other


# [
#   {
#     lat: lat,
#     lon: lon,
#     spectrum: [power_for_each_range in spectrum_ranges]
#   },
# ]
def load_data
  res = []
  json_file = File.read(DATA_FILE)
  data = JSON.parse(json_file)[1]
  spectrum = data['Spectrum']
  data['Location'].each do |ts, loc|
    data_point = {lat: loc[0], lon: loc[1], ts: ts.to_i}
    if farther_than(MIN_DISTANCE, res, data_point)
      # puts '+ ' + ts.to_s
      res.push(data_point.merge({spectrum: get_ranges(spectrum[ts])}))
    else
      # puts './tmp/' + ts.to_i.to_s + '.0.png'
    end
  end
  return res
end


# calculate combined power of signal inside the band
#
def get_ranges(spectrum)
  res = []
  # puts "newpoint"
  BAND_LOWER_FREQ.each do |lf|
    hf = lf + BAND_WIDTH
#    res.push spectrum.keys.select{|f| (lf..hf).include?(f.to_f)  }
#get all frequencies within the band range
# get all powers relating to these frequencies
# find the peak power within the band 
    puts "start----- #{lf} MHz ->  #{hf} MHz --------------------------------------------------"
    puts spectrum.keys.select{|f| (lf..hf).include?(f.to_f)  }
    freqs_inrange = spectrum.keys.select{|f| (lf..hf).include?(f.to_f)  }
    powers = []
    freqs_inrange.each do |frequency|
      powers.push spectrum[frequency];
      puts "power for #{frequency.to_f} is #{spectrum[frequency]}"
    end
    puts "the max power in this band is #{powers.max}, the minimum is #{powers.min}"
    res.push powers.max
    puts "end------- #{lf} MHz ->  #{hf} MHz ----------------------------------------------------"
#      .reduce(0) {|memo, k| if memo == nil
#                            memo = 10000
#                          elsif memo > spectrum[k]
#                            memo = spectrum[k]
#                          end
#                  }
      #puts res
      #puts "endband--------------- " ,lf, "MHZ"
      #.select{|f| (lf..hf).include?(f.to_f) }
      #.inject(0) { |memo, k| memo +=  spectrum[k]} / ( spectrum.keys.select{|f| (lf..hf).include?(f.to_f) }.size )
  end
  return res
end


# convert absolute power values to relative 'weight' of each point
#
def normalize(data)
  return [] if data.empty?
  min_power = max_power = data[0][:spectrum][0]
  data.each do |dp|
    min_power = [min_power, dp[:spectrum].min].min
    max_power = [max_power, dp[:spectrum].max].max
  end
  puts "minmax #{min_power} #{max_power}"
  #edited to * 10 instead of *100
  data.map{|dp| dp[:spectrum] = dp[:spectrum].map{|dsp| (10*(dsp - min_power)/max_power).round(1)}; dp}
end


# distance in meters between two points on Earth
#
def distance(p1, p2)
  a = [p1[:lat], p1[:lon]]
  b = [p2[:lat], p2[:lon]]

  rad_per_deg = Math::PI/180  # PI / 180
  rkm = 6371                  # Earth radius in kilometers
  rm = rkm * 1000             # Radius in meters

  dlon_rad = (b[1]-a[1]) * rad_per_deg  # Delta, converted to rad
  dlat_rad = (b[0]-a[0]) * rad_per_deg

  lat1_rad, lon1_rad = a.map! {|i| i * rad_per_deg }
  lat2_rad, lon2_rad = b.map! {|i| i * rad_per_deg }

  a = Math.sin(dlat_rad/2)**2 + Math.cos(lat1_rad) * Math.cos(lat2_rad) * Math.sin(dlon_rad/2)**2
  c = 2 * Math::atan2(Math::sqrt(a), Math::sqrt(1-a))
  rm * c # Delta in meters
end


# true, если point находится дальше от всех точек accepted, чем meters
def farther_than(meters, accepted, point)
  accepted.reverse.find{|p| distance(p, point) < meters}.nil?
end



res = {
  bands: BAND_LOWER_FREQ,
  band_width: BAND_WIDTH,
  points: normalize(load_data),
}
OPEN_OUT.puts res.to_json
OPEN_OUT.close
