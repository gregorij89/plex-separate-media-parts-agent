import os, unicodedata
import config
import helpers
import re
from subprocess import check_output
import json
import urllib
import sqlite3
import time
import urlparse
from sqlite3 import Error

try:
    any
except NameError:
    def any(s):
        for v in s:
            if v:
                return True
        return False


def findAudio(parts, conn):
    base_name = ""
    
    
    for part in parts:
        
        part_file = helpers.unicodize(part.file)
        dir_path = os.path.dirname(part_file)
        Log.Debug('Processing file %s',part_file)
        part_base_name = os.path.basename(part_file)
        separator_position = part_base_name.find(' - ')
        if separator_position > 0:
            part_base_name=part_base_name[:separator_position]
        else:
            (part_base_name, ext) = os.path.splitext(part_base_name)
        
        Log.Debug('Base name is %s',part_base_name)
        
        cur = conn.cursor()
        cur.execute('SELECT id, media_item_id FROM media_parts WHERE file = "' + part_file + '"')
        (media_part_id, media_item_id) = cur.fetchone()
        cur.close

        last_index = 0
        for stream in [x for x in part.streams if x.type == 2]:
            if last_index < stream.index:
                last_index = stream.index
        last_index = last_index + 1
        if last_index < 1000:
            Log.Debug('There is no sided audio stream for current video file. Setting audio stream index to 1000')
            last_index = 1000
        else:
            Log.Debug('Sided audio stream for current video file was found. Setting audio stream index to %s', last_index)

        found_audio_streams = []
        for file_path in sorted(os.listdir(dir_path)):
            file_path = helpers.unicodize(file_path)
            full_path = os.path.join(dir_path,file_path)
            (root, ext) = os.path.splitext(file_path)
            
            if ext.lower()[1:] not in config.AUDIO_TRACKS:
                Log.Debug('File %s is not an audio track. Skipping.',file_path)
                continue

            audio_regex = r"^" + re.escape(part_base_name) + r"\.[a-zA-Z]{2,3}\.[a-zA-Z0-9_.-]*"
            audio_with_commnet = re.match(audio_regex, root)

            audio_regex = r"^" + re.escape(part_base_name) + r"\.[a-zA-Z]{2,3}$"
            audio_no_commnet = re.match(audio_regex, root)

            if (not audio_with_commnet and not audio_no_commnet):
                Log.Debug('File %s is not an audio track for processed item. Skipping',file_path)
                continue
            
            file_lang_search = re.search(r"^" + re.escape(part_base_name) + r"\.([a-zA-Z]{2,3})",root)
            if file_lang_search:
                file_lang = file_lang_search.group(1)
            media_data = check_output([os.path.join(Prefs['ffmpeg_path'],"ffprobe"), "-hide_banner", "-loglevel", "fatal", "-show_error", "-show_streams", "-select_streams", "a", "-print_format", "json", "-i", full_path]).decode("utf-8")
            media_data = json.loads(media_data)
            for media_stream in media_data['streams']:
                result = type('AudioResult', (object,), {})()
                
                result.codec = media_stream["codec_name"]
                if result.codec == "dts":
                    result.codec = "dca"
                
                result.extra_data = {}
                if 'channel_layout' in media_stream:
                    result.extra_data['ma:audioChannelLayout'] = media_stream['channel_layout']

                if 'sample_rate' in media_stream:
                    result.extra_data['ma:samplingRate'] = media_stream['sample_rate']

                if result.codec == "dca":
                    if 'bits_per_raw_sample' in media_stream:
                        result.extra_data['ma:bitDepth'] = media_stream['bits_per_raw_sample']
                    else:
                        result.extra_data['ma:bitDepth'] = 24

                if 'profile' in media_stream:
                    result.extra_data['ma:profile'] = profile(media_stream['profile'])
                
                result.language = 'und'
                title = ''
                if 'tags' in media_stream:
                    if 'title' in media_stream['tags']:
                        result.extra_data['ma:title'] = media_stream['tags']['title']
                    if 'language' in media_stream['tags']:
                        result.language = media_stream['tags']['language']
                
                if result.language != file_lang and ('tags' not in media_stream or 'language' not in media_stream['tags']):
                    result.language = file_lang
                
                if title != "" and ('tags' not in media_stream or 'title' not in media_stream['tags']):
                    result.extra_data['ma:title'] = title
                
                result.extra_data = urllib.urlencode(result.extra_data)

                result.bitrate = None
                if "bit_rate" in media_stream:
                    result.bitrate = int(media_stream["bit_rate"])

                
                result.stream_type_id = 2
                result.url = 'file://' + full_path
                result.channels=media_stream["channels"]
                result.index = media_stream["index"]
                
                found_audio_streams.append(result.url)            

                if (any(hasattr(x, 'url') and x.url == result.url for x in part.streams)):
                    Log.Debug('Audio track %s is already assigned',file_path)
                    continue

                Log.Debug('Adding audio track %s to the processed item with stream index %s',file_path, last_index)
                
                
                date = time.strftime('%Y-%m-%d %H:%M:%S')
                data = (None, 2, media_item_id, result.url, result.codec, result.language, date, date, last_index, media_part_id, result.channels, result.bitrate, result.index, 0, 0, result.extra_data,)
                cur = conn.cursor()
                cur.execute('INSERT INTO `media_streams` (`id`, `stream_type_id`, `media_item_id`, `url`, `codec`, `language`, `created_at`, `updated_at`, `index`, `media_part_id`, `channels`, `bitrate`, `url_index`, `default`, `forced`, `extra_data`) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);', data)
                cur.execute('SELECT `metadata_item_id` FROM `media_items` WHERE `id` = ? LIMIT 1', (media_item_id,))
                (metadata_item_id,) = cur.fetchone()
                cur.execute('UPDATE `metadata_items` SET `added_at`=? WHERE `id`=?', (date, metadata_item_id,))
                cur.close()
                last_index = last_index + 1
        
        cur = conn.cursor()
        
        if len(found_audio_streams) > 0:
            # Nothing from https://support.plex.tv/articles/203810286-what-media-formats-are-supported/ supports split, so we will use that to force transcoding
            cur.execute('UPDATE `media_items` SET `container` = "split", `audio_codec` = ? WHERE `id` = ?', (result.codec,media_item_id,))
            Log.Debug('Updating media item container attribute')

            cur.execute('SELECT `extra_data` FROM `media_parts` WHERE `file` = ? LIMIT 1', (part.file,))
            (extra_data_part,) = cur.fetchone()
            sq = urlparse.parse_qsl(extra_data_part)
            extra_data = dict(sq)
            extra_data['ma:container'] = 'split'
            extra_data_encoded = urllib.urlencode(extra_data)
            cur.execute('UPDATE `media_parts` SET `extra_data` = ? WHERE `file` = ?', (extra_data_encoded,part.file,))
            Log.Debug('Updating media part container attribute')
        
        for del_stream in [x for x in part.streams if hasattr(x, 'url') and x.type == 2 and x.url not in found_audio_streams]:
            Log.Debug("Deleting unused stream %s", del_stream.url)
            cur.execute('DELETE FROM `media_streams` WHERE `url` = ?', (del_stream.url,))
        cur.close()

    conn.commit()
    

                    




def profile(p):
    if p == "DTS":
        return "dts"

    if p == "DTS-HD MA":
        return "ma"

    print("Unknown profile: %s" % p)
    return p
