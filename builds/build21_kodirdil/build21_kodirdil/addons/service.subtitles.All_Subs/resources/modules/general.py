import os,time
import xbmc,xbmcaddon,xbmcvfs,xbmcgui
import threading

from urllib.parse import  unquote_plus, unquote,  quote
import unicodedata
from resources.modules import log
iconx=xbmcaddon.Addon().getAddonInfo('icon')
xbmc_tranlate_path=xbmcvfs.translatePath
user_dataDir = xbmc_tranlate_path(xbmcaddon.Addon().getAddonInfo("profile"))
if not os.path.exists(user_dataDir):
     os.makedirs(user_dataDir)
CachedSubFolder=xbmc_tranlate_path(os.path.join(user_dataDir, 'Cached_subs'))
if not os.path.exists(CachedSubFolder):
     os.makedirs(CachedSubFolder)
MySubFolder = xbmc_tranlate_path(os.path.join(user_dataDir, 'Downloaded_subs'))
MyScriptID = xbmcaddon.Addon().getAddonInfo('id')
TransFolder=xbmc_tranlate_path(os.path.join(user_dataDir, 'trans_subs'))
if not os.path.exists(TransFolder):
     os.makedirs(TransFolder)
MyScriptName = xbmcaddon.Addon().getAddonInfo('name')
addonPath = xbmc_tranlate_path(xbmcaddon.Addon().getAddonInfo("path"))
global with_dp,show_msg,progress_msg
show_msg=""
progress_msg=0
global break_all
break_all=False
with_dp=True
DEFAULT_REQUEST_TIMEOUT = int(xbmcaddon.Addon().getSetting('max_search_time')) or 10

class OverlayText:
    def __init__(self):
        log.warning('(Overlay) Initialize overlay text')
        x, y, w, h,x2, y2, w2, h2,x3, y3, w3, h3 = self._calculate_the_size()

        self._shown       = False
        self._window     = xbmcgui.Window(12005)
        self._label      = xbmcgui.ControlLabel(x, y, w, h, '', alignment=0x00000002 | 0x00000004, font='font14')
        
        
        self._icon = xbmcgui.ControlImage(x2, y2, w2, h2, iconx)
        self._background = xbmcgui.ControlImage(x3, y3, w3, h3, os.path.join(addonPath,"resources","art","background.png"))
        self._background.setColorDiffuse("0xD0000000")

    def __enter__(self):
        return self

    def open(self):
        if not self._shown:
            self._window.addControls([self._background,self._icon, self._label])
            self._shown = True

    def isShowing(self):
        return self._shown

    def setText(self, text):
        if self._shown:
            self._label.setLabel(text)

    def _calculate_the_size(self):
        # get skin resolution
        #tree = ET.parse(os.path.join(xbmc_tranlate_path("special://skin/"), "addon.xml"))
        #res = tree.findall("./extension/res")[0]
        viewport_w =1920 #int(res.attrib["width"])
        viewport_h =1080 #int(res.attrib["height"])
        # Adjust size based on viewport, we are using 1080p coordinates
        
        
        # label
        w = int(int(1920.0 * 0.7) * viewport_w / 1920.0)
        h = int(150 * viewport_h / 1088.0)
        x = int((viewport_w - w) / 2)
        y = int(35)
        
        # icon
        w2 = 95#int(int(20.0 * 0.7) * viewport_w / 20.0)
        h2 = int(95 * viewport_h / 1088.0)
        x2 = 170
        y2 = int(30)
        
        # background
        w3 = 1330#int(int(20.0 * 0.7) * viewport_w / 20.0)
        h3 = 150
        x3 = 135
        y3 = 20
        
        
        return x, y, w, h,x2, y2, w2, h2,x3, y3, w3, h3

    def __exit__(self, *exc_info):
        self.close()
        return not exc_info[0]

    def __del__(self):
        self.close()

    def close(self):
        if hasattr(self, '_icon') and self._shown:
            self._window.removeControls([self._background,self._icon, self._label])
            self._shown = False


class Thread (threading.Thread):
   def __init__(self, target, *args):
    super().__init__(target=target, args=args)
   def run(self, *args):
      
      self._target(*self._args)
      return 0
   def exit(self):
        SystemExit()
def show_results(show_dp=True):
    global break_all,progress_msg
    
    from resources.modules.general import with_dp
    show_dp=with_dp
    break_all=False
    
    time_out=0
    if (show_dp):
        dp = xbmcgui.DialogProgress()
        dp.create("מחפש כתוביות")
                      
        while(1):
            from resources.modules.general import show_msg
            if (show_msg!="END"):
                dp.update(progress_msg,str(show_msg))
            if dp.iscanceled():
                break_all=True
                dp.close()
                break
            if (show_msg=="END"):
                break_all=True
                
                dp.close()
                break
            time.sleep(0.1)
            time_out+=1
            if (time_out>1200):
                break_all=True
                dp.close()
                break
        dp.close()
        '''
        menu2 = infoDialog("plugin://%s/"%addon_id)
        menu2.doModal()
        del menu2
        '''
    else:
        try:
            cond=xbmc.Monitor().abortRequested()
        except:
            cond=xbmc.abortRequested
            
        close_overlay=False
        time_out=0
        with OverlayText() as _overlay:
          
          while (not cond) and (xbmc.Player().isPlaying()):
            from resources.modules.general import show_msg
            _overlay.open()
            if close_overlay:
              break
             
                
             
                
            if _overlay.isShowing():
                if (show_msg!="END"):
                    add_str=""
                    for i in range(0,int(120-(time_out/10))):
                        add_str+='_';
                    _overlay.setText(show_msg+'\n'+add_str)

            time.sleep(0.1)
            time_out+=1
            if (show_msg=="END") or (time_out>1200):
                close_overlay=True
                _overlay.close()
                
def notify(msg_id, times=3500, icon=iconx,sound=False):
        xbmcgui.Dialog().notification(MyScriptName, f"[COLOR yellow]{msg_id}[/COLOR]", icon, int(times), sound)
        

def extract_season_episode_numbers(subtitle_file_name):

    import re
    optional_separators = r'[\s._\-x+,&:]{0,2}' # 0-2 occurrences
    optional_middle_separators = r'[\s._\-x+,&:]{0,4}' # 0-4 occurrences

    regex_pattern = re.compile(
        r'S[e]?(?:ason)?' + optional_separators +
        '(?P<season_number>\d{1,2})' + optional_middle_separators +
        'E[p]?(?:isode)?' + optional_separators +
        '(?P<episode_number>\d{1,3})',
        re.IGNORECASE
    )
    
    match = regex_pattern.search(subtitle_file_name)
    if match:
        # Fill leading zero if needed
        return match.group('season_number').zfill(2), match.group('episode_number').zfill(2)

    return None, None

def set_media_type(video_data):

    def _translate_media_type(media_type):
        # TV Show
        if media_type in ['tvshow', 'season', 'episode']:
            return 'tv'
            
        # Movie
        # TEMPORARY: 'movies' should be 'movie' in Telemedia's code
        elif media_type in ['movie', 'movies']:
            return 'movie'
            
        return None

    if xbmc.Player().isPlaying():
        try:
            # https://alwinesch.github.io/group__python___info_tag_video.html#gae415e4abfc18ab4178c49953159e1233)
            # Try to get media_type parameter from playing addon's setMediaType function from InfoTagVideo API (From Kodi 20 and above)
            # Example supporting addons: Telemedia, Mando, Fen, Fen Light, Cobra, Kitana, Twilight, Otaku
            video_data['media_type_videoInfoTag'] = xbmc.Player().getVideoInfoTag().getMediaType()
            log.warning(f"DEBUG | get_video_data | set_media_type | media_type_videoInfoTag = {video_data['media_type_videoInfoTag']}")

            media_type = _translate_media_type(video_data['media_type_videoInfoTag'])
            if media_type:
                video_data['media_type'] = media_type
                return video_data
        except:
            pass
            
    else:
            video_data['media_type_ListItem.DBTYPE'] = xbmc.getInfoLabel("ListItem.DBTYPE")
            log.warning(f"DEBUG | get_video_data | set_media_type | media_type_ListItem.DBTYPE = {video_data['media_type_ListItem.DBTYPE']}")

            media_type = _translate_media_type(video_data['media_type_ListItem.DBTYPE'])
            if media_type:
                video_data['media_type'] = media_type
                return video_data
    

    # Fallback - manually determine media_type based on other parameters
    log.warning(f"DEBUG | get_video_data | set_media_type | Fallbacks to manually set media_type.")
    if video_data['TVShowTitle'] and (video_data['season'] != '0' or video_data['episode'] != '0'):
        video_data['media_type'] = 'tv'
    else:
        video_data['media_type'] = 'movie'
    return video_data
        

def get_playing_addon(playing_addon=""):
    playing_addon_temp = xbmc.getInfoLabel("ListItem.FileNameAndPath")
    
    if len(playing_addon_temp) > 0 and any(prefix in playing_addon_temp for prefix in ['plugin://', 'smb://', 'pvr://']):
        if 'pvr://' in playing_addon_temp:
            playing_addon = 'pvr://video' 
        else:
            regex = '//(.+?)/'
            import re
            match = re.findall(regex, playing_addon_temp)
            playing_addon = match[0] if match else playing_addon_temp
            
    return playing_addon
      
def take_title_from_focused_item():
    labelType = xbmc.getInfoLabel("ListItem.DBTYPE")  # movie/tvshow/season/episode
    labelMovieTitle = xbmc.getInfoLabel("ListItem.OriginalTitle")
    labelYear = xbmc.getInfoLabel("ListItem.Year")
    labelTVShowTitle = xbmc.getInfoLabel("ListItem.TVShowTitle")
    labelSeason = xbmc.getInfoLabel("ListItem.Season")
    labelEpisode = xbmc.getInfoLabel("ListItem.Episode")
    isItMovie = xbmc.getCondVisibility("Container.Content(movies)") or labelType == 'movie'
    isItEpisode = xbmc.getCondVisibility("Container.Content(episodes)") or labelType == 'episode'

    title = 'SearchFor...'
    if isItMovie and labelMovieTitle and labelYear:
        title = labelMovieTitle + " " + labelYear
    elif isItEpisode and labelTVShowTitle and labelSeason and labelEpisode:
        title = ("%s S%.2dE%.2d" % (labelTVShowTitle, int(labelSeason), int(labelEpisode)))

    return title


def remove_color_tags(input_string):
    log.warning(f"DEBUG | get_video_data | BEFORE remove_color_tags | input_string={input_string}")
    
    # Example: [COLOR white]הכפיל[/COLOR]
    import re
    output_string = re.sub(r'\[COLOR [^\]]*\]|\[/COLOR\]', '', input_string, flags=re.IGNORECASE)
    
    log.warning(f"DEBUG | get_video_data | AFTER remove_color_tags | output_string={output_string}")
    return output_string

def clean_title(title):
    
    def _remove_diacritics(title):
        # Removing diacritics - Handles titles such as "Shôgun", "Narcos: México" from IMDB/TMDB - To match title in Ktuvit.
        # Example: https://www.ktuvit.me/MovieInfo.aspx?ID=4BAFC19F06D861F298DB6B723A6888C6
        return ''.join([c for c in unicodedata.normalize('NFKD', title) if not unicodedata.combining(c)])

    title =  title.lower().replace('%20',' ').replace('%3a',':').replace('%27',"'").replace('  ',' ')

    title = _remove_diacritics(title)
    
    return title

def remove_release_year_from_title_if_exists(title, year):
    year = str(year)
    if not year:
        log.warning(f"DEBUG | get_video_data | remove_release_year_from_title_if_exists | Year is empty.")
        return title
    # Avoids: "Wonder Woman 1984" --> "Wonder Woman" (Release year is 2020)
    if year not in title:
        log.warning(f"DEBUG | get_video_data | remove_release_year_from_title_if_exists | No release year ({year}) to remove from {title}")
        return title
    log.warning(f"DEBUG | get_video_data | remove_release_year_from_title_if_exists | Removing year {year} from title {title}...")
    
    import re
    # Remove year from title if exists ("Avengers 2012" / "Avengers (2012)" --> "Avengers")
    try:
        title = re.compile(r"([ .\w'\-]+?)(\W" + year + r"\W?.*)").findall(title)[0][0].strip()
        return title
    except:
        return title

def manual_search_for_imdb_id(video_data):
                
    ################### Manual Search for IMDb ID using TMDB API #############################
    # Queries TMDB API with media_type, original_title, and year - Gets TMDB ID
    # Queries TMDB API with TMDB ID - Gets IMDb ID
    
    media_type = video_data['media_type']
    original_title = video_data['OriginalTitle']
    year = video_data['year']
    
    import requests
    
    log.warning(f"DEBUG | get_video_data | manual_search_for_imdb_id | Searching manually for IMDb ID | media_type={media_type} | original_title={original_title} | year={year}")
    
    TMDB_API_KEY = 'b370b60447737762ca38457bd77579b3'
    TMDB_API_BASE_URL = 'https://api.themoviedb.org/3/'

    params = {
        'api_key': TMDB_API_KEY,
        'query': original_title,
        'language': 'en'
    }

    search_with_year = False
    if year and int(year) > 0:
        search_with_year = True
        params['year'] = year

    search_for_tmdb_id_url = f'{TMDB_API_BASE_URL}search/{media_type}'

    try:
        response = requests.get(search_for_tmdb_id_url, params=params, timeout=DEFAULT_REQUEST_TIMEOUT)
        log.warning(f"DEBUG | get_video_data | manual_search_for_imdb_id | Full search_for_tmdb_id_url: {response.request.url}")
        data = response.json()
                
        ################### Sort results from TMDB API #############################
        # First by title, then by year
        # title - JSON parameter from TMDB API - For movies: ['title'] | For TV Shows: ['name']
        # year - JSON parameter from TMDB API - For movies: ['release_date'] | For TV Shows: ['first_air_date']
        
        # Define lambda function for title comparison
        title_comparison = lambda x: (
            x['title'].lower() == original_title.lower() if media_type == 'movie' else x['name'].lower() == original_title.lower()
        )
        
        # Define lambda function for year comparison
        year_comparison = lambda x: (
            str(year) in str(x.get('release_date', '')) if media_type == 'movie' else str(year) in str(x.get('first_air_date', ''))
        )

        # Define sorting key based on media type and year
        if search_with_year:
            key = lambda x: (title_comparison(x), year_comparison(x))
        else:
            key = title_comparison

        # Sort results based on sorting key
        sorted_results = sorted(data['results'], key=key, reverse=True)
        ############################################################################

        # Get the first result from the sorted list
        if sorted_results:
            first_result = sorted_results[0]
            # Check if the search result has an ID
            tmdb_id = first_result.get('id')
            # Fetch the details of the movie or TV show to get the IMDb ID
            search_for_imdb_id_url = f'{TMDB_API_BASE_URL}{media_type}/{tmdb_id}'
            params = {
                'api_key': TMDB_API_KEY,
                'append_to_response': 'external_ids',
                'language': 'en'
            }
            
            response = requests.get(search_for_imdb_id_url, params=params, timeout=DEFAULT_REQUEST_TIMEOUT)
            log.warning(f"DEBUG | get_video_data | manual_search_for_imdb_id | Full search_for_imdb_id_url: {response.request.url}")
            data = response.json()
            
            # Extract IMDb ID
            video_data['imdb'] = imdb_id = data['external_ids']['imdb_id']
            log.warning(f"DEBUG | get_video_data | manual_search_for_imdb_id | Found imdb_id={imdb_id} | IMDb URL: https://www.imdb.com/title/{imdb_id}")
            
            if not search_with_year:
                # Extract Release Year
                release_date_key = 'release_date' if media_type == "movie" else 'first_air_date'
                video_data['year'] = release_year = str(data.get(release_date_key, year).split('-')[0])
                log.warning(f"DEBUG | get_video_data | manual_search_for_imdb_id | Found year={release_year}")
                
            return video_data
            
        else:
            log.warning(f"DEBUG | get_video_data | manual_search_for_imdb_id | No TMDB results found.")
            return video_data
            
    except Exception as e:
        log.warning(f"DEBUG | get_video_data | manual_search_for_imdb_id | manual_search_for_imdb_id | Exception: {str(e)}")
        return video_data
      
def get_playing_filename():

    # Get the full path of the currently playing video and unquote it to handle any URL encoding
    file_original_path = unquote((xbmc.Player().getPlayingFile()))
    
    # Split the path to remove any query parameters
    file_original_path = file_original_path.split("?")[0]
    
    # Extract the basename of the file from the path
    file_original_path = os.path.basename(file_original_path)
            
    return file_original_path
    
