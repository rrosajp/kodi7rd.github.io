import xbmcaddon,xbmcvfs,os,time
global global_var,stop_all,site_id,sub_color#global
global_var=[]
from resources.modules import log
import requests,json,re,shutil
from resources.modules import cache
Addon=xbmcaddon.Addon()
MyScriptID=Addon.getAddonInfo('id')
from resources.modules.extract_sub import extract
import urllib.parse
from resources.modules.general import DEFAULT_REQUEST_TIMEOUT
Addon=xbmcaddon.Addon()
MyScriptID=Addon.getAddonInfo('id')
que=urllib.parse.quote_plus
xbmc_tranlate_path=xbmcvfs.translatePath
__profile__ = xbmc_tranlate_path(Addon.getAddonInfo('profile'))
MyTmp = xbmc_tranlate_path(os.path.join(__profile__, 'temp_ktuvit'))

site_id='[Ktuvit]'
sub_color='springgreen'

def extract_imdb_id_from_itt(itt):

    # Extract the IMDb ID from the IMDb link, Remove trailing slash if it exists
    imdb_link_from_ktuvit = str(itt.get('IMDB_Link', '')).rstrip("/")
    # Split the URL by "/", Get the last part of the URL, which should be the IMDb ID (tt123456)
    imdb_parts = imdb_link_from_ktuvit.split("/")
    imdb_id_from_ktuvit = imdb_parts[-1] if imdb_parts else ''
            
    # FALLBACK - Check if imdb_id_from_ktuvit is empty or doesn't start with "tt"
    if not imdb_id_from_ktuvit.startswith("tt"):
        imdb_id_from_ktuvit = str(itt.get('ImdbID', ''))
        
    return imdb_id_from_ktuvit


def get_login_cookie():
  
    headers = {
    'authority': 'www.ktuvit.me',
    'accept': 'application/json, text/javascript, */*; q=0.01',
    'x-requested-with': 'XMLHttpRequest',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36',
    'content-type': 'application/json',
    'origin': 'https://www.ktuvit.me',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    
    'accept-language': 'en-US,en;q=0.9',
    
    }

    data = '{"request":{"Email":"hatzel6969@gmail.com","Password":"Jw1n9nPOZRAHw9aVdarvjMph2L85pKGx79oAAFTCsaE="}}'

    login_cook = requests.post('https://www.ktuvit.me/Services/MembershipService.svc/Login', headers=headers, data=data,timeout=DEFAULT_REQUEST_TIMEOUT).cookies
    login_cook_fix={}
    for cookie in login_cook:

            login_cook_fix[cookie.name]=cookie.value

    return login_cook_fix


def search_title_in_ktuvit(s_title, s_type, s_WithSubsOnly):
        
    headers = {
        'authority': 'www.ktuvit.me',
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'x-requested-with': 'XMLHttpRequest',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36',
        'content-type': 'application/json',
        'origin': 'https://www.ktuvit.me',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'referer': 'https://www.ktuvit.me/Search.aspx',
        'accept-language': 'en-US,en;q=0.9'
    }

    data = {
        "request": {
            "FilmName": s_title,
            "Actors": [],
            "Studios": None,
            "Directors": [],
            "Genres": [],
            "Countries": [],
            "Languages": [],
            "Year": "",
            "Rating": [],
            "Page": 1,
            "SearchType": s_type,
            "WithSubsOnly": s_WithSubsOnly
        }
    }

    try:
        response = requests.post('https://www.ktuvit.me/Services/ContentProvider.svc/SearchPage_search', headers=headers, json=data, timeout=DEFAULT_REQUEST_TIMEOUT).json()
        j_data = json.loads(response['d'])['Films']
        return j_data
    except Exception as e:
        log.warning(f"KTUVIT | search_title_in_ktuvit | Exception: {str(e)}")
        return []
    
    
def get_subs(item):
    log.warning('Searching Ktuvit')
    global global_var
    regexHelper = re.compile('\W+', re.UNICODE)
    

    login_cook=cache.get(get_login_cookie,1, table='subs')
        
    media_type = item["media_type"]
    
    s_title=item["OriginalTitle"]
    if media_type == 'movie':
        s_type='0'
        s_WithSubsOnly = "true"
    else:
        s_type='1'
        s_WithSubsOnly = "false"
        
    ################ KTUVIT TITLE MISMATCH MAPPING ##############################
    s_title = get_matching_ktuvit_name(s_title)
    log.warning(f"KTUVIT | get_matching_ktuvit_name | title after mapping: {s_title}")
    #############################################################################
    
    
    j_data = search_title_in_ktuvit(s_title, s_type, s_WithSubsOnly)
    
    
    #############################################################################
    # IF NO RESULTS FOR TV SHOW's OriginalTitle - RE-SEARCH BY TVShowTitle
    if not j_data and media_type == 'tv' and item["TVShowTitle"]:
        s_title = item["TVShowTitle"]
        log.warning(f"KTUVIT | Re-searching TV Show title | s_title={s_title}")
        j_data = search_title_in_ktuvit(s_title, s_type, s_WithSubsOnly)
    #############################################################################
    
    
    f_id=''
    
    for itt in j_data:
        
        imdb_id_from_ktuvit = extract_imdb_id_from_itt(itt)
        if imdb_id_from_ktuvit in item['imdb']:
            f_id=itt['ID']
            break

    # if ids still empty (wrong imdb on ktuvit page) filtered by text                
    if f_id == '':
        s_title = regexHelper.sub('', s_title).lower()        
        for itt in j_data:
            eng_name = regexHelper.sub('', regexHelper.sub(' ', itt['EngName'])).lower()
            heb_name = regexHelper.sub('', itt['HebName'])

            if (s_title.startswith(eng_name) or eng_name.startswith(s_title) or
                    s_title.startswith(heb_name) or heb_name.startswith(s_title)):
                f_id=itt["ID"]
                break
        
    if media_type == 'tv':
        url='https://www.ktuvit.me/MovieInfo.aspx?ID='+f_id
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0',
            'Accept': 'text/html, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.5',
            'X-Requested-With': 'XMLHttpRequest',
            'Connection': 'keep-alive',
            'Referer': url,
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
            'TE': 'Trailers',
        }

        params = (
            ('moduleName', 'SubtitlesList'),
            ('SeriesID', f_id),
            ('Season', item["season"]),
            ('Episode', item["episode"]),
        )

        response = requests.get('https://www.ktuvit.me/Services/GetModuleAjax.ashx', headers=headers, params=params, cookies=login_cook,timeout=DEFAULT_REQUEST_TIMEOUT).content
    else:
        headers = {
            'authority': 'www.ktuvit.me',
            'cache-control': 'max-age=0',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'referer': 'https://www.ktuvit.me/MovieInfo.aspx?ID='+f_id,
            'accept-language': 'en-US,en;q=0.9',
            
        }
        params = (
            ('ID', f_id),
        )
        
        response = requests.get('https://www.ktuvit.me/MovieInfo.aspx', headers=headers, params=params, cookies=login_cook,timeout=DEFAULT_REQUEST_TIMEOUT).content
        
    
    regex='<tr>(.+?)</tr>'
    m_pre=re.compile(regex,re.DOTALL).findall(response.decode('utf-8'))
    
    subtitle=' '
    subtitle_list=[]
    for itt in m_pre:
       
        regex='<div style="float.+?>(.+?)<br />.+?data-subtitle-id="(.+?)"'
        m=re.compile(regex,re.DOTALL).findall(itt)
        if len(m)==0:
            continue

        if ('i class' in m[0][0]):    #burekas fix for KT titles
            regex='כתובית מתוקנת\'></i>(.+?)$'
            n=re.compile(regex,re.DOTALL).findall(m[0][0])
            nm=n[0]
        else:
            nm=m[0][0]

        nm=nm.strip().replace('\n','').replace('\r','').replace('\t','').replace(' ','.')
        nm=nm.replace("'", '') # Remove problematic character from sub filename (creates error saving the file)
        
        data='{"request":{"FilmID":"%s","SubtitleID":"%s","FontSize":0,"FontColor":"","PredefinedLayout":-1}}'%(f_id,m[0][1])
        download_data={}
        download_data['id']=f_id
        download_data['data']=data
        
        url = "plugin://%s/?action=download&filename=%s&download_data=%s&source=ktuvit&language=Hebrew" % (MyScriptID,que(nm),que(json.dumps(download_data)))
 
        json_data={'url':url,
                         'label':"Hebrew",
                         'label2':site_id+' '+nm,
                         'iconImage':"0",
                         'thumbnailImage':"he",
                         'hearing_imp':'false',
                         'site_id':site_id,
                         'sub_color':sub_color,
                         'filename':nm,
                         'sync': 'false'}
  

      
        subtitle_list.append(json_data)
        
    global_var=subtitle_list


