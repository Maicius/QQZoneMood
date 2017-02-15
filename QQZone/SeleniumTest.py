import time
from selenium import webdriver

driver = webdriver.Chrome('E:/chromedriver/chromedriver')  # Optional argument, if not specified will search path.
#driver.get('http://www.google.com/xhtml')
driver.get('http://user.qzone.qq.com/1272082503')
#driver.get('http://www.baidu.com')
#time.sleep(5) # Let the user actually see something!
search_box = driver.find_element_by_name('q')
search_box.send_keys('QQ空间')
search_box.submit()
time.sleep(100)
driver.quit()
