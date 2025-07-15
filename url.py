from fastapi import APIRouter
from pydantic import BaseModel
from fastapi.responses import JSONResponse

router = APIRouter()

class SiteUrlRequest(BaseModel):
    siteUrl: str

@router.post("/url/", tags=["url"])
def get_url(siteUrl: SiteUrlRequest): 
    """
    사이트 URL을 받아 리소스를 지정 폴더에 다운로드
    INPUT : 사이트 URL 
    OUTPUT : "unique_id#0" 반환
    """
    
    rd = ResourcesDownload(siteUrl.siteUrl)
    is_error, err_msg = rd.examine_url()
    time_info = rd.set_time()
    rd.make_folder(time_info)
    
    if not is_error: 
        rd.get_resources()
        folder_name = rd.return_unique_id()
        return JSONResponse(content = {"folder_name":folder_name})
    print(err_msg)


import os
import json
import time
import base64
import datetime
import requests
from selenium import webdriver
from urllib.parse import urlparse
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class ResourcesDownload:
    def __init__(self, url):
        self.url = url
        self.parsed = urlparse(self.url)
        self.unique_id = ""

    def examine_url(self):
        if self.parsed.scheme not in ["http", "https"] or not self.parsed.netloc:
            return True, "URL 형식이 올바르지 않습니다."
        try:
            response = requests.head(self.url, timeout=5)
            print(response.status_code)
            if response.status_code == 404:
                return True, "존재하지 않는 사이트입니다."
        except:
            return True, "문제가 발생했습니다."
        return False, ""
    
    def set_time(self):
        present_time = datetime.datetime.now()
        time_to_str = str(present_time).replace('-','').replace(' ','').replace(':','').replace('.','')
        time_to_hex = hex(int(time_to_str)).removeprefix('0x')
        return str(time_to_hex)
    
    def make_folder(self, time_to_hex):
        url = self.parsed.netloc.replace('.','_')
        self.unique_id = f"{url}_{time_to_hex}#0"
        os.makedirs(self.unique_id, exist_ok=True)
    
    def get_resources(self):
        
        options = Options()
        options.add_argument("--headless=chrome")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--ignore-ssl-errors")
        options.add_argument("--ignore-certificate-errors-spki-list")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--disable-web-security")
        options.add_argument("--accept-insecure-certs")
        options.add_argument("--user-agent=Mozilla/5.0")
        options.add_experimental_option("useAutomationExtension", False)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        options.set_capability('acceptInsecureCerts', True)
        options.page_load_strategy = 'eager'

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.execute_cdp_cmd('Network.enable', {})
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": "Mozilla/5.0"})
        
        print(f"접속 중: {self.url}")
        driver.get(self.url)
        time.sleep(3)

        with open(f"{self.unique_id}/index.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)

        resources = {
            p['requestId']: p['response']
            for log in driver.get_log('performance')
            if (msg := json.loads(log['message'])['message'])['method'] == 'Network.responseReceived'
            and (p := msg['params'])
        }

        for rid, res in resources.items():
            try:
                resp = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': rid})
                name = os.path.basename(urlparse(res['url']).path) or f"file_{hash(res['url']) % 1000}"
                ext = '.js' if 'javascript' in res.get('mimeType', '') else '.css' if 'css' in res.get('mimeType', '') else ''
                name = name + ext if '.' not in name and ext else name
                save_path = os.path.join(self.unique_id, name)
                with open(save_path, 'wb' if resp.get('base64Encoded') else 'w',
                            encoding=None if resp.get('base64Encoded') else 'utf-8') as f:
                    f.write(base64.b64decode(resp['body']) if resp.get('base64Encoded') else resp['body'])
                print(f"저장됨: {name}")
            except:
                pass

        driver.quit()
        print(f"리소스 다운로드가 완료되었습니다: {self.unique_id}\n")
    
    def return_unique_id(self):
        return self.unique_id
