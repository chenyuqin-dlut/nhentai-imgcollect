import requests
import os
import re
from threading import Thread
from queue import Queue
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QThread ,  pyqtSignal
import sys
from qt.layout import Ui_MainWindow as UIM

class BackendThread(QThread):
    update_date = pyqtSignal(str)

    def __init__(self, http_url,thread_num):
        super(BackendThread, self).__init__()
        self.http_url = http_url
        self.thread_num = thread_num
        

    def run(self):
        self.download_queue = Queue()
        self.get_img(self.http_url,self.thread_num)
        
    def save_img(self,img_path):
        while not self.download_queue.empty():
                img_url = self.download_queue.get()
                img_url_list = re.findall(re.compile('/([0-9]*).jpg'), img_url)
                img_save_index = int(img_url_list[0])
                self.update_date.emit("第{}张图片开始下载".format(img_save_index))
                try:
                    img_content = requests.get(img_url)
                    filename = '{}/{}.jpg'.format(img_path,img_save_index)
                    with open(filename, 'wb') as f_img:
                        f_img.write(img_content.content)
                    self.update_date.emit(str("第{}张图片下载完成".format(img_save_index)))
                except Exception as e:
                    self.update_date.emit(f'请求出错,地址：{img_url} 错误：{e} ')

    def find_element(self,reg,strhtml):
        element_re = re.compile(reg)
        element_list = re.findall(element_re, strhtml)
        return element_list

    def createFile(self,filePath):
        if os.path.exists(filePath):
            self.update_date.emit('文件夹%s:存在'%filePath)
        else:
            try:
                os.mkdir(filePath)
                self.update_date.emit('新建文件夹：%s'%filePath)
            except Exception as e:
                os.makedirs(filePath)
                self.update_date.emit('新建多层文件夹：%s' % filePath)

    def get_base_data(self):
        gethtml = requests.get(self.http_url)  # Get方式获取网页数据
        self.num_list = self.find_element('<span class="num-pages">(.+?)</span>',gethtml.text)
        self.img_list = self.find_element('src="(.+?\.jpg)" width=',gethtml.text)
        for img_index in range(2,int(self.num_list[0]) + 1):
            self.img_list.append(self.img_list[0].replace('/1.','/' + str(img_index) + '.'))
        
        for url in self.img_list:
            self.update_date.emit(url)
            self.download_queue.put(url, block=False)
    
    # @excute_time_decorator
    def get_img(self,http_url,thread_num = 8):
        try:
            self.thread_num = thread_num
            self.save_dir = self.find_element('/([0-9]+)/',http_url)[0]
            self.http_url = http_url + '1/'
            img_path=os.getcwd() + '\\画册' + self.save_dir
            self.createFile(img_path)
            self.update_date.emit(f'正在对{http_url}进行爬取')
            self.update_date.emit("文件列表：")
            self.get_base_data()
            self.update_date.emit('开始下载')
            self.update_date.emit('--------------------------------------------------------------------------')
            threads = []

            for i in range(self.thread_num):
                t = Thread(target=self.save_img,args=(img_path,))
                t.setDaemon(True)
                t.start()
                threads.append(t)

            for t in threads:
                t.join()

            self.update_date.emit(str(f'下载完毕，文件保存在{img_path}'))
        except Exception as e:
            self.update_date.emit(f'错误信息：{e}')
            self.update_date.emit(f'发生错误，请检查输入的简介页URL是否完整、网络设置是否正确')
            self.update_date.emit(f'如果不知道什么是“简介页URL”和正确的网络设置，请点击“使用帮助”按钮进行查看')
        
class UIM_Version(UIM,QtWidgets.QWidget):
    send_args = pyqtSignal(str , int)

    def __init__(self):
        QtWidgets.QWidget.__init__(self)#因为继承关系，要对父类初始化
        
    def setupFunction(self):
        self.pushButton.clicked.connect(self.send)
        self.pushButton_2.clicked.connect(self.onButtonClick) 
        self.pushButton_3.clicked.connect(self.open_tip) 
        self.pushButton_4.clicked.connect(self.open_dir) 

    def onButtonClick(self ):  
        #此处发送信号的对象是button1按钮        
        qApp = QtWidgets.QApplication.instance()
        qApp.quit()

    def send(self):
        http_url = self.lineEdit.text()    # 获取第一个文本框中的内容
        thread_num = int(self.spinBox.text())   # 获取第二个框中的内容
        if http_url == '':
            self.msg("提示","请输入简介页url")
        else:
            self.backend = BackendThread(http_url,thread_num)
            self.backend.update_date.connect(self.handleDisplay)
            self.backend.start()
            self.send_args.emit(http_url,thread_num)

    def open_tip(self):
        QtWidgets.QMessageBox.about(None,"使用帮助",'<p style="color:red;">本软件是完全免费、开源的软件，仅用于交流学习，请勿用于商业用途</p> \
        <p>简介页URL：从首页点击封面所进入页面的浏览器地址栏值，完全复制过来即可</p> \
        <p>简介页URL形如：https://xxxxtai.net/g/297941/ </p> \
        <p>下载线程数：创建多个线程以同时下载，此值过大可能导致封IP，请谨慎使用</p> \
        <p>请在网络通畅的情况下使用，如果你使用的是ss代理，请将代理置于全局模式</p> \
        <p>如果对源码感兴趣,可以在GitHub上查看:</p> \
        <a href="https://github.com/chenyuqin-dlut/nhentai-imgcollect" rel="nofollow">GitHub项目地址</a>')
        
    def msg(self,title,msg):
        QtWidgets.QMessageBox.information(self, title, msg,QtWidgets.QMessageBox.Yes)

    def handleDisplay(self,data):
        self.textBrowser.append(data)   #在指定的区域显示提示信息
        self.cursor=self.textBrowser.textCursor()
        self.textBrowser.moveCursor(self.cursor.End)  #光标移到最后，这样就会自动显示出来
        QtWidgets.QApplication.processEvents()  #一定加上这个功能，不然有卡顿

    def open_dir(self):
        path = os.getcwd()
        os.system("explorer.exe %s" % path)

if __name__ == "__main__":
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = UIM_Version()
    ui.setupUi(MainWindow)
    ui.setupFunction()
    ui.handleDisplay("如果你不知道该如何使用本软件，请点击“使用说明”按钮查看帮助")
    MainWindow.show()
    sys.exit(app.exec_())

    


     

