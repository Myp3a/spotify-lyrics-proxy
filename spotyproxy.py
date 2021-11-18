import asyncio
import aiohttp
import random
import string
from aiohttp import web
import sqlite3
import logging
import json
import time
import math

logging.basicConfig(level=logging.INFO)

routes = web.RouteTableDef()

spotyurl = 'https://spclient.wg.spotify.com'

def dbg(var,varname=None,compact=False):
    if compact:
        if varname is None:
            varname = ""
        print(f'{varname} ({type(var)},{len(var)}): {var}')
    else:
        print('vvvvv')
        if varname is not None:
            print(varname)
        else:
            print('no name')
        print(f'type: {type(var)}')
        print(f'len: {len(var)}')
        try:
            var_json = json.dumps(var)
            print(json.dumps(var, indent=4, sort_keys=True))
        except:
            print(var)
        print('^^^^^')

@routes.get('/partner-userid/encrypted/crashlytics')
async def crashlytics(req):
    data = await get_handler(req)
    return data

@routes.get('/quicksilver/v2/triggers')
async def triggers(req):
    data = await get_handler(req)
    return data

@routes.get('/quicksilver/v2/messages')
async def messages(req):
    data = await get_handler(req)
    return data

@routes.get('/partner-userid/encrypted/branch')
async def branch(req):
    data = await get_handler(req)
    return data

@routes.get('/stories-view/v1/stories/playlists')
async def playlists(req):
    data = await get_handler(req)
    return data

@routes.get('/homeview/v1/home')
async def home(req):
    data = await get_handler(req)
    return data

@routes.get('/social-connect/v2/sessions/current')
async def current_session(req):
    data = await get_handler(req)
    return data

@routes.get('/hubview-mobile-v1/browse/')
async def browse_clear(req):
    data = await get_handler(req)
    return data

@routes.get('/hubview-mobile-v1/browse/{duck}')
async def browse(req):
    data = await get_handler(req)
    return data

@routes.get('/artist-storylines-view/v0/storylines/entities')
async def storylines(req):
    data = await get_handler(req)
    return data

@routes.get('/accountsettings/v1/profile/email')
async def email(req):
    data = await get_handler(req)
    return data

@routes.get('/searchview/v2/search')
async def search(req):
    data = await get_handler(req)
    return data

@routes.get('/searchview/v2/search/{duck}')
async def search_smth(req):
    data = await get_handler(req)
    return data

@routes.get('/album-entity-view/v2/album/{duck}')
async def album(req):
    data = await get_handler(req)
    return data

@routes.get('/artistview/v1/artist/{duck}')
async def artist(req):
    data = await get_handler(req)
    return data

@routes.get('/artistview/v1/artist/{duck}/releases')
async def artist_releases(req):
    data = await get_handler(req)
    return data

@routes.get('/inspiredby-mix/v2/seed_to_playlist/{duck}')
async def inspired_by(req):
    data = await get_handler(req)
    return data

@routes.get('/external-accessory-categorizer/v1/categorize/{duck}')
async def ext_categorize(req):
    data = await get_handler(req)
    return data

@routes.get('/concerts/v2/concerts/artist/{duck}')
async def concerts_artist(req):
    data = await get_handler(req)
    return data

@routes.get('/concerts/v1/concert/view/{duck}')
async def concerts_view(req):
    data = await get_handler(req)
    return data

@routes.get('/creatorabout/v0/artist/{duck}/about')
async def creatorabout(req):
    data = await get_handler(req)
    return data  

@routes.get('/vanilla/v1/views/hub2/made-for-x-hub')
async def made_for_x(req):
    data = await get_handler(req)
    return data 

@routes.get('/chartview/v4/overview/android')
async def chartview_overview(req):
    data = await get_handler(req)
    return data 

@routes.get('/chartview/v4/albums/{duck}/android')
async def chartview_album(req):
    data = await get_handler(req)
    return data 

@routes.get('/consumer-only-you/v1/consumer')
async def only_you(req):
    data = await get_handler(req)
    return data

@routes.get('/scannable-id/id/{duck}')
async def scannable_id(req):
    data = await get_handler(req)
    return data

@routes.get('/vanilla/v1/views/hub2/nft/recommendations-in-free-tier-playlist')
async def recommendations_in_free_tier_playlist(req):
    data = await get_handler(req)
    return data

@routes.get('/podcast-ap4p/ctaCardsEligibility')
async def podcast_eligibility(req):
    data = await get_handler(req)
    return data

@routes.get('/partner-client-integrations/v1/categories/voice-assistants')
async def voice_assistants(req):
    data = await get_handler(req)
    return data

@routes.get('/premium-notification/v1/GetPremiumMessage')
async def get_premium_message(req):
    data = await get_handler(req)
    return data

@routes.get('/carthing-proxy/device/v1/mydevices')
async def my_devices(req):
    data = await get_handler(req)
    return data

@routes.get('/vanilla/v1/views/hub2/nft/shows-episode-recommendations')
async def shows_episode_recommendations(req):
    data = await get_handler(req)
    return data

@routes.get('/podcast-ap4p/sponsoredSection/{duck}')
async def podcast_sponsored(req):
    data = await get_handler(req)
    return data

