#!/usr/bin/env python
# coding: utf-8

# In[31]:


from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

from bs4 import BeautifulSoup as bs

from datetime import timedelta
import time
import threading 
import _thread as thread

import os
import platform
import sys
import csv


import smtplib
from email.message import EmailMessage as EmailMessage

import logging as log


# In[32]:


#-------------------------------------
#         System Methods
#------------------------------------- 
# def log(message, logLevel='info', exception=None):
#     pass

#-------------------------------------
#         Selection Methods
#-------------------------------------
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

def getSelectionPropValue(soup, cssSelection, property='', index = 0):
    selection = getSelectionIfExists(soup, cssSelection, index)
    if selection is None:
        log.debug (f'Selection not found. Selection: {cssSelection}')
        return ''
    
    try:
        return selection[property]
    except:
        log.debug(f'Property not found. Selection: {cssSelection}')
        return ''
    
#-------------------------------------
#         General
#-------------------------------------      
    
class Listing:
  def __init__(self, store, listName = '', price = '', listingUrl='', fulfillmentSummary='', cartButtonText='', skuValue='', skuId=''):
    
    self.store = store
    self.listName = listName
    self.price = price
    self.listingUrl = listingUrl
    self.fulfillmentSummary = fulfillmentSummary
    self.cartButtonText = cartButtonText
    self.skuValue = skuValue
    self.skuId = skuId

def getProductDicts():
    productList = []
    input_file = csv.DictReader(open("products.csv"))
    for row in input_file:
        productList.append(dict(row))

    return productList

#-------------------------------------
#         Best Buy Specific Methods
#-------------------------------------  

def getBestBuySite(url: str):
    hasLeadingSlash = url.startswith('/')
    url = '/' + url if not hasLeadingSlash else url
    return f'https://www.bestbuy.com{url}' 

def getDataFromListingSoups_bestbuy(soup):
    result = {}
    name = getSelectionText(soup,'h4[class="sku-header"] > a')
    listingUrl = getBestBuySite(getSelectionPropValue(soup, 'h4[class="sku-header"] > a','href'))
    fulfillmentSummary = getSelectionText(soup, 'div[class="fulfillment-fulfillment-summary"]')
    addToCartText = getSelectionText(soup, 'button[class*="add-to-cart-button"]')
    skuValue = getSelectionText(soup, 'span[class*="sku-value"]', index=1)
    skuId = soup['data-sku-id']
    

    price = getSelectionText(soup, 'span[class="sr-only"]').split('$')[-1]
    return Listing(BESTBUY_STORE, name, price, listingUrl, fulfillmentSummary, addToCartText, skuValue, skuId)

#Function to see any listing is sold out
def getListingsInStock(listingsList):   #Fix typing here?
    return list(filter(lambda l: l.cartButtonText.lower() == 'add to cart', listingsList))

#-------------------------------------
#         General Methods
#------------------------------------- 

#Process Data then send email
def getListingData(store, listings):
    log.info('Parsing data from listings in page')
    
    listingList = []

    if store == BESTBUY_STORE:
        for l in listings:
            data = getDataFromListingSoups_bestbuy(l)
            listingList.append(data)
        
#         For Testings
        # listingList.append(Listing(BESTBUY_STORE, 'Test PS5', '599.99', 'facebook.com', 'we got it', 'Add To Cart', 'randomNumber', 'anotherRandomNumer'))

    else:
        return None
    
    return listingList


#Function to make email notification
def getEmailMessageForInStockItem(listing: Listing): 
    msg = EmailMessage()
    msg['Subject'] = f'{listing.listName} in stock! @ {listing.store.capitalize()}'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = EMAIL_ADDRESS
    msg.set_content(f'listing URL is here: {listing.listingUrl}')
    return msg

#Function to send email
def sendEmail(listing: Listing, message, debug = True):
    log.info(f'Sending Email Notification for {listing.listName}')
    mailServer = 'localhost' if debug else 'smtp.gmail.com'
    mailServerPort = '25' if debug else '465'
    
    try:
        if debug:
            with smtplib.SMTP(mailServer, mailServerPort) as smtp:
                smtp.login(EMAIL_ADDRESS, PASSWORD)
                smtp.send_message(message)
        else:
            with smtplib.SMTP_SSL(mailServer, mailServerPort) as smtp:
                smtp.login(EMAIL_ADDRESS, PASSWORD)
                smtp.send_message(message)
        log.info('Email Sent')
        
    except BaseException as err:
        log.error(f'Something wrong happened when sending notication')

