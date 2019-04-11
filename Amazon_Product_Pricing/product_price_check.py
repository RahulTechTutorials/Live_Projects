##Importing Libraries
import pandas as pd
import datetime as date
from selenium import webdriver
import os
from bs4 import BeautifulSoup
import requests
import numpy as np
import re
import copy
from functools import reduce
##import seaborn as sns
import smtplib
import schedule
import time
##date.datetime.now().strftime("%d-%m-%Y")
##import matplotlib.pyplot as plt
##%matplotlib inline

##os.getcwd()
os.chdir('/Users/rahuljain/Desktop/Python/Live_Projects/Amazon_Product_Pricing/')
def amazon_product_pricing():
    ##getting the url in an object
    my_url = 'https://www.amazon.in/s?k=WD+portable+hard+drive&ref=nb_sb_noss'
    ##Using Chrome Web driver to open the url and load the dependent components
    driver = webdriver.Chrome("/Users/rahuljain/Desktop/Python/Dependencies/chromedriver")
    driver.get(my_url)
    ##execute the script and return the html
    html = driver.execute_script("return document.documentElement.outerHTML")
    ##Parse the html with lxml parser
    soup = BeautifulSoup(html,'lxml')
    ##FindAll div tags for outer containers
    product_soup = soup.findAll('div',{"class" : 's-include-content-margin s-border-bottom'})
    product_catalog = []
    ##Looping through all the div classes and capturing the title,price & product_id
    for product in product_soup:
        try:
            title  = product.find('span',class_ = 'a-size-medium a-color-base a-text-normal').text.strip()
            price = product.find('span',{"class" : "a-price-whole"}).text.strip()
            product_id = product.find('h5',{"class" : "a-color-base s-line-clamp-2"}).a['href']
            product_catalog.append((product_id,title,price))
        except:
            pass

    ##Creating a DataFrame with List of Tuples
    product_df = pd.DataFrame(product_catalog,columns = ['product_id','Product_name',date.datetime.now().strftime("%d-%m-%Y")])
    ##Extracting the Product_id from href
    product_df['product_id'] = product_df['product_id'].apply(lambda x : re.search(r'((?<=dp/)\w{10}(?=/))|((?<=dp%2F)\w{10}(?=%2F))',x).group(0))
    ##Making Product Id as Index
    product_df.set_index('product_id',inplace=True)
    ##Dropping duplicates from the DataFrame
    product_df.drop_duplicates(inplace=True)
    ##Removing the comma from price and casting it as Int
    product_df.iloc[:,-1] = product_df.iloc[:,-1].str.replace(',','').astype('float64')

    ###Generating the csv file
    today = date.datetime.now().strftime("%d-%m-%Y")
    filename = today+'.txt'
    header = 'product_id,Product_name,'+today+'\n'
    ##Creating a csv object with comma delimited extract
    product_csv = product_df.to_csv(header=False,quoting=1, escapechar='"')
    ##Opening FileHandler to write
    with open(filename,'w') as fh:
        fh.write(header)
        fh.write(product_csv)
    ##Extracting the files from the directory, loading them in dataframe and creating a list of dataframe
    product_df_dict = []
    for file in (os.listdir()):
        if file.endswith(".txt"):
            product_df_dict.append(pd.read_csv(file))
        else:
            continue
    ###Merging all the dataframes into one
    product_df_dict[0] = product_df_dict[0].set_index('product_id')
    product_super_final = reduce(lambda left,right : pd.merge(left,right.set_index('product_id').iloc[:,-1].to_frame(),how='left',left_index=True, right_index=True),product_df_dict)
    ###checking if there are any variation in the prices over the time -- 
    df = product_super_final.T.iloc[1:,:].describe(include='all').T
    change_prod_list = df[df.unique > 1].index.values
    print(product_super_final.loc[change_prod_list,:])
    ##df_for_plot = product_super_final.loc[change_prod_list,:].reset_index().melt(id_vars='product_id', value_vars=['09-04-2019','10-04-2019']).sort_values(by= 'product_id')
    ##_, ax = plt.subplots(figsize=(20, 10))
    ##g = sns.pointplot(x="variable", y="value", hue='product_id', data=df_for_plot,ax=ax)
    return(str(product_super_final.loc[change_prod_list,:]))
###Sending a mail with the contents of the product for which the price changes
def send_email():    
    email_from = 'your email account'
    email_to = 'to email account'
    pswd = 'your email password'
    server = smtplib.SMTP('smtp.gmail.com',587)
    ###Calling the amazon_product_pricing function and returning the price delta
    message = amazon_product_pricing()
    server.starttls()
    server.login(email_from,pswd)
    server.sendmail(email_from,email_to,message)
    server.quit()
###Schedule for every 120 seconds or daily at 10:00 AM - Choose as oer requirement 
schedule.every(120).seconds.do(send_email)
##schedule.every().day.at("10:00").do(send_email)
##schedule.every().hour.do(send_email)


while True:
    schedule.run_pending()
    time.sleep(1)
