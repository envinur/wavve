# -*- coding: utf-8 -*-

import os
import xbmc, xbmcaddon
import json
import re
try:
    from urllib2 import Request, urlopen
    from urlparse import parse_qsl, urlparse
    from urllib import  urlencode
except:
    from urllib.parse import parse_qsl, urlparse, urlencode
    from urllib.request import Request, urlopen

__profile__ = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
CREDENTIALDATA = xbmc.translatePath( os.path.join( __profile__, 'credential.dat') )
LOCAL_PROGRAM_LIST = xbmc.translatePath( os.path.join( __profile__, 'programlist.txt') )

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

    def GetCredential( self, user_id, user_pw ):
        isLogin = False
        try:
            url_path = 'login'
            params = {'apikey': self.apikey,
                      'credential': self.credential,
                      'device': self.device,
                      'drm': self.drm,
                      'partner': self.partner,
                      'pooqzone': self.pooqzone,
                      'region': self.region,
                      'targetage': self.targetage}
            payload = {'id': user_id,
                       'password': user_pw,
                       "profile": '0',
                       'pushid': '',
                       'type': 'general'}
            data = urlencode(payload).encode()
            url = self.api_domain + url_path + '?%s' % urlencode(params)
            req = Request(url, data)
            resp = urlopen(req)
            resp_json = json.load(resp)
            credential = resp_json['credential']
            if credential: isLogin = True
            write_file(CREDENTIALDATA, credential )
        except:
            islogin = False
        return isLogin

    def GetListSub(self, mode):
        try:
            url_path = 'cf/filters'
            type = '%sgenre' % mode.lower()
            params = dict(apikey=self.apikey, type=type)
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
        url = '%s%s%s?apikey=%s&credential=none&device=pc&drm=wm&partner=pooq&pooqzone=none&region=kor&targetage=auto' % (self.api_domain, url_path, code, self.apikey)
        req = Request(url)
        resp = urlopen(req)
        resp_json = json.load(resp)
        return resp_json
    def GetVODEpisode(self, pcode, pageno_ep):
        url = 'https://apis.wavve.com/vod/programs-contents/%s?orderby=new&apikey=%s' % (pcode, self.apikey)
        u = urlparse(url)
        params = dict(parse_qsl(u.query))
        params.update(limit=self.limit, offset=(pageno_ep - 1) * self.limit)
        url = u._replace(query=urlencode(params)).geturl()
        req = Request(url)
        resp = urlopen(req)
        resp_json = json.load(resp)
        return resp_json

    def GetVODList(self, pageno, url, order):
        try:
            u = urlparse('https://%s' % url)
            params = dict(parse_qsl(u.query))
            params.update(limit=self.limit, offset=(pageno-1)*self.limit, orderby=order)
            url = u._replace(query= urlencode(params)).geturl()
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
                params.update(broadcastid = '150905', sptheme='svod', uitype='MN85')
            elif type == 'playy':
                params.update(broadcastid='122681', sptheme='playy', uitype='MN85')
            params.update(limit=self.limit, offset=(pageno-1)*self.limit, orderby=order)
            url = u._replace(query= urlencode(params)).geturl()
            req = Request(url)
            resp = urlopen(req)
            resp_json = json.load(resp)
            result = resp_json['cell_toplist']
        except:
            result = []
        return result

    def GetLiveList(self, pageno, genre):
        try:
            url_path = 'cf/live/all-channels'
            params = { 'apikey' : self.apikey,
                       'offset' : (pageno - 1) * self.limit ,
                       'limit' : self.limit,
                       'genre' : genre
                       }
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
        url_path = 'streaming'
        params = {'apikey': self.apikey, 'credential': credential, 'contentid': code, 'contenttype': mode,
                  'quality': quality,  'authtype': 'cookie'}
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
        awscookie= resp_json['awscookie'].replace(';', '&')
        query = dict(parse_qsl(awscookie))
        awscookie = ''
        for key in query.keys():
            query[key] = query[key].replace('+', '-').replace('=', '_').replace('/', '~')
            if awscookie: awscookie += '; '
            awscookie+= '%s=%s' % (key, query[key])
        return drm, playurl, awscookie

    def Search( self, vod_type, keyword, pageno ):
        try:
            url_path = 'cf/search/list.js'
            params = { 'keyword': keyword,
                        'limit': self.limit,
                        'offset': (pageno-1) * self.limit,
                        'orderby': 'score',
                        'type': vod_type,
                        'apikey': 'self.apikey',
                       }
            url = '%s%s?%s' % (self.api_domain, url_path, urlencode(params))
            req = Request(url)
            resp = urlopen(req)
            resp_json = json.load(resp)
            result = resp_json['cell_toplist']
        except:
            result = []
        return result

    def LoadProgramList(self):
        try:
            f = open(LOCAL_PROGRAM_LIST, 'r')
            result = f.readlines()
            f.close()
            return result
        except Exception as e:
            result = []
        return result

    def SaveProgramList(self, data):
        try:
            result = self.LoadProgramList()
            param = dict(parse_qsl(data))
            code = 'pcode' if 'pcode' in param else 'code'
            with open(LOCAL_PROGRAM_LIST, 'w') as fw:
                data = data.encode('utf-8') + '\n'
                fw.write(data)
                num = 1
                for line in result:
                    item = dict(parse_qsl(line))
                    if item['category'] != param['category']:
                        fw.write(line)
                        num += 1
                    elif item[code] != param[code]:
                        fw.write(line)
                        num += 1
                    if num == 100: break
        except:
            pass
        return

def load_file( filename ):
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
