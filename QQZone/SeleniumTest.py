import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
driver = webdriver.Chrome('E:/chromedriver/chromedriver')
driver.get('http://qzone.qq.com/')
wait = WebDriverWait(driver, 10)
print('getFinished')
time.sleep(10)
print('sleepFinished')
login = driver.find_element_by_link_text('说说')
login.click()
like = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'c_tx')))
like.click()

while(driver.find_element_by_link_text('查看更多')):
    like_more = driver.find_element_by_link_text('查看更多')
    like_more.click()
like_name = driver.find_element_by_class_name('info_name')
like_info = driver.find_element_by_class_name('info_detail')
print(like_name)
print(like_info)


time.sleep(5)