def get_local_media_data(video_data):

    log.warning(f"DEBUG | get_video_data | get_local_media_data | file_original_path={video_data['file_original_path']}")
    log.warning(f"DEBUG | get_video_data | get_local_media_data | BEFORE PTN | video_data={video_data}")
    
    # Parse torrent title
    from resources.modules import parse_torrent_title
    PTN_results = parse_torrent_title.parse(video_data['file_original_path'])
    
    # Update video_data with PTN results
    video_data['title'] = PTN_results.get('title', video_data['title'])
    video_data['year'] = str(PTN_results.get('year', video_data['year']))
    video_data['season'] = str(PTN_results.get('season', video_data['season']))
    video_data['episode'] = str(PTN_results.get('episode', video_data['episode']))
    
    # Set TVShowTitle if it's a TV media type
    if video_data['season'] != '0' or video_data['episode'] != '0':
        video_data['TVShowTitle'] = video_data['title']

    log.warning(f"DEBUG | get_video_data | get_local_media_data | AFTER PTN | video_data={video_data}")
    
    return video_data

def get_video_data_playing():

    video_data = {}
    

    video_data['state'] = "playing"


    # Get the IMDb unique ID property of the currently playing video
    video_data['imdb_UniqueID'] = xbmc.getInfoLabel("VideoPlayer.UniqueID(imdb)")
    # Get the IMDBNumber property of the currently playing video
    video_data['IMDBNumber'] = xbmc.getInfoLabel("VideoPlayer.IMDBNumber")
    
    if video_data['imdb_UniqueID'].startswith('tt'):
        video_data['imdb'] = video_data['imdb_UniqueID']
    else:
        video_data['imdb'] = video_data['IMDBNumber']


    # Get the TMDB unique ID property of the currently playing video
    video_data['tmdb'] = xbmc.getInfoLabel("VideoPlayer.UniqueID(tmdb)")
    
    
    # Get the title of the currently playing video
    video_data['title'] = xbmc.getInfoLabel("VideoPlayer.Title")


    # Get the original title of the currently playing video
    video_data['OriginalTitle'] = xbmc.getInfoLabel("VideoPlayer.OriginalTitle")
        
    
    # Get the title of the TV show if the currently playing video is an episode of a TV show
    video_data['TVShowTitle'] = xbmc.getInfoLabel("VideoPlayer.TVShowTitle")
        

    # Get the year of release of the currently playing video
    video_data['year'] = xbmc.getInfoLabel("VideoPlayer.Year")
    
    
    # Get the season number of the currently playing video (if empty - 0)
    video_data['season'] = xbmc.getInfoLabel("VideoPlayer.Season") or '0'
        
        
    # Get the episode number of the currently playing video (if empty - 0)
    video_data['episode'] = xbmc.getInfoLabel("VideoPlayer.Episode") or '0'
    
    
    # Get the MPAA rating of the currently playing video
    video_data['mpaa'] = xbmc.getInfoLabel("VideoPlayer.mpaa")


    # Get the tagline of the currently playing video
    video_data['VideoPlayer.Tagline'] = xbmc.getInfoLabel("VideoPlayer.Tagline")
    # Fen addon tagline property
    video_data['Tagline_From_Fen'] = xbmcgui.Window(10000).getProperty("subs.player_filename")
    # Assign video_data['Tagline']
    video_data['Tagline'] = video_data['Tagline_From_Fen'] or video_data['VideoPlayer.Tagline']
    
    
    # Get the full path of the currently playing video and remove video file extension if exists
    video_data['file_original_path'] = get_playing_filename()
    
    
    return video_data
    
