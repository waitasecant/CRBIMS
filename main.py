from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from datetime import datetime, timedelta
import pandas as pd

monthsDict = {
    "JAN":"01",
    "FEB":"02",
    "MAR":"03",
    "APR":"04",
    "MAY":"05",
    "JUN":"06",
    "JUL":"07",
    "AUG":"08",
    "SEP":"09",
    "OCT":"10",
    "NOV":"11",
    "DEC":"12"
}
districts = ["Amritsar","Barnala","Bathinda","Faridkot","Fatehgarh Sahib","Fazilka","Firozpur","Gurdaspur","Hoshiarpur",
             "Jalandhar","Kapurthala","Ludhiana","Mansa","Moga","Muktsar","Pathankot","Patiala","Rupnagar","Sangrur",
             "SAS Nagar","SBS Nagar","Tarn Taran"]

dt = datetime.today()-timedelta(days=1)
dt = datetime.strftime(dt,"%Y-%m-%d")

web = 'http://gis-prsc.punjab.gov.in/residue/index.aspx'
service = Service(executable_path="chromedriver.exe")
options = Options()
options.add_argument('--headless=new')
driver = webdriver.Chrome(service=service, options=options)
driver.get(web)

for d in [dt]:
    data = []
    getYear, getMonth, getDay = d.split('-')
    # Wait for dateBox and click
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.ID, 'StartTime')))

    dateBox = driver.find_element(By.ID, 'StartTime')
    dateBox.click()

    # Wait for calendar
    WebDriverWait(driver,2).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'dtp-content')))

    # Select correct month
    selectMonthNum = 0
    while selectMonthNum!=int(getMonth):
        rightMoveMonth = driver.find_element(by='xpath', value='//div[@class="dtp-date"]/div/div[@class="right center p10"]')
        rightMoveMonth.click()
        selectMonth = driver.find_element(by='xpath', value='//div[@class="dtp-date"]/div/div[@class="dtp-actual-month p80"]').text
        selectMonthNum = int(monthsDict[selectMonth])

    # Select correct year
    selectYear = int(driver.find_element(by='xpath', value='//div[@class="dtp-date"]/div/div[@class="dtp-actual-year p80"]').text)
    if selectYear < int(getYear):
        for i in range(abs(selectYear-int(getYear))):
            rightMoveYear = driver.find_element(by='xpath', value='//div[@class="dtp-date"]/div[3]/div[@class="right center p10"]')
            rightMoveYear.click()
            
    if selectYear > int(getYear):
        for i in range(abs(selectYear-int(getYear))):
            leftMoveYear = driver.find_element(by='xpath', value='//div[@class="dtp-date"]/div[3]/div[@class="left center p10"]')
            leftMoveYear.click()
    selectYear = int(driver.find_element(by='xpath', value='//div[@class="dtp-date"]/div/div[@class="dtp-actual-year p80"]').text)

    # Select correct day
    isBreak = False
    for i in range(7):
        xpathSelectDates = f'//div[@class="dtp-picker"]/div[@class="dtp-picker-calendar"]/table[@class="table dtp-picker-days"]/tbody/tr[{i+1}]/td/a[@class="dtp-select-day"]'
        selectDates = driver.find_elements(by='xpath', value=xpathSelectDates)
        if selectDates!=[]:
            for selectDate in selectDates:
                dateText = selectDate.text
                if dateText == getDay:
                    selectDate.click()
                    isBreak = True
                    break
            if isBreak==True:
                break
    # Press OK
    okButton = driver.find_element(by='xpath', value='//div[@class="dtp-buttons"]/button[@class="dtp-btn-ok btn btn-success"]')
    okButton.click()

    # Press Submit
    submitButton = driver.find_element(by='xpath', value='//div[@class="card-body new"]/h4/input[@type="submit"]')
    submitButton.click()

    # Wait for the data to load
    WebDriverWait(driver, 2).until(
        EC.presence_of_element_located((By.ID, 'StartTime')))

    # Click menu button
    menuButton = driver.find_element(by='xpath', value='//div[@aria-label="Chart menu"]/button')
    menuButton.click()

    # Click view data table
    viewTable = driver.find_element(by='xpath', value='//div[@class="highcharts-contextmenu"]/ul/li[9]')
    viewTable.click()

    # Wait for table to be located
    WebDriverWait(driver,2).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'highcharts-data-table')))

    # Go through table and append to data
    # Check if the table is empty
    testtableData = driver.find_element(by='xpath', value='//div[@class="highcharts-data-table"]/table/tbody/tr/th')
    if testtableData.get_attribute("class")=="empty":
        for i in districts:
            dt = "-".join([str(selectYear),str(selectMonthNum),str(dateText)])
            data.append([datetime.strptime(dt,'%Y-%m-%d').strftime('%Y-%m-%d'),i, 0])
    else:
        tableData = driver.find_elements(by='xpath', value='//div[@class="highcharts-data-table"]/table/tbody/tr')
        districtFireList = []
        for tableRow in tableData:
            districtName = tableRow.find_element(by='xpath', value='./th[@class="text"]').text
            districtFireList.append(districtName)
            fireCount = int(tableRow.find_element(by='xpath', value='./td[@class="number"]').text)
            dt = "-".join([str(selectYear),str(selectMonthNum),str(dateText)])
            data.append([datetime.strptime(dt,'%Y-%m-%d').strftime('%Y-%m-%d'),districtName, fireCount])

        districtNoFire = list(set(districts).symmetric_difference(districtFireList))

        for i in districtNoFire:
            dt = "-".join([str(selectYear),str(selectMonthNum),str(dateText)])
            data.append([datetime.strptime(dt,'%Y-%m-%d').strftime('%Y-%m-%d'),i, 0])

    df = pd.DataFrame(data,columns=["Date", "District", "fireCount"])
    df.sort_values(by=["Date", "District"], inplace=True)
    df_old = pd.read_csv("data.csv")
    df = pd.concat([df_old, df], axis=0)
    df.to_csv("data.csv", index=False)
driver.quit()