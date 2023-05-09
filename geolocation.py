import json
import requests

def ip_info(addr=''):
    if addr == '':
        url = 'https://ipinfo.io/json?token=d68e5853d12b66'
    else:
        url = 'https://ipinfo.io/' + addr + '/json?token=d68e5853d12b66'

    res = requests.get(url)
    data = json.loads(res.text)

    for attr in data.keys():
        print(attr,' '*13+'\t->\t',data[attr])


ip_info()
