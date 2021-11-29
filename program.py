# %%
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select

from bs4 import BeautifulSoup as bs

from datetime import timedelta
import time
import threading 
import _thread as thread

import random
import json
import os
import platform
import sys
import csv
from pydub import AudioSegment
from pydub.playback import play

import smtplib
from email.message import EmailMessage as EmailMessage

import logging as log


# %%
#-------------------------------------
#         System Methods
#------------------------------------- 

def playSound():
    # log.info('Playing Sound.')
    try:
        wd = os.getcwd()
        NOTIFICATION_FILE_PATH = f'{wd}\\assets\\youGotmail.wav'
        command = f'powershell -c (New-Object Media.SoundPlayer "{NOTIFICATION_FILE_PATH}").PlaySync()'
        os.system(command)
    except:
        # log.exception('Something wrong happened when playing sound')
        print('Something wrong happened./')

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
        log.debug(f'Unable to get index of selection: {cssSelection}. Index: {index}')
        return None

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
  def __init__(self, store, listName = '', price = '', listingUrl='', fulfillmentSummary='', cartButtonText='', skuValue='', skuId='', soup = None):
    
    self.store = store
    self.listName = listName
    self.price = price
    self.listingUrl = listingUrl
    self.fulfillmentSummary = fulfillmentSummary
    self.cartButtonText = cartButtonText
    self.skuValue = skuValue
    self.skuId = skuId
    self.soup = soup

def getEmailList() -> list:
    emailList = []
    with open('emailList.txt') as file:
        for line in file:
           emailList.append(line.rstrip())
    return emailList
        

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
    name = getSelectionText(soup,'h4[class="sku-header"] > a')
    listingUrl = getBestBuySite(getSelectionPropValue(soup, 'h4[class="sku-header"] > a','href'))
    fulfillmentSummary = getSelectionText(soup, 'div[class="fulfillment-fulfillment-summary"]')
    addToCartText = getSelectionText(soup, 'button[class*="add-to-cart-button"]')
    skuValue = getSelectionText(soup, 'span[class*="sku-value"]', index=1)
    skuId = soup['data-sku-id']
    
    price = getSelectionText(soup, 'span[class="sr-only"]').split('$')[-1]
    return Listing(BESTBUY_STORE, name, price, listingUrl, fulfillmentSummary, addToCartText, skuValue, skuId, soup)

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


def getEmailMessage_ItemInStock(listing: Listing): 
    log.info('Composing "Item in stock" message')
    msg = EmailMessage()
    msg['Subject'] = f'!!! {listing.listName} in stock! @ {listing.store.capitalize()}'
    msg['From'] = info['email']
    msg['To'] = info['email']
    msg.set_content(f'listing URL is here: {listing.listingUrl}')
    return msg

def getEmailMessagesForEmailList_ItemInStock(listing: Listing): 
    emailList = getEmailList()
    messages = []
    for email in emailList:
        log.info(f'Composing "Item in stock" message for "{email}"')
        msg = EmailMessage()
        msg['Subject'] = f'!!! {listing.listName} in stock! @ {listing.store.capitalize()}'
        msg['From'] = info['email']
        msg['To'] = email
        msg.set_content(f'listing URL is here: {listing.listingUrl}')
        messages.append(msg)
    return messages

def getEmailMessage_ItemPurchased(listing: Listing, buyResult: dict): #Successfully purchase. Will need confirmation number and etc.
    log.info('Composing "Item Purchased" message')
    msg = EmailMessage()
    msg['Subject'] = f'!!! {listing.listName} purchased from {listing.store.capitalize()}, {buyResult["order_number"]}'
    msg['From'] = info['email']
    msg['To'] = info['email']
    msg.set_content(f'{listing.listingUrl} Purchased! \n {buyResult["order_number"]} \n Order URL Here: {buyResult["order_status_url"]}') # Send Confirmation Number Here
    return msg

