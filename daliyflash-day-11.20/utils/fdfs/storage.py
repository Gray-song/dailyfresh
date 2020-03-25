from django.core.files.storage import Storage
from django.conf import settings
from fdfs_client.client import Fdfs_client

class FDFSStorage(Storage):
    '''自定义文件存储类'''

    def __init__(self, client_conf=None, base_url=None):
        '''初始化'''
        if client_conf is None:
            client_conf = settings.FDFS_CLIENT_CONF
        self.client_conf = client_conf

        if base_url is None:
            base_url = settings.FDFS_URL
        self.base_url = base_url
    def _open(self,name,mode='rb'):
        '''打开文件时使用'''
        pass

    def _save(self,name,content):
        '''保存文件时使用,把文件存在ＦＤＦＳ服务器中'''
        #要上传的文件名字
        #要上传文件内容的FILE对象
        #１、创建链接ｆｄｆｓ服务器的客户端连接对象
        client = Fdfs_client(self.client_conf)
        #２、按文件内容上传文件
        res = client.upload_by_buffer(content.read())
        if res.get('Status') != 'Upload successed.':
            # 上传失败
            raise Exception('上传文件到fast dfs失败')

            # 获取返回的文件ID
        filename = res.get('Remote file_id')

        return filename

    def exists(self, name):
        '''Django判断文件名是否可用'''
        return False

    def url(self,name):
        '''返回文件的访问路径'''
        return self.base_url+name
