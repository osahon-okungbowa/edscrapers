# -*- coding: utf-8 -*-
import re
import json

import bs4

from edscrapers.scrapers import base
import edscrapers.scrapers.base.parser as base_parser
from edscrapers.scrapers.ocr import parsers

# contains list of data resources to exclude from dataset
deny_list = []

def parse(res):
    """ function parses content to create a dataset model
    or return None if no resource in content"""

    soup_parser = bs4.BeautifulSoup(res.text, 'html5lib')
    # check if the content contains any of the extensions
    if soup_parser.body.find(name='a', href=base_parser.resource_checker,
                             recursive=True) is None:
        # no resource on this page, so return None
        return None

    # if code gets here, at least one resource was found
    
    # check if the parser is working on OCR State & National Estimations (variant 1)
    if soup_parser.body.find(class_='accordiontitle', recursive=True) is not None:
        # parse the page with the parser and return result
        return parsers.parser1.parse(res)
    # check if the parser is working on OCR State & National Estimations (variant 2)
    if soup_parser.body.select_one('#container #maincontent') is not None:
        # parse the page with the parser and return result
        return parsers.parser2.parse(res)
    else:
        return None


    