def get_video_data_not_playing():

    video_data = {}
    

    video_data['state'] = "not_playing"


    # Get the IMDb unique ID property of the currently selected item
    video_data['imdb_UniqueID'] = xbmc.getInfoLabel("ListItem.UniqueID(imdb)")
    # Get the IMDBNumber property of the currently selected item
    video_data['IMDBNumber'] = xbmc.getInfoLabel("ListItem.IMDBNumber")
    
    if video_data['imdb_UniqueID'].startswith('tt'):
        video_data['imdb'] = video_data['imdb_UniqueID']
    else:
        video_data['imdb'] = video_data['IMDBNumber']
        
        
    # Get the title of the currently selected item
    video_data['title'] = xbmc.getInfoLabel("ListItem.Title")
    
    
    # Get the original title of the currently selected item
    video_data['OriginalTitle'] = xbmc.getInfoLabel("ListItem.OriginalTitle")
    
    
    # Get the title of the TV show if the currently selected item is an episode of a TV show
    video_data['TVShowTitle'] = xbmc.getInfoLabel("ListItem.TVShowTitle")
    
    
    # Get the year of release of the currently selected item
    video_data['year'] = xbmc.getInfoLabel("ListItem.Year")
    
    
    # Get the season number of the currently selected item (if empty - 0)
    video_data['season'] = xbmc.getInfoLabel("ListItem.Season") or '0'
    
    
    # Get the episode number of the currently selected item (if empty - 0)
    video_data['episode'] = xbmc.getInfoLabel("ListItem.Episode") or '0'
    
    
    # Get the MPAA rating of the currently selected item
    video_data['mpaa'] = xbmc.getInfoLabel("ListItem.Mpaa")
    
    
    # Get the tagline of the currently selected item
    video_data['Tagline'] = xbmc.getInfoLabel("ListItem.Tagline")
        
        
    # Set the full path of the currently selected item to title
    video_data['file_original_path'] = video_data['title']
    
    
    return video_data

def get_video_data():

    ################### Get Video Data #######################################################
    if xbmc.Player().isPlaying():
        video_data = get_video_data_playing()
    else:
        video_data = get_video_data_not_playing()
    ##########################################################################################
                  

    ################### Local Media / External Player Support ################################
    video_data['is_local_media_playing'] = False
    
    if xbmc.Player().isPlaying():
    
        # When all three keys are empty
        if all(not video_data[key] for key in ['OriginalTitle', 'year', 'TVShowTitle']):
            video_data['is_local_media_playing'] = True
            log.warning(f"DEBUG | get_video_data | is_local_media_playing=True | Running get_local_media_data function.")
            video_data = get_local_media_data(video_data)
            
        # When at least one of the keys has a value
        else:
            log.warning(f"DEBUG | get_video_data | is_local_media_playing=False | Skipping get_local_media_data function.")
    ##########################################################################################


    ################### Set Media Type #######################################################
    video_data = set_media_type(video_data)
    ##########################################################################################


    ################### Fillnull OriginalTitle ###############################################
    if video_data['media_type'] == 'tv':
        video_data['OriginalTitle'] = video_data['OriginalTitle'] or video_data['TVShowTitle']
    else:
        video_data['OriginalTitle'] = video_data['OriginalTitle'] or video_data['title']
    ##########################################################################################


    ################### Clean Titles #########################################################
    video_data['title'] = clean_title(video_data['title'])
    
    video_data['OriginalTitle'] = clean_title(video_data['OriginalTitle'])
    
    if video_data['media_type'] == 'tv':
        video_data['TVShowTitle'] = clean_title(video_data['TVShowTitle'])
    ##########################################################################################


    ################### Telemedia - ListItem Remove Color Tags ###############################
    # Only when NOT playing
    if not xbmc.Player().isPlaying() and get_playing_addon() == 'plugin.video.telemedia':
        video_data['title'] = remove_color_tags(video_data['title'])
        video_data['OriginalTitle'] = remove_color_tags(video_data['OriginalTitle'])
        if video_data['media_type'] == 'tv':
            video_data['TVShowTitle'] = remove_color_tags(video_data['TVShowTitle'])
    ##########################################################################################
    
    
    ################### Remove Year From Titles ##############################################
    # Local media only.
    if video_data['is_local_media_playing'] == True:
        video_data['title'] = remove_release_year_from_title_if_exists(video_data['title'], video_data['year'])
        video_data['OriginalTitle'] = remove_release_year_from_title_if_exists(video_data['OriginalTitle'], video_data['year'])
        if video_data['media_type'] == 'tv':
            video_data['TVShowTitle'] = remove_release_year_from_title_if_exists(video_data['TVShowTitle'], video_data['year'])
    ##########################################################################################


    ################### Manual Search for IMDb ID using TMDB API #############################
    if not video_data['imdb'].startswith('tt'):
        log.warning(f"DEBUG | get_video_data | IMDb ID from video addon not found. searching manually using TMDB API...")
        video_data = manual_search_for_imdb_id(video_data)
    ##########################################################################################
    
    
    log.warning(f"DEBUG | get_video_data | FINAL | video_data={video_data}")
    return video_data

