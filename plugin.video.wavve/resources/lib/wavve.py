# -*- coding: utf-8 -*-

import os
import xbmc, xbmcaddon
import json
import re
import time
import pytz
from datetime import datetime, timedelta
from urllib2 import Request, urlopen, quote
from urlparse import parse_qsl, urlparse
from urllib import urlencode
from tzlocal import get_localzone
__profile__ = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
CREDENTIALDATA = xbmc.translatePath(os.path.join(__profile__, 'credential.dat'))



class Wavve(object):
    def __init__(self):
        self.api_domain = 'https://apis.wavve.com/'
        self.apikey = 'E5F3E0D30947AA5440556471321BB6D9'
        self.credential = 'none'
        self.device = 'pc'
        self.drm = 'WC'
        self.partner = 'pooq'
        self.pooqzone = 'none'
        self.region = 'kor'
        self.targetage = 'auto'
        self.limit = 30
        self.param = {'apikey': self.apikey,
                      'credential': self.credential,
                      'device': self.device,
                      'drm': self.drm,
                      'partner': self.partner,
                      'pooqzone': self.pooqzone,
                      'region': self.region,
                      'targetage': self.targetage}
    def GetGUID(self):
        import hashlib
        m = hashlib.md5()

        def GenerateID(media):
            requesttime = datetime.now().strftime('%Y%m%d%H%M%S')
            randomstr = GenerateRandomString(5)
            uuid = randomstr + media + requesttime
            return uuid

        def GenerateRandomString(num):
            from random import randint
            rstr = ""
            for i in range(0, num):
                s = str(randint(1, 5))
                rstr += s
            return rstr

        uuid = GenerateID("POOQ")
        m.update(uuid)

        return str(m.hexdigest())

    def GetWeekday(self):
        day = ['일', '월', '화', '수', '목', '금', '토', '일']
        weekday = datetime.utcnow().weekday()
        return day[weekday]
    def GetCredential(self, user_id, user_pw):
        isLogin = False
        try:
            url_path = 'login'
            params = self.param
            payload = {'id': user_id,
                       'password': user_pw,
                       "profile": '0',
                       'pushid': '',
                       'type': 'general'}
            data = urlencode(payload).encode()
            url = '%s%s?%s' % (self.api_domain, url_path ,urlencode(params))
            req = Request(url, data)
            resp = urlopen(req)
            resp_json = json.load(resp)
            credential = resp_json['credential']
            if credential: isLogin = True
            write_file(CREDENTIALDATA, credential)
        except:
            isLogin = False
        return isLogin

    def GetListSub(self, mode):
        try:
            url_path = 'cf/filters'
            type = '%sgenre' % mode.lower()
            params = self.param
            params['type'] = type
            url = '%s%s?%s' % (self.api_domain, url_path, urlencode(params))
            req = Request(url)
            resp = urlopen(req)
            resp_json = json.load(resp)
            items = resp_json[type]
        except:
            items = []
        return items

    def Getpcode(self, code):
        url_path = 'cf/vod/contents/'
        params = self.param
        url = '%s%s%s?%s' % (self.api_domain, url_path, code, urlencode(params))
        req = Request(url)
        resp = urlopen(req)
        resp_json = json.load(resp)
        return resp_json

    def GetMovieInfo(self, code):
        url_path = 'cf/movie/contents/'
        params = self.param
        url = '%s%s%s?%s' % (self.api_domain, url_path, code, urlencode(params))
        req = Request(url)
        resp = urlopen(req)
        resp_json = json.load(resp)
        return resp_json

    def GetVODEpisode(self, pcode, pageno_ep):
        params = self.param
        params.update({'orderby': 'new',
                       'limit': self.limit,
                       'offset': (pageno_ep - 1) * self.limit,
                      })
        url_path = 'vod/programs-contents/'
        url = '%s%s%s?%s' % (self.api_domain, url_path, pcode, urlencode(params))
        req = Request(url)
        resp = urlopen(req)
        resp_json = json.load(resp)
        return resp_json

    def GetVODList(self, pageno, url, order):
        try:
            u = urlparse('https://%s' % url)
            params = dict(parse_qsl(u.query))
            params.update(limit=self.limit, offset=(pageno - 1) * self.limit)
            if order: params.update(orderby=order)
            url = u._replace(query=urlencode(params)).geturl()
            req = Request(url)
            resp = urlopen(req)
            resp_json = json.load(resp)
            result = resp_json['cell_toplist']
        except:
            result = []
        return result

    def GetMovieList(self, pageno, url, order, type):
        try:
            u = urlparse('https://%s' % url)
            params = dict(parse_qsl(u.query))
            if type == 'wavvie':
                params.update(broadcastid='150905', sptheme='svod', uitype='MN85')
            elif type == 'playy':
                params.update(broadcastid='122681', sptheme='playy', uitype='MN85')
            params.update(limit=self.limit, offset=(pageno - 1) * self.limit, orderby=order)
            url = u._replace(query=urlencode(params)).geturl()
            req = Request(url)
            resp = urlopen(req)
            resp_json = json.load(resp)
            result = resp_json['cell_toplist']
        except:
            result = []
        return result

    def GetEPGList(self, genre):
        def CovertTime(t1, t2, timestring):
            if t1.hour == t2.hour and t1.minute == t2.minute:
                return timestring
            else:
                min =  t1.minute - t2.minute + int(timestring[-2:])
                hr = (t1.hour-t2.hour + int(timestring[:2]) + min // 60) % 24
                min %= 60
                return '%02d:%02d' % (hr, min)
        try:
            t1 = datetime.now(tz=get_localzone()).replace(second=0, microsecond=0) + timedelta(minutes=1)
            t2 = t1.astimezone(tz=pytz.timezone('Asia/Seoul'))
            starttime = t2.replace(second=0, microsecond=0) + timedelta(minutes=1)
            endtime = starttime + timedelta(hours=3)
            url_path = 'live/epgs'
            params = {'offset': '0',
                      'limit': '1000',
                      'genre': genre
                      }
            url = ('%s%s?%s&startdatetime=%s&enddatetime=%s' % (
            self.api_domain, url_path, urlencode(params), quote(starttime.strftime("%Y-%m-%d %H:%M")),
            quote(endtime.strftime("%Y-%m-%d %H:%M"))))
            req = Request(url)
            resp = urlopen(req)
            resp_json = json.load(resp)
            result = resp_json['list']
            epglist = {}
            for i in result:
                plot = ''
                for j in i['list']:
                    if plot: plot += '\n\n'
                    plot += j['title'].replace('&lt;', '<').replace('&gt;', '>')
                    plot += '\n%s ~ %s' % (CovertTime(t1,t2,j['starttime'][-5:]), CovertTime(t1,t2,j['endtime'][-5:]))
                epglist[i['channelid']] = plot
        except:
            epglist = []
        return epglist

    def GetLiveList(self, pageno, genre):
        try:
            url_path = 'cf/live/all-channels'
            params = self.param
            params.update({'offset': (pageno - 1) * self.limit,
                           'limit': self.limit,
                           'genre': genre
                           })
            url = '%s%s?%s' % (self.api_domain, url_path, urlencode(params))
            req = Request(url)
            resp = urlopen(req)
            resp_json = json.load(resp)
            result = resp_json['cell_toplist']
        except:
            result = []
        return result

    def GetStreamUrl(self, code, quality, mode):
        credential = load_file(CREDENTIALDATA)
        try:
            url_path = 'streaming'
            params = self.param
            params.update({'credential': credential, 'contentid': code, 'contenttype': mode,
                      'quality': quality, 'authtype': 'cookie', 'action': 'stream', 'drm': 'wm'})
            url = '%s%s?%s' % (self.api_domain, url_path, urlencode(params))
            req = Request(url)
            resp = urlopen(req)
            resp_json = json.load(resp)
            if resp_json['drm']:
                params['action'] = 'dash'
                url = '%s%s?%s' % (self.api_domain, url_path, urlencode(params))
                req = Request(url)
                resp = urlopen(req)
                resp_json = json.load(resp)
            playurl = resp_json['playurl']
            drm = resp_json['drm']
            awscookie = resp_json['awscookie']
        except:
            url_path = 'https://wapie.pooq.co.kr/'
            quality_list = {'1080p': '5000', '720p': '2000', '480p': '1000', '360p': "500", '100p': '0'}
            if mode == 'live':
                url_path += 'v1/lives30/%s/url' % code
                params = {'deviceTypeId': self.device,
                          'marketTypeId': 'generic',
                          'deviceModelId': 'Macintosh',
                          'drm': 'WM',
                          'country': self.region,
                          'authType': 'cookie',
                          'guid': self.GetGUID(),
                          'lastPlayId': 'none',
                          'credential': credential,
                          'quality': quality_list[quality]}
            else:
                if 'vod' in mode:
                    if mode == 'onairvod': mode = 'qvod'
                    code, cornerid = code.split('.')
                else: cornerid = '1'
                url_path += 'v1/permission30'
                params = {'deviceTypeId': self.device,
                          'marketTypeId': 'generic',
                          'deviceModelId': 'Macintosh',
                          'drm': 'WM',
                          'country': self.region,
                          'authType': 'cookie',
                          'guid': self.GetGUID(),
                          'lastPlayId': 'none',
                          'credential': credential,
                          'quality': quality_list[quality],
                          'type': mode,
                          'cornerId': cornerid,
                          'id': code,
                          'action': 'stream'}
            url = '%s?%s' % (url_path, urlencode(params))
            xbmc.Player().stop()
            t_end = time.time() + 15
            while time.time() < t_end:
                xbmc.sleep(500)
                req = Request(url)
                resp = urlopen(req)
                resp_json = json.load(resp)
                if resp_json['message'] == 'success': break
            resp_json = resp_json['result']
            playurl = resp_json['url']
            if mode == 'live':
                drm = ''
            elif resp_json['drmCustomData'] and resp_json['drmHost']:
                drm = {'customdata': resp_json['drmCustomData'], 'drmhost': resp_json['drmHost']}
            else:
                drm = ''
            awscookie = resp_json['awsCookie']
        return drm, playurl, awscookie

    def Search(self, type, keyword, pageno):
        try:
            url_path = 'cf/search/list.js'
            params = self.param
            params.update({'keyword': keyword,
                           'limit': self.limit,
                           'offset': (pageno - 1) * self.limit,
                           'orderby': 'score',
                           'type': type,
                          })
            url = '%s%s?%s' % (self.api_domain, url_path, urlencode(params))
            req = Request(url)
            resp = urlopen(req)
            resp_json = json.load(resp)
            result = resp_json['cell_toplist']
        except:
            result = []
        return result

    def LoadProgramList(self, mode):
        try:
            filename = xbmc.translatePath(os.path.join(__profile__, 'programlist_%s.txt' % mode))
            f = open(filename, 'r')
            result = f.readlines()
            f.close()
            return result
        except:
            result = []
        return result

    def SaveProgramList(self, data, file):
        try:
            filename = xbmc.translatePath(os.path.join(__profile__, 'programlist_%s.txt' % file))
            result = self.LoadProgramList(file)
            param = dict(parse_qsl(data))
            code = 'code' if 'code' in param else 'pcode'
            with open(filename, 'w') as fw:
                data = data.encode('utf-8') + '\n'
                fw.write(data)
                num = 1
                for line in result:
                    item = dict(parse_qsl(line))
                    if param[code] != item[code]:
                        fw.write(line)
                        num += 1
                    if num == 50: break
        except:
            pass
        return

def load_file(filename):
    try:
        with open(filename, "r") as f:
            data = f.read()
        f.close()
    except:
        data = None
    return data


def write_file(filename, data):
    try:
        with open(filename, "w") as f:
            f.write(str(data))
        f.close()
    except:
        pass
