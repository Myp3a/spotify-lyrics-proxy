# Spotify lyrics proxy
# What's this?
This is a simple websocket proxy that receives API calls from Spotify and injects lyrics in them.  
# Why do I need it?
You might have noticed that some songs on Spotify have lyrics with them, and some are not. 
Moreover, lyrics are mixed with some story about the song. 
This proxy in combination with a modded app let you view lyrics for any of your Liked songs.
# How to use?
1. Acquire a webserver with TLS certificate
2. Get all needed tokens
3. Run both proxy components
4. Expose proxy port with webserver
5. Rebuild a Spotify app with your server address
6. All done!
