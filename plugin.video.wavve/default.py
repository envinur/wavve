# -*- coding: utf-8 -*-

import os
import inputstreamhelper
from resources.lib.wavve import *
import xbmcplugin, xbmcgui, xbmcaddon
import time
from urllib.parse import parse_qsl, urlparse, quote_plus, urlencode, quote, unquote
from urllib.request import Request, urlopen

__addon__ = xbmcaddon.Addon()
__language__ = __addon__.getLocalizedString
__profile__ = xbmc.translatePath(__addon__.getAddonInfo('profile'))
__version__ = __addon__.getAddonInfo('version')
__id__ = __addon__.getAddonInfo('id')
__name__ = __addon__.getAddonInfo('name')
__cwd__ = xbmc.translatePath(__addon__.getAddonInfo('path'))

SHOW_GRADE = __addon__.getSetting('show_grade')
ONLY_NINETEEN = __addon__.getSetting('show_only_over_19')
HIDE_ADULT_Contents = __addon__.getSetting('hide_adult_contents_list')

# root
def dp_main():
    addon_log('Display main!')
    # login process
    wavve_id, wavve_pw = __addon__.getSetting('id'), __addon__.getSetting('pwd')

    if wavve_id and wavve_pw:
        # check login
        if not Wavve().GetCredential(wavve_id, wavve_pw):
            # login failed
            addon_noti(__language__(30203).encode('utf8'))
    else:
        dialog = xbmcgui.Dialog()
        ret = dialog.yesno(__name__, __language__(30201).encode('utf8'), __language__(30202).encode('utf8'))
        if ret:
            __addon__.openSettings()
            sys.exit()
    items = [
            {'title': __language__(30009).encode('utf8'), 'category': 'Live'},
            {'title': __language__(30004).encode('utf8'), 'category': 'VOD'},
            {'title': __language__(30005).encode('utf8'), 'category': 'Movie'},
            {'title': __language__(30011).encode('utf8'), 'category': 'ProgramList'},
            {'title': __language__(30006).encode('utf8'), 'category': 'Search'}
            ]
    for item in items:
        addDir(item)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def dp_live_list_sub(p):
    mode = p['category']
    submode = '%s_Sub' % mode
    item = {'category': submode, 'title': '전체 장르', 'genre': 'all'}
    addDir(item)
    genres = Wavve().GetListSub(mode)
    for genre in genres:
        addon_log('Display %s List!' % submode)
        item = dict(category=submode, title=genre['text'], genre=genre['id'])
        addDir(item)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def dp_vod_sub1():
    addon_log('Display VOD sub1!')
    submode = 'VOD_Sub1'
    items = [['최신순', 'VN1'],
             ['인기순', 'VN2'],
             ['신규순', 'VN28'],
             ['어제 %s요일 프로그램', 'VN21']]
    for item in items:
        title = item[0] % Wavve().GetWeekday() if item[1] == 'VN21' else item[0]
        param = dict(title=title, id=item[1], category=submode)
        addDir(param)
    items = Wavve().GetListSub('vod')
    for item in items:
        for order in [['최신순', 'new'], ['인기순', 'viewtime'], ['가나다순', 'title']]:
            param = dict(title='%s - %s' % (item['text'], order[0]), id=item['id'], category=submode, order=order[1])
            addDir(param)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def dp_vod_sub2(p):
    addon_log('Display %s!' % p['category'])
    id = p['id']
    if 'order' in p: order = p['order']
    if id in ['VN1', 'VN2', 'VN28', 'VN21']:
        url = 'https://apis.pooq.co.kr/cf/deeplink/%s' % id
        req = Request(url)
        resp = urlopen(req)
        resp_json = json.load(resp)
        p['url'] = resp_json['url']
        dp_vod_title(p)
    else:
        submode = 'VOD_Sub2'
        items = Wavve().GetListSub('vod')
        for item in items:
            if id == item['id']:
                for sublist in item['sublist']:
                    param = dict(title=sublist['text'], order=order, url=sublist['url'], category=submode)
                    addDir(param)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