def processListingData(listings: list):
    if listings == None or len(listings) == 0:
        log.info('No listings found.')
        return
    log.info(f'{len(listings)} listing(s) found')
    
    listingsInStock = getListingsInStock(listings)
    log.info(f'{len(listingsInStock)} listing(s) in stock')
    
    if(len(listingsInStock) > 0):
        for l in listingsInStock:
            message = getEmailMessageForInStockItem(l)
            sendEmail(l, message, False)
            # sendEmail(l, message)
    
    listingFight = {}
    listingFight['listingCount'] = len(listings)
    listingFight['listingsInStock'] = len(listingsInStock)
    
    return listingFight

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

    
def recycleDriver(driver):
    log.info('Quiting driver')
    try:
        driver.close()
        driver.quit()
    except BaseException as err:
        log.error(f'Quiting driver fail => {err.args[0]}')

    driver = None
    
    
def has_connection(driver):
    try:
        driver.find_element_by_xpath('//span[@jsselect="heading" and @jsvalues=".innerHTML:msg"]')
        return False
    
    except: 
        return True

def logRunReport(reportDict, storeInfoDict,timeElapsed):
    if reportDict is not None:
        log.info(f"Run report => Store: {storeInfoDict['store']} Product: {storeInfoDict['product']} ListingsFound: {reportDict['listingCount']} In-Stock {reportDict['listingsInStock']}")
    log.info(f'Run time => {str(timedelta(seconds=timeElapsed))}')

def runScrapForSearchUrl(storeInfoDict):
    runCounter = 0
    while storeInfoDict['stop'] is False:
        runCounter += 1
        try:
            if navigateToPage(storeInfoDict['driver'],storeInfoDict['url']) is False:
                url = storeInfoDict['url']
                log.error(f'Unable to navigate to page, {url}')
                raise BaseException('Recyclng....')

            pageSoup = bs(storeInfoDict['driver'].page_source, 'html.parser')
            listings = pageSoup.find_all('li', {"class": "sku-item"})
            data = getListingData(storeInfoDict['store'], listings)
            reportDict = processListingData(data)
            logRunReport(reportDict, storeInfoDict)

            WebDriverWait(storeInfoDict['driver'], 30, poll_frequency=30, ignored_exceptions=None)

        except BaseException as err:
            log.error(f'Something happened. => {err.args[0]}')
            recycleDriver(storeInfoDict['driver'])
            storeInfoDict['driver'] = getDriver()
    
    log.error('Stop called..')
    recycleDriver(storeInfoDict['driver'])
    log.info(f'Exiting Thread for {storeInfoDict["product"]}')



# In[ ]:


#Worker functions
def doWork_Threads(searchInfos):
    threads = []
    for info in searchInfos:
        info['stop'] = False
        product = info['product']
        store = info['store']

        log.info(f'Getting driver for {product} => {store}')
        info['driver'] = getDriver()
        log.info(f'Starting thread for {product} => {store}')
        thread = threading.Thread(target=runScrapForSearchUrl, args=(info,))
        threads.append(thread)
        thread.start()

    while True:
        try:
            log.info('Things are going well..')
            time.sleep(5)
        except KeyboardInterrupt:
            for info in searchInfos:
                info['stop'] = True
            break

    for t in threads:
        t.join()


def doWork_Single(searchInfos):
    runCounter = 0
    driver = getDriver()
    while True:
        try:
            startTime = time.time()

            indexForSearch = runCounter % len(searchInfos)
            storeInfoDict = searchInfos[indexForSearch]

            if navigateToPage(driver,storeInfoDict['url']) is False:
                    url = storeInfoDict['url']
                    log.error(f'Unable to navigate to page, {url}')
                    raise BaseException('Recyclng....')

            pageSoup = bs(driver.page_source, 'html.parser')
            listings = pageSoup.find_all('li', {"class": "sku-item"})
            data = getListingData(storeInfoDict['store'], listings)
            reportDict = processListingData(data)

            endTime = time.time()

            logRunReport(reportDict,storeInfoDict, endTime-startTime)
            
            runCounter += 1
            WebDriverWait(driver, 30, poll_frequency=30, ignored_exceptions=None)

        except KeyboardInterrupt:
            log.Error('Stop Called')
            recycleDriver(driver)
    
        except BaseException as err:
            log.exception(f'Something happened. => {err.args[0]}')
            recycleDriver(driver)
            driver = getDriver()

# In[ ]:


#Configuring Logging
log.basicConfig(format='%(asctime)s => %(levelname)s => %(funcName)s => %(message)s', filename='log.log', level=log.INFO)

#Constants
isWindows = 'windows' in platform.platform().lower() 
DRIVER_FILE_NAME = 'chromedriver.exe' if isWindows else '/usr/lib/chromium-browser/chromedriver'
DRIVER_FILE_PATH = os.path.join(os.getcwd(), DRIVER_FILE_NAME)
BESTBUY_STORE = 'best_buy'

EMAIL_ADDRESS = os.environ.get('G_USE')
PASSWORD = os.environ.get('G_PASS')

searchInfos = getProductDicts()

# doWork_Threads(searchInfos)
doWork_Single(searchInfos)

log.info('Exiting program')


# In[ ]:


# #Kill
# raise KeyboardInterrupt


# In[ ]:




