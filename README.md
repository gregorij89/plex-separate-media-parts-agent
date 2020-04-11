# Separate media parts feature
=========

The idea of this feature is to have separate files for video, audio and subtitles. In that case, one can have multiple video files in different resolutions and codecs, multiple audio files also in different quality and then combine them together during playback. The result is that Plex can support different players (TVs, Web, PC, etc.) and serve them content, that is best suited for such player, without actual need of cpu expensive transcoding. Of course, muxing on the server side is needed for that. On the other hand, muxing is relatively inexpensive task. That´s what i.e. youtube is doing with their videos.

For better understanding, when using this feature, your movie folder should look similar to this:

The Movie (2020) /base folder for the movie/

- The Movie (2020).mkv /video track in the highest quality (4k HDR hevc)/
- The Movie (2020) - 1080p.mkv /video track in lower quality (1080p hevc)/
- The Movie (2020) - 720p.mkv /another video track in lower quality (720p avc)/
- The Movie (2020).en.atmos.mka /audio track for all the video versions/
- The Movie (2020).en.aac.mka /audio track for all the video versions/
- The Movie (2020).fr.dts.mka /another audio track for all the video versions/
- The Movie (2020).fr.aac.mka /another audio track for all the video versions/
- The Movie (2020).cs.ac3.mka /another audio track for all the video versions/
- The Movie (2020).cs.aac.mka /another audio track for all the video versions/
- The Movie (2020).en.srt /subtitles for all video versions/
- The Movie (2020).en.forced.srt /subtitles for all video versions/
- … similarly subtitles for other languages …
- Trailers /or any other folder for local assets/

The good thing here is, that majority of plex clients will choose the best configuration for them. So for example my PC on local network choose 4k HDR hevc video with Atmos audio track. When I open the same movie in the remote web browser, the client will choose 720p avc video with aac stereo audio track, etc. So the spectator is always served with the best looking content, that his device can handle.

## What is needed

This feature consist of two independent parts. Firstly, it is needed to tell Plex Media Server, that for the particular movie, separated files are used. This is task for the metadata agent, that needs to be installed and enabled for the Library. You can find this metadata agent in [github repository](https://github.com/gregorij89/plex-separate-media-parts-agent).

When you want to play the movie, Plex needs to know, that it has to mux audio and video into the stream. Default transcoder is not aware of such configuration, so it will play only the video without an audio. For that, simple script is needed, that replaces the default transcoder, checks if requested movie has sided audio, and then handover the job with all needed information to the default transcoder. Because I am operating Plex as a docker container, I've prepared my own dockerfile, that alter official Plex image with this feature. This dockerfile can be found in its [github repository](https://github.com/gregorij89/plex-separate-media-parts-docker)

## Metadata agent

Metadata agent (plugin) for identifying separated audio files for the video files. It is required as the first step for using separate audio feature. Firstly, you have to install this agent as any other metadata agent or Plex plugin. You can find the steps, how to do that, on the [Plex support](https://support.plex.tv/articles/201187656-how-do-i-manually-install-a-plugin/). You have to extract the content of this repository into folder 

```
path_to_plex_config_folder/Plex Media Server/Plug-ins/SeparateMediaParts.bundle
```

Then in the agents settings for the movies, you need to config and enable this agent. There are two things, that needs to be configured:

- Path to the library folder. That is the configuration folder, where the configuration of Plex is stored. For docker, it is /config/Library.
- Path to the ffmpeg tool. In order to parse information from the audio tracks, ffprobe is used. This path leads the script to the folder, where ffprobe is located. Use the folder, script will automaticaly adds ffprobe.

Now, whenever metadata for the movie in the Library are scaned, this agent will also scan for the sided audio tracks and adds them to the movie.

# Known issues

This feature is proven to be working on Plex Web Client, Plex Windows Client and Plex iOS Client. Others haven't been tested. Also there is an issue with Plex for Kodi addon. This addon completely fails to cooperate with this feature and results in the Playback failure when used.

# Disclaimer

This feature is provided as is without any support and responsibility. It is not mature enough to be widely used. So use it only on your own risk and be 100 % sure that you know what you are doing. Unfortunatelly, expected behavior of this feature is reachable only with direct altering of Plex databse and replacing core components of Plex Media Server - therefore it is not how Plex is intendend to be used.

Please note that this Github repositories are only mirrors of my private personal git repositories, that I am using and developing against.