from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from browsermobproxy import Server
import os
import sys
import json
import time
import datetime
import requests
from moviepy.editor import VideoFileClip

URL = 'https://zoo.sandiegozoo.org/cams/ape-cam'

try:
    if sys.argv[1]:
        pass
except:
    print("Please add time argument")
    os.system("PAUSE")
    sys.exit()

#Start proxy server
server = Server('D:/Users/Aran/Desktop/programming/ape cam downloader/browsermob-proxy-2.1.4/bin/browsermob-proxy')
server.start()
proxy = server.create_proxy()

#Selenium arguments
options = webdriver.ChromeOptions()
options.add_argument('headless')
options.add_argument(f"--proxy-server={proxy.proxy}")

caps = DesiredCapabilities.CHROME.copy()
caps['acceptSslCerts'] = True
caps['acceptInsecureCerts'] = True

proxy.new_har("ape-cam",options={'captureHeaders': True,'captureContent':True,'captureBinaryContent': True})

driver = webdriver.Chrome('./chromedriver.exe', options=options, desired_capabilities=caps)
driver.get(URL)

#Time to wait before capture
print(f"\nWaiting to capture ~{sys.argv[1]} seconds of video\n")
proxy.wait_for_traffic_to_stop(10000, int(sys.argv[1])*1000)

filename = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")+'.mpeg'

fetched = []
for ent in proxy.har['log']['entries']:
    _url = ent['request']['url']
    _response = ent['response']
    
    #Make sure havent already downloaded this piece
    if _url in fetched:
        continue
        
    if _url.endswith('.ts'):
        #Check if this url had a valid response, if not, ignore it
        if 'text' not in _response['content'].keys() or not _response['content']['text']:
            continue
            
        
        r1 = requests.get(_url, stream=True)
        if(r1.status_code == 200 or r1.status_code == 206):
			print(_url+'\n')
			
            #Re-open output file to append new video
            with open(f"./recordings/{filename}",'ab') as f:
                data = b''
                for chunk in r1.iter_content(chunk_size=1024):
                    if(chunk):
                        data += chunk
                f.write(data)
                fetched.append(_url)
        else:
            print(f"Received unexpected status code {r1.status_code}")


clip = VideoFileClip(f"./recordings/{filename}")
print(f"Captured {clip.duration} seconds of video")

server.stop()
driver.quit()