def dp_vod_title(p):
    mode = p['category']
    addon_log('Display %s' % mode)
    submode = 'VOD_Episode'
    pageno = int(p.get('pageno', 1))
    order = p.get('order', None)
    url = p['url']
    items = Wavve().GetVODList(pageno, url, order)
    if 'celllist' in items:
        for list in items['celllist']:
            if 'contenttype=vod' in url:
                submode = 'VOD_Sub_List'
                title = list['title_list'][0]['text'].replace('&lt;', '<').replace('&gt;', '>')
                item = {'category': submode, 'title': title, 'img': list['thumbnail'],
                        'age': list['age'] or '0'}
                for bodylist in list['event_list'][0]['bodylist']:
                    if bodylist.startswith('uicode:'):
                        item['code'] = bodylist[7:]
                        pass
                item['sub_title'] = list['title_list'][1]['text'].replace('&lt;', '<').replace('&gt;', '>').replace(' $O$ ',' ')
                infoLabels = {'mediatype': 'episode', "title": title,
                              "plot": item['sub_title']
                              if 'sub_title' in item else item['title']}
                addDir(item, infoLabels)
            else:
                item = {'category': submode, 'title': list['title_list'][0]['text'], 'pageno': pageno,
                        'img': list['thumbnail'],  'age': list['age'] or '0'}
                for bodylist in list['event_list'][0]['bodylist']:
                    if bodylist.startswith('uicode'):
                        if 'contentid' in list['event_list'][1]['url']:
                            item['code'] =  bodylist[7:]
                        else:
                            item['pcode'] = bodylist[7:]
                        pass
                addDir(item)
    if pageno != 1:
        item = p
        item['pageno'] = pageno - 1
        item['title'] = '<< '.encode('utf8') + __language__(30012)
        addDir(item)
    if int(items['pagecount']) > Wavve().limit:
        item = p
        item['pageno'] = pageno + 1
        item['title'] = __language__(30002).encode('utf8') + ' >>'.encode('utf8')
        addDir(item)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def dp_vod_list(p):
    mode = p['category']
    addon_log('Display %s' % mode)
    submode = 'VOD_Sub_List'
    pageno_ep = int(p.get('pageno_ep', 1))
    if not 'pcode' in p:
        p['pcode'] = Wavve().Getpcode(p['code'])['programid']
    code = p['pcode']
    items = Wavve().GetVODEpisode(code, pageno_ep)
    addon_log('%s!!!!' % items)
    if 'list' in items:
        for item in items['list']:
            title = item['episodetitle'].replace('&lt;', '<').replace('&gt;', '>').encode('UTF-8')
            epno = item['episodenumber'].encode('UTF-8')
            if title:
                if epno not in title: title += ' %s회'.encode('UTF-8') % epno
            else: title = '%s회'.encode('UTF-8') % epno
            plot = item['synopsis'].replace('<br>', '').replace('</br>', '').replace(
                              '<b>', '[B]').replace('</b>', '[/B]') if 'synopsis' in item else item['episodetitle']
            param = {'category': submode, 'title': title, 'img': item['image'],
                     'code': item['contentid'], 'pcode': code, 'programimage': p['img'],
                     'age': item['targetage'] or '0'}
            if plot: param['plot'] = quote(plot)
            param['programtitle'] = quote(item['programtitle'].encode('UTF-8'))
            infoLabels = {'mediatype': 'episode', "title": item['episodetitle'],
                          "plot": plot}
            addDir(param, infoLabels)
    if pageno_ep != 1:
        item = p
        item['pageno_ep'] = pageno_ep - 1
        item['title'] = '<< ' + __language__(30012).encode('utf8')
        addDir(item)
    if int(items['pagecount']) > Wavve().limit:
        item = p
        item['pageno_ep'] = pageno_ep + 1
        item['title'] = __language__(30002).encode('utf8') + ' >>'
        addDir(item)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def dp_movie_sub1():
    addon_log('Display movie sub1!')
    submode = 'Movie_Sub1'
    items = [
        {'title': 'wavvie', 'category': submode, 'type': 'wavvie'},
        {'title': 'PLAYY', 'category': submode, 'type': 'playy'},
        {'title': 'All', 'category': submode, 'type': 'all'}
    ]
    for item in items:
        title = item['title']
        for order in [['업데이트순', 'regdate'], ['개봉일순', 'release'], ['인기순', 'viewtime'], ['가나다순', 'title']]:
            param = item
            param['title'] = '%s 영화관 - %s' % (title, order[0])
            param['order'] = order[1]
            addDir(param)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def dp_movie_sub2(p):
    mode = 'Movie'
    submode = 'Movie_Sub'
    order = p['order']
    type = p['type']
    item = dict(category=submode,
                url='apis.wavve.com/cf/movie/contents?WeekDay=all&broadcastid=132257&came=movie&contenttype=movie&genre=all&limit=20&offset=0&price=all&uiparent=FN0&uirank=0&uitype=MN4&apikey=E5F3E0D30947AA5440556471321BB6D9',
                type=type,
                title='전체',
                order=order)
    addDir(item)
    params = Wavve().GetListSub(mode)
    for param in params:
        item = dict(category=submode, url=param['url'], type=type, title=param['text'], order=order)
        addDir(item)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def dp_list(p):
    mode = p['category']
    if 'type' in p: type = p['type']
    if 'order' in p: order = p['order']
    submode = '%s_List' % mode
    addon_log('Display %s List!' % mode)
    pageno = int(p.get('pageno', 1))
    if mode == 'Live_Sub':
        genre = p['genre']
        items = Wavve().GetLiveList(pageno, genre)
        epgitems = Wavve().GetEPGList(genre)
    elif mode == 'Movie_Sub':
        url = p['url']
        items = Wavve().GetMovieList(pageno, url, order, type)
    if 'celllist' in items:
        for list in items['celllist']:
            title = list['title_list'][0]['text'].replace('&lt;', '<').replace('&gt;', '>')
            item = {'category': submode, 'title': title,
                    'img': list['thumbnail'], 'age': list['age'] or '0'}
            for bodylist in list['event_list'][0]['bodylist']:
                if bodylist.startswith('uicode:'):
                    item['code'] = bodylist[7:]
                    pass
            infoLabels = {'mediatype': 'episode', "title": title}
            if mode == 'Live_Sub':
                item['sub_title'] = list['title_list'][1]['text'].replace('&lt;', '<').replace('&gt;', '>')
                infoLabels['plot'] = epgitems.get(item['code'], title)
            else:
                infoLabels['plot'] = item['sub_title'] if 'sub_title' in item else item['title']
            addDir(item, infoLabels)
    if pageno != 1:
        item = p
        item['pageno'] = pageno - 1
        item['title'] = '<< '.encode('utf8') + __language__(30012).encode('utf8')
        addDir(item)
    if int(items['pagecount']) > Wavve().limit:
        item = p
        item['pageno'] = pageno + 1
        item['title'] = __language__(30002).encode('utf8') + ' >>'.encode('utf8')
        addDir(item)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def play_list(p):
    addon_log('Play Live!')
    mode = p['category'].lower().split('_')[0]
    code = p['code']
    age = p['age'] if 'age' else 0
    if code.startswith('PQV'):
        mode = 'onairvod'
    addon_log('%s!!' % code)
    quality_list = ['1080p', '720p', '480p', '360p', '100p']
    quality_idx = choose_stream_quality()
    if quality_idx is not None:
        quality = quality_list[quality_idx]
        addon_log('%s!!' % quality)
        # get stream url
        drm, url, awscookie = Wavve().GetStreamUrl(code, quality, mode)
        if 'preview' in url: addon_noti(__language__(30001).encode('utf-8'))
        item = xbmcgui.ListItem(path='%s|Cookie=%s' % (url, awscookie))
        if drm:
            PROTOCOL = "mpd"
            DRM = 'com.widevine.alpha'
            is_helper = inputstreamhelper.Helper(PROTOCOL, drm=DRM)
            if is_helper.check_inputstream():
                item.setProperty('inputstream.adaptive.license_type', DRM)
                item.setMimeType('application/dash+xml')
                item.setContentLookup(False)
                header = {'DNT': '1', 'Origin': 'https://www.wavve.com',
                          'Referer': 'https://www.wavve.com/player/movie?movieid=%s' % code, 'Sec-Fetch-Mode': 'cors',
                          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36',
                          'Content-type': 'application/octet-stream', 'pallycon-customdata': drm['customdata']}
                item.setProperty('inputstreamaddon', 'inputstream.adaptive')
                item.setProperty('inputstream.adaptive.manifest_type', PROTOCOL)
                item.setProperty('inputstream.adaptive.license_key', '%s|%s|R{SSM}|' % (drm['drmhost'], urlencode(header)))
                item.setProperty('inputstream.adaptive.stream_headers', 'Cookie=%s' % awscookie)
                addon_log(urlencode(header))
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
        param = dict(category='VOD_Episode' if p['category'] == 'VOD_Sub_List' else p['category'], age=age)
        if p['category'] == 'VOD_Sub_List':
            programitems = Wavve().Getpcode(code)
            if programitems['programid']:
                param['pcode'] = programitems['programid']
                param['ptitle'] = quote(programitems['programtitle'].encode('UTF-8'))
                param['pimg'] = programitems['programimage']
            else:
                param['pcode'] = p['pcode']
                param['ptitle'] = p['ptitle']
                param['pimg'] = p['pimg']
            if programitems['programsynopsis']:
                param['pplot'] = quote(programitems['programsynopsis'].encode('UTF-8'))
            elif 'pplot' in p:
                param['pplot'] = p['pplot']
            title = programitems['episodetitle'].replace('&lt;', '<').replace('&gt;', '>').encode('UTF-8')
            programtitle = programitems['programtitle'].encode('UTF-8')
            if programtitle not in title: title = '%s - %s' % (programtitle, title)
            epno = programitems['episodenumber'].encode('UTF-8')
            plot = ''
            data = urlencode(sorted(param.items(), key=lambda val: val[0]))
            Wavve().SaveProgramList(data, 'program')
            param['category'] = 'VOD_Sub_List'
            if code == programitems['contentid']:
                if title:
                    if epno not in title: title += ' %s회'.encode('UTF-8') % epno
                else: title = '%s회'.encode('UTF-8') % epno
                param['title'] = quote(title)
                plot = programitems['synopsis'].replace('<br>', '').replace('</br>', '').replace(
                    '<b>', '[B]').replace('</b>', '[/B]')
        elif p['category'] == 'Movie_Sub_List':
            movieitems = Wavve().GetMovieInfo(code)
            plot = movieitems['synopsis'].replace('<br>', '').replace('</br>', '').replace(
                '<b>', '[B]').replace('</b>', '[/B]')
        else: plot = ''
        if 'img' in p:
            param['img'] = p['img'].split('?')[0] if '?' in p['img'] else p['img']
        if plot:
            param['plot'] = quote(plot)
        elif 'plot' in p:
            param['plot'] = p['plot']
        param['code'] = code
        if 'title' not in param: param['title'] = unquote(p['title'])
        data = urlencode(sorted(param.items(), key=lambda val: val[0]))
        if mode == 'live':
            Wavve().SaveProgramList(data, 'live')
        elif mode == 'movie':
            if int(age) < 18:
                Wavve().SaveProgramList(data, 'movie_general')
            else:
                Wavve().SaveProgramList(data, 'movie_adult')
        else:
            Wavve().SaveProgramList(data, 'vod')
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

