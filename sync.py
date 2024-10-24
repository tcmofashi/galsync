# -*- coding: UTF8 -*-
import os
import json
import yaml
import socket
import datetime
# import psutil
import zipfile
import io
import shutil
import netifaces
import logging


def get_folder_modification_time(folder_path,oldest=False):
    """
    获取文件夹的最后修改时间，并将其转换为 ISO 8601 格式的字符串。
    """
    # 获取文件夹的最后修改时间的时间戳
    modification_time_timestamp = os.path.getmtime(folder_path)
    # 将时间戳转换为 datetime 对象
    modification_time_datetime = datetime.datetime.fromtimestamp(modification_time_timestamp)
    if oldest:
        modification_time_datetime = datetime.datetime.fromtimestamp(1)
    # 将 datetime 对象转换为 ISO 8601 格式的字符串
    modification_time_iso = modification_time_datetime.isoformat()
    return modification_time_iso

def get_local_ips():
    """获取本机的所有 IPv4 和 IPv6 地址"""
    local_ips = {
        'ipv4': [],
        'ipv6': []
    }
    for ifaceName in netifaces.interfaces():
        ip4 = [i['addr'] for i in netifaces.ifaddresses(ifaceName).setdefault(netifaces.AF_INET, [{'addr':'None'}] )]
        for i in ip4:
            if i!='None':
                local_ips['ipv4'].append(i)
        ip6 = [i['addr'] for i in netifaces.ifaddresses(ifaceName).setdefault(netifaces.AF_INET6, [{'addr':'None'}] )]
        for i in ip6:
            if i!='None':
                if r'%' in i:
                    local_ips['ipv6'].append(i.split('%')[0])
                else:
                    local_ips['ipv6'].append(i)
    # 获取主机名
    print(local_ips)
    return local_ips



def get_root_folder_name(iostream):
    """
    获取压缩包根目录下的唯一文件夹名称
    :param zip_path: 压缩文件的路径
    :return: 根目录下的唯一文件夹名称
    """
    with zipfile.ZipFile(iostream, 'r') as zipf:
        root_folders = set([os.path.dirname(name).split('/')[0] for name in zipf.namelist() if '/' in name])
        if len(root_folders) == 1:
            return root_folders.pop()
        else:
            raise ValueError("压缩包根目录下没有唯一的文件夹或有多个文件夹")



config_template={
    'tcmofashi':{
    'username':'none',
    'devicename':'test',
    'ipv4':{
        # 'test1':[['10.42.0.32','60721']],
        # 'server':['10.42.0.1'] #save for test
    },
    'ipv6':{
        # 'test1':[],
        # 'server':['2001:da8:b801:285e:78b6:2427:99e7:56ec'],
    },
    'filemap':{
        #     '1':{
        #  'path':{
        #  'test1':r"/home/tcmofashi/proj/galsync/test1/1",
        #  # 'server':r'/mnt/E/ATRI -My Dear Moments-', # get from remote
        #  },
        #  'mtime':{},
        #  'mode':'newest' # mode:'devicename' or 'newest',empty path won't be origin
        #  }
    }
    }
}

yaml_config={
    'tcmofashi':{
    'username':'tcmofashi',
    'devicename':'test1',
    'allowAllUser':True,
    'localipv4':[['10.42.0.32',60721]],
    'localipv6':[],
    'remoteipv4':[['10.42.0.32',50721]], # for default
    'remoteipv6':[],
    'filemap':[
        {
            'name':'1',
            'path':r"/home/tcmofashi/proj/galsync/test1/1",
            'mode':'newest',
        }
,
        {
            'name':'2',
            'path':r"/home/tcmofashi/proj/galsync/test1/2",
            'mode':'newest',
        }
,
        {
            'name':'3',
            'path':r"/home/tcmofashi/proj/galsync/test1/3",
            'mode':'newest',
        }
,
        {
            'name':'4',
            'path':r"/home/tcmofashi/proj/galsync/test1/4",
            'mode':'newest',
        }

    ]
    }
}

global_config={
    'enableUserName':'tcmofashi',
    'allowAllUser':True,
    'cacheAll':True,
    'cacheDir':'./tmp',
    'defaultDeviceName':'pc1',
    'defaultPort':60721,
    'outputMode':'DEBUG'
}

logging.basicConfig(level=logging.DEBUG)

