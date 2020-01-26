import os
import shutil
import io
import codecs
import sys


def Start():
    """ Start of plugin """
    strLog = ''.join((
        str(L('STARTING')),
        ' %s ' % (L('PLUGIN_NAME')) ))
    Log.Info(strLog)
    try:
        print (strLog)
    except Exception:
        pass

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
        """ Return a dummy object to satisfy the framework """
        results.Append(MetadataSearchResult(id='null', score=100))

    def update(self, metadata, media, lang, force):
        """ Handle the object returned to us, so we
        can find the directory to look in """