#   Copyright (C) 2021 Evinr
#
#
# This file is part of NASA APOD ScreenSaver.
#
# NASA APOD ScreenSaver is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# NASA APOD ScreenSaver is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NASA APOD ScreenSaver.  If not, see <http://www.gnu.org/licenses/>.

import json, os, random, datetime, requests, itertools, re, random, requests_cache
from datetime import datetime
from datetime import timedelta

from six.moves     import urllib
# from simplecache   import use_cache, SimpleCachev
from kodi_six      import xbmc, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs, py2_encode, py2_decode


# Plugin Info
ADDON_ID       = 'screensaver.nasa.apod'
REAL_SETTINGS  = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME     = REAL_SETTINGS.getAddonInfo('name')
SETTINGS_LOC   = REAL_SETTINGS.getAddonInfo('profile')
ADDON_PATH     = REAL_SETTINGS.getAddonInfo('path')
ADDON_VERSION  = REAL_SETTINGS.getAddonInfo('version')
ICON           = REAL_SETTINGS.getAddonInfo('icon')
FANART         = REAL_SETTINGS.getAddonInfo('fanart')
LANGUAGE       = REAL_SETTINGS.getLocalizedString
KODI_MONITOR   = xbmc.Monitor()

# Global Info
# TODO: Update base mapping
BASE_URL       = 'https://apod.nasa.gov'
NEXT_JSON      = '/apod/%s.html'
BASE_API       = (REAL_SETTINGS.getSetting("Last") or NEXT_JSON%('astropix'))
# TODO: get the settings working for these values
TIMER          = 60#int(REAL_SETTINGS.getSetting("RotateTime"))
# TODO: Determine what these id's relate to
IMG_CONTROLS   = [30000,30100]
# TODO: Determine what this is
CYC_CONTROL    = itertools.cycle(IMG_CONTROLS).__next__ #py3

# in-memory cache 
session = requests_cache.CachedSession(ADDON_ID, backend='memory')

