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


# Sync system time to NTP 
# Note: this code requires super-user privilege 
def sync_system_time():
    try:
        client = ntplib.NTPClient()
        response = client.request('pool.ntp.org')
        os.system('date ' + time.strftime('%m%d%H%M%Y.%S',time.localtime(response.tx_time)))
    except:
        print('Could not sync with time server.')


class Blinkt:
    def __init__(self, max_brightness):
        self.turned_on = False
        self.max_brightness = max_brightness
        self.hue_start = 0 
        self.hue_end = 60
        blinkt.set_clear_on_exit()
        blinkt.clear()
        blinkt.show()


    def sleep_led_on(self):
        print('ON')
        blinkt.set_brightness(self.max_brightness)
        hue = self.hue_start + (((self.hue_end - self.hue_start) / float(blinkt.NUM_PIXELS)) * 2)
        r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(hue/360.0, 1.0, 1.0)]
        blinkt.set_all(r, g, b)
        blinkt.show()
        self.turned_on = True


    def sleep_led_off(self):
        print('OFF')
        blinkt.clear()
        blinkt.show()
        self.turned_on = False 


    def set_max_brightness(self, max_brightness):
        self.max_brightness = max_brightness


    def set_hue_start(self, hue_start):
        self.hue_start = hue_start


    def set_hue_end(self, hue_end):
        self.hue_end = hue_end


class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer = None
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.next_call = time.time()


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


class HourMinute:
    def __init__(self, hour, min):
        self.hour = hour 
        self.min = min


    # Convert UTC datetime string to local time 
    def utc_to_local(self, utc_str):
        format = '%H:%M:%S %p'

        # Get current time 
        now = time.localtime() 
        # Check whether day light saving is in effect.
    
        dst = now.tm_isdst # localtime() returns a tuple

        # Create datetime object in local timezone 
        dt_utc = datetime.strptime(utc_str, format)
        dt_utc = dt_utc.replace(tzinfo = pytz.UTC)

        # Get local timezone 
        local_tz = get_localzone()

        # Convert timezone of datetime from UTC to local 
        dt_local = dt_utc.astimezone(local_tz)

        self.hour = dt_local.hour + dst
        self.min = dt_local.minute


class SunriseSunsetTime:
    def __init__(self, lat, lng):
        self.sunrise = HourMinute(6, 0)
        self.sunset = HourMinute(18, 0)
        self.lat = lat 
        self.lng = lng 
        self.fetch()


    def fetch(self):
        api_url = 'https://api.sunrise-sunset.org/json?lat={}&lng={}%date=today'.format(self.lat, self.lng)
        response = requests.get(api_url)
        json_response = json.loads(response.text)
        if json_response['status'] == 'OK':
            sunrise_time = json_response['results']['sunrise']
            sunset_time = json_response['results']['sunset']

            self.sunrise.utc_to_local(sunrise_time)
            self.sunset.utc_to_local(sunset_time)

            print ("Today's sunrise at {:0>2}:{:0>2}".format(self.sunrise.hour, self.sunrise.min))
            print ("         sunset at {:0>2}:{:0>2}".format(self.sunset.hour, self.sunset.min))
        else: 
            print ('Error in getting sunrise and sunset time')


class SunsetTimer:
    def __init__(self, interval):
        self.interval = interval 
        self.blinkt = Blinkt(0.5)
        self.last_check_hour = 0 
        self.last_check_min = 0
        self.current_pos_lat = 0 
        self.current_pos_lng = 0 
        self.get_location_info()
        self.sunrise_sunset_time = SunriseSunsetTime(self.current_pos_lat, self.current_pos_lng)
        self.rt = RepeatedTimer(self.interval, self.check_time)


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
    def ip_geolocation_info(self, addr=''):
        if addr == '':
            url = 'https://ipinfo.io/json'
        else:
            url = 'https://ipinfo.io/' + addr + '/json'

        res = requests.get(url)
        data = json.loads(res.text)

        return data 


    def get_location_info(self):
        # Get public IP address 
        ip = requests.get('https://api.ipify.org').text
        print('My public IP address is: {}'.format(ip))

        # Get current location using the public IP address 
        geoloc_data = self.ip_geolocation_info(ip)

        # Print a few geolocation data
        print('******** Geo-Location Info ********')
        print('Country',' '*13+'\t->\t', geoloc_data['country'])
        print('Region',' '*13+'\t->\t', geoloc_data['region'])
        print('City',' '*13+'\t->\t', geoloc_data['city'])

        # Latitude and longitude
        lat_lng = geoloc_data['loc']
        lat_lng.index(',')
        self.current_pos_lat = lat_lng[:lat_lng.index(',')]
        self.current_pos_lng = lat_lng[lat_lng.index(',')+1:]
        print('Latitude',' '*13+'\t->\t', self.current_pos_lat)
        print('Longitude',' '*13+'\t->\t',self.current_pos_lng)


    def is_lighting_needed(self, now):
        current_h = now.tm_hour 
        current_m = now.tm_min 

        if current_h < self.last_check_hour:
            self.sunrise_sunset_time.fetch()

        sunrise_h = self.sunrise_sunset_time.sunrise.hour 
        sunrise_m = self.sunrise_sunset_time.sunrise.min  

        sunset_h = self.sunrise_sunset_time.sunset.hour 
        sunset_m = self.sunrise_sunset_time.sunset.min  

        if current_h < sunrise_h or sunset_h < current_h:
            return True 

        if ((current_h == sunrise_h and current_m < sunrise_m) or (current_h == sunset_h and sunset_m < current_m)):
            return True 

        self.last_check_hour = current_h 
        self.last_check_min = current_m

        return False 


    def check_time(self):
        # Get current date and time 
        now = datetime.now().timetuple()
        print("now = {:0>2}:{:0>2}:{:0>2}".format(now.tm_hour, now.tm_min, now.tm_sec))

        if self.is_lighting_needed(now):
            self.blinkt.sleep_led_on()
        else:
            self.blinkt.sleep_led_off()


    def update_sunrise_sunset(self):
        self.sunrise_sunset_time.fetch()


    def start(self):
        self.rt.start()


    def stop(self):
        self.rt.stop()



if __name__ == '__main__':
    sync_system_time()
    timer = SunsetTimer(60)

    try:
        timer.start()
        while True:
            time.sleep(1)
    finally:
        timer.stop() # better in a try/finally block to make sure the program ends!

