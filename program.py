#!/usr/bin/env python
# coding: utf-8

# # Operation PS5

# In[25]:


from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

from bs4 import BeautifulSoup as bs

import time
import _thread as thread

import os
import platform

import smtplib
from email.message import EmailMessage as EmailMessage

import logging as log


# In[26]:


#Configuring Logging
log.basicConfig(format='%(asctime)s => %(levelname)s => %(funcName)s => %(message)s', filename='log.log', level=log.INFO)

#Constants
isWindows = 'windows' in platform.platform().lower() 
DRIVER_FILE_NAME = 'chromedriver.exe' if isWindows else '/usr/lib/chromium-browser/chromedriver'
DRIVER_FILE_PATH = os.path.join(os.getcwd(), DRIVER_FILE_NAME)

EMAIL_ADDRESS = os.environ.get('G_USE')
PASSWORD = os.environ.get('G_PASS')

BESTBUY_STORE = 'best_buy'
BESTBUY_PS5 = {'store': BESTBUY_STORE, 'product': 'Playstation 5', 'url': 'https://www.bestbuy.com/site/playstation-5/ps5-consoles/pcmcat1587395025973.c?id=pcmcat1587395025973'}
BESTBUY_XBOX_X = {'store': BESTBUY_STORE,'product' : 'Xbox X', 'url' : 'https://www.bestbuy.com/site/searchpage.jsp?_dyncharset=UTF-8&browsedCategory=pcmcat1586900952752&id=pcat17071&iht=n&ks=960&list=y&qp=modelfamily_facet%3DModel%20Family~Xbox%20Series%20X&sc=Global&st=categoryid%24pcmcat1586900952752&type=page&usc=All%20Categories'} 

# In[3]:


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
#         Classes
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

    if store is BESTBUY_STORE:
        for l in listings:
            data = getDataFromListingSoups_bestbuy(l)
            listingList.append(data)
        
#         For Testings
#         listingList.append(Listing(BESTBUY_STORE, 'Test PS5', '599.99', 'facebook.com', 'we got it', 'Add To Cart', 'randomNumber', 'anotherRandomNumer'))

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
#             sendEmail(l, message, False)
            sendEmail(l, message)
    
    listingFight = {}
    listingFight['listingCount'] = len(listings)
    listingFight['listingsInStock'] = len(listingsInStock)
    
    return listingFight

def getDriver(driver = None):
    if driver is None:
        try:
            log.info(f'Chrome Driver Path is {DRIVER_FILE_PATH}')
            chromeOptions = webdriver.ChromeOptions()
            chromeOptions.add_argument('--no-sandbox')
            chromeOptions.add_argument('--headless')
            chromeOptions.add_argument('--disable-extensions')
            chromeOptions.add_argument('--disable-gpu')
            chromeOptions.add_argument('--disable-dev-shm-usage')
            driver = webdriver.Chrome(executable_path=DRIVER_FILE_PATH, chrome_options=chromeOptions)

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
    
def runScrapForSearchUrl(storeInfoDict):
    runCounter = 0
    while 0 < 1337:
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
            listingCount = reportDict['listingCount']
            listingsInStock = reportDict['listingsInStock']
            product = storeInfoDict['product']
            store = storeInfoDict['store']

            
            log.info(f'Run report => Store: {store} Product: {product} ListingsFound: {listingCount} In-Stock {listingsInStock}')
                     
            WebDriverWait(storeInfoDict['driver'], 30, poll_frequency=30, ignored_exceptions=None)

        except BaseException as err:
            log.error(f'Something happened. => {err.args[0]}')
            recycleDriver(storeInfoDict['driver'])
            storeInfoDict['driver'] = getDriver()




# In[4]:

searchDict = [BESTBUY_PS5,BESTBUY_XBOX_X]

# In[6]:

threadList = []
for info in searchDict:
    product = info['product']
    store = info['store']
    log.info(f'Getting driver for {product} => {store}')
    info['driver'] = getDriver()

    log.info(f'Starting thread for {product} => {store}')
    thread.start_new_thread(runScrapForSearchUrl, (info,))