def download(download_data,MySubFolder):
    
    try:
        shutil.rmtree(MyTmp)
    except: pass
    xbmcvfs.mkdirs(MyTmp)

    log.warning(download_data)  


    id=download_data['data']
    login_cook=cache.get(get_login_cookie,1, table='subs')

    f_id=download_data['id']
    count=0
    data = id
    result="הבקשה לא נמצאה, נא לנסות להוריד את הקובץ בשנית"
    log.warning(f"KTUVIT | checking if response is not {result}")
    while ("הבקשה לא נמצאה, נא לנסות להוריד את הקובץ בשנית" in result):
    
        count+=1        
        log.warning(f"KTUVIT | Number of try: {count} | Sending RequestSubtitleDownload request...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.5',
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': 'https://www.ktuvit.me',
            'Connection': 'keep-alive',
            'Referer': 'https://www.ktuvit.me/MovieInfo.aspx?ID='+f_id,
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
            'TE': 'Trailers',
            }
        
        x = requests.post('https://www.ktuvit.me/Services/ContentProvider.svc/RequestSubtitleDownload', headers=headers, cookies=login_cook, data=data, timeout=DEFAULT_REQUEST_TIMEOUT).json()
        log.warning(f"KTUVIT | Number of try: {count} | RequestSubtitleDownload response: {json.loads(x['d'])['DownloadIdentifier']}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Referer': 'https://www.ktuvit.me/MovieInfo.aspx?ID='+f_id,
            'Upgrade-Insecure-Requests': '1',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
            'TE': 'Trailers',
            }

        params = (
        ('DownloadIdentifier', json.loads(x['d'])['DownloadIdentifier']),
        )

        response = requests.get('https://www.ktuvit.me/Services/DownloadFile.ashx', headers=headers, params=params, cookies=login_cook, timeout=DEFAULT_REQUEST_TIMEOUT)
        log.warning(f"KTUVIT | Number of try: {count} | Sending DownloadFile request...")
       
    
        time.sleep(0.1)
        result=response.text

        if (count>10):
            log.warning(f"KTUVIT | Number of try: {count} | Reached max tries count. breaking...")
            break
            
    log.warning(f"KTUVIT | Number of try: {count} | While loop finished.")
    headers=(response.headers)
    
    file_name=headers['Content-Disposition'].split("filename=")[1]
    log.warning(f"KTUVIT | Number of try: {count} | filename: {file_name}")

    archive_file = os.path.join(MyTmp, file_name)
    # Throw an error for bad status codes
    response.raise_for_status()
   
    with open(archive_file, 'wb') as handle:
        for block in response.iter_content(1024):
            handle.write(block)
    log.warning(archive_file)
    sub_file=extract(archive_file,MySubFolder)
    log.warning(sub_file)
    return sub_file


################ KTUVIT TITLE MISMATCH MAPPING ##############################
def c_get_ktuvit_original_title_mapping():
    ktuvit_original_title_mapping = requests.get('https://kodi7rd.github.io/repository/other/DarkSubs_Ktuvit_Title_Mapping/darksubs_ktuvit_title_mapping.json', timeout=DEFAULT_REQUEST_TIMEOUT).json()
    return ktuvit_original_title_mapping

def get_matching_ktuvit_name(video_data_original_title):
    try:
        ktuvit_original_title_mapping = cache.get(c_get_ktuvit_original_title_mapping, 24,table='subs')
        return ktuvit_original_title_mapping.get(video_data_original_title, video_data_original_title).lower()
    except Exception as e:
        log.warning(f"KTUVIT | get_matching_ktuvit_name | Exception: {str(e)}")
        return video_data_original_title
        pass
#############################################################################