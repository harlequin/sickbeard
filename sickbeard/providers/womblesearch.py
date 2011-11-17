import re
import time
import urllib
import datetime

import xml.etree.cElementTree as etree

import sickbeard
import generic

from sickbeard import classes, logger, show_name_helpers
from sickbeard import tvcache
from sickbeard.exceptions import ex
from sickbeard.common import Quality

class WombleSearchProvider(generic.NZBProvider):
    def Load (self):
        pass
    
    def Save(self, cfg):
        pass
    
    
    def __init__(self):
        generic.NZBProvider.__init__(self, "WombleSearch")
        self.supportsBacklog = False

        self.cache = WombleSearchCache(self)
        self.name = "womblesearch"
        self.url = 'http://newshost.co.za/'
        
    def isEnabled(self):
        return True
    
    def _get_season_search_strings(self, show, season):
        sceneSearchStrings = set(show_name_helpers.makeSceneSeasonSearchString(show, season, "NZBIndex"))

        # search for all show names and episode numbers like ("a","b","c") in a single search
        return [' '.join(sceneSearchStrings)]

    def _get_episode_search_strings(self, ep_obj):
        # tvrname is better for most shows
        if ep_obj.show.tvrname:
            searchStr = ep_obj.show.tvrname + " S%02dE%02d"%(ep_obj.season, ep_obj.episode)
        else:
            searchStr = ep_obj.show.name + " S%02dE%02d"%(ep_obj.season, ep_obj.episode)
        return [searchStr]
    
    def getQuality(self, item):
        (title,url) = item
        quality = Quality.nameQuality(title)
        return quality

    def _get_title_and_url(self, item):
        (title,url) = item
        if url:
            url = url.replace('&amp;','&')  #not shure if we really need this
        return (title, url)
    
    def _doSearch(self, curString, quotes=False, show=None):

        term =  re.sub('[\.\-]', ' ', curString).encode('utf-8')
        term = term.replace(' ', '%')
        if quotes:
            term = "\""+term+"\""
            
        params = {"s" : term }
        searchURL = self.url  + "?" + urllib.urlencode(params)
        print searchURL
        result = self.getURL(searchURL,[("User-Agent","Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:5.0) Gecko/20100101 Firefox/5.0"),("Accept","text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),("Accept-Language","de-de,de;q=0.8,en-us;q=0.5,en;q=0.3"),("Accept-Charset","ISO-8859-1,utf-8;q=0.7,*;q=0.7"),("Connection","keep-alive"),("Cache-Control","max-age=0")])
        
        
        
        #opener = urllib.URLopener()
        #result = opener.open(searchURL)
        
        results = []
        
        titlere = re.compile('nzb[\w./-]*')
        for line in result.split('\n'):
            if ( line.find("<a href=\"nzb") != -1):                
                t = titlere.search(line)                
                last_slash = line[t.start():t.end()].rfind("/")
                
                results.append(
                               (
                               str(line[t.start() + last_slash + 1:t.end()].replace(".nzb", "")),
                               str(self.url + line[t.start():t.end()])
                               )
                               )    
        return results
        


    def findPropers(self, date=None):
        results = []

        for curResult in self._doSearch("(PROPER,REPACK)"):

            title = curResult.findtext('title')
            url = curResult.findtext('link').replace('&amp;','&')

            descriptionStr = curResult.findtext('description')
            dateStr = re.search('<b>Added:</b> (\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)', descriptionStr).group(1)
            if not dateStr:
                logger.log(u"Unable to figure out the date for entry "+title+", skipping it")
                continue
            else:
                resultDate = datetime.datetime.strptime(dateStr, "%Y-%m-%d %H:%M:%S")

            if date == None or resultDate > date:
                results.append(classes.Proper(title, url, resultDate))

        return results



class WombleSearchCache(tvcache.TVCache):

    def __init__(self, provider):

        tvcache.TVCache.__init__(self, provider)
        self.minTime = 25


    def _getRSSData(self):
    
        url = "http://newshost.co.za/rss/"

        logger.log(u"WombleSearch cache update URL: "+ url, logger.DEBUG)

        data = self.provider.getURL(url)

        return data


provider = WombleSearchProvider()
