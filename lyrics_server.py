import aiohttp
import json
import math
from aiohttp import web
import re
import transliterate
import string
from difflib import SequenceMatcher

import tokens
tkn = tokens.mxm_api_token
tkn_app = tokens.mxm_app_token
tkn_aws = tokens.mxm_AWSELB

genius_client_id = tokens.genius_client_id
genius_client_secret = tokens.genius_client_secret
genius_client_token = tokens.genius_client_token

lyrics_regex = re.compile(r'(?:<span class="lyrics__content__)(?:ok|warning|error)(?:">)(.*?)(?:</span>)',flags=re.DOTALL)
#same as above, but only head
lyrics_head_regex = re.compile(r'<span class="lyrics__content__(?:ok|warning|error)">',flags=re.DOTALL)

routes = web.RouteTableDef()

async def check_for_lyrics(url):
    #Site - parsing, not API
    #User-Agent is mandatory
    async with aiohttp.ClientSession() as sess:
        async with sess.get(url,headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0"}) as res:
            page = await res.text()
    lyrics_arr = re.findall(lyrics_regex,page)
    if lyrics_arr == []:
        return False
    else:
        return True

async def mxm_parse(name,author,track_len,lyrics_ref):
    print('-'*25)
    print('mxm - parse')
    lyr_ref = None
    err = False
    captcha = False
    detailed_lyrics = False 
    lyrics = []
    track_len = int(track_len)
    search_link = f'https://api.musixmatch.com/ws/1.1/track.search?format=jsonp&callback=bruh&q_track={name}&q_artist={author}&quorum_factor=1&apikey={tkn}'
    async with aiohttp.ClientSession() as session:
        async with session.get(search_link) as search:
            search_text_raw = await search.text()
            search_text = search_text_raw.replace('bruh(','').replace(');','')
            search_json = json.loads(search_text)
            if search_json['message']['header']['available'] == 0:
                print(search_link)
                print(search_json)
                err = True
            else:
                tracks = search_json['message']['body']['track_list']
                tracks_db = []
                for track in tracks:
                    rating = track['track']['track_rating']
                    link = track['track']['track_share_url'].split('?utm_source')[0]
                    #check_for_lyrics() is slow. It loads pages and checks them for lyrics.
                    #API doesn't return lyrics availability if they aren't verified.
                    #This is made to bypass this restriction.
                    #If it is slow for you and it's okay to sacrifice some accuracy, change it to "track['track']['has_lyrics'] == 1"
                    has_lyrics = await check_for_lyrics(link)
                    tracks_db.append({'rating':rating,'link':link,'has_lyrics':has_lyrics})
                rating = -1
                sel = False
                for track in tracks_db:
                    if track['has_lyrics'] and track['rating'] > rating:
                        rating = track['rating']
                        sel = track['link']
                if not sel:
                    print(search_link)
                    print(search_json)
                    err = True
                    print(f'{author} - {name}: no lyrics')
                else:
                    async with session.get(sel,headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0"}) as lyr:
                        lyr_html = await lyr.text()
                        lyrics_arr_crap = re.findall(lyrics_regex,lyr_html)
                        lyrics_arr = []
                        for line in lyrics_arr_crap:
                            parts = line.split('\n')
                            for part in parts:
                                lyrics_arr.append(part)
                        #print(lyrics_arr)
                        print(f'{author} - {name}: parsed lyrics')
                        lyr_ref = []
                        for lyrline in lyrics_arr:
                            lyr_ref.append({'contents':lyrline})
                        lyrics = []
                        lyric_temp = {'contents':None,'contentType':'lyrics','author':{'verified':False},'timestamp':None}
                        lyrics_parts = math.ceil(len(lyrics_arr) / 2)
                        lyrics_per_part = track_len / 1000 / lyrics_parts
                        for offset in range(lyrics_parts):
                            line = ''
                            for i in range(4):
                                if line != '':
                                    line += '\n'
                                try:
                                    line += lyrics_arr[offset*2+i]
                                except:
                                    pass
                            lyric_line = dict(lyric_temp)
                            lyric_line['contents'] = line
                            lyric_line['timestamp'] = lyrics_per_part * offset
                            lyrics.append(lyric_line)

        return {'lyrics':lyrics,'err':err,'captcha':captcha,'detailed':detailed_lyrics,'ref':lyr_ref}
    
async def mxm_search(name,author,track_len):
    print('-'*25)
    print('mxm')
    track_len = int(track_len)
    async with aiohttp.ClientSession() as session:
        usertoken = tkn_app
        AWSELB = tkn_aws
        async with session.get(f'https://apic.musixmatch.com/ws/1.1/macro.subtitles.get?subtitle_format=mxm&q_artist={author}&q_track={name}&usertoken={usertoken}&app_id=android-player-v1.0&format=json',headers={'Cookie':f'AWSELB="{AWSELB}"'}) as lyrics_raw:
            lyrics_data = await lyrics_raw.text()
            lyrics_data = json.loads(lyrics_data)
            err = False
            captcha = False
            detailed_lyrics = False
            lyr_ref = None
            try:
                if lyrics_data['message']['header'].get('hint',None) == 'captcha':
                    err = True
                    captcha = True
                elif lyrics_data['message']['body']['macro_calls']['track.subtitles.get']['message']['header'].get('available',None) == 1:
                    lyrics_arr = json.loads(lyrics_data['message']['body']['macro_calls']['track.subtitles.get']['message']['body']['subtitle_list'][0]['subtitle']['subtitle_body'])
                    detailed_lyrics = True
                elif lyrics_data['message']['body']['macro_calls']['track.lyrics.get']['message']['header']['status_code'] == 200:
                    lyrics_arr = lyrics_data['message']['body']['macro_calls']['track.lyrics.get']['message']['body']['lyrics']['lyrics_body'].split('\n')    
                else:
                    print(f'https://apic.musixmatch.com/ws/1.1/macro.subtitles.get?subtitle_format=mxm&q_artist={author}&q_track={name}&usertoken={usertoken}&app_id=android-player-v1.0&format=json')
                    print(lyrics_data)     
                    err = True                            
            except:
                print('clearly errored')
                print(f'https://apic.musixmatch.com/ws/1.1/macro.subtitles.get?subtitle_format=mxm&q_artist={author}&q_track={name}&usertoken={usertoken}&app_id=android-player-v1.0&format=json')
                print(lyrics_data)
                err = True
            #print(lyrics_arr)
            #print(json.loads(lyrics_arr))
        if not err:
            lyr_ref = []
            if detailed_lyrics:
                print(f'{author} - {name}: timed lyrics')
                lyric_temp = {'contents':None,'contentType':'lyrics','author':{'verified':False},'timestamp':None}
                lyrics = []
                last_timestamp = lyrics_arr[0]['time']['total']
                line = ''
                cntr = 0
                first_ts = lyrics_arr[0]['time']['total']
                for lyric_line in lyrics_arr:
                    lyr_ref.append({'contents':lyric_line['text']})
                    ts = lyric_line['time']['total']
                    if cntr > 3 or ts - last_timestamp > 10:
                        line_dict = dict(lyric_temp)
                        line_dict['contents'] = line
                        line_dict['timestamp'] = first_ts
                        lyrics.append(line_dict)
                        line = ''
                        cntr = 0
                        first_ts = ts
                    if cntr != 0:
                        line += '\n'
                    cntr += 1
                    line += lyric_line['text']
                    last_timestamp = ts
                line_dict = dict(lyric_temp)
                line_dict['contents'] = line
                line_dict['timestamp'] = first_ts
                lyrics.append(line_dict)
            else:
                print(f'{author} - {name}: guessed lyrics')
                for lyrline in lyrics_arr:
                    lyr_ref.append({'contents':lyrline})
                lyrics = []
                lyric_temp = {'contents':None,'contentType':'lyrics','author':{'verified':False},'timestamp':None}
                lyrics_parts = math.ceil(len(lyrics_arr) / 2)
                lyrics_per_part = track_len / 1000 / lyrics_parts
                for offset in range(lyrics_parts):
                    line = ''
                    for i in range(4):
                        if line != '':
                            line += '\n'
                        try:
                            line += lyrics_arr[offset*2+i]
                        except:
                            pass
                    lyric_line = dict(lyric_temp)
                    lyric_line['contents'] = line
                    lyric_line['timestamp'] = lyrics_per_part * offset
                    lyrics.append(lyric_line)
        else:
            if captcha:
                print(f'{author} - {name}: captcha\'d')
                lyrics = [{'contents':'Rate limit, wait a minute and try again','contentType':'lyrics','author':{'verified':False},'timestamp':0.0}]
            else:
                print(f'{author} - {name}: no lyrics')
                lyrics = [{'contents':'No lyrics available :c','contentType':'lyrics','author':{'verified':False},'timestamp':0.0}]
        
        return {'lyrics':lyrics,'err':err,'captcha':captcha,'detailed':detailed_lyrics,'ref':lyr_ref}
        
async def genius_search(name,author,track_len,lyrics_ref):
    print('-'*25)
    print('genius')
    detailed_lyrics = False
    captcha = False
    err = False
    lyrics = None
    track_len = int(track_len)
    client_id = genius_client_id
    client_secret = genius_client_secret
    client_token = genius_client_token
    track_path = None
    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.genius.com/search',params={'q':f'{author} - {name}'},headers={'Authorization': f'Bearer {client_token}'}) as search_raw:
            search = await search_raw.json()
            #print(search)
            for hit in search['response']['hits']:
                if SequenceMatcher(None,hit['result']['title'],name).ratio() > 0.5 and SequenceMatcher(None,hit['result']['primary_artist']['name'],author).ratio() > 0.5:
                    track_path = search['response']['hits'][0]['result']['path']
                    track_url = f'https://genius.com{track_path}'
            if track_path is None:
                print(f'{author} - {name}: no lyrics')
                return {'lyrics':lyrics,'err':True,'captcha':captcha,'detailed':detailed_lyrics}
        async with session.get(track_url) as lyrics_html_raw:
            lyrics_html = await lyrics_html_raw.text()
        lyr_arr_crap_raw = re.findall(r'(?:class="lyrics".*?<p>)(.*?)(?:</p>)',lyrics_html,re.DOTALL)
        if len(lyr_arr_crap_raw) == 0:
            return {'lyrics':lyrics,'err':True,'captcha':captcha,'detailed':detailed_lyrics}
        lyr_arr_crap = lyr_arr_crap_raw[0].split('\n')
        lyrics_arr = []
        for item in lyr_arr_crap:
            newitem = re.findall(r'(?:>?)([^>]*?)(?:<)',item)
            if newitem != [] and newitem != ['']:
                newitem = newitem[0]
                if newitem[0] == '[':
                    lyrics_arr.append('')
                else:
                    lyrics_arr.append(newitem)
        lyric_temp = {'contents':None,'contentType':'lyrics','author':{'verified':False},'timestamp':None}
        lyrics_parts = math.ceil(len(lyrics_arr) / 2)
        lyrics_per_part = track_len / 1000 / lyrics_parts
        lyrics = []
        #print(lyrics_arr)
        for offset in range(lyrics_parts):
            line = ''
            for i in range(4):
                if line != '':
                    line += '\n'
                try:
                    line += lyrics_arr[offset*2+i]
                except:
                    pass
            lyric_line = dict(lyric_temp)
            lyric_line['contents'] = line
            lyric_line['timestamp'] = lyrics_per_part * offset
            lyrics.append(lyric_line)
        print(f'{author} - {name}: guessed lyrics')
    return {'lyrics':lyrics,'err':err,'captcha':captcha,'detailed':detailed_lyrics}

async def netease_search(name,author,lyrics_ref):
    async def lyr_parser(sid):
        lyr = await http_wrap('get',f'http://music.163.com/api/song/lyric?lv=-1&tv=-1&id={sid}')
        print(lyr)
        if lyr == 'err':
            return 'err'
        if lyr.get('uncollected',False):
            return ""
        lyr_text = lyr['lrc']['lyric']
        lyrics = []
        lyric_temp = {'contents':None,'contentType':'lyrics','author':{'verified':False},'timestamp':None}
        cntr = 0
        lyr_line_long = ''
        newts = 0
        change_ts = False
        for line in lyr_text.split('['):
            line = line.strip()
            if line == '':
                continue
            #print(line)
            ts_raw, lyrline = line.split(']')
            ts_min,ts_sec = ts_raw.split(':')
            ts = int(ts_min)*60 + float(ts_sec)
            if change_ts:
                newts = ts
                change_ts = False
            lyrline = lyrline.replace('\\','')
            cntr += 1
            if lyrline == '':
                lyr_part = dict(lyric_temp)
                lyr_part['timestamp'] = newts
                lyr_part['contents'] = lyr_line_long
                change_ts = True
                lyrics.append(lyr_part)
                cntr = 0
            if cntr == 1:
                lyr_line_long = lyrline
            else:
                lyr_line_long += '\n'
                lyr_line_long += lyrline
            if cntr == 4: 
                lyr_part = dict(lyric_temp)
                lyr_part['timestamp'] = newts
                lyr_part['contents'] = lyr_line_long
                change_ts = True
                lyrics.append(lyr_part)
                cntr = 0
        if lyrline != '':
            lyr_part = dict(lyric_temp)
            lyr_part['timestamp'] = ts
            lyr_part['contents'] = lyrline
            lyrics.append(lyr_part)
        return lyrics

    print('-'*25)
    print('netease')
    detailed_lyrics = True
    captcha = False
    err = False
    lyrics = None
    search_author = transliterate.translit(author,'ru',reversed=True)
    async def http_wrap(meth,url,data=None):
        #print(url)
        resp = None
        async with aiohttp.ClientSession() as session:
            while resp is None:
                try:
                    if meth == 'get':
                        async with session.get(url) as raw:
                            tmp_resp = await raw.text()
                    elif meth == 'post':
                        async with session.post(url,data=data) as raw:
                            tmp_resp = await raw.text()
                    tmp_resp = json.loads(tmp_resp)
                    if tmp_resp['code'] == 200:
                        resp = tmp_resp
                    else:
                        print(f'fuck. code {tmp_resp["code"]}')
                        return "err"
                except:
                    print('fuck.')
        #print(resp)
        #print(type(resp))
        return resp
    srch = await http_wrap('post','http://music.163.com/api/search/get',{'s': f'{search_author} - {name}','type': 1,'offset': 0,'total': 'true','limit': 100})
    data = srch['result']
    sid = None
    for item in data['songs']:
        it_author = item['artists'][0]['name']
        it_name = item['name']
        if it_author == author and it_name == name:
            sid_tmp = item['id']
            lyrics_tmp = await lyr_parser(sid_tmp)
            if lyrics_tmp == "err":
                return {'lyrics':None,'err':True,'captcha':True,'detailed':detailed_lyrics}
            if lyrics_ref is not None:
                lyr_oneline = await oneliner(lyrics_tmp)
                #print(lyrics_ref)
                #print('------')
                #print(lyr_oneline)
                ratio = SequenceMatcher(None, lyrics_ref.lower(),lyr_oneline.lower()).ratio()
                print(ratio)
                if ratio > 0.1:
                    sid = sid_tmp
                    break
            else:
                if lyrics_tmp == "":
                    continue
                else:
                    sid = sid_tmp
                    break
    if sid is None:
        srch = await http_wrap('post','http://music.163.com/api/search/get',{'s': f'{search_author}','type': 1,'offset': 0,'total': 'true','limit': 100})
        data = srch['result']
        for item in data['songs']:
            it_author = item['artists'][0]['name']
            it_name = item['name']
            if it_author == author and it_name == name:
                sid_tmp = item['id']
                lyrics_tmp = await lyr_parser(sid_tmp)
                if lyrics_tmp == "err":
                    return {'lyrics':None,'err':True,'captcha':True,'detailed':detailed_lyrics}
                if lyrics_ref is not None:
                    lyr_oneline = await oneliner(lyrics_tmp)
                    ratio = SequenceMatcher(None, lyrics_ref,lyr_oneline).ratio()
                    print(ratio)
                    if ratio > 0.1:
                        sid = sid_tmp
                        break
                else:
                    if lyrics_tmp == "":
                        continue
                    else:
                        sid = sid_tmp
                        break
    if sid is None:
        print('song not found.')
        return {'lyrics':None,'err':True,'captcha':captcha,'detailed':detailed_lyrics}
    lyrics = await lyr_parser(sid)
    #print(lyrics)
    print(f'{author} - {name}: timed lyrics')
    return {'lyrics':lyrics,'err':err,'captcha':captcha,'detailed':detailed_lyrics} 

async def oneliner(lyr):
    line = ""
    for item in lyr:
        line = line + " " + item['contents']
    line = line.replace('\n',' ').replace('  ',' ')
    return line

@routes.get('/lyrics')
async def lyrics_handler(req):
    query_params = req.query
    name = query_params['name']
    author = query_params['author']
    track_len = query_params['len']

    replacements = {'Alyona Shvets':'алена швец.'}

    author = replacements.get(author,author)
    lyrics_ref = None
    lyrics_base = None

    lyrics_mxm_search = await mxm_search(name,author,track_len)
    if not lyrics_mxm_search['err']:
        if lyrics_mxm_search['detailed']:
            return web.json_response(lyrics_mxm_search['lyrics'])
        else:
            lyrics_base = lyrics_mxm_search['lyrics']
            lyrics_ref = await oneliner(lyrics_mxm_search['ref'])
    if lyrics_ref is None:
        lyrics_mxm_parse = await mxm_parse(name,author,track_len,lyrics_ref)
        if not lyrics_mxm_parse['err']:
            lyrics_base = lyrics_mxm_parse['lyrics']
            if lyrics_ref is None:
                lyrics_ref = await oneliner(lyrics_mxm_parse['ref'])
    lyrics_netease = await netease_search(name,author,lyrics_ref)
    if not lyrics_netease['err']:
        return web.json_response(lyrics_netease['lyrics'])
    if lyrics_base is not None:
        return web.json_response(lyrics_base)
    lyrics_genius = await genius_search(name,author,track_len,lyrics_ref)
    if not lyrics_genius['err']:
        return web.json_response(lyrics_genius['lyrics'])
    return web.json_response([{'contents':'No lyrics available :c','contentType':'lyrics','author':{'verified':False},'timestamp':0.0}])

app = web.Application()
app.add_routes(routes)
web.run_app(app,host='127.0.0.1',port=10100)