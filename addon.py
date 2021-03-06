# coding: utf-8
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
import re
import sys
import json
from datetime import datetime
import inputstreamhelper

try:
    from urllib.parse import parse_qsl
    from urllib.request import Request as urllib_Request
    from urllib.request import HTTPHandler, HTTPSHandler, urlopen, install_opener, build_opener
except ImportError:
    from urllib2 import Request as urllib_Request
    from urllib2 import urlopen, install_opener, build_opener, HTTPError, HTTPSHandler, HTTPHandler
    from urlparse import parse_qsl

import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin

# import web_pdb


API_VERSION = "v2"
API_BASEURL = "https://services.err.ee/api/{}/".format(API_VERSION)
UA = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1'

# Get the plugin url in plugin:// notation.
PATH = sys.argv[0]
# Get the plugin _handle as an integer number.
_handle = int(sys.argv[1])

FANART = 'https://s.err.ee/photo/crop/2020/03/30/765343had90t16.png'

__settings__ = xbmcaddon.Addon(id='plugin.video.jupiter.err.ee')

KODI_VERSION_MAJOR = int(xbmc.getInfoLabel('System.BuildVersion').split('.')[0])
PROTOCOL = 'mpd'
DRM = 'com.widevine.alpha'
MIME_TYPE = 'application/dash+xml'
is_helper = inputstreamhelper.Helper(PROTOCOL, drm=DRM)

def download_url(url, header=None):
    for retries in range(0, 5):
        try:
            r = urllib_Request(url)
            r.add_header('User-Agent', UA)
            if header:
                for h_key, h_value in header.items():
                    r.add_header(h_key, h_value)
            http_handler = HTTPHandler(debuglevel=0)
            https_handler = HTTPSHandler(debuglevel=0)
            opener = build_opener(http_handler, https_handler)
            install_opener(opener)
            u = urlopen(r)
            contents = u.read()
            u.close()
            return contents
        except:
            raise RuntimeError('Could not open URL: {}'.format(url))


def listCategory():
    items = list()
    # create main menu. There is no good api that includes A-Ü, so let's do it manually for now
    # video
    item = xbmcgui.ListItem('[COLOR %s]Video[/COLOR]' % get_colour(__settings__.getSetting('colourCategory')))
    item.setArt({'fanart': FANART, 'poster': FANART, 'icon': FANART})
    items.append((PATH + '?action=category&category={}'.format('saated'), item, False))
    item = xbmcgui.ListItem(' Saated')
    item.setArt({'fanart': FANART})
    items.append((PATH + '?action=category&category={}'.format('v-saated'), item, True))
    item = xbmcgui.ListItem(' Sarjad')
    item.setArt({'fanart': FANART})
    items.append((PATH + '?action=category&category={}'.format('sarjad'), item, True))
    item = xbmcgui.ListItem(' Filmid')
    item.setArt({'fanart': FANART})
    items.append((PATH + '?action=category&category={}'.format('filmid'), item, True))
    item = xbmcgui.ListItem(' Sport')
    item.setArt({'fanart': FANART})
    items.append((PATH + '?action=category&category={}'.format('sport'), item, True))
    item = xbmcgui.ListItem(' Saated A-Ü')
    item.setArt({'fanart': FANART})
    items.append((PATH + '?action=listing&category={}'.format('video'), item, True))
    # audio
    item = xbmcgui.ListItem('[COLOR %s]Audio[/COLOR]' % get_colour(__settings__.getSetting('colourCategory')))
    item.setArt({'fanart': FANART, 'poster': FANART, 'icon': FANART})
    items.append((PATH + '?action=category&category={}'.format('audio'), item, False))
    item = xbmcgui.ListItem(' Saated')
    item.setArt({'fanart': FANART})
    items.append((PATH + '?action=category&category={}'.format('audio'), item, True))
    item = xbmcgui.ListItem(' Muusika')
    item.setArt({'fanart': FANART})
    items.append((PATH + '?action=category&category={}'.format('muusika'), item, True))
    item = xbmcgui.ListItem(' Raadioteater')
    item.setArt({'fanart': FANART})
    items.append((PATH + '?action=category&category={}'.format('raadioteater'), item, True))
    item = xbmcgui.ListItem(' Saated A-Ü')
    item.setArt({'fanart': FANART})
    items.append((PATH + '?action=listing&category={}'.format('audio'), item, True))
    # make menu
    xbmcplugin.addDirectoryItems(_handle, items)
    xbmcplugin.endOfDirectory(_handle)


