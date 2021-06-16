import numpy as np
import cv2
import imutils
import pytesseract as tess
tess.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
import time

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

from googleapiclient.discovery import build
from google.oauth2 import service_account

image = cv2.imread('car2.jpg')

image = imutils.resize(image, width=500)
cv2.imshow("Original Image", image)

gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

gray = cv2.bilateralFilter(gray, 11, 17, 17)

edged = cv2.Canny(gray, 50, 200)

(new, cnts, _) = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:30]

NumberPlateCnt = None

count = 0
for c in cnts:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:  # Select the contour with 4 corners
            NumberPlateCnt = approx  # This is our approx Number Plate Contour
            break

cv2.drawContours(image, [NumberPlateCnt], -1, (0, 255, 0), 3)
cv2.imshow("Final Image With Number Plate Detected", image)

mask = np.zeros(gray.shape, np.uint8)
new_image = cv2.drawContours(mask, [NumberPlateCnt], 0, 255, -1)
new_image = cv2.bitwise_and(image, image, mask=mask)


config = ('-l eng --oem 1 --psm 3')

text = tess.image_to_string(new_image, config=config)


text = text.split('\n')
text = text[0]

print('Vehicle Number is:', text)

# Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

result = db.collection('info').document('C7jIqYsBCtFxmWh6eSEX').get()
result = result.to_dict()
result = result[text]

print('This Vehicle belongs to:', result)

date = time.asctime(time.localtime(time.time()))

# Spreadsheet
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

SERVICE_ACCOUNT_FILE = 'keys.json'

creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)

SPREADSHEET_ID = '1Ruun_PeIQmMNcGqyEOlF45sXVb2Ehpr6cPTS30qxzNY'

service = build('sheets', 'v4', credentials=creds)

sheet = service.spreadsheets()


i = 1
k = str(i)
loc = "info!A" + k
result1 = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=loc).execute()
values = result1.get('values')

while values is not None:
    i = i+1
    k = str(i)
    loc = "info!A" + k
    result11 = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=loc).execute()
    values = result11.get('values')

dtr = [[date, text, result]]

result2 = sheet.values().update(spreadsheetId=SPREADSHEET_ID,
                                range=loc, valueInputOption="USER_ENTERED", body={"values": dtr}).execute()

cv2.waitKey(0)