def dp_program_list():
    items = [
            {'title': __language__(30009).encode('utf8'), 'type': 'live'},
            {'title': __language__(30013).encode('utf8'), 'type': 'program'},
            {'title': __language__(30014).encode('utf8'), 'type': 'vod'},
            {'title': __language__(30015).encode('utf8'), 'type': 'movie_general'},
            {'title': __language__(30016).encode('utf8'), 'type': 'movie_adult'}
            ]
    for item in items:
        if HIDE_ADULT_Contents == 'true' and item['type'] == 'movie_adult': continue
        item['category']= 'ProgramList_%s' % item['type']
        addDir(item)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def dp_program_list_sub(p):
    mode = p['category'][12:]
    addon_log(mode+'!!!')
    items = Wavve().LoadProgramList(mode)
    if mode == 'live': epgitems = Wavve().GetEPGList('all')
    for item in items:
        param = dict(parse_qsl(item.rstrip()))
        if param['category'] == 'VOD_Episode':
            param['title'] = unquote(param['ptitle'])
            param['img'] = param['pimg']
            infoLabels = {'mediatype': 'season', "title": param['title']}
            if "pplot" in param:  infoLabels['plot'] = unquote(param['pplot'])
        else:
            param['title'] = unquote(param['title'])
            infoLabels = {'mediatype': 'episode', "title": param['title']}
            if mode == 'live':
                infoLabels['plot'] = epgitems.get(param['code'], param['title'])
                if param['code'] in epgitems: param['sub_title'] = epgitems[param['code']].split('\n')[0]
            elif 'plot' in param: infoLabels['plot'] = unquote(param['plot'])
        addDir(param, infoLabels)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def dp_search():
    addon_log('dp_search!!')
    submode = 'Search_Sub'
    items = [
            {'title': __language__(30009).encode('utf8'), 'searchby': 'live'},
            {'title': __language__(30013).encode('utf8'), 'searchby': 'program'},
            {'title': __language__(30014).encode('utf8'), 'searchby': 'vod'},
            {'title': __language__(30005).encode('utf8'), 'searchby': 'movie'}
            ]
    for item in items:
        item['category']= submode
        addDir(item)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def search_list(p):
    addon_log('search_list!')
    searchby = p['searchby']
    pageno = int(p.get('pageno', 1))

    kwd = p['kwd'] if 'kwd' in p else get_keyboard_input(__language__(30003).encode('utf-8'))
    if kwd:
        try:
            items = Wavve().Search(searchby, kwd, pageno)
            if 'celllist' in items:
                for list in items['celllist']:
                    submodelist = dict(live='Live_Sub_List', movie='Movie_Sub_List', vod= 'VOD_Sub_List')
                    if searchby in submodelist:
                        submode = submodelist[searchby]
                        title = list['title_list'][0]['text'].replace('&lt;', '<').replace('&gt;', '>')
                        item = {'category': submode, 'title': title, 'img': list['thumbnail'],
                                'age': list['age'] or '0'}
                        for bodylist in list['event_list'][0]['bodylist']:
                            if bodylist.startswith('uicode:'):
                                item['code'] = bodylist[7:]
                                pass
                        if searchby in ['live', 'vod']:
                            item['sub_title'] = list['title_list'][1]['text'].replace('&lt;', '<').replace('&gt;', '>').replace(' $O$ ',' ')
                        infoLabels = {'mediatype': 'episode', "title": title,
                                      "plot": item['sub_title']
                                      if 'sub_title' in item else item['title']}
                        addDir(item, infoLabels)
                    else:
                        submode = 'VOD_Episode'
                        item = {'category': submode, 'title': list['title_list'][0]['text'], 'pageno': pageno,
                                'img': list['thumbnail'], 'age': list['age'] or '0'}
                        for bodylist in list['event_list'][0]['bodylist']:
                            if bodylist.startswith('uicode'):
                                if 'contentid' in list['event_list'][1]['url']:
                                    item['code'] = bodylist[7:]
                                else:
                                    item['pcode'] = bodylist[7:]
                        addDir(item)
            if pageno != 1:
                item = dict(pageno = int(pageno)-1, category = p['category'], kwd = kwd, searchby = searchby)
                item['title'] = '<< ' + __language__(30012).encode('utf8')
                addDir(item)
            if int(items['pagecount']) > Wavve().limit:
                item = dict(pageno = int(pageno)+1, category = p['category'], kwd = kwd, searchby = searchby)
                item['title'] = __language__(30002).encode('utf8') + ' >>'
                addDir(item)
            xbmcplugin.endOfDirectory(int(sys.argv[1]))
        except:
            addon_noti(__language__(30206).encode('utf8'))


