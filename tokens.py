# API tokens 

#Musixmatch API token, can be obtained at https://developer.musixmatch.com
#Limited to 30% of lyrics, so can't be used alone
#Used to search and parse Musixmatch website - sadly, no timestamps
mxm_api_token = ""

#Tokens intercepted from call to https://apic.musixmatch.com/ws/1.1/macro.subtitles.get in Musixmatch app.
#Used to get text and timestamps from Musixmatch
#App token and AWSELB cookie.
#Temporary ones here, but they are limited to 10 rps - highly recommended to obtain your own.
mxm_app_token = "21111897178be2c090691bf38c19a0434ab4a83f7a66afe4d20460"
mxm_AWSELB = "55578B011601B1EF8BC274C33F9043CA947F99DCFF54A16893E4652A2B41708ABC8D30C64133664C5AA40C28C1BF7A7ADBC96AE984320B7F2C84490C2C97351FDE34690157"

#Genius API token, can be obtained at https://genius.com/api-clients
#Used to get lyrics data from Genius - no timestamps available
genius_client_token = ""
