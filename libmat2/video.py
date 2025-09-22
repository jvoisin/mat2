import subprocess
import functools
import shutil
import logging

from typing import Union, Dict

from . import exiftool
from . import bubblewrap


class AbstractFFmpegParser(exiftool.ExiftoolParser):
    """ Abstract parser for all FFmpeg-based ones, mainly for video. """
    # Some fileformats have mandatory metadata fields
    meta_key_value_allowlist: Dict[str, Union[str, int]] = dict()

    def remove_all(self) -> bool:
        if self.meta_key_value_allowlist:
            logging.warning('The format of "%s" (%s) has some mandatory '
                            'metadata fields; mat2 filled them with standard '
                            'data.', self.filename, ', '.join(self.mimetypes))
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
            if self.sandbox:
                bubblewrap.run(cmd, check=True,
                               input_filename=self.filename,
                               output_filename=self.output_filename)
            else:
                subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            logging.error("Something went wrong during the processing of %s: return code %d", self.filename, e.returncode)
            return False
        return True

    def get_meta(self) -> Dict[str, Union[str, Dict]]:
        meta = super().get_meta()

        ret: Dict[str, Union[str, Dict]] = dict()
        for key, value in meta.items():
            if key in self.meta_key_value_allowlist:
                if value == self.meta_key_value_allowlist[key]:
                    continue
            ret[key] = value
        return ret


class WMVParser(AbstractFFmpegParser):
    mimetypes = {'video/x-ms-wmv', }
    meta_allowlist = {'AudioChannels', 'AudioCodecID', 'AudioCodecName',
                      'ErrorCorrectionType', 'AudioSampleRate', 'DataPackets',
                      'Directory', 'Duration', 'ExifToolVersion',
                      'FileAccessDate', 'FileInodeChangeDate', 'FileLength',
                      'FileModifyDate', 'FileName', 'FilePermissions',
                      'FileSize', 'FileType', 'FileTypeExtension',
                      'FrameCount', 'FrameRate', 'ImageHeight', 'ImageSize',
                      'ImageWidth', 'MIMEType', 'MaxBitrate', 'MaxPacketSize',
                      'Megapixels', 'MinPacketSize', 'Preroll', 'SendDuration',
                      'SourceFile', 'StreamNumber', 'VideoCodecName', }
    meta_key_value_allowlist = {  # some metadata are mandatory :/
        'AudioCodecDescription': '',
        'CreationDate': '0000:00:00 00:00:00Z',
        'FileID': '00000000-0000-0000-0000-000000000000',
        'Flags': 2,  # FIXME: What is this? Why 2?
        'ModifyDate': '0000:00:00 00:00:00',
        'TimeOffset': '0 s',
        'VideoCodecDescription': '',
        'StreamType': 'Audio',
        }


class AVIParser(AbstractFFmpegParser):
    mimetypes = {'video/x-msvideo', }
    meta_allowlist = {'SourceFile', 'ExifToolVersion', 'FileName', 'Directory',
                      'FileSize', 'FileModifyDate', 'FileAccessDate',
                      'FileInodeChangeDate', 'FilePermissions', 'FileType',
                      'FileTypeExtension', 'MIMEType', 'FrameRate', 'MaxDataRate',
                      'FrameCount', 'StreamCount', 'StreamType', 'VideoCodec',
                      'VideoFrameRate', 'VideoFrameCount', 'Quality',
                      'SampleSize', 'BMPVersion', 'ImageWidth', 'ImageHeight',
                      'Planes', 'BitDepth', 'Compression', 'ImageLength',
                      'PixelsPerMeterX', 'PixelsPerMeterY',
                      'NumImportantColors', 'NumColors',
                      'RedMask', 'GreenMask', 'BlueMask', 'AlphaMask',
                      'ColorSpace', 'AudioCodec', 'AudioCodecRate',
                      'AudioSampleCount',
                      'AudioSampleRate', 'Encoding', 'NumChannels',
                      'SampleRate', 'AvgBytesPerSec', 'BitsPerSample',
                      'Duration', 'ImageSize', 'Megapixels'}


class MP4Parser(AbstractFFmpegParser):
    mimetypes = {'video/mp4', }
    meta_allowlist = {'AudioFormat', 'AvgBitrate', 'Balance', 'TrackDuration',
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
    meta_key_value_allowlist = {  # some metadata are mandatory :/
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


@functools.lru_cache(maxsize=None)
def _get_ffmpeg_path() -> str:  # pragma: no cover
    which_path = shutil.which('ffmpeg')
    if which_path:
        return which_path

    raise RuntimeError("Unable to find ffmpeg")
