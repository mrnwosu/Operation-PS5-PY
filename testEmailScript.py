import smtplib
from email.message import EmailMessage as EmailMessage

import platform
import os
import logging as log
import sys


def sendEmail(message, debug = True):
    log.info(f'Sending Test Email')
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

def getEmailMessageForInStockItem(message='Test Message'): 
    msg = EmailMessage()
    msg['Subject'] = f'Test Message'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = EMAIL_ADDRESS
    msg.set_content(f'{message} from {platform.platform()}')
    return msg

EMAIL_ADDRESS = os.environ.get('G_USE')
PASSWORD = os.environ.get('G_PASS')

emailMessage = getEmailMessageForInStockItem()

if 'real' in sys.argv:
    sendEmail(emailMessage, False)
else:
    sendEmail(emailMessage)

