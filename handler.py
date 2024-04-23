import datetime
import logging
import pandas as pd
import boto3
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# https://sso.gtlconnect.com/users/sign_in
# email: hoku2dreamer@gmail.com
# pass: Il0vecat5!

def updateTickerSymbols(event, context):
	dynamoDBClient = boto3.client('dynamodb')


def dailyStockData(event, context):
	current_time = datetime.datetime.now().time()
	name = context.function_name
	logger.info("Your cron function " + name + " ran at " + str(current_time))

	tickers = getTickerSymbols(event, context) #QQQ, SPY, RSP, UWM, ^TNX, TLH, ^VIX
	stockDataFrames = []

	# for ticker in tickers:
	# 	stockDataFrames.append(getSiteData(f'https://finance.yahoo.com/quote/{ticker}/history', ticker))

	# print(pd.concat(stockDataFrames))
	

def getTickerSymbols(event, context):
	dynamoDBClient = boto3.client('dynamodb')
	data = dynamoDBClient.get_item(
		TableName='StockDataDB',
		Key={
			'ID': {
				'S': 'TickerDataRow'
			}
		}
	)

	print(data)
	print(data["Item"])
	print(data["Item"]["Tickers"])

	return data


def getSiteData(url, ticker):
	try:  
		print(url)

		options = Options()
		options.add_argument("-headless") 
		driver = webdriver.Firefox(options=options)
		driver.get(url)

		headers = {}

		dataTemplate = {
			'Open': [],
			'High': [],
			'Low': [],
			'Close': []
		}

		headerRow = WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.XPATH, '//*[@id="nimbus-app"]/section/section/section/article/div[1]/div[3]/table/thead/tr')));
		headerElements = headerRow.find_elements(By.TAG_NAME, 'th')

		for elem in range(len(headerElements)):
			if headerElements[elem].text in dataTemplate.keys():
				headers[headerElements[elem].text] = elem

		firstRow = driver.find_element(By.XPATH, '//*[@id="nimbus-app"]/section/section/section/article/div[1]/div[3]/table/tbody/tr[1]');
		rowData = firstRow.find_elements(By.TAG_NAME, 'td')

		for key in headers.keys():
			dataTemplate[key].append(rowData[headers[key]].text)
		
		return pd.DataFrame(dataTemplate, index=[ticker])

	except Exception as e:
		print('ERROR: ', e)
		return pd.DataFrame(dataTemplate, index=[ticker])
	finally:
		driver.close()