def get_keyboard_input(heading, hidden=False):
    input_text = None
    kb = xbmc.Keyboard()
    kb.setHeading(heading)
    if hidden: kb.setHiddenInput(hidden)
    xbmc.sleep(1000)
    kb.doModal()
    if (kb.isConfirmed()):
        input_text = kb.getText()
    return input_text

def choose_stream_quality():
    isManualQuality = __addon__.getSetting('manual_quality')
    if isManualQuality == 'true':
        list = [__language__(30104).encode('utf-8'),
                __language__(30105).encode('utf-8'),
                __language__(30106).encode('utf-8'),
                __language__(30107).encode('utf-8'),
                __language__(30110).encode('utf-8'),
                ]
        choose_idx = xbmcgui.Dialog().select(__language__(30205).encode('utf-8'), list)
        return choose_idx
    else:
        sel_quality_idx = int(__addon__.getSetting('selected_quality'))
    return sel_quality_idx

def addon_noti(sting):
    try:
        dialog = xbmcgui.Dialog()
        dialog.notification(__name__, sting)
    except:
        addon_log('addonException: addon_noti')

def addon_log(string, isDebug=False):
    try:
        log_message = string.encode('utf-8', 'ignore')
    except Exception as e:
        log_message = e.message
    if isDebug:
        level = xbmc.LOGDEBUG
    else:
        level = xbmc.LOGNOTICE
    xbmc.log("[%s-%s]: %s" % (__id__, __version__, log_message), level=level)

