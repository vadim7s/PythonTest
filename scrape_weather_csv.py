import requests


filename = 'test_weather.csv'
link = 'http://www.bom.gov.au/climate/dwo/202203/html/IDCJDW3050.202203.shtml'
data = requests.get(link)  # request the link, response 200 = success


with open(filename, 'wb') as f:
    f.write(data.content)  # write content of request to file
f.close()