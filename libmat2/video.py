import os
import subprocess
import logging

from typing import Dict, Union

from . import exiftool


class AbstractFFmpegParser(exiftool.ExiftoolParser):
    """ Abstract parser for all FFmpeg-based ones, mainly for video. """
    def remove_all(self) -> bool:
        cmd = [_get_ffmpeg_path(),
               '-i', self.filename,      # input file
               '-y',                     # overwrite existing output file
               '-map', '0',              # copy everything all streams from input to output
               '-codec', 'copy',         # don't decode anything, just copy (speed!)
               '-loglevel', 'panic',     # Don't show log
               '-hide_banner',           # hide the banner
               '-map_metadata', '-1',    # remove supperficial metadata
               '-map_chapters', '-1',    # remove chapters
               '-disposition', '0',      # Remove dispositions (check ffmpeg's manpage)
               '-fflags', '+bitexact',   # don't add any metadata
               '-flags:v', '+bitexact',  # don't add any metadata
               '-flags:a', '+bitexact',  # don't add any metadata
               self.output_filename]
        try:
            subprocess.check_call(cmd)
        except subprocess.CalledProcessError as e:
            logging.error("Something went wrong during the processing of %s: %s", self.filename, e)
            return False
        return True


class AVIParser(AbstractFFmpegParser):
    mimetypes = {'video/x-msvideo', }
    meta_whitelist = {'SourceFile', 'ExifToolVersion', 'FileName', 'Directory',
                      'FileSize', 'FileModifyDate', 'FileAccessDate',
                      'FileInodeChangeDate', 'FilePermissions', 'FileType',
                      'FileTypeExtension', 'MIMEType', 'FrameRate', 'MaxDataRate',
                      'FrameCount', 'StreamCount', 'StreamType', 'VideoCodec',
                      'VideoFrameRate', 'VideoFrameCount', 'Quality',
                      'SampleSize', 'BMPVersion', 'ImageWidth', 'ImageHeight',
                      'Planes', 'BitDepth', 'Compression', 'ImageLength',
                      'PixelsPerMeterX', 'PixelsPerMeterY', 'NumColors',
                      'NumImportantColors', 'NumColors', 'NumImportantColors',
                      'RedMask', 'GreenMask', 'BlueMask', 'AlphaMask',
                      'ColorSpace', 'AudioCodec', 'AudioCodecRate',
                      'AudioSampleCount', 'AudioSampleCount',
                      'AudioSampleRate', 'Encoding', 'NumChannels',
                      'SampleRate', 'AvgBytesPerSec', 'BitsPerSample',
                      'Duration', 'ImageSize', 'Megapixels'}

class MP4Parser(AbstractFFmpegParser):
    mimetypes = {'video/mp4', }
    meta_whitelist = {'AudioFormat', 'AvgBitrate', 'Balance', 'TrackDuration',
                      'XResolution', 'YResolution', 'ExifToolVersion',
                      'FileAccessDate', 'FileInodeChangeDate', 'FileModifyDate',
                      'FileName', 'FilePermissions', 'MIMEType', 'FileType',
                      'FileTypeExtension', 'Directory', 'ImageWidth',
                      'ImageSize', 'ImageHeight', 'FileSize', 'SourceFile',
                      'BitDepth', 'Duration', 'AudioChannels',
                      'AudioBitsPerSample', 'AudioSampleRate', 'Megapixels',
                      'MovieDataSize', 'VideoFrameRate', 'MediaTimeScale',
                      'SourceImageHeight', 'SourceImageWidth',
                      'MatrixStructure', 'MediaDuration'}
    meta_key_value_whitelist = {  # some metadata are mandatory :/
        'CreateDate': '0000:00:00 00:00:00',
        'CurrentTime': '0 s',
        'MediaCreateDate': '0000:00:00 00:00:00',
        'MediaLanguageCode': 'und',
        'MediaModifyDate': '0000:00:00 00:00:00',
        'ModifyDate': '0000:00:00 00:00:00',
        'OpColor': '0 0 0',
        'PosterTime': '0 s',
        'PreferredRate': '1',
        'PreferredVolume': '100.00%',
        'PreviewDuration': '0 s',
        'PreviewTime': '0 s',
        'SelectionDuration': '0 s',
        'SelectionTime': '0 s',
        'TrackCreateDate': '0000:00:00 00:00:00',
        'TrackModifyDate': '0000:00:00 00:00:00',
        'TrackVolume': '0.00%',
    }

    def remove_all(self) -> bool:
        logging.warning('The format of "%s" (video/mp4) has some mandatory '
                        'metadata fields; mat2 filled them with standard data.',
                        self.filename)
        return super().remove_all()

    def get_meta(self) -> Dict[str, Union[str, dict]]:
        meta = super().get_meta()

        ret = dict()  # type: Dict[str, Union[str, dict]]
        for key, value in meta.items():
            if key in self.meta_key_value_whitelist.keys():
                if value == self.meta_key_value_whitelist[key]:
                    continue
            ret[key] = value
        return ret


def _get_ffmpeg_path() -> str:  # pragma: no cover
    ffmpeg_path = '/usr/bin/ffmpeg'
    if os.path.isfile(ffmpeg_path):
        if os.access(ffmpeg_path, os.X_OK):
            return ffmpeg_path

    raise RuntimeError("Unable to find ffmpeg")