def get_category(category):
    # web_pdb.set_trace()
    url = API_BASEURL + 'category/getByUrl?url={}&domain=jupiter.err.ee'.format(category)
    # xbmc.log('%s url: %s' % (category, url), xbmc.LOGNOTICE)
    items = list()

    data = json.loads(download_url(url))
    # xbmc.log('Data: %s' % data, xbmc.LOGNOTICE)
    for header in data["data"]["category"]["frontPage"]:
        # xbmc.log('Header item: %s' % header["header"].encode('ascii', 'ignore'), xbmc.LOGNOTICE)
        item = xbmcgui.ListItem("[COLOR {}]{}[/COLOR]".format(get_colour(__settings__.getSetting('colourCategory')), header['header']))
        items.append((PATH, item))
        for content in header["data"]:
            plot = ''
            fanart = ''
            if 'lead' in content:
                plot = strip_tags(content['lead'])
            info_labels = {'title': content["heading"], 'plot': plot}
            try:
                if 'photoUrlOriginal' in content['verticalPhotos'][0]:
                    fanart = content['verticalPhotos'][0]['photoUrlOriginal']
            except KeyError:
                try:
                    if 'photoTypes' in content['photos'][0]:
                        fanart = content['photos'][0]['photoTypes']['5']['url']
                except KeyError:
                    pass

            item = xbmcgui.ListItem(content["heading"])
            if 'true' in __settings__.getSetting('enableImages'):
                item.setArt({'fanart': fanart, 'poster': fanart, 'icon': fanart})
            item.setInfo(type="Video", infoLabels=info_labels)
            items.append((PATH + '?action=section&section={}&sub=false'.format(content["id"]), item, True))
    xbmcplugin.addDirectoryItems(_handle, items)
    xbmcplugin.endOfDirectory(_handle)


def get_section(section, sub=''):
    # web_pdb.set_trace()
    url = API_BASEURL + 'vodContent/getContentPageData?contentId={}'.format(section)
    items = list()
    data = json.loads(download_url(url), encoding='utf-8')
    content_type = data['data']['pageType']
    if 'type' in data['data']['seasonList']:
        season_type = data['data']['seasonList']['type']
    if content_type in ('series') or sub == 'marine':
        for season in data['data']['seasonList']['items']:
            try:
                # Season
                item = xbmcgui.ListItem("[COLOR {}]Hooaeg: {}[/COLOR]".format(get_colour(__settings__.getSetting('colourSeason')),str(season['id'])))
                items.append(
                    (PATH + '?action=section&section={}&sub=marine'.format(season['firstContentId']), item, True))
            except:
                pass
            if season_type == 'monthly':
                for month in season['items']:
                    item = xbmcgui.ListItem(" [COLOR {}]{}[/COLOR]".format(get_colour(__settings__.getSetting('colourCategory')), month['name']))
                    # item.setArt({'fanart': fanart, 'poster': fanart, 'icon': fanart})
                    items.append(
                        (PATH + '?action=section&section={}&sub=marine'.format(month['firstContentId']), item, True))
                    try:
                        for day in month['contents']:
                            fanart = ''
                            title = ''
                            if day['episode'] > 0:
                                title = day['heading'] + " " + str(day['episode'])
                            else:
                                title = day['heading']
                            # no plot, use on-air date
                            plot = convert_timestamp(day['scheduleStart'])
                            info_labels = {'title': title, 'plot': plot}
                            # get photos if posible
                            if 'horizontalPhotos' in day:
                                if 'photoUrlOriginal' in day['horizontalPhotos'][0]:
                                    fanart = day['horizontalPhotos'][0]['photoUrlOriginal']
                            elif 'photos' in day:
                                if 'photoUrlOriginal' in day['photos'][0]:
                                    fanart = day['photos'][0]['photoUrlOriginal']
                            item = xbmcgui.ListItem("  {}".format(title))
                            if 'true' in __settings__.getSetting('enableImages'):
                                item.setArt({'fanart': fanart, 'poster': fanart, 'icon': fanart})
                            item.setInfo(type="Video", infoLabels=info_labels)
                            items.append((PATH + '?action=section&section={}&sub=false'.format(day['id']), item, True))
                    except (KeyError, IndexError):
                        pass
            elif season_type in ('seasonal', 'shortSeriesList'):
                try:
                    for episood in season['contents']:
                        # xbmc.log(' EpisoodiId: %s' % str(episood['id']), xbmc.LOGNOTICE)
                        fanart = ''
                        if 'subHeading' in episood and len(episood['subHeading']) > 2:
                            title = episood['subHeading']
                        elif 'heading' in episood:
                            title = episood['heading']
                        else:
                            title = str(episood['episode'])

                        if 'photoUrlOriginal' in episood['photos'][0]:
                            fanart = episood['photos'][0]['photoUrlOriginal']
                        item = xbmcgui.ListItem(title)
                        if 'true' in __settings__.getSetting('enableImages'):
                            item.setArt({'fanart': fanart, 'poster': fanart, 'icon': fanart})
                        items.append((PATH + '?action=section&section={}&sub=false'.format(episood['id']), item, True))
                except:
                    pass
    elif content_type in ('movie', 'episode'):
        fanart = ''
        sub = []
        languages = []
        languages.extend((
            get_subtitle_language(__settings__.getSetting('primaryLanguage')),
            get_subtitle_language(__settings__.getSetting('secondaryLanguage'))
        ))

        title = data['data']['mainContent']['heading']
        video = data['data']['mainContent']['medias'][0]['src']['hls'].replace('//', 'http://', 1)
        plot = strip_tags(data['data']['mainContent']['body'])
        drm = data['data']['mainContent']['medias'][0]['restrictions']['drm']
        # we can play DRM content
        if drm:
            # title = '[COLOR {}][I]{}[/I][/COLOR]'.format(get_colour(__settings__.getSetting('colourUnplayable')),title)
            token = data['data']['mainContent']['medias'][0]['jwt']
            license_server = data['data']['mainContent']['medias'][0]['licenseServerUrl']['widevine']
            video = data['data']['mainContent']['medias'][0]['src']['dash'].replace('//', 'https://', 1)
        info_labels = {'title': title, 'plot': plot}
        try:
            for language in languages:
                for subtitle in data['data']['mainContent']['medias'][0]['subtitles']:
                    if subtitle['srclang'] == language:
                        sub = (subtitle['src'], language)
                        break
        except KeyError:
            pass
        # web_pdb.set_trace()
        if 'photoUrlOriginal' in data['data']['mainContent']['photos'][0]:
            fanart = data['data']['mainContent']['photos'][0]['photoUrlOriginal']
        item = xbmcgui.ListItem(title, path=video)
        if 'true' in __settings__.getSetting('enableImages'):
            item.setArt({'fanart': fanart, 'poster': fanart, 'icon': fanart})
        item.setInfo(type="Video", infoLabels=info_labels)
        item.setProperty('IsPlayable', 'True')
        item.setProperty('isFolder', 'False')
        if drm:
            if is_helper.check_inputstream():
               item.setContentLookup(False)
               item.setMimeType(MIME_TYPE)
               if KODI_VERSION_MAJOR >= 19:
                item.setProperty('inputstream', is_helper.inputstream_addon)
               else:
                item.setProperty('inputstreamaddon', is_helper.inputstream_addon)
               item.setProperty('inputstream.adaptive.manifest_type', PROTOCOL)
               item.setProperty('inputstream.adaptive.license_type', DRM)
               item.setProperty('inputstream.adaptive.license_key', license_server + '|X-AxDRM-Message='+token+'|R{SSM}|')     
        try:
            if sub:
                item.setSubtitles(sub)
        except:
            pass

        items.append((video, item))
    xbmcplugin.addDirectoryItems(_handle, items)
    xbmcplugin.endOfDirectory(_handle)


