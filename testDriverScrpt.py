from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions

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

def checkAndAddArguments(options):
    for arg in sys.argv:
        if arg.startswith('--'):
            log.info(f'Adding following argument :=> {arg}')
            options.add_argument(arg)
    return options

def getOptions():
    options = None
    if '-chrome' in sys.argv:
        options = webdriver.ChromeOptions()
    
    elif '-firefox' in sys.argv:
        options = FirefoxOptions()
    else:
        raise BaseException('No Driver Selected')

    return checkAndAddArguments(options)

def getDriver(driver = None):
    if driver is None:
        try:
            options = getOptions()

            log.info(f'{options}')
            log.info(f'Driver arguments are {options.arguments}')
            
            if '-chrome' in sys.argv:
                log.info(f'Chrome Driver Path is {DRIVER_FILE_PATH}')
                driver = webdriver.Chrome(executable_path=DRIVER_FILE_PATH, options=options)
            
            elif '-firefox' in sys.argv:
                log.info('Using Geckodriver in PATH')
                driver = webdriver.Firefox(options=options)

        except BaseException as err:
            log.exception(f'Unable to stand up new driver => {err.args[0]}')
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

log.info(f'System arguments are as follows: {sys.argv}')

products = getProductDicts()
log.debug(products)
try:
    driver = {} 
    for product in products:
        doTest(driver, product)
except:
    log.exception('Something happened')

recycleDriver(driver['driver'])
