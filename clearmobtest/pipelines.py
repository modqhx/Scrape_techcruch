# -*- coding: utf-8 -*-

# Item pipelines here
#
# add your pipeline to the ITEM_PIPELINES setting
# 

import csv
from clearmobtest.items import Article

from nltk import ne_chunk, pos_tag, word_tokenize
from nltk.tree import Tree
import re
import collections


class ClearmobtestPipeline(object):
    header = False
    def __init__(self):
        self.data = collections.defaultdict(str)
        self.url = []


    def process_item(self, item, spider):
        'can process items here async'
        print item

        clean_body = self.remove_non_ascii(str(item['body']).encode('utf-8')) # Remove unicode characters
        clean_article_url = self.remove_non_ascii(str(item['url']).encode('utf-8')) 
        clean_title_with_html = self.remove_non_ascii(str(item['title']).encode('utf-8'))
        clean_article_title = self.remove_html_tags(clean_title_with_html) # cleans out html tags 

        entities = self.extract_entities_from_articles(clean_body) # POS tagging + NLP 
        ###
        #Final dataframe to write to file
        self.data["company name"] = entities[1:8] # taking only a portion of entire set
        self.data["company website"] = self.find_urls(str(item['body'])) #finding for company website before cleaning using regex

        self.data["article url"] = clean_article_url
        self.data["article title"] = clean_article_title[1:-1]


        ### WRITE TO CSV ####
        with open("output.csv", "a") as csv_file:
            w = csv.DictWriter(csv_file, self.data.keys())
            if ClearmobtestPipeline.header == False: # Header row
                w.writeheader()
                ClearmobtestPipeline.header = True
            w.writerow(self.data)

        return item

    def extract_entities_from_articles(self, text):
        chunks = ne_chunk(pos_tag(word_tokenize(text))) # ('HI', NN), ('AIRBNB', ZZ) ... 
        prev = None
        cur_chunk, cont_chunk = [], []
        for i in chunks:
            if type(i) == Tree:
                cur_chunk.append(" ".join([token for token, pos in i.leaves()]))
            elif cur_chunk:
                named_entity = " ".join(cur_chunk)
                if named_entity not in cont_chunk:
                    cont_chunk.append(named_entity)
                    cur_chunk = []
        return cont_chunk


    def remove_html_tags(self, raw_html):
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', raw_html)
        return cleantext


    def find_urls(self, text):
        urls = re.findall(r'href=[\'"]?([^\'" >]+)', text)

        url_string = (', '.join([url for url in urls[:3] if self.blacklist_urls(url)]))

        return url_string if url_string else "n/a"


    def blacklist_urls(self, url_text):
        if (url_text.startswith("https://tech") or
            url_text.startswith("https://crunchbase") or
            url_text.startswith("https://blog") or url_text.startswith("https://money")):
            return False
        else:
            return True


    def remove_non_ascii(self, text):
        x = re.sub(r'[^\x00-\x7f]', r' ', text).strip()
        return x


    def close_spider(self, spider):
        print "Done processing text!"
