from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from browsermobproxy import Server
import datetime
import httpx
import os
from moviepy.editor import VideoFileClip

URL = 'https://zoo.sandiegozoo.org/cams/ape-cam'

#Start proxy server
server = Server(os.path.realpath('./browsermob-proxy-2.1.4/bin/browsermob-proxy'))
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

filename = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")+'.mpeg'

fetched = []
try:
    while True:
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
                    
                with httpx.stream("GET", _url) as r1:
                    if(r1.status_code == 200 or r1.status_code == 206):
                        print(f"Downloading chunk...{_url[45:]}"+'\n')
            			
                        #Re-open output file to append new video
                        with open(f"./recordings/{filename}",'ab') as f:
                            data = b''
                            for chunk in r1.iter_bytes():
                                if(chunk):
                                    data += chunk
                            f.write(data)
                            fetched.append(_url)
                    else:
                        print(f"Received unexpected status code {r1.status_code}")
except KeyboardInterrupt:
    pass


def bytesto(bytes, to, bsize=1024): 
    a = {'k' : 1, 'm': 2, 'g' : 3, 't' : 4, 'p' : 5, 'e' : 6 }
    r = float(bytes)
    return bytes / (bsize ** a[to])

#Display length and size of file
clip = VideoFileClip(f"./recordings/{filename}")
print(f"Captured {'%.2f'%clip.duration} seconds of video ({'%.1f'%bytesto(os.path.getsize(os.path.realpath('./recordings/'+filename)), 'm')}MB)")

server.stop()
driver.quit()
