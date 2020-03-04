import requests
import os, time
import re
from threading import Thread
from queue import Queue
from sys import argv

def excute_time_decorator(func):
    def excuteTime(*args):
        start = time.time()
        func(*args)
        end = time.time()
        cost = round(end - start)
        print(f'运行时间: {cost} 秒')
    return excuteTime

class GetHentaiImg():

    def __init__(self,http_url,thread_num):
        self.thread_num = thread_num
        self.save_dir = self.find_element('/([0-9]+)/',http_url)[0]
        self.http_url = http_url + '1/'
        self.download_queue = Queue()

    def get_base_data(self):
        gethtml = requests.get(self.http_url)  # Get方式获取网页数据
        
        self.num_list = self.find_element('<span class="num-pages">(.+?)</span>',gethtml.text)
        self.img_list = self.find_element('src="(.+?\.jpg)" width=',gethtml.text)
        for img_index in range(2,int(self.num_list[0]) + 1):
            self.img_list.append(self.img_list[0].replace('/1.','/' + str(img_index) + '.'))
        for url in self.img_list:
            print(url)
            self.download_queue.put(url, block=False)

    def find_element(self,reg,strhtml):
        element_re = re.compile(reg)
        element_list = re.findall(element_re, strhtml)
        print(element_list)
        return element_list

    def createFile(self,filePath):
        if os.path.exists(filePath):
            print('%s:存在'%filePath)
        else:
            try:
                os.mkdir(filePath)
                print('新建文件夹：%s'%filePath)
            except Exception as e:
                os.makedirs(filePath)
                print('新建多层文件夹：%s' % filePath)

    def save_img(self,img_path):
        while not self.download_queue.empty():
                img_url = self.download_queue.get()
                img_url_list = re.findall(re.compile('/([0-9]*).jpg'), img_url)
                img_save_index = int(img_url_list[0])
                print("第{}张图片开始下载".format(img_save_index))
                try:
                    img_content = requests.get(img_url)
                    filename = '{}/{}.jpg'.format(img_path,img_save_index)
                    with open(filename, 'wb') as f_img:
                        f_img.write(img_content.content)
                    print("第{}张图片下载完成".format(img_save_index))
                except Exception as e:
                    print(f'请求出错,地址：{img_url} 错误：{e} ')
                    time.sleep(0.5)

    @excute_time_decorator
    def start(self):
        img_path=os.getcwd() + '\\画册' + self.save_dir
        self.createFile(img_path)
        self.get_base_data()
        print('开始下载')
        print('--------------------------------------------------------------------------')
        threads = []

        for i in range(self.thread_num):
            t = Thread(target=self.save_img,args=(img_path,))
            t.setDaemon(True)
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        print('下载完毕')
        print(f'下载完毕，文件保存在{img_path}')
        input("按回车键退出")

if __name__ == '__main__':
    try:
        print(argv)   
        len(argv)
        crawler = GetHentaiImg(argv[1] , int(argv[2]) )
        crawler.start()
    except Exception as e:
        print(f'发生错误，错误信息：{e} ')
        print('请检查输入的简介页URL是否完整、准确')
        print('简介页URL：从首页点击封面所进入页面的浏览器地址栏值，完全复制过来即可')
        print('形如: https://xxxxtai.net/g/297941/')
        input("按回车键退出")