def addDir(item, infoLabels=None):
    title = item['title']
    if 'age' in item:
        age = int(item['age'])
        if SHOW_GRADE == 'true':
            if (age == 21):
                title = "[19+] " + title
            elif (age == 18):
                title = "[19] " + title
            elif ONLY_NINETEEN == 'false':
                if age > 0 and age != 21 and age:
                    title = "[%s] %s" % (age, title)
    else: age = 0
    item['title'] = quote(item['title'])
    if 'sub_title' in item:
        if item['sub_title']: title += ' - %s ' % item.pop('sub_title')
    img = 'http://%s' % item['img'] if 'img' in item else 'DefaultFolder.png'
    if item['category'] == 'Live_Sub_List': img += '?timestamp=%s' % int(time.time())
    url = '%s?%s' % (sys.argv[0], urlencode(item))
    listitem = xbmcgui.ListItem(title)
    listitem.setArt({'thumbnailImage':img, 'icon':img, 'poster': img})
    if infoLabels is None:
        isfolder = True
    else:
        if age:
           infoLabels['mpaa'] = 18 if age > 18 else age
        else: infoLabels['mpaa'] = 'ALL'
        listitem.setInfo(type="Video", infoLabels=infoLabels)
        if item['category'] != 'VOD_Episode':
            listitem.setProperty('IsPlayable', 'true')
            isfolder = False
        else:
            isfolder = True
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, isfolder)

