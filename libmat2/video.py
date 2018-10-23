import os
import subprocess
import logging

from . import exiftool


class AVIParser(exiftool.ExiftoolParser):
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

    def remove_all(self):
        cmd = [_get_ffmpeg_path(),
               '-i', self.filename,      # input file
               '-y',                     # overwrite existing output file
               '-loglevel', 'panic',     # Don't show log
               '-hide_banner',           # hide the banner
               '-codec', 'copy',         # don't decode anything, just copy (speed!)
               '-map_metadata', '-1',    # remove supperficial metadata
               '-map_chapters', '-1',    # remove chapters
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


def _get_ffmpeg_path() -> str:  # pragma: no cover
    ffmpeg_path = '/usr/bin/ffmpeg'
    if os.path.isfile(ffmpeg_path):
        if os.access(ffmpeg_path, os.X_OK):
            return ffmpeg_path

    raise RuntimeError("Unable to find ffmpeg")
