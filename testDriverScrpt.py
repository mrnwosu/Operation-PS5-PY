from selenium import webdriver
import os
import platform
import csv
import logging as log
from bs4 import BeautifulSoup as bs
from pyfiglet import Figlet
import time
import sys

def getProductDicts():
    productList = []
    input_file = csv.DictReader(open("products.csv"))
    for row in input_file:
        productList.append(dict(row))

    return productList

def getDriver(driver = None):
    if driver is None:
        try:
            log.info(f'Chrome Driver Path is {DRIVER_FILE_PATH}')
            chromeOptions = webdriver.ChromeOptions()
            
            if '--no-sandbox' in sys.argv:
                chromeOptions.add_argument('--no-sandbox')
            
            if '--headless' in sys.argv:
                chromeOptions.add_argument('--headless')

            if '--disable-gpu' in sys.argv:
                chromeOptions.add_argument('--disable-gpu')
            
            if '--disable-extensions' in sys.argv:
                chromeOptions.add_argument('--disable-extensions')
            
            if '--disable-dev-shm-usage' in sys.argv:
                chromeOptions.add_argument('--disable-dev-shm-usage')

            driver = webdriver.Chrome(executable_path=DRIVER_FILE_PATH, chrome_options=chromeOptions)
            #driver = webdriver.Chrome(executable_path=DRIVER_FILE_PATH)

        except BaseException as err:
            log.error(f'Unable to stand up new driver => {err.args[0]}')
            raise
    
    return driver

def navigateToPage(driver, searchUrl):
    log.info(f'Navigating to {searchUrl[0:20]}...')
    try:
        driver.get(searchUrl)
        
    except BaseException as err:
        log.error(f'Driver navigation fail => {err.args[0]}')
        raise

def navigateToPage(driver, searchUrl):
    log.info(f'Navigating to {searchUrl[0:20]}...')
    try:
        driver.get(searchUrl)
        
    except BaseException as err:
        log.error(f'Driver navigation fail => {err.args[0]}')
        raise

def getSelectionIfExists(soup, cssSelection, index=0): 
    result = soup.select(cssSelection)
    if len(result) == 0 or property == None:
        return None
    
    try:
        return result[index]
    except:
        log.debug(f'Possibly out of range. Selection: {cssSelection}')

def getSelectionText(soup, cssSelection, property='', index = 0):
    selection = getSelectionIfExists(soup, cssSelection, index)
    return '' if selection is None else selection.text

def recycleDriver(driver):
    log.info('Quiting driver')
    try:
        driver.close()
        driver.quit()
    except BaseException as err:
        log.error(f'Quiting driver fail => {err.args[0]}')

    driver = None

def doTest(iDict: {}, product):
    newDriver = False
    if 'driver' not in iDict.keys():
        iDict['driver'] = getDriver()
        newDriver = True

    start = time.time()
    navigateToPage(iDict['driver'], product['url'])

    pageSoup = bs(iDict['driver'].page_source, 'html.parser')
    listings = pageSoup.find_all('li', {"class": "sku-item"})

    log.info(f'There are {len(listings)} from the results.')

    if len(listings) > 0:
        listingTitles = []
        for listing in listings:
            name = getSelectionText(listing,'h4[class="sku-header"] > a')
            log.info(f'Found {name}')
    end = time.time()
    timeElapsed = end - start
    if newDriver:
        log.info(f'Getting new driver plus first scrape time => {timeElapsed}')
    else:
        log.info(f'Driver exists scrape time => {timeElapsed}')


def banner(message):
    custom_fig = Figlet(font='graffiti')
    log.info(custom_fig.renderText(message))

log.basicConfig(format='%(asctime)s => %(levelname)s => %(funcName)s => %(message)s', filename='log.log', level=log.DEBUG)
banner('Driver Test.')


isWindows = 'windows' in platform.platform().lower() 
DRIVER_FILE_NAME = 'chromedriver.exe' if isWindows else '/usr/lib/chromium-browser/chromedriver'
DRIVER_FILE_PATH = os.path.join(os.getcwd(), DRIVER_FILE_NAME)
BESTBUY_STORE = 'best_buy'

products = getProductDicts()
log.debug(products)
try:
    driver = {} 
    for product in products:
        doTest(driver, product)
except:
    log.exception('Something happened')

recycleDriver(driver['driver'])