def get_params():
    p = dict(parse_qsl(sys.argv[2][1:]))
    return p

params = get_params()
try:
    mode = params['category']
except:
    mode = None

if mode == None:
    dp_main()
elif mode == 'Live':
    dp_live_list_sub(params)
elif mode == 'Movie':
    dp_movie_sub1()
elif mode == 'Movie_Sub1':
    dp_movie_sub2(params)
elif mode == 'VOD':
    dp_vod_sub1()
elif mode == 'VOD_Sub1':
    dp_vod_sub2(params)
elif mode == 'VOD_Sub2':
    dp_vod_title(params)
elif mode == 'VOD_Episode':
    dp_vod_list(params)
elif mode in ['Movie_Sub', 'Live_Sub']:
    dp_list(params)
elif mode in ['VOD_Sub_List', 'Movie_Sub_List', 'Live_Sub_List']:
    play_list(params)
elif mode == 'ProgramList':
    dp_program_list()
elif mode in ['ProgramList_live', 'ProgramList_program', 'ProgramList_vod', 'ProgramList_movie_general', 'ProgramList_movie_adult']:
    dp_program_list_sub(params)
elif mode == 'Search':
    dp_search()
elif mode == 'Search_Sub':
    search_list(params)
else:
    addon_log('################### funcs not defined ###################')