def getEmailMessage_ItemNotPurchase(listing: Listing):
    log.info('Composing "Item NOT Purchased" message')
    msg = EmailMessage()
    msg['Subject'] = f'!!! {listing.listName} unable to be purchase from {listing.store.capitalize()}'
    msg['From'] = info['email']
    msg['To'] = info['email']
    msg.set_content(f'listing URL is here: {listing.listingUrl}') # Maybe capture the exception and put here.
    return msg

def sendEmail(message, debug = True):
    log.info(f'Sending email with subject => {message["Subject"]}')
    mailServer = 'localhost' if debug else 'smtp.gmail.com'
    mailServerPort = '25' if debug else '465'
    
    try:
        if debug:
            with smtplib.SMTP(mailServer, mailServerPort) as smtp:
                smtp.login(info['email'], info['email_password'])
                smtp.send_message(message)
        else:
            with smtplib.SMTP_SSL(mailServer, mailServerPort) as smtp:
                smtp.login(info['email'], info['email_password'])
                smtp.send_message(message)
        log.info('Email Sent')
        
    except BaseException as err:
        log.error(f'Something wrong happened when sending notication')

def processListingData(driver, listings: list):
    if listings == None or len(listings) == 0:
        log.info('No listings found.')
        return
    log.info(f'{len(listings)} listing(s) found')
    
    listingsInStock = getListingsInStock(listings)
    log.info(f'{len(listingsInStock)} listing(s) in stock')
    
    if(len(listingsInStock) > 0):
        playSound()
        for l in listingsInStock:
            messages = getEmailMessagesForEmailList_ItemInStock(l)
            for m in messages:
                sendEmail(m, False)

            makeMoney(l.soup, driver, l)
            
    listingFight = {}
    listingFight['listingCount'] = len(listings)
    listingFight['listingsInStock'] = len(listingsInStock)
    
    return listingFight

def checkAndAddArguments(options):
    for arg in sys.argv:
        if arg.startswith('--'):
            log.info(f'Adding following argument :=> {arg}')
            options.add_argument(arg)
    options.add_argument('--disable-blink-features=AutomationControlled')
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


# %%
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
            reportDict = processListingData(driver, data)

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



# %%
def getElemSelector(driver, cssSelector):
    try:
        return WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, cssSelector))
    )
    except:
        return None 

def getElemId(driver, id):
    try:
        return WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, id))
    )
    except:
        return None 
    
def findElemBySelectorAndClick(driver, cssSelector):
    elem = getElemSelector(driver, cssSelector)
    elem.click()
    
def findElemByIdAndClick(driver, id):
    elem = getElemId(driver, id)
    elem.click()
    
def findElemBySelectorAndSendKeys(driver, cssSelector, text):
    elem = getElemSelector(driver, cssSelector)
    elem.clear()
    elem.send_keys(text)
    
def findElemByIdAndSendKeys(driver, id, text):
    elem = getElemId(driver, id)
    elem.send_keys(text)
    
def findSelectByIdAndSelect(driver,id,option):
    elem = getElemId(driver, id)
    select = Select(elem)
    select.select_by_visible_text(option)
    
def findSelectBySelectorAndSelect(driver,cssSelector,option):
    elem = getElemSelector(driver, cssSelector)
    select = Select(elem)
    select.select_by_visible_text(option)
    
def isProductInCart(driver):
    soup = bs(driver.page_source,'html.parser')
    dotSoup = soup.find('div', {'class':'dot'})
    if dotSoup is None:
        return False
    else:
        return True
    
#Check if successfully added
# Listing Try add to card 
def tryAddToCart(soup, driver, listingTitle = '') -> bool:
    log.warning(f'Adding {listingTitle} to cart')
    removeElementByClass(driver, 'blue-assist-tab')

    addToCartButtonSoup = soup.find('button', {'data-button-state':'ADD_TO_CART'})
    sku = addToCartButtonSoup['data-sku-id']

    attempt = 0
    while True:
        attempt += 1
        log.warning(f'Attempt {attempt}...')
        findElemBySelectorAndClick(driver, f'button[data-sku-id="{sku}"]')
        time.sleep(3)
        if isProductInCart(driver):
            log.warning('Added item to cart.')
            return True
        else:
            if attempt > 20:
                log.error(f'Unable to add item to cart => "{listingTitle}"')
                return False


