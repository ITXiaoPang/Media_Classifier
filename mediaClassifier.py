#!/usr/bin/env python
# -*- coding:utf-8 -*-

# @Time: 2018/4/6 19:21
# @File: mediaClassifier.py
# @Project: Media_Classifier
# @IDE: PyCharm
# @Author: ITXiaoPang
# @Site: http://www.OSSky.org

import os
import sys
import time
import json
import shutil
import datetime
import exifread
import videoprops
import subprocess

__version__ = "1.0.0"


def get_picture_shooting_date(my_file: str):
    try:
        with open(my_file, 'rb') as f:
            my_exif_tags = exifread.process_file(
                f=f,
                stop_tag='DateTimeOriginal',
                details=False,
                strict=False,
                debug=False
            )
            shooting_time = my_exif_tags.get('EXIF DateTimeOriginal')
            if shooting_time:
                shooting_time = str(shooting_time)
                shooting_date = shooting_time.split(' ')[0].replace(':', '')
                ret = shooting_date
            else:
                ret = None
    except Exception as ex:
        ret = None
        print(ex)
    return ret


def get_video_shooting_date(my_file: str):

    def utc2local(utc_st):
        """UTC时间转本地时间（+8: 00）"""
        now_stamp = time.time()
        local_time = datetime.datetime.fromtimestamp(now_stamp)
        utc_time = datetime.datetime.utcfromtimestamp(now_stamp)
        offset = local_time - utc_time
        local_st = utc_st + offset
        return local_st

    def get_video_properties(movie: str):
        ffprobe_args = (
            '-loglevel', 'panic',
            '-select_streams', 'v:0',
            '-show_streams',
            '-show_format',
            '-print_format', 'json'
        )
        if not os.path.isfile(movie) or not os.access(movie, os.R_OK):
            raise RuntimeError(f'File not found or inaccessible: {movie}')

        output = subprocess.check_output([videoprops.which_ffprobe(), *ffprobe_args, movie])
        props = json.loads(output)

        return props

    try:
        video_info = get_video_properties(my_file)

        streams_info = video_info.get('streams', [])
        if streams_info:
            tags_creation_time = streams_info[0].get('tags', {}).get('creation_time', None)
        else:
            tags_creation_time = None

        format_creation_time = video_info.get('format', {}).get('tags', {}).get('creation_time', None)

        if tags_creation_time:
            shooting_time = tags_creation_time
        elif format_creation_time:
            shooting_time = format_creation_time
        else:
            shooting_time = None
    except Exception as ex:
        print(ex)
        shooting_time = None

    if shooting_time:
        ret = utc2local(datetime.datetime.strptime(shooting_time, "%Y-%m-%dT%H:%M:%S.%fZ")).strftime("%Y%m%d")
    else:
        ret = None
    return ret


def get_modify_date(my_file: str):
    my_m_time = os.stat(my_file).st_mtime
    ret = time.strftime("%Y%m%d", time.localtime(my_m_time))
    return ret


def mkdir_if_not_exist(my_folder: str):
    if not os.path.isdir(my_folder):
        os.mkdir(my_folder)


def do_classify(my_path: str):
    idx = 0
    if os.path.isdir(my_path):
        my_files = [f for f in os.listdir(my_path) if os.path.isfile(os.path.join(my_path, f))]
        num_of_files = len(my_files)
        print('Number of files: ' + str(num_of_files))
        for i in my_files:
            idx += 1
            print(f'{i} ({idx}/{num_of_files})')
            my_file = os.path.join(my_path, i)

            picture_shooting_date = get_picture_shooting_date(my_file)
            if picture_shooting_date:
                folder_name = os.path.join(my_path, picture_shooting_date)
            else:
                video_shooting_date = get_video_shooting_date(my_file)
                if video_shooting_date:
                    folder_name = os.path.join(my_path, video_shooting_date)
                else:
                    modify_date = get_modify_date(my_file)
                    no_shooting_date_folder = os.path.join(my_path, '无拍摄时间')
                    mkdir_if_not_exist(no_shooting_date_folder)
                    folder_name = os.path.join(no_shooting_date_folder, modify_date)

            mkdir_if_not_exist(folder_name)
            shutil.move(my_file, folder_name)


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        list(map(do_classify, sys.argv[1:]))
    else:
        do_classify(input('Path:'))
