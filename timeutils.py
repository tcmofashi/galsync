# -*- coding: UTF8 -*-
import os
import datetime


def get_folder_modification_time(folder_path):
    """
    获取文件夹的最后修改时间，并将其转换为 ISO 8601 格式的字符串。
    """
    # 获取文件夹的最后修改时间的时间戳
    modification_time_timestamp = os.path.getmtime(folder_path)
    
    # 将时间戳转换为 datetime 对象
    modification_time_datetime = datetime.datetime.fromtimestamp(modification_time_timestamp)
    
    # 将 datetime 对象转换为 ISO 8601 格式的字符串
    modification_time_iso = modification_time_datetime.isoformat()
    
    return modification_time_iso