def save_file_name(filename,language,video_data):

    video_data_tagline = quote(video_data['Tagline'])
    video_data_file_original_path = quote(video_data['file_original_path'])
    
    try:
        from sqlite3 import dbapi2 as database
    except:
        from pysqlite2 import dbapi2 as database
    cacheFile=os.path.join(user_dataDir,'database.db')
    dbcon = database.connect(cacheFile)
    dbcur = dbcon.cursor()
    
    dbcur.execute("CREATE TABLE IF NOT EXISTS %s ("
                  "language TEXT, "
                  "filename TEXT, "
                  "video_data_tagline TEXT, "
                  "video_data_file_original_path TEXT);" % ('list_subs_cache'))


    dbcur.execute("SELECT * FROM list_subs_cache ")
    list_sub = dbcur.fetchall()
    dbcur.execute("INSERT INTO list_subs_cache Values ('{0}','{1}','{2}','{3}')".format(language,filename,video_data_tagline,video_data_file_original_path))

    dbcon.commit()
    dbcon.close()
def get_db_data(video_data):

    video_data_tagline = quote(video_data['Tagline'])
    video_data_file_original_path = quote(video_data['file_original_path'])
    
    try:
      from sqlite3 import dbapi2 as database
    except:
      from pysqlite2 import dbapi2 as database
    
    cacheFile=os.path.join(user_dataDir,'database.db')
    dbcon = database.connect(cacheFile)
    dbcur = dbcon.cursor()
    dbcur.execute("CREATE TABLE IF NOT EXISTS %s ("
                  "language TEXT, "
                  "filename TEXT, "
                  "video_data_tagline TEXT, "
                  "video_data_file_original_path TEXT);" % ('list_subs_cache'))
                  
    dbcur.execute("SELECT * FROM list_subs_cache")
    list_sub = dbcur.fetchall()
    dbcur.close()
    dbcon.close()
    
    all_subs={}
    for sub_language, sub_name, tagline, file_original_path in list_sub:
        if tagline == video_data_tagline or file_original_path == video_data_file_original_path:
            all_subs.setdefault(sub_name, []).append(sub_language)
            
    last_sub_name_in_cache=''
    last_sub_language_in_cache = ''
    
    # Get the LATEST written cached subtitle+language combination for current video Tagline/file path. (reversed list - first row is the last written)
    for sub_language, sub_name, tagline, file_original_path in reversed(list_sub):
        if tagline == video_data_tagline or file_original_path == video_data_file_original_path:
            last_sub_name_in_cache = sub_name
            last_sub_language_in_cache = sub_language
            break
    
    return last_sub_name_in_cache,last_sub_language_in_cache,all_subs


################### Future Use ###########################################################
# https://alwinesch.github.io/group__python___info_tag_video.html
# https://github.com/a4k-openproject/a4kSubtitles/pull/80

# if xbmc.Player().isPlaying():
    # videoInfo = xbmc.Player().getVideoInfoTag()
    # log.warning(f"DEBUG | videoInfo.getFilenameAndPath()={videoInfo.getFilenameAndPath()}")
    # log.warning(f"DEBUG | videoInfo.getFile()={videoInfo.getFile()}")
    # log.warning(f"DEBUG | videoInfo.getMediaType()={videoInfo.getMediaType()}")
    # log.warning(f"DEBUG | videoInfo.getTitle()={videoInfo.getTitle()}")
    # log.warning(f"DEBUG | videoInfo.getOriginalTitle()={videoInfo.getOriginalTitle()}")
    # log.warning(f"DEBUG | videoInfo.getTVShowTitle()={videoInfo.getTVShowTitle()}")
    # log.warning(f"DEBUG | videoInfo.getYear()={videoInfo.getYear()}")
    # log.warning(f"DEBUG | videoInfo.getSeason()={videoInfo.getSeason()}")
    # log.warning(f"DEBUG | videoInfo.getEpisode()={videoInfo.getEpisode()}")
    # log.warning(f"DEBUG | videoInfo.getUniqueID('imdb')={videoInfo.getUniqueID('imdb')}")
    # log.warning(f"DEBUG | videoInfo.getIMDBNumber()={videoInfo.getIMDBNumber()}")
    # log.warning(f"DEBUG | videoInfo.getTagLine()={videoInfo.getTagLine()}")
##########################################################################################
