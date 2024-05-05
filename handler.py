import datetime
import logging
import pandas as pd
import boto3
import json
from tempfile import mkdtemp
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# https://sso.gtlconnect.com/users/sign_in
# email: hoku2dreamer@gmail.com
# pass: Il0vecat5!

def updateTickerSymbols(event, context):
	data = json.loads(event["body"])["tickers"]
	print(data)
	dynamoDBClient = boto3.client('dynamodb')
	dynamoDBClient.update_item(
		TableName='StockDataDB',
		Key={
			'ID': {
				'S': 'TickerDataRow'
			}
		},
		ExpressionAttributeNames={
				'#tickers': "Tickers"
		},
		ExpressionAttributeValues={
				':tickers': {
						'SS': data
				}
		},
		UpdateExpression='SET #tickers = :tickers'
	)

def dailyStockData(event, context):
	current_time = datetime.datetime.now().time()
	name = context.function_name
	logger.info("Your cron function " + name + " ran at " + str(current_time))

	tickers = ['QQQ', 'RSP', 'SPY', 'TLH', 'UWM', '^TNX', '^VIX'] #getTickerSymbols(event, context) #['QQQ', 'RSP', 'SPY', 'TLH', 'UWM', '^TNX', '^VIX']
	print(tickers)
	stockDataFrames = []

	for ticker in tickers:
		stockDataFrames.append(getSiteData(f'https://finance.yahoo.com/quote/{ticker}/history', ticker))

	print(pd.concat(stockDataFrames))
	

def getTickerSymbols(event, context):
	dynamoDBClient = boto3.client('dynamodb')
	return dynamoDBClient.get_item(
		TableName='StockDataDB',
		Key={
			'ID': {
				'S': 'TickerDataRow'
			}
		}
	)["Item"]["Tickers"]["SS"]


def getSiteData(url, ticker):

	options = webdriver.ChromeOptions()
	service = webdriver.ChromeService("/opt/chromedriver")

	options.binary_location = '/opt/chrome/chrome'
	options.add_argument("--headless=new")
	options.add_argument('--no-sandbox')
	options.add_argument("--disable-gpu")
	options.add_argument("--window-size=1280x1696")
	options.add_argument("--single-process")
	options.add_argument("--disable-dev-shm-usage")
	options.add_argument("--disable-dev-tools")
	options.add_argument("--no-zygote")
	options.add_argument(f"--user-data-dir={mkdtemp()}")
	options.add_argument(f"--data-path={mkdtemp()}")
	options.add_argument(f"--disk-cache-dir={mkdtemp()}")
	options.add_argument("--remote-debugging-port=9222")

	driver = webdriver.Chrome(options=options, service=service)
	
	try:  
		print(url)
		
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