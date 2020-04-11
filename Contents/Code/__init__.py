import os, string, hashlib, base64, re, plistlib, unicodedata
import config
import localaudio
import sqlite3


def Start():
    """ Start of plugin """
    strLog = ''.join((
        str(L('STARTING')),
        ' %s ' % (L('PLUGIN_NAME')) ))
    Log.Info(strLog)

class separateMediaPartsAgentMovies(Agent.Movies):
    """ Movies Plug-In """
    name = L('PLUGIN_NAME') + ' (Movies)'
    languages = [Locale.Language.NoLanguage]
    primary_provider = False
    contributes_to = [
        'com.plexapp.agents.imdb',
        'com.plexapp.agents.themoviedb',
        'com.plexapp.agents.plexmovie',
        'com.plexapp.agents.none']

    def search(self, results, media, lang, manual):
        Log.Debug("---------------------BEGIN SEARCH---------------------")
        
        db_file = os.path.join(Prefs['library_path'],'Application Support/Plex Media Server/Plug-in Support/Databases/com.plexapp.plugins.library.db')
        Log.Debug('Opening database file %s', db_file)
        conn = sqlite3.connect(db_file, timeout=30000)

        for item in media.items:
            localaudio.findAudio(item.parts, conn)

        """ Return a dummy object to satisfy the framework """
        results.Append(MetadataSearchResult(id='null', score=100))

        conn.close()

        Log.Debug("---------------------END SEARCH---------------------")

    def update(self, metadata, media, lang, force):
        
        Log.Debug("---------------------BEGIN UPDATE---------------------")
        
        # Clear out the title to ensure stale data doesn't clobber other agents' contributions.
        metadata.title = None
        
        all_subs = {}
        for item in media.items:
            for part in item.parts:
                for sub_stream in [x for x in part.streams if hasattr(x, 'url') and x.type == 3]:
                    if not all_subs.has_key(sub_stream.url):
                        file_name = sub_stream.url[7:]
                        forced = ''
                        default = ''
                        (file, ext) = os.path.splitext(file_name)
                        split_tag = file.rsplit('.', 1)
                        if len(split_tag) > 1 and split_tag[1].lower() in ['forced', 'default'] :
                            if 'forced' == split_tag[1].lower():
                                forced = '1'
                            if 'default' == split_tag[1].lower():
                                default = '1'                        
                        all_subs[sub_stream.url] = type('Subtitle', (object,), {})()
                        all_subs[sub_stream.url].subtitleObject = Proxy.LocalFile(file_name, codec = sub_stream.codec, format = sub_stream.format, default = default, forced = forced)
                        all_subs[sub_stream.url].language = Locale.Language.Match(sub_stream.language)
                        all_subs[sub_stream.url].basename = os.path.basename(file_name)
                        Log.Debug('Discovered subtitle file: ' + all_subs[sub_stream.url].basename + ' language: ' + all_subs[sub_stream.url].language + ' codec: ' + sub_stream.codec + ' format: ' + sub_stream.format + ' default: ' + default + ' forced: ' + forced)
        
        for item in media.items:    
            for part in item.parts:
                arr = all_subs
                for subs_key in list(set(all_subs.keys()) - set([x.url for x in part.streams if hasattr(x, 'url') and x.type == 3])):
                    sub = all_subs[subs_key]
                    part.subtitles[sub.language][sub.basename] = sub.subtitleObject
                    Log.Debug('Added subtitle file %s for item %s', subs_key, part.file)
                

        Log.Debug("---------------------END UPDATE---------------------")