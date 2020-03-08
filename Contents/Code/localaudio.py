import os, unicodedata
import config
import helpers
import re

def findAudio(parts=[]):
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

            Log.Debug('Adding audio track %s to the processed item',file_path)