class GUI(xbmcgui.WindowXMLDialog):
    def __init__( self, *args, **kwargs ):
        self.isExiting = False
        self.cache     = SimpleCache()
        self.baseAPI   = BASE_API
        
        
    def log(self, msg, level=xbmc.LOGDEBUG):
        xbmc.log('%s-%s-%s'%(ADDON_ID,ADDON_VERSION,msg),level)
            
            
    def notificationDialog(self, message, header=ADDON_NAME, sound=False, time=4000, icon=ICON):
        try: xbmcgui.Dialog().notification(header, message, icon, time, sound=False)
        except Exception as e:
            self.log("notificationDialog Failed! " + str(e), xbmc.LOGERROR)
            xbmc.executebuiltin("Notification(%s, %s, %d, %s)" % (header, message, time, icon))
        return True
         
         
    def onInit(self):
        # TODO: what is this???
        self.winid = xbmcgui.Window(xbmcgui.getCurrentWindowDialogId())
        self.winid.setProperty('earth_animation', 'okay' if REAL_SETTINGS.getSetting("Animate") == 'true' else 'nope')
        self.winid.setProperty('earth_time'     , 'okay' if REAL_SETTINGS.getSetting("Time") == 'true' else 'nope')
        self.winid.setProperty('earth_overlay'  , 'okay' if REAL_SETTINGS.getSetting("Overlay") == 'true' else 'nope')
        self.startRotation()


    def loadJSON(self, item):
        try: return json.loads(item, strict=False)
        except Exception as e: self.log("loadJSON failed! %s\n%s"%(e,item), xbmc.LOGERROR)
          

    def openURL(self, url):
    
        # user agent needs to get updated regularly to align with 
        # https://techblog.willshouse.com/2012/01/03/most-common-user-agents/
        
        # header={'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36'}, life=timedelta(hours=24)
        
        # self.log('getURL, url = %s, header = %s'%(url, header))
        # show all cached URLs
        self.log("openURL Cached URLs: " + session.cache.urls, xbmc.LOGERROR)
        
        headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36'}

        session.get(url, headers=headers)

        # self.log("openURL type: " + type('%s.getURL, url = %s.%s.%s'%(ADDON_ID,url,param,header)), xbmc.LOGERROR)
        # cacheresponse = self.cache.get('%s.getURL, url = %s.%s.%s'%(ADDON_ID,url,param,header))
        # cacheresponse = self.cache.get(url)
        self.log("openURL cacheresponse: " + cacheresponse, xbmc.LOGERROR)
        if not cacheresponse:
            try:
                req = requests.get(url, param, headers=header)
                self.log("openURL req: " + req, xbmc.LOGERROR)
                cacheresponse = req.text()
                req.close()
            except Exception as e: 
                self.log("getURL, Failed! %s"%(e), xbmc.LOGERROR)
                self.notificationDialog(LANGUAGE(30001))
                return {}
            self.cache.set('%s.getURL, url = %s.%s.%s'%(ADDON_NAME,url,param,header), json.dumps(cacheresponse), expiration=life)
            return cacheresponse
        return self.loadJSON(cacheresponse)
     
        
    def findNextRandomImage(self):
        try: 
            #grab from the random URL
            then = datetime(1995, 5, 20)        # Date of first stable APODs
            now  = datetime.now()                         # Now
            duration = now - then                         # For build-in functions
            duration_in_s = duration.total_seconds()      # Total number of seconds between
            random_offset_from_apod_creation = datetime.fromtimestamp(random.randrange(int(duration_in_s)))
            random_apod = now - random_offset_from_apod_creation
            nextImage = "ap" + datetime.fromtimestamp(random_apod.total_seconds()).strftime("%y%m%d")
            self.log("findNextImage nextImage: " + nextImage, xbmc.LOGERROR)
            return nextImage   
        except Exception as e:
            self.log("findNextImage Failed! " + str(e), xbmc.LOGERROR)
            # TODO: hardcode the default image
            return 'ap210817'
            
    def parseJPG(self, response):
        try:
            # self.log("parseJPG results: " + response, xbmc.LOGERROR)
            match = re.findall(r"image.*?\.jpg", response) 
            if match:
                return str("/" + match[0])
            # if no match is found then return static images
            return random.choice(['/image/2107/ForestWindow_Godward_2236.jpg', '/image/2012/Neyerm63_l2.jpg', '/image/2012/EagleNebula_Paladini_2854.jpg', '/image/2107/Walk_Milkyway.jpg', '/image/2108/Luna-Tycho-Clavius-high.jpg', '/image/2108/m74_APOD.jpg', '/image/2107/sh2_101_04.jpg'])
        except Exception as e:
            self.log("parseJPG Failed! " + str(e), xbmc.LOGERROR)
            return '/image/1912/NGC6744_FinalLiuYuhang.jpg'
    
    #  TODO: Parse the lable/title/contents
         
    def setImage(self, id):
        try:
            # get the HTML from the URL path
            # TODO: implement caching
            headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36'}

            session.get('%s%s'%(BASE_URL,self.baseAPI), headers=headers)

            # results = self.openURL('%s%s'%(BASE_URL,self.baseAPI))
            # results = requests.get('%s%s'%(BASE_URL,self.baseAPI))
            
            # get the JPG from HTML                    
            imagePath = self.parseJPG(results.text)
            
            # TODO: Add the check for the proportions
            # Sets the actual image 
            self.getControl(id).setImage('%s%s'%(BASE_URL,imagePath))
            
            # TODO: https://romanvm.github.io/Kodistubs/_autosummary/xbmcgui.html#xbmcgui.ControlImage
            # self.image = xbmcgui.ControlImage(100, 250, 125, 75, aspectRatio=2)
            
            # TODO: Fix the labels
            # self.getControl(id+1).setLabel(('%s, %s'%(results.get('region',' '),results.get('country',''))).strip(' ,'))
            
            # Sets up the path for the next image
            nextAPOD = self.findNextRandomImage()
            # Create new string for URL path for next lookup
            baseAPI = NEXT_JSON%(nextAPOD)
        except Exception as e:
            self.log("setImage Failed! " + str(e), xbmc.LOGERROR)
            # TODO: hardcode the default image
            baseAPI = NEXT_JSON%('ap210817')
        # set the global path to the next images URL
        self.baseAPI = baseAPI
    
          
    def startRotation(self):
        # these ID relate to the screen/viewport that is being 
        # TODO: understand these ID's better
        self.currentID = IMG_CONTROLS[0]
        self.nextID    = IMG_CONTROLS[1]
        
        # sets the first image
        # self.setImage(self.currentID)
        # self.log("settings Last" + REAL_SETTINGS.getSetting("Last"), xbmc.LOGERROR)
        self.log("settings RotateTime" + REAL_SETTINGS.getSetting("RotateTime"), xbmc.LOGERROR)
        # REAL_SETTINGS.getSetting("RotateTime")
        # screensaver is running
        while not KODI_MONITOR.abortRequested():
            # self.log("settings Last" + REAL_SETTINGS.getSetting("Last"), xbmc.LOGERROR)
            self.log("settings RotateTime" + REAL_SETTINGS.getSetting("RotateTime"), xbmc.LOGERROR)
            # handles the swapping out of images cleanly
            self.getControl(self.nextID).setVisible(False)
            self.getControl(self.currentID).setVisible(True)
            self.nextID    = self.currentID # I think the naming convention for these is backwards currentID -> nextID
            self.currentID = CYC_CONTROL() # how does the CYC_CONTROL() provide a new ID?
            
            # set the image once we are in the loop
            self.setImage(self.currentID)
            self.log("TIMER: " + str(TIMER), xbmc.LOGERROR)
            # self.log("KODI_MONITOR.waitForAbort(TIMER) type: " + type(KODI_MONITOR.waitForAbort(TIMER)), xbmc.LOGERROR)
            # stops the screensaver
            # if KODI_MONITOR.waitForAbort(TIMER) == True or self.isExiting == True: break
            # TODO: Fix the TIMER value to pickup from the settings. 0 in the settings and not defaulting to a value in the list.
            if KODI_MONITOR.waitForAbort(TIMER) == True or self.isExiting == True: break
            
        # # sets the last image as the cached result to pick up where we left off
        REAL_SETTINGS.setSetting("Last",self.baseAPI)

                     
    def onAction(self, action):
        # not called by this script
        self.isExiting = True
        self.close()