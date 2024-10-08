import datetime
import logging
import pandas as pd
import boto3
import json
import os
from tempfile import mkdtemp
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver import ActionChains
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

loadWaitTime = 120

def updateTickerSymbols(event, context):
	data = json.loads(event["body"])["tickers"]
	logger.info(data)
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
		logger.info(url)
		
		driver.get(url)

		headers = {}

		dataTemplate = {
			'Open': [],
			'High': [],
			'Low': [],
			'Close': [],
			'Volume': [],
		}

		headerRow = WebDriverWait(driver, loadWaitTime).until(EC.presence_of_element_located((By.XPATH, '//*[@id="nimbus-app"]/section/section/section/article/div[1]/div[3]/table/thead/tr')))
		headerElements = headerRow.find_elements(By.TAG_NAME, 'th')

		for elem in range(len(headerElements)):
			if headerElements[elem].text in dataTemplate.keys():
				headers[headerElements[elem].text] = elem

		firstRow = driver.find_element(By.XPATH, '//*[@id="nimbus-app"]/section/section/section/article/div[1]/div[3]/table/tbody/tr[1]')
		rowData = firstRow.find_elements(By.TAG_NAME, 'td')

		if len(rowData) < 4:
			return pd.DataFrame({
			'Open': ['N/A'],
			'High': ['N/A'],
			'Low': ['N/A'],
			'Close': ['N/A'],
			'Volume': ['N/A'],
		}, index=[ticker])

		for key in headers.keys():
			dataTemplate[key].append(rowData[headers[key]].text)
		
		return pd.DataFrame(dataTemplate, index=[ticker])

	except Exception as e:
		logger.error('ERROR: ', e)
		return pd.DataFrame({
			'Open': ['N/A'],
			'High': ['N/A'],
			'Low': ['N/A'],
			'Close': ['N/A'],
			'Volume': ['N/A'],
		}, index=[ticker])
	finally:
		driver.close()

def sendMessage(message):

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

		driver.get('https://visit.telmate.com/user/messages')
		driver.maximize_window()

		loginPage = WebDriverWait(driver, loadWaitTime).until(EC.presence_of_element_located((By.XPATH, '//*[@id="user_email"]')))

		loginEmailInput = loginPage.find_element(By.XPATH, '//*[@id="user_email"]')
		loginEmailInput.send_keys(os.environ['EMAIL'])

		loginPasswordInput = loginPage.find_element(By.XPATH, '//*[@id="user_password"]')
		loginPasswordInput.send_keys(os.environ['PASSWORD'])

		loginButton = loginPage.find_element(By.XPATH, '//*[@id="new_user"]/div[4]/button')
		loginButton.click()

		logger.info("Login Passed")

		agreementsPage = WebDriverWait(driver, loadWaitTime).until(EC.presence_of_element_located((By.XPATH, '//*[@id="tos-pp"]')))

		tosButton = agreementsPage.find_element(By.XPATH, '//*[@id="tos-pp"]')
		tosButton.click()

		comButton = agreementsPage.find_element(By.XPATH, '//*[@id="communications"]')
		comButton.click()

		agreeButton = agreementsPage.find_element(By.XPATH, '//*[@id="tos-form"]/div[3]/div/div[2]/button')
		agreeButton.click()

		logger.info("Agreement Passed")


		verificationPage = WebDriverWait(driver, loadWaitTime).until(EC.presence_of_element_located((By.XPATH, '//*[@id="mainWrapper"]/div[1]/div/div/div/div/div/div[2]/div[1]')))

		# driver.save_screenshot('/tmp/screenshot.png')

		# logger.info('Screenshot Created')

		verificationCookieButton = verificationPage.find_element(By.XPATH, '//*[@id="onetrust-accept-btn-handler"]')
		ActionChains(driver).scroll_to_element(verificationCookieButton).perform()
		verificationCookieButton.click()
		
		verificationButton = verificationPage.find_element(By.XPATH, '//*[@id="mainWrapper"]/div[1]/div/div/div/div/div/div[2]/div[1]')
		ActionChains(driver).scroll_to_element(verificationButton).perform()
		verificationButton.click()

		logger.info("Verification Passed")

		mainPage = WebDriverWait(driver, loadWaitTime).until(EC.presence_of_element_located((By.XPATH, '//*[@id="mainWrapper"]/div[1]/div/div[1]/div[3]/button')))

		messageButton = mainPage.find_element(By.XPATH, '//*[@id="mainWrapper"]/div[1]/div/div[1]/div[3]/button')
		messageButton.click()

		messagePage = WebDriverWait(driver, loadWaitTime).until(EC.presence_of_element_located((By.XPATH, '//*[@id="newMessage"]')))
		
		newMessageButton = messagePage.find_element(By.XPATH, '//*[@id="newMessage"]')
		newMessageButton.click()

		contactButton = WebDriverWait(driver, loadWaitTime).until(EC.presence_of_element_located((By.XPATH, '//*[@id="contactGroup-1"]/li')))
		ActionChains(driver).scroll_to_element(contactButton).perform()
		contactButton.click()

		messageField = WebDriverWait(driver, loadWaitTime).until(EC.presence_of_element_located((By.XPATH, '//*[@id="message_body"]')))
		messageField.send_keys(message)

		logger.info('Message Page')

		# driver.save_screenshot('/tmp/screenshot-message.png')

		# s3_client = boto3.client('s3')

		# s3_client.upload_file('/tmp/screenshot.png', 'stock-data-debug-bucket', 'screenshot.png')

		# logger.info('Screenshot Saved')

		sendButton = WebDriverWait(driver, loadWaitTime).until(EC.presence_of_element_located((By.XPATH, '//*[@id="recipientArea"]/div[3]/button')))
		ActionChains(driver).scroll_to_element(sendButton).perform()
		sendButton.click() 

		# logger.info('Message Sent')

	except Exception as e:
		logger.error('ERROR: ', e)
	finally:
		driver.close()

def dailyStockData(event, context):
	current_time = datetime.datetime.now().time()
	name = context.function_name
	logger.info("Your cron function " + name + " ran at " + str(current_time))

	tickers = getTickerSymbols(event, context) #['QQQ', 'RSP', 'SPY', 'TLH', 'UWM', '^TNX', '^VIX'] 
	logger.info(tickers)
	stockDataFrames = []

	for ticker in tickers:
		stockDataFrames.append(getSiteData(f'https://finance.yahoo.com/quote/{ticker}/history', ticker))

	stockData = pd.concat(stockDataFrames)
	StockDataString = stockData.to_string(col_space=3)

	logger.info(StockDataString)

	sendMessage(StockDataString)
	

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

# dailyStockData({}, {})