def get_all_shows(type):
    url = API_BASEURL + 'series/getSeriesData?type={}'.format(type)
    # xbmc.log('url: %s' % url, xbmc.LOGNOTICE)
    items = list()
    data = json.loads(download_url(url))
    for show in data['data']['items']:
        item = xbmcgui.ListItem("{}".format(show['heading']))
        if 'photoUrlOriginal' in show['photos'][0]:
            fanart = show['photos'][0]['photoUrlOriginal']
            if 'true' in __settings__.getSetting('enableImages'):
                item.setArt({'fanart': fanart, 'poster': fanart, 'icon': fanart})
        items.append((PATH + '?action=section&section={}&sub=false'.format(show['id']), item, True))
    xbmcplugin.addDirectoryItems(_handle, items)
    xbmcplugin.endOfDirectory(_handle)


def get_subtitle_language(lang):
    # helper function to map human readable settings to required abbreviation
    if int(lang) == 0:
        return "ET"
    elif int(lang) == 1:
        return "VA"
    elif int(lang) == 2:
        return "RU"
    else:
        pass

def get_colour(color):
    colours = {
        0:'white',
        1:'ivory',
        2:'silver',
        3:'gray',
        4:'limegreen',
        5:'green',
        6:'lightblue',
        7:'blue',
        8:'deeppink',
        9:'turquoise',
        10:'gold',
        11:'yellow',
        12:'brown',
        13:'orange',
        14:'red'
    }
    return colours.get(int(color),'blue')

def convert_timestamp(input):
    return datetime.fromtimestamp(int(input)).strftime('%Y-%m-%d %H:%M:%S')


def strip_tags(string):
    # simple, unsafe stripper
    return re.sub('<[^<]+?>', '', string)


def router(paramstring):
    params = dict(parse_qsl(paramstring))
    if params:
        if params['action'] == 'category':
            get_category(params['category'])
        elif params['action'] == 'section':
            get_section(params['section'], params['sub'])
        elif params['action'] == 'listing':
            get_all_shows(params['category'])
        else:
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        listCategory()


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])