def fillAddress(driver):
    print('Filling Billing/Shipping address')

    findElemBySelectorAndSendKeys(driver,'input[id$="firstName"]',info['first_name']) 
    findElemBySelectorAndSendKeys(driver,'input[id$="lastName"]',info['last_name']) 
    findElemBySelectorAndSendKeys(driver,'input[id$="street"]',info['address'])
    time.sleep(2)
    findElemBySelectorAndClick(driver, 'body') #Clearing autocomplete might need better solution
    time.sleep(2)
    findElemBySelectorAndClick(driver, 'button[class*="address-form__showAddress2Link"]')
    time.sleep(2)
    findElemBySelectorAndSendKeys(driver,'input[id$="street2"]',info['apt'])
    findElemBySelectorAndSendKeys(driver,'input[id$="city"]',info['city'])
    findSelectBySelectorAndSelect(driver,'select[id$="state"]', 'MD')
    findElemBySelectorAndSendKeys(driver,'input[id$="zipcode"]',info['zip'])

def fillContactInfo(driver):
    log.warning('Filling Contact info')
    findElemByIdAndSendKeys(driver,'user.emailAddress',info['email'])
    findElemByIdAndSendKeys(driver,'user.phone',info['phone_number'])

def selectCard(driver):
    log.warning('Selecting Card')
    findElemByIdAndSendKeys(driver,'optimized-cc-card-number',info['card_number'])
    time.sleep(1)
    findElemBySelectorAndClick(driver, 'section[class*="credit-card-form"] > div:nth-child(3) > div > div > button')
    time.sleep(1)
    try:
        findElemBySelectorAndClick(driver, 'label[class="reward-calculator__label"]')
    except:
        log.info('swallowing reward card selection')

def clickButtonForPaymentInformation(driver):
    log.warning('Continuing to payment information.')
    findElemBySelectorAndClick(driver,'div[class="button--continue"] > button') 

def clickButtonForShippingInstead(driver):
    findElemBySelectorAndClick(driver, 'div[class="streamlined__switch"] > a')

def purchaseSuccessfull(driver) -> bool:
    log.warning('Checking if purchase was succesfull')
    try:
        elem = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class="thank-you-enhancement__info-bd"]' ))
            )
        log.warning('Success')
        return True
    except:
        log.warning('Fail')
        return False

def getConfirmationDetails(driver) -> dict:
    log.warning('Getting dummy')
    # confirmationSoup = bs(driver.page_source, 'html.parser')
    d = {}
    d['arrival_date'] = 'Arrival Date' #getSelectionText(confirmationSoup, 'div[class="thank-you-enhancement__info-bd" > p > span[class="thank-you-enhancement__emphasis"')
    d['confirm_email'] = 'randomConfirmationEmail@mailinator.com' # getSelectionText(confirmationSoup, 'div[class="thank-you-enhancement__email-confirmation" > span[class="thank-you-enhancement__emphasis"')
    d['order_number'] = 'Order number: ' # getSelectionText(confirmationSoup, 'div[class="thank-you-enhancement__order-number" > span[class="thank-you-enhancement__emphasis"')
    d['order_status_url'] = 'This is an order status url' # getSelectionPropValue(confirmationSoup, 'div[class="thank-you-enhancement__order-number" > a"', 'href' )
    log.warning(f'Confirmation Details Here {d}')
    return d
    
def makePurchase(driver) -> dict:
    log.warning('!!!!!! BUYING THE THING.')
    findElemBySelectorAndClick(driver, 'button[data-track="Place your Order - Contact Card"')
    if purchaseSuccessfull(driver):
        return getConfirmationDetails(driver)
    else:
        return None

