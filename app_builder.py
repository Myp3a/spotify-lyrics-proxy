from sys import platform
import requests
import subprocess
import shutil
import os
import re
import io
import zipfile

SERVER_IP = ''

if os.path.exists('apktool.jar'):
    pass
else:
    print('No apktool found, downloading...')
    try:
        with open('apktool.jar','wb') as apktool_file:
            with requests.get('https://bitbucket.org/iBotPeaches/apktool/downloads/apktool_2.5.0.jar', stream=True) as apktool_req:
                apktool_size = apktool_req.headers.get('content-length')
                if apktool_size is None:
                    apktool_file.write(apktool_req.content)
                else:
                    downloaded = 0
                    apktool_size = int(apktool_size)
                    print(f'Downloading {apktool_size / 1024 / 1024:.2f} MiB')
                    for part in apktool_req.iter_content(chunk_size=4096):
                        downloaded += len(part)
                        apktool_file.write(part)
                        done = int(50 * downloaded / apktool_size)
                        print(f'\r[{done*"="}{(50-done) * " "}]',end='')
                    print()
    except KeyboardInterrupt:
        print()
        print('Cancelling download.')
        os.remove('apktool.jar')
        quit()

if os.path.exists('apksigner.jar'):
    pass
else:
    print('No apksigner found, downloading...')
    try:
        with open('apksigner.jar','wb') as apksigner_file:
            with requests.get('https://dl.google.com/android/repository/build-tools_r30.0.1-windows.zip', stream=True) as build_tools_req:
                build_tools = io.BytesIO()
                build_tools_size = int(build_tools_req.headers.get('content-length'))
                downloaded = 0
                print(f'Downloading {build_tools_size / 1024 / 1024:.2f} MiB')
                for part in build_tools_req.iter_content(chunk_size=4096):
                    downloaded += len(part)
                    build_tools.write(part)
                    done = int(50 * downloaded / build_tools_size)
                    print(f'\r[{done*"="}{(50-done) * " "}]',end='')
                print()
            build_tools.seek(0)
            platform_tools_zip = zipfile.ZipFile(build_tools)
            platform_tools_zip.extract('android-11/lib/apksigner.jar')
            shutil.move(os.path.join('android-11','lib','apksigner.jar'),'apksigner.jar')
            shutil.rmtree('android-11')
    except KeyboardInterrupt:
        print()
        print('Cancelling download.')
        os.remove('apksigner.jar')
        quit()
    

apktool = subprocess.run('java -jar apktool.jar -V', capture_output=True)
if 'Apktool v2.5.0' in apktool.stdout.decode():
    print('apktool here.')
else:
    print('apktool error. Delete apktool.jar and try again')
    quit()

if os.path.exists('Spotify_modded.apk'):
    print('Modded Spotify already exists! Remove "Spotify_modded.apk" to continue.')
    quit()

if os.path.exists('Spotify.apk'):
    pass
else:
    print('Download Spotify apk and save it as "Spotify.apk"')
    quit()

if os.path.exists('Spotify_decompiled'):
    print('Decompiled files exist, removing')
    shutil.rmtree('Spotify_decompiled')
    
print('Decompiling apk...')
decomp = subprocess.run('java -jar apktool.jar d Spotify.apk -o Spotify_decompiled', capture_output=True)
print(decomp.stdout.decode())
print('Decompiled.')

patches = [0,0,0]
for directory in os.walk('Spotify_decompiled'):
    for filename in directory[2]:
        path = os.path.join(directory[0],filename)
        if path.endswith('.smali'):
            with open(path,'r+',encoding='utf-8') as smalifile:
                filetext = smalifile.read()
                if 'spclient.wg.spotify.com' in filetext:
                    if filetext.count(';,') > 200:
                        filetext = filetext.replace('spclient.wg.spotify.com',SERVER_IP)
                        smalifile.seek(0)
                        smalifile.truncate()
                        smalifile.write(filetext)
                        patches[0] += 1
                    elif 'FAIL_ON_UNKNOWN_PROPERTIES' in filetext:
                        filetext = filetext.replace('spclient.wg.spotify.com',SERVER_IP)
                        smalifile.seek(0)
                        smalifile.truncate()
                        smalifile.write(filetext)
                        patches[1] += 1
                    elif 'if-nez v0' in filetext:
                        ifs = re.findall(r'.method public.*?.end method',filetext,re.DOTALL)
                        met_len = 0
                        met_text = ""
                        for met in ifs:
                            if len(met) > met_len:
                                met_len = len(met)
                                met_text = met
                        #print(met_text)
                        lines = re.findall(r'.line [0-9]',met_text,re.DOTALL)
                        #for line in lines:
                            #print(line)
                        last_line = lines[-1]
                        last_line_index = int(last_line[-1])
                        
                        met_text_orig = str(met_text)
                        check = re.findall(r'.line '+str(last_line_index-2)+r'.*?'+str(last_line_index-1),met_text,re.DOTALL)[0].replace(f'.line {last_line_index-1}','')
                        url = re.findall(r'(?:const-string v0, ")(.*?)(?:")',check)[0]
                        #print(url)
                        replacement = check + check.replace(f'.line {last_line_index-2}',f'.line {last_line_index-1}').replace(url,SERVER_IP)
                        #print(f'.line {last_line_index}',f'.line {last_line_index+1}')
                        #met_text.replace(f'.line {last_line_index}',f'.line {last_line_index+1}')
                        #print(check)
                        #print(replacement)
                        met_text = met_text.replace(f'.line {last_line_index}',f'.line {last_line_index+1}').replace(f'.line {last_line_index-1}',f'.line {last_line_index}').replace(check,replacement)
                        #print(met_text_orig)
                        #print('-'*50)
                        #print(met_text)
                        filetext = filetext.replace(met_text_orig,met_text)
                        smalifile.seek(0)
                        smalifile.truncate()
                        smalifile.write(filetext)
                        patches[2] += 1

if patches == [1,1,1]:
    print('Patched successfully.')
else:
    print(f'Failed to patch! Applied patches count: {patches}')
                        

print('Compiling apk...')
comp = subprocess.run('java -jar apktool.jar b Spotify_decompiled -o Spotify_modded.apk -use-aapt2', capture_output=True)
print(comp.stdout.decode())
print('Compiled.')

print('Signing apk...')
sign = subprocess.run('java -jar apksigner.jar sign --key key.pk8 --cert certificate.pem --out Spotify_signed.apk Spotify_modded.apk', capture_output=True)
print(sign.stdout.decode())
print('Signed.')

print('Done!')
#print(apktool.stdout.decode())