@routes.get('/vanilla/v1/views/hub2/nft/episode-featured-content')
async def episode_featured_content(req):
    data = await get_handler(req)
    return data

@routes.get('/newepisodenotifications/v1/optin')
async def notifications_optin(req):
    data = await get_handler(req)
    return data

@routes.get('/annotations/v1/genius/enabled-tracks-and-resources')
async def genius_enabled_tracks_and_resources(req):
    data = await get_handler(req,genius=True)
    return data

@routes.get('/annotations/v1/genius/track/{track_id}')
async def genius_proxy(req):
    print('genuis proxy')
    spotify_track_id = req.match_info['track_id']
    new_headers = {}
    headers = req.headers
    for header in headers:
        if header.lower() not in ['connection','host']:
            new_headers[header] = headers.get(header)
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://api.spotify.com/v1/tracks/{spotify_track_id}',headers=new_headers) as resp:
            track_data = await resp.json()
            track_name = track_data['name']
            track_artist = track_data['artists'][0]['name']
            track_album = track_data['album']['name']
            track_len = track_data['duration_ms']

        async with session.get('http://127.0.0.1:10100/lyrics',params={'len':track_len,'name':track_name,'author':track_artist}) as lyrics_raw:
            lyrics = await lyrics_raw.json()
        #print(lyrics)
        genius_fake = {'genius_song_id':666,'spotify_uuid':'duck','annotations':lyrics,'artist':track_artist,'title':track_name}
        #print(genius_fake)
        # print(genius_fake)
        return web.json_response(genius_fake)


@routes.post('/pushka-tokens/register')
async def pushka_tokens(req):
    data = await post_handler(req)
    return data
    
@routes.post('/gabo-receiver-service/v3/events')
async def gabo_receiver_service(req):
    data = await post_handler(req)
    return data
    
@routes.post('/v1/pses/screenconfig')
async def screenconfig(req):
    data = await post_handler(req)
    return data

@routes.post('/bootstrap/v1/bootstrap')
async def bootstrap(req):
    data = await post_handler(req)
    return data

@routes.post('/socialgraph/v2/following')
async def social_following(req):
    data = await post_handler(req)
    return data

@routes.post('/playlistextender/v2/extendp')
async def extendp(req):
    data = await post_handler(req)
    return data

@routes.post('/blend-invitation/v1/generate')
async def blend_gen(req):
    data = await post_handler(req)
    return data

@routes.post('/content-feed-service/v1/feed')
async def content_feed_feed(req):
    data = await post_handler(req)
    return data

#INFO:aiohttp.access:127.0.0.1 [23/Feb/2021:22:13:00 +0000] "DELETE /socialgraph/v2/following?format=json HTTP/1.0" 405 203 "-" "Spotify/8.5.98 Android/30 (ONEPLUS A3003)"
async def get_handler(req,genius=False):
    print('get req')
    #print(req.rel_url)
    new_headers = {}
    headers = req.headers
    for header in headers:
        if header.lower() not in ['connection','host']:
            new_headers[header] = headers.get(header)
    url = spotyurl + str(req.rel_url)
    async with aiohttp.ClientSession() as session:
        if genius:
            #print(new_headers)
            offset = 0
            limit = 50
            got_tracks = [1]*50
            tracks_arr = []
            while len(got_tracks) == 50:
                async with session.get(f'https://api.spotify.com/v1/me/tracks?offset={offset}&limit={limit}',headers=new_headers) as tracks:
                    got_tracks_raw = await tracks.json()
                    #print(got_tracks_raw)
                    got_tracks = got_tracks_raw['items']
                    for track in got_tracks:
                        tracks_arr.append(f'spotify:track:{track["track"]["id"]}')
                    offset = offset + 50
            #print(tracks_arr)
        async with session.get(url,headers=new_headers) as resp:
            if genius:
                resp_data = await resp.json()
                for track in tracks_arr:
                    resp_data['trackUris'].append(track)
                return web.json_response(resp_data)
            resp_data = await resp.read()
            #if 'genius' in url:
            #print(resp.url)
            #for header in new_headers:
            #    print(f'{header}: {new_headers.get(header)}')
            #print(resp.status)
            #    print(resp_data)
            #print(await resp.text())
    return web.Response(body=resp_data)

async def post_handler(req):
    print('post req')
    print(req.rel_url)
    headers = req.headers
    new_headers = {}
    for header in headers:
        if header.lower() not in ['connection','host']:
            new_headers[header] = headers.get(header)
    url = spotyurl + str(req.rel_url)
    async with aiohttp.ClientSession() as session:
        data = await req.post()
        async with session.post(url,headers=new_headers,data=data) as resp:
            resp_data = await resp.read()
    return web.Response(body=resp_data)

async def dragons(req):
    text = """<html>
    <head></head>
    <body>
        <div style="position:fixed;width:100%;height:100%;background:black;left:0;top:0;z-index:9000"><div style="text-align:center;width:100%;height:100%;padding-top:40%;color:black">Here be dragons.</div></div>
    </body>
</html>"""
    return web.Response(text=text,content_type='text/html')

app = web.Application(handler_args={'tcp_keepalive':False})
app.add_routes(routes)
app.add_routes([web.route('*', '/', dragons)])
web.run_app(app,host='127.0.0.1',port=9090)
