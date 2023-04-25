

# encoding = utf-8



import os

import sys

import time

import datetime

import re

import logging

import urllib

from urllib import request

from lxml import html

import json



def validate_input(helper, definition):

    pass



def collect_events(helper, ew):

    # init values

    url=helper.get_arg('download_url')

    index=helper.get_arg('index')

    deep_link = ""

    file_name = ""

    latest_date = 0
    
    enable_checkpoint=helper.get_arg('enable_checkpointing')
    
    helper.log_info("checkpoint fuction : {}".format(enable_checkpoint))
    
    headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'
        }


    # get and set the meta values for each event

    input_name = helper.get_input_stanza_names()

    sourcetype = helper.get_sourcetype()

    source = "azure://{}".format(input_name)

    host = 'localhost'


    def index_events(response):

        obj = response.json()

        helper.log_info("Azure ServiceTags Download completed. Status=Completed Filename={}".format(deep_link))

        items = obj.get("values",[])

        input_name = helper.get_input_stanza_names()

        source = "azure://{}".format(input_name)

        helper.log_debug("Azure ServiceTags parsing") 

        # Write each item as an event    

        for i in range(len(items)):

            text=json.dumps(items[i])

            event=helper.new_event(

                text,

                time=datetime.datetime.now(),

                host=host,

                index=index,

                source=source,

                sourcetype=sourcetype,

                done=True,

                unbroken=True

            )

            ew.write_event(event)

            helper.log_debug("wrote : {}".format(text))

        

        helper.log_info("Azure ServiceTags Indexing complete. Wrote {} events into index={} sourcetype={}".format(len(items),index,sourcetype))

 

    def get_check_point():

        #helper.save_check_point("latest_time",0)

        checkpoint = helper.get_check_point("latest_time")


        if checkpoint is None:

            helper.log_info("Initialize checkpoint to 0")

            checkpoint=0

        else:

            helper.log_info("Checkpoint is at : {}".format(checkpoint))

            checkpoint=int(checkpoint)

        return checkpoint

    

    def get_download_link():

        try:

            response = helper.send_http_request(url, "GET", headers=headers, timeout=120)

            response.raise_for_status()

            helper.log_debug("RESPONSE : {}".format(response.content))

            tree = html.fromstring(response.content)

            helper.log_debug("TREE : {}".format(tree))

            element = tree.xpath('//*[@data-bi-id="downloadretry"]')

            deep_link = element[0].attrib["href"]

            helper.log_debug("DEEPLINK : {}".format(deep_link))

            # Validate the data file name from the deep link 

            file_name_pattern = re.compile('(ServiceTags_Public_\d+\.json$)')

            file_name_matched = file_name_pattern.search(deep_link)

            file_name = file_name_matched.group(1)

        except Exception as e:

            helper.log_error("Exception on getting deep_link : {}".format(e))

            os._exit(1)



        if not file_name:

            helper.log_error("Invalid file name : {} from the deep link : {} ".format(file_name,deep_link))   

        

        return deep_link

    

    def download_index():

        try:
    
            response = helper.send_http_request(deep_link, "GET", headers=headers, timeout=200)
    
            helper.log_info("Download file : {} initiated".format(file_name))
    
            index_events(response)
    
        except Exception as e:
    
            helper.log_error("Exception on download & indexing : {}".format(e))
    
            os._exit(1)


    deep_link=get_download_link()

    date=re.search(r"(\d{8})",deep_link)

    latest_date = int(date.group(0))

    if helper.get_arg('checkpointing'):
        
        checkpoint=get_check_point()
        
        if latest_date > checkpoint:
            
            download_index()
            
            helper.save_check_point("latest_time",latest_date)
            
            helper.log_info("setting checkpoint to : {}".format(str(latest_date)))
            
        else:
            
            helper.log_info("Ignoring download of already indexed file")
            
    else:
        download_index()
