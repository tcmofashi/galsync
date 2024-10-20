# -*- coding: UTF8 -*-
import os
import json
import timeutils
import yaml
import socket
import datetime
import psutil
import zipfile
import io

def get_local_ips():
    """获取本机的所有 IPv4 和 IPv6 地址"""
    local_ips = {
        'ipv4': [],
        'ipv6': []
    }

    # 获取主机名
    hostname = socket.gethostname()

    # 获取主机名对应的地址信息
    addr_info = socket.getaddrinfo(hostname, None)

    for info in addr_info:
        family, _, _, _, sockaddr = info
        ip = sockaddr[0]

        if family == socket.AF_INET:  # IPv4
            local_ips['ipv4'].append(ip)
        elif family == socket.AF_INET6:  # IPv6
            local_ips['ipv6'].append(ip)

    return local_ips





config_template={
    'tcmofashi':{
    'username':'tcmofashi',
    'devicename':'pc1',
    'ipv4':{
        'pc1':['10.42.0.32'],
        # 'server':['10.42.0.1'] #save for test
    },
    'ipv6':{
        'pc1':['fe80::f1d8:7788:e710:f6d5'],
        # 'server':['2001:da8:b801:285e:78b6:2427:99e7:56ec'],
    },
    'filemap':{
            'ATRI':{
         'path':{
         'pc1':r"E:\wode2\ATRI -My Dear Moments-",
         'server':r'/mnt/E/ATRI -My Dear Moments-', # get from remote
         },
         'mtime':None,
         'mode':'newest' # mode:'devicename' or 'newest',empty path won't be origin
         }
    }
    }
}

yaml_config={
    'tcmofashi':{
    'username':'tcmofashi',
    'devicename':'pc1',
    'allowAllUser':True,
    'localipv4':['10.42.0.32'],
    'localipv6':[],
    'localport':60721,
    'remoteipv4':['10.42.0.1:60721'], # for default
    'remoteipv6':[],
    'filemap':[
        {
            'name':'ATRI',
            'path':r"E:\wode2\ATRI -My Dear Moments-",
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
    'defaultDeviceName':'pc1'
}

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
                self.global_config=yaml.load(fp)
        else:
            self.global_config=global_config
            with open('././important_config.yaml','w',encoding='utf-8') as fp:
                yaml.dump(self.global_config,fp)

        if os.path.exists('./config.yaml'):
            with open('./config.yaml','r',encoding='utf-8') as fp:
                self.yaml_cfg=yaml.load(fp)
        else:
            self.yaml_cfg=yaml_config
            with open('./config.yaml','w',encoding='utf-8') as fp:
                yaml.dump(self.yaml_cfg,fp)

        self.allowAllUser=self.global_config['allowAllUser']
        self.cacheAll=self.global_config['cacheAll']
        self.cacheDir=self.global_config['cacheDir']
        self.enableUserName=self.global_config['enableUserName']
        self.local_ip=get_local_ips()
        for user in self.yaml_cfg.keys():
            self.origin_cfg[user]['username']=self.yaml_cfg[user]['username']
            self.origin_cfg[user]['devicename']=self.yaml_cfg[user]['devicename']

            self.yaml_cfg[user]['localipv4']=list(filter(lambda x:not x.startswith(127.),self.local_ip['ipv4']))
            self.yaml_cfg[user]['localipv6']=list(filter(lambda x:x!='::1',self.local_ip['ipv6']))
            self.origin_cfg[user]['ipv4'][self.origin_cfg[user]['devicename']]=self.yaml_cfg[user]['localipv4']
            self.origin_cfg[user]['ipv6'][self.origin_cfg[user]['devicename']]=self.yaml_cfg[user]['localipv6']

            self.username= self.origin_cfg[user]['username']
            self.devicename=self.origin_cfg[user]['devicename']
            for f in self.yaml_cfg[user]['filemap']:
                if f['name'] in self.origin_cfg[user]['filemap'].keys():
                    self.origin_cfg[user]['filemap'][f['name']]['path'][self.devicename]=f['path']
                    self.origin_cfg[user]['filemap'][f['name']]['mode']=f['mode']
                else:
                    self.origin_cfg[user]['filemap'][f['name']]={
                        'path':{
                            self.username:f['path']
                        },
                        'mode':f['mode']
                    }
    

    def send(self,username=None):
        for user in self.origin_cfg.keys():
            for f_key in self.origin_cfg[user]['filemap'].keys():
                self.origin_cfg[user]['filemap'][f_key]['mtime'][self.origin_cfg[user]['devicename']]=timeutils.get_folder_modification_time(self.origin_cfg[user]['filemap'][f_key]['path'][self.origin_cfg[user]['devicename']])

        if username is None:
            return json.dumps({'username':self.enableUserName,'data':self.origin_cfg})
        else:
            return json.dumps({'username':username,'data':self.origin_cfg})

        
    def merge(self,recv_data):
        for user in self.origin_cfg.keys():
            for f_key in self.origin_cfg[user]['filemap'].keys():
                self.origin_cfg[user]['filemap'][f_key]['mtime'][self.origin_cfg[user]['devicename']]=timeutils.get_folder_modification_time(self.origin_cfg[user]['filemap'][f_key]['path'][self.origin_cfg[user]['devicename']])

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
                    self.origin_cfg[k]['filemap'][f_key]['mtime'][others_config[k]['devicename']]=others_config[k]['filemap'][f_key]['mtime'][others_config[k]['devicename']]

                    if self.global_config['cacheAll']:
                        self.origin_cfg[k]['filemap'][f_key]['path'][self.origin_cfg[k]['devicename']]=os.path.join(os.path.normpath(self.global_config['cacheDir']),f_key)
                        self.origin_cfg[k]['filemap'][f_key]['mtime'][self.origin_cfg[k]['devicename']]=datetime.datetime.now().isoformat()

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
        self.datacfg={}
        filemap=self.origin_cfg[self.enableUserName]['filemap']
        for key in filemap.keys():
            if self.local_devicename not in filemap['path'].keys() or self.remote_devicename not in filemap['path'].keys():
                continue
            if datetime.datetime.fromisoformat(filemap[key]['mtime'][self.local_devicename])<datetime.datetime.fromisoformat(filemap[key]['mtime'][self.remote_devicename]):
                self.datacfg[key]='send'
            else:
                self.datacfg[key]='recv'
    
    def genData(self,):
        self.bzipfile=io.BytesIO()
        self.zipf=zipfile.ZipFile(self.bzipfile,'w',zipfile.ZIP_DEFLATED)

        filemap=self.origin_cfg[self.enableUserName]['filemap']
        for key in self.datacfg.keys():
            if self.datacfg[key]=='send':
                for root,dirs,files in os.walk(filemap[key]['path'][self.local_devicename]):
                    for file in files:
                        self.zipf.write(os.path.join(root, file), os.path.join(key,os.path.relpath(os.path.join(root, file), filemap[key]['path'][self.local_devicename])))
                self.datacfg[key]=='send_fin'
                break
            else:
                continue
        self.zipf.close()
        return self.bzipfile
        

class SyncCtl:


