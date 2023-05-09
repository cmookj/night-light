import json 
import os 
import pytz 
import time
import threading

import requests 
import ntplib

from datetime import datetime
from tzlocal import get_localzone # $ pip install tzlocal

import colorsys
import blinkt

blinkt.set_clear_on_exit()
max_brightness = 0.4
steps = 20
duration = 5

blinkt.clear()
start = 0
end = 60
turned_on = False

def sleep_led_on():
    print('ON')

    if turned_on == False:
        for i in range(steps):
            blinkt.set_brightness(max_brightness / steps * i)
            hue = start + (((end - start) / float(blinkt.NUM_PIXELS)) * 2)
            r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(hue/360.0, 1.0, 1.0)]
            blinkt.set_all(r, g, b)
            blinkt.show()
            time.sleep(duration / steps)
        turned_on = True


def sleep_led_off():
    print('OFF')
    blinkt.clear()
    blinkt.show()
    turned_on = False


class repeated_timer(object):
  def __init__(self, interval, function, *args, **kwargs):
    self._timer = None
    self.interval = interval
    self.function = function
    self.args = args
    self.kwargs = kwargs
    self.is_running = False
    self.next_call = time.time()
    self.start()

  def _run(self):
    self.is_running = False
    self.start()
    self.function(*self.args, **self.kwargs)

  def start(self):
    if not self.is_running:
      self.next_call += self.interval
      self._timer = threading.Timer(self.next_call - time.time(), self._run)
      self._timer.start()
      self.is_running = True

  def stop(self):
    self._timer.cancel()
    self.is_running = False


# Convert UTC datetime string to local time 
def utc_to_local_hm(utc_str):
    format = '%H:%M:%S %p'

    # Get current time 
    now = time.localtime() 
    # Check whether day light saving is in effect.
  
    dst = now.tm_isdst # localtime() returns a tuple

    # Create datetime object in local timezone 
    dt_utc = datetime.strptime(utc_str, format)
    dt_utc = dt_utc.replace(tzinfo = pytz.UTC)

    print ('Datetime in UTC time zone: ', dt_utc)

    # Get local timezone 
    local_tz = get_localzone()

    # Convert timezone of datetime from UTC to local 
    dt_local = dt_utc.astimezone(local_tz)
    # print ('Datetime in Local time zone: ', dt_local)

    # local_time_str = dt_local.strftime(format)
    # print ('Time as string in local time zone', local_time_str)

    local_time_h = dt_local.hour + dst
    local_time_m = dt_local.minute

    return local_time_h, local_time_m


# ip_geolocation_info
#
# Example output of this function
#   ip              	->	 72.193.74.9
#   hostname        	->	 ip72-193-74-9.lv.lv.cox.net
#   city            	->	 Las Vegas
#   region          	->	 Nevada
#   country         	->	 US
#   loc             	->	 36.1750,-115.1372
#   org             	->	 AS22773 Cox Communications Inc.
#   postal          	->	 89111
#   timezone        	->	 America/Los_Angeles
#
def ip_geolocation_info(addr=''):
    if addr == '':
        url = 'https://ipinfo.io/json'
    else:
        url = 'https://ipinfo.io/' + addr + '/json'

    res = requests.get(url)
    data = json.loads(res.text)

    return data 


def get_sunrise_sunset_time(api_url):
    response = requests.get(api_url)
    json_response = json.loads(response.text)
    if json_response['status'] == 'OK':
        sunrise_time = json_response['results']['sunrise']
        sunset_time = json_response['results']['sunset']

        sunrise_h, sunrise_m = utc_to_local_hm(sunrise_time)
        sunset_h, sunset_m = utc_to_local_hm(sunset_time)
    else: 
        print ('Error in getting sunrise and sunset time')

    return sunrise_h, sunrise_m, sunset_h, sunset_m


def is_lighting_needed(now, sunrise_h, sunrise_m, sunset_h, sunset_m):
    current_h = now.tm_hour 
    current_m = now.tm_min 

    if current_h < sunrise_h or sunset_h < current_h:
        return True 

    if ((current_h == sunrise_h and current_m < sunrise_m) or (current_h == sunset_h and sunset_m < current_m)):
        return True 

    return False 


def check_time():
# Get current date and time 
    now = datetime.now().timetuple()
    print("now = {:0>2}:{:0>2}:{:0>2}".format(now.tm_hour, now.tm_min, now.tm_sec))

    if is_lighting_needed(now, sunrise_h, sunrise_m, sunset_h, sunset_m):
        sleep_led_on()
    else:
        sleep_led_off()

def forever():
    while True:
        time.sleep(1)


# Sync system time to NTP 
# Note: this code requires super-user privilege 
try:
    client = ntplib.NTPClient()
    response = client.request('pool.ntp.org')
    os.system('date ' + time.strftime('%m%d%H%M%Y.%S',time.localtime(response.tx_time)))
except:
    print('Could not sync with time server.')


# Get public IP address 
ip = requests.get('https://api.ipify.org').text
print('My public IP address is: {}'.format(ip))

# Get current location using the public IP address 
geoloc_data = ip_geolocation_info(ip)

# Print a few geolocation data
print('******** Geo-Location Info ********')
print('Country',' '*13+'\t->\t',geoloc_data['country'])
print('Region',' '*13+'\t->\t',geoloc_data['region'])
print('City',' '*13+'\t->\t',geoloc_data['city'])

# Latitude and longitude
lat_lng = geoloc_data['loc']
lat_lng.index(',')
current_pos_lat = lat_lng[:lat_lng.index(',')]
current_pos_lng = lat_lng[lat_lng.index(',')+1:]
print('Latitude',' '*13+'\t->\t',current_pos_lat)
print('Longitude',' '*13+'\t->\t',current_pos_lng)

# Get today's sunrise and sunset time
api_url = 'https://api.sunrise-sunset.org/json?lat={}&lng={}%date=today'.format(current_pos_lat, current_pos_lng)
sunrise_h, sunrise_m, sunset_h, sunset_m = get_sunrise_sunset_time(api_url)
print ("Today's sunrise at {}:{}".format(sunrise_h, sunrise_m))
print ("         sunset at {}:{}".format(sunset_h, sunset_m))

rt = repeated_timer(30, check_time) # it auto-starts, no need of rt.start()
try:
    forever()
finally:
    rt.stop() # better in a try/finally block to make sure the program ends!