def getRandomWait(start: int, finish: int) -> int:
    return random.randrange(start,finish)

def consolidatedFill(driver):
    log.warning('Running Consolidated Flow')
    clickButtonForShippingInstead(driver)
    fillAddress(driver)
    fillContactInfo(driver)
    clickButtonForPaymentInformation(driver)
    selectCard(driver)
    return makePurchase(driver)

def normalFill(driver):
    log.warning('Running Normal Flow')
    clickButtonForShippingInstead(driver)
    fillAddress(driver)
    fillContactInfo(driver)
    clickButtonForPaymentInformation(driver)
    selectCard(driver)
    return makePurchase(driver)

def runScriptNoError(driver, script):
    try:
        driver.execute_script(script)
    except:
        log.exception('Running the script threw an exception. Oh no')
    
def removeElementByClass(driver, className):
    runScriptNoError(driver, f'return document.getElementsByClassName("{className}")[0].remove()')
    
def removeElementById(driver, id):
    runScriptNoError(driver, f'return document.getElementById("{id}").remove()')

#Either return None if unable to buy or confirmation summery 
def tryToBuy(driver) -> dict:
    try:
        log.warning('Navigating to cart')
        #Viewing Cart
        driver.get('https://www.bestbuy.com/cart')

        #Checking out 
        findElemBySelectorAndClick(driver, 'button[data-track="Checkout - Top"]')
        
        #Continuing as guest
        findElemBySelectorAndClick(driver, 'button[class*="cia-guest-content__continue"]')

        elem = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class="button--continue"] > button' ))
        )

        pageSoup = bs(driver.page_source, 'html.parser')
        if len(pageSoup.select('input[id^="consolidatedAddresses"]')) > 0:
            log.warning('Running consolidated flow.')
            return consolidatedFill(driver)
        else:
            log.warning('Running regular flow.')
            return normalFill(driver)
        
    except BaseException as err:
        log.exception('Something wrong happened when trying to purchase the item.')
        return None

def makeMoney(listingSoup, driver, listing):
    log.warn('TIME TO MAKE SOME MONEY')
    if tryAddToCart(listingSoup, driver, listing.listName):
        buyResult = tryToBuy(driver)
        if buyResult is not None: 
            message = getEmailMessage_ItemPurchased(listing, buyResult)
            sendEmail(message)
        else:
            message = getEmailMessage_ItemNotPurchase(listing)
            sendEmail(message)


# # %%
# #Configuring Logging
log.basicConfig(format='%(asctime)s: %(levelname)s: %(funcName)s => %(message)s', filename='log.log', level=log.INFO)

# #Constants
isWindows = 'windows' in platform.platform().lower() 
DRIVER_FILE_NAME = 'chromedriver.exe' if isWindows else '/usr/lib/chromium-browser/chromedriver'
DRIVER_FILE_PATH = os.path.join(os.getcwd(), DRIVER_FILE_NAME)
BESTBUY_STORE = 'best_buy'

NOTIFICATION_FILE_PATH = './assets/youGotmail.mp3'

info = json.loads(os.environ.get('G_INFO'))

searchInfos = getProductDicts()
doWork_Single(searchInfos)

# url = 'https://www.bestbuy.com/site/promo/cyber-monday-laptop-computer-deals-1?qp=systemmemoryram_facet%3DRAM~16%20gigabytes'
# driver = webdriver.Chrome(executable_path=DRIVER_FILE_PATH)
# driver.get(url)
# soup = bs(driver.page_source,'html.parser')
# listings = soup.select('li[class="sku-item"]')
# parsedListings = getListingData('best_buy', listings)
# firstListingSoup = listings[0]
# listingInQuestion = parsedListings[0]

# makeMoney(firstListingSoup, driver, listingInQuestion)
# %%