class Config:
    def __init__(self,) -> None:
        if os.path.exists('./sync.json'):
            with open('./sync.json','r',encoding='utf-8') as fp:
                txt=fp.read()
                self.origin_cfg=json.loads(txt)
        else:
            self.origin_cfg=config_template
            with open('./sync.json','w',encoding='utf-8') as fp:
                json.dump(self.origin_cfg,fp)

        if os.path.exists('./important_config.yaml'):
            with open('././important_config.yaml','r',encoding='utf-8') as fp:
                self.global_config=yaml.safe_load(fp)
        else:
            self.global_config=global_config
            with open('././important_config.yaml','w',encoding='utf-8') as fp:
                yaml.dump(self.global_config,fp)

        if os.path.exists('./config.yaml'):
            with open('./config.yaml','r',encoding='utf-8') as fp:
                self.yaml_cfg=yaml.safe_load(fp)
        else:
            self.yaml_cfg=yaml_config
            with open('./config.yaml','w',encoding='utf-8') as fp:
                yaml.dump(self.yaml_cfg,fp)

        self.allowAllUser=self.global_config['allowAllUser']
        self.cacheAll=self.global_config['cacheAll']
        self.cacheDir=self.global_config['cacheDir']
        self.enableUserName=self.global_config['enableUserName']
        self.defaultDeviceName=self.global_config['defaultDeviceName']
        self.defaultPort=self.global_config['defaultPort']
        self.local_ip=get_local_ips()
        for user in self.yaml_cfg.keys():
            self.origin_cfg[user]['username']=self.yaml_cfg[user]['username']
            self.origin_cfg[user]['devicename']=self.yaml_cfg[user]['devicename']

            self.yaml_cfg[user]['localipv4']=list(map(lambda x:[x,self.defaultPort],list(filter(lambda x:not x.startswith('127.'),self.local_ip['ipv4']))))
            self.yaml_cfg[user]['localipv6']=list(map(lambda x:[x,self.defaultPort],list(filter(lambda x:(x!='::1') and (not x.startswith('fe80')),self.local_ip['ipv6']))))

            self.origin_cfg[user]['ipv4'][self.origin_cfg[user]['devicename']]=self.yaml_cfg[user]['localipv4']
            self.origin_cfg[user]['ipv6'][self.origin_cfg[user]['devicename']]=self.yaml_cfg[user]['localipv6']

            self.username= self.origin_cfg[user]['username']
            self.devicename=self.origin_cfg[user]['devicename']
            if self.yaml_cfg[user]['filemap'] is None:
                self.yaml_cfg[user]['filemap']=[]
            for f in self.yaml_cfg[user]['filemap']:
                if f['name'] in self.origin_cfg[user]['filemap'].keys():
                    self.origin_cfg[user]['filemap'][f['name']]['path'][self.devicename]=f['path']
                    self.origin_cfg[user]['filemap'][f['name']]['mode']=f['mode']
                    # self.origin_cfg[user]['filemap'][f['name']]['mtime']
                else:
                    self.origin_cfg[user]['filemap'][f['name']]={
                        'path':{
                            self.devicename:f['path']
                        },
                        'mode':f['mode'],
                        'mtime':{}
                    }
            for f_key in self.origin_cfg[user]['filemap'].keys():
                if f_key not in list(map(lambda x:x['name'],self.yaml_cfg[user]['filemap'])):
                    if self.origin_cfg[user]['devicename'] in self.origin_cfg[user]['filemap'][f_key]['path'].keys():
                        del self.origin_cfg[user]['filemap'][f_key]['path'][self.origin_cfg[user]['devicename']]
                    if self.origin_cfg[user]['devicename'] in self.origin_cfg[user]['filemap'][f_key]['mtime'].keys():
                        del self.origin_cfg[user]['filemap'][f_key]['mtime'][self.origin_cfg[user]['devicename']]
        with open('./sync.json','w',encoding='utf-8') as fp:
            json.dump(self.origin_cfg,fp)

    

    def send(self,username=None):
        for user in self.origin_cfg.keys():
            for f_key in self.origin_cfg[user]['filemap'].keys():
                if self.origin_cfg[user]['devicename'] in self.origin_cfg[user]['filemap'][f_key]['path'].keys():
                    if len(os.listdir(self.origin_cfg[user]['filemap'][f_key]['path'][self.origin_cfg[user]['devicename']]))==0:
                        self.origin_cfg[user]['filemap'][f_key]['mtime'][self.origin_cfg[user]['devicename']]=get_folder_modification_time(self.origin_cfg[user]['filemap'][f_key]\
                                                        ['path'][self.origin_cfg[user]['devicename']],oldest=True)
                    else:
                        self.origin_cfg[user]['filemap'][f_key]['mtime'][self.origin_cfg[user]['devicename']]=\
                            get_folder_modification_time(self.origin_cfg[user]['filemap'][f_key]\
                                                            ['path'][self.origin_cfg[user]['devicename']])

        if username is None:
            return json.dumps({'username':self.enableUserName,'data':self.origin_cfg})
        else:
            return json.dumps({'username':username,'data':self.origin_cfg})

        
    def merge(self,recv_data):
        for user in self.origin_cfg.keys():
            for f_key in self.origin_cfg[user]['filemap'].keys():
                if self.origin_cfg[user]['devicename'] in self.origin_cfg[user]['filemap'][f_key]['path'].keys():
                    if len(os.listdir(self.origin_cfg[user]['filemap'][f_key]['path'][self.origin_cfg[user]['devicename']]))==0:
                        self.origin_cfg[user]['filemap'][f_key]['mtime'][self.origin_cfg[user]['devicename']]=get_folder_modification_time(self.origin_cfg[user]['filemap'][f_key]\
                                                        ['path'][self.origin_cfg[user]['devicename']],oldest=True)
                    else:
                        self.origin_cfg[user]['filemap'][f_key]['mtime'][self.origin_cfg[user]['devicename']]=\
                            get_folder_modification_time(self.origin_cfg[user]['filemap'][f_key]\
                                                            ['path'][self.origin_cfg[user]['devicename']])


        recv_cfg=json.loads(recv_data)
        others_config=recv_cfg['data']
        recv_name=recv_cfg['username']
        if not self.allowAllUser:
            return False
        else:
            self.enableUserName=recv_name

        for k in others_config.keys():
            if k not in self.origin_cfg.keys():
                if not self.allowAllUser:
                    return False
                self.origin_cfg[k]={
                    'username':k,
                    'devicename':self.global_config['defaultDeviceName'],
                    'ipv4':{
                        self.global_config['defaultDeviceName']:list(filter(lambda x:not x.startswith(127.),self.local_ip['ipv4'])),
                    },
                    'ipv6':{
                        self.global_config['defaultDeviceName']:list(filter(lambda x:x!='::1',self.local_ip['ipv6']))
                    },
                    'filemap':{},
                }
            if others_config[k]['devicename']==self.origin_cfg[k]['devicename']:
                print("devicename conflict")
                return False
            self.origin_cfg[k]['ipv4'][others_config[k]['devicename']]=others_config[k]['ipv4'][others_config[k]['devicename']]
            self.origin_cfg[k]['ipv6'][others_config[k]['devicename']]=others_config[k]['ipv6'][others_config[k]['devicename']]
            for f_key in others_config[k]['filemap'].keys():
                if f_key not in self.origin_cfg[k]['filemap'].keys():
                    self.origin_cfg[k]['filemap'][f_key]=others_config[k]['filemap'][f_key]
                    # self.origin_cfg[k]['filemap'][f_key]['mtime'][others_config[k]['devicename']]=others_config[k]['filemap'][f_key]['mtime'][others_config[k]['devicename']]
                    if self.global_config['cacheAll']:
                        os.makedirs(os.path.join(os.path.normpath(self.global_config['cacheDir']),k,f_key),exist_ok=True)
                        self.origin_cfg[k]['filemap'][f_key]['path'][self.origin_cfg[k]['devicename']]=os.path.join(os.path.normpath(self.global_config['cacheDir']),k,f_key)
                        self.origin_cfg[k]['filemap'][f_key]['mtime'][self.origin_cfg[k]['devicename']]=datetime.datetime.now().isoformat()
                    else:
                        if self.origin_cfg[k]['devicename'] in self.origin_cfg[k]['filemap'][f_key]['path'].keys():
                            del self.origin_cfg[k]['filemap'][f_key]['path'][self.origin_cfg[k]['devicename']]
                        if self.origin_cfg[k]['devicename'] in self.origin_cfg[k]['filemap'][f_key]['mtime'].keys():
                            del self.origin_cfg[k]['filemap'][f_key]['mtime'][self.origin_cfg[k]['devicename']]  


                else:
                    self.origin_cfg[k]['filemap'][f_key]['path'][others_config[k]['devicename']]=others_config[k]['filemap'][f_key]['path'][others_config[k]['devicename']]
                    self.origin_cfg[k]['filemap'][f_key]['mtime'][others_config[k]['devicename']]=others_config[k]['filemap'][f_key]['mtime'][others_config[k]['devicename']]
            for f_key in self.origin_cfg[k]['filemap'].keys():
                if f_key in others_config[k]['filemap'].keys():
                    continue
                if others_config[k]['devicename'] in self.origin_cfg[k]['filemap'][f_key]['path'].keys():
                    del self.origin_cfg[k]['filemap'][f_key]['path'][others_config[k]['devicename']]
                if others_config[k]['devicename'] in self.origin_cfg[k]['filemap'][f_key]['mtime'].keys():
                    del self.origin_cfg[k]['filemap'][f_key]['mtime'][others_config[k]['devicename']]
        self.remote_devicename=others_config[self.enableUserName]['devicename']
        self.local_devicename=self.origin_cfg[self.enableUserName]['devicename']
        self.genDataCfg()
    
    def genDataCfg(self): # list file need trans
        with open('./sync.json','w',encoding='utf-8') as fp:
            json.dump(self.origin_cfg,fp)
        self.datacfg={}
        filemap=self.origin_cfg[self.enableUserName]['filemap']
        for key in filemap.keys():
            if self.local_devicename not in filemap[key]['path'].keys() or self.remote_devicename not in filemap[key]['path'].keys():
                continue
            if datetime.datetime.fromisoformat(filemap[key]['mtime'][self.local_devicename])>=datetime.datetime.fromisoformat(filemap[key]['mtime'][self.remote_devicename]):
                self.datacfg[key]='send'
            else:
                self.datacfg[key]='recv'
        # print(filemap,self.datacfg)
    
    def genData(self,):
        bzipfile=io.BytesIO()
        self.zipf=zipfile.ZipFile(bzipfile,'w',zipfile.ZIP_DEFLATED)

        filemap=self.origin_cfg[self.enableUserName]['filemap']
        fin_flag=1
        for key in self.datacfg.keys():
            if self.datacfg[key]=='send':
                for root,dirs,files in os.walk(filemap[key]['path'][self.local_devicename]):
                    for file in files:
                        self.zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), filemap[key]['path'][self.local_devicename]))
                self.datacfg[key]='send_fin'
                fin_flag=0
                break
            else:
                continue
        self.zipf.close()
        bzipfile.seek(0)
        if fin_flag:
            return False
        return key,bzipfile
    
    def extractData(self,name,iobyte):
        logging.debug(f'extract {name}')
        zipf=zipfile.ZipFile(io.BytesIO(iobyte),'r',)
        path=self.origin_cfg[self.enableUserName]['filemap'][name]['path'][self.local_devicename]
        shutil.rmtree(path)
        os.makedirs(path,exist_ok=True)
        zipf.extractall(path,)
        zipf.close()
        self.datacfg[name]='recv_fin'

    def genAvailableIp(self):
        defaultipv4=self.yaml_cfg[self.enableUserName]['remoteipv4']
        defaultipv6=self.yaml_cfg[self.enableUserName]['remoteipv6']
        v4=[]
        v6=[]
        for key in self.origin_cfg[self.enableUserName]['ipv4'].keys():
            if key==self.origin_cfg[self.enableUserName]['devicename']:
                continue
            for ipaddr in defaultipv4:
                if ipaddr in self.origin_cfg[self.enableUserName]['ipv4'][key]:
                    defaultipv4.pop(defaultipv4.index(ipaddr))
            for ipaddr in defaultipv6:
                if ipaddr in self.origin_cfg[self.enableUserName]['ipv6'][key]:
                    defaultipv6.pop(defaultipv6.index(ipaddr))
            v4.append(self.origin_cfg[self.enableUserName]['ipv4'][key])
            v6.append(self.origin_cfg[self.enableUserName]['ipv6'][key])
        print([defaultipv4,defaultipv6,v4,v6])
        return [defaultipv4,defaultipv6,v4,v6] #[[ip1,ip2,...],[ip1,ip2,...],...]
        
        

CONFIG=Config()

# class SyncCtl:
#     def __init__(self) -> None:
#         pass

#     def stage1_config_exchange(self):



