# -*- coding: utf-8 -*-
"""
截图FTP上传工具 - 南安专用版
银河麒麟v10系统兼容版
"""
import sys
import os
import time
import threading
import warnings
from datetime import datetime
from ftplib import FTP, error_perm
import pyperclip
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                           QWidget, QLabel, QSystemTrayIcon, QMenu, QAction, 
                           QMessageBox, QTextEdit, QHBoxLayout, QSplitter,
                           QStyle)
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QSize, QThread
from PyQt5.QtGui import QIcon, QTextCursor, QPixmap
from pynput import keyboard
from PIL import ImageGrab, Image
import io

# 忽略警告
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Linux 系统兼容性处理
IS_LINUX = sys.platform.startswith('linux')

class Logger(QObject):
    log_signal = pyqtSignal(str, str)  # 消息, 级别
    
    def __init__(self):
        super().__init__()
    
    def info(self, message):
        self.log_signal.emit(message, "info")
    
    def error(self, message):
        self.log_signal.emit(message, "error")
    
    def success(self, message):
        self.log_signal.emit(message, "success")
    
    def warning(self, message):
        self.log_signal.emit(message, "warning")

# 中文路径编码尝试函数
def get_encoded_paths(original_path):
    """生成不同编码的路径尝试列表"""
    paths = []
    
    # 原始路径
    paths.append(original_path)
    
    # GBK编码版本
    try:
        gbk_path = original_path.encode('gbk').decode('latin1')
        paths.append(gbk_path)
    except:
        pass
    
    # UTF-8编码版本
    try:
        utf8_path = original_path.encode('utf-8').decode('latin1')
        paths.append(utf8_path)
    except:
        pass
    
    # CP936编码版本
    try:
        cp936_path = original_path.encode('cp936').decode('latin1')
        paths.append(cp936_path)
    except:
        pass
    
    # GB18030编码版本
    try:
        gb18030_path = original_path.encode('gb18030').decode('latin1')
        paths.append(gb18030_path)
    except:
        pass
    
    # 试验特殊编码
    special_encodings = [
        "/nanAn/",
        "/NanAn/",
        "/NANAN/",
        "/nan_an/",
        "/%C4%CF%B0%B2/",  # URL编码
        "/南安/",
        "/南安",
        "南安/",
        "南安",
        "/",
    ]
    
    paths.extend(special_encodings)
    
    # 去重
    unique_paths = []
    for path in paths:
        if path not in unique_paths:
            unique_paths.append(path)
    
    return unique_paths

class FTPTestThread(QThread):
    # 创建信号用于通知主线程测试结果
    finished = pyqtSignal(bool, str)
    log_signal = pyqtSignal(str, str)
    
    def __init__(self, host, user, password, path_candidates):
        super().__init__()
        self.host = host
        self.user = user
        self.password = password
        self.path_candidates = path_candidates
        self.working_directory = None
    
    def run(self):
        """线程运行的主函数，执行FTP连接测试"""
        self.log_signal.emit(f"开始测试FTP连接: {self.host}", "info")
        try:
            # 连接FTP服务器
            ftp = FTP(self.host)
            ftp.encoding = 'gbk'  # 设置FTP服务器编码为GBK
            self.log_signal.emit(f"尝试登录FTP: 用户名={self.user}", "info")
            ftp.login(user=self.user, passwd=self.password)
            self.log_signal.emit("FTP登录成功", "success")
            
            # 列出根目录内容，帮助调试
            self.log_signal.emit("列出根目录内容:", "info")
            try:
                root_dirs = ftp.nlst()
                for item in root_dirs:
                    self.log_signal.emit(f"  - {item}", "info")
            except Exception as e:
                self.log_signal.emit(f"无法列出根目录内容: {str(e)}", "warning")
            
            # 尝试所有候选路径
            success = False
            for path in self.path_candidates:
                try:
                    self.log_signal.emit(f"尝试切换到目录: {path}", "info")
                    ftp.cwd(path)
                    self.log_signal.emit(f"成功访问目录: {path}", "success")
                    
                    # 列出当前目录内容
                    try:
                        dir_list = ftp.nlst()
                        self.log_signal.emit("当前目录内容:", "info")
                        if dir_list:
                            for item in dir_list:
                                self.log_signal.emit(f"  - {item}", "info")
                        else:
                            self.log_signal.emit("  (目录为空)", "info")
                    except Exception as e:
                        self.log_signal.emit(f"无法列出目录内容: {str(e)}", "warning")
                    
                    # 测试上传权限
                    test_data = io.BytesIO(b"FTP connection test")
                    test_filename = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                    
                    try:
                        self.log_signal.emit(f"尝试上传测试文件: {test_filename}", "info")
                        ftp.storbinary(f'STOR {test_filename}', test_data)
                        self.log_signal.emit("测试文件上传成功", "success")
                        
                        # 记住成功的路径
                        self.working_directory = path
                        success = True
                        
                        # 尝试删除测试文件
                        try:
                            ftp.delete(test_filename)
                            self.log_signal.emit("测试文件已删除", "info")
                        except:
                            self.log_signal.emit("无法删除测试文件，但这可能是正常的", "warning")
                        
                        break  # 成功找到可用路径，退出循环
                    except error_perm as e:
                        self.log_signal.emit(f"在目录 {path} 中无法上传文件: {str(e)}", "error")
                        # 继续尝试下一个路径
                except error_perm as e:
                    self.log_signal.emit(f"无法访问目录 {path}: {str(e)}", "error")
                    # 继续尝试下一个路径
            
            ftp.quit()
            
            if success:
                self.log_signal.emit(f"已找到可上传的目录: {self.working_directory}", "success")
                self.finished.emit(True, f"FTP连接测试成功！可以上传文件到目录: {self.working_directory}")
            else:
                self.log_signal.emit("未找到可上传的目录，请检查账户权限", "error")
                self.finished.emit(False, "未找到可上传的目录，请检查账户权限")
                
        except Exception as e:
            self.log_signal.emit(f"FTP连接测试失败: {str(e)}", "error")
            self.finished.emit(False, f"FTP连接测试失败: {str(e)}")

class FTPUploader:
    def __init__(self, host, user, password, logger):
        self.host = host
        self.user = user
        self.password = password
        self.logger = logger
        self.working_directory = None  # 将在连接测试时设置
        
        # 获取所有可能的编码路径
        self.path_candidates = get_encoded_paths("/南安/")
    
    def test_connection(self):
        """创建并返回测试线程，不阻塞主线程"""
        self.test_thread = FTPTestThread(self.host, self.user, self.password, self.path_candidates)
        
        # 连接日志信号
        self.test_thread.log_signal.connect(self.logger.log_signal.emit)
        
        return self.test_thread
        
    def upload_image(self, image_data, filename):
        """上传图像到FTP服务器"""
        if not self.working_directory:
            self.logger.error("未设置有效的工作目录，无法上传文件")
            return False
            
        try:
            self.logger.info(f"开始上传图片: {filename}")
            ftp = FTP(self.host)
            ftp.encoding = 'gbk'  # 设置FTP服务器编码为GBK
            self.logger.info(f"正在连接FTP服务器: {self.host}")
            ftp.login(user=self.user, passwd=self.password)
            self.logger.info("FTP登录成功")
            
            # 切换到目标目录
            self.logger.info(f"切换到目录: {self.working_directory}")
            ftp.cwd(self.working_directory)
            
            # 上传文件
            self.logger.info(f"开始上传文件: {filename}")
            ftp.storbinary(f'STOR {filename}', image_data)
            self.logger.success(f"文件上传成功: {filename}")
            
            ftp.quit()
            return True
        except Exception as e:
            self.logger.error(f"FTP上传错误: {e}")
            return False

class KeyboardListener(QObject):
    screenshot_taken = pyqtSignal()
    
    def __init__(self, logger):
        super().__init__()
        self.running = False
        self.listener = None
        self.logger = logger
    
    def start_listening(self):
        if not self.running:
            self.running = True
            self.logger.info("开始监听Print Screen键")
            self.listener = keyboard.Listener(on_press=self.on_press)
            self.listener.start()
    
    def stop_listening(self):
        if self.running and self.listener:
            self.running = False
            self.logger.info("停止监听Print Screen键")
            self.listener.stop()
            self.listener = None
    
    def on_press(self, key):
        if hasattr(key, 'name') and key.name == 'print_screen':
            self.logger.info("检测到Print Screen键被按下")
            self.screenshot_taken.emit()

# Linux系统截图处理
def linux_grab_clipboard_image():
    """在Linux系统下从剪贴板获取图像"""
    try:
        # 尝试使用PyQt5获取剪贴板图像
        clipboard = QApplication.clipboard()
        mimeData = clipboard.mimeData()
        
        if mimeData.hasImage():
            qimage = clipboard.image()
            buffer = QPixmap.fromImage(qimage).toImage()
            
            # 创建一个QPixmap并将缓冲区绘制到其上
            pixmap = QPixmap.fromImage(buffer)
            
            # 转换为PIL图像
            image_buffer = io.BytesIO()
            pixmap.save(image_buffer, "PNG")
            image_buffer.seek(0)
            
            return Image.open(image_buffer)
        else:
            return None
    except Exception as e:
        print(f"Linux剪贴板获取错误: {e}")
        return None

class ScreenshotManager:
    def __init__(self, ftp_uploader, logger):
        self.ftp_uploader = ftp_uploader
        self.logger = logger
    
    def capture_and_upload(self):
        try:
            # 等待系统完成截图并复制到剪贴板
            self.logger.info("等待系统完成截图 (0.5秒)")
            time.sleep(0.5)
            
            # 从剪贴板获取图像
            self.logger.info("尝试从剪贴板获取图像")
            
            # 针对不同操作系统使用不同的截图方法
            if IS_LINUX:
                image = linux_grab_clipboard_image()
            else:
                image = ImageGrab.grabclipboard()
            
            if image:
                if isinstance(image, Image.Image):
                    # 获取图像尺寸
                    width, height = image.size
                    self.logger.info(f"成功获取截图，尺寸: {width}x{height}")
                    
                    # 生成文件名
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"screenshot_{timestamp}.png"
                    
                    # 转换图像为字节流
                    self.logger.info("准备图像数据用于上传")
                    img_byte_arr = io.BytesIO()
                    image.save(img_byte_arr, format='PNG')
                    img_byte_arr.seek(0)
                    
                    # 上传到FTP
                    self.logger.info("开始上传图像到FTP")
                    success = self.ftp_uploader.upload_image(img_byte_arr, filename)
                    if success:
                        self.logger.success(f"截图上传成功: {filename}")
                    return success, filename
                else:
                    self.logger.error(f"剪贴板中的内容不是图像，而是: {type(image)}")
                    return False, "剪贴板中的内容不是图像"
            else:
                self.logger.error("剪贴板中没有图像")
                return False, "剪贴板中没有图像"
        except Exception as e:
            self.logger.error(f"截图处理错误: {e}")
            return False, str(e)

class LogWidget(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setLineWrapMode(QTextEdit.WidgetWidth)
        self.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                color: #333333;
                font-family: Monospace;
                font-size: 9pt;
                border: 1px solid #cccccc;
            }
        """)
    
    def append_log(self, message, level="info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if level == "error":
            html = f'<p style="margin:0;"><span style="color:#888888;">[{timestamp}]</span> <span style="color:#ff0000;font-weight:bold;">[错误]</span> {message}</p>'
        elif level == "warning":
            html = f'<p style="margin:0;"><span style="color:#888888;">[{timestamp}]</span> <span style="color:#ff9900;">[警告]</span> {message}</p>'
        elif level == "success":
            html = f'<p style="margin:0;"><span style="color:#888888;">[{timestamp}]</span> <span style="color:#009900;">[成功]</span> {message}</p>'
        else:  # info
            html = f'<p style="margin:0;"><span style="color:#888888;">[{timestamp}]</span> <span style="color:#0066cc;">[信息]</span> {message}</p>'
        
        self.append(html)
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.setTextCursor(cursor)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 创建日志组件
        self.logger = Logger()
        
        # FTP配置
        self.ftp_host = "44.112.2.110"
        self.ftp_user = "msk350500"
        self.ftp_password = "qzxz@334"
        
        # 初始化组件
        self.ftp_uploader = FTPUploader(self.ftp_host, self.ftp_user, self.ftp_password, self.logger)
        self.screenshot_manager = ScreenshotManager(self.ftp_uploader, self.logger)
        self.keyboard_listener = KeyboardListener(self.logger)
        self.keyboard_listener.screenshot_taken.connect(self.on_screenshot)
        
        # 设置UI
        self.setWindowTitle("截图FTP上传工具 - 南安专用版")
        self.setGeometry(300, 300, 600, 500)
        
        # 创建分割器
        splitter = QSplitter(Qt.Vertical)
        self.setCentralWidget(splitter)
        
        # 上半部分控制面板
        control_widget = QWidget()
        control_layout = QVBoxLayout(control_widget)
        
        # 添加标签
        info_label = QLabel("按下Print Screen键自动上传截图到FTP服务器")
        info_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        control_layout.addWidget(info_label)
        
        # FTP配置信息标签
        self.ftp_info_label = QLabel(f"FTP服务器: {self.ftp_host}\n目录: /南安/ (将自动查找正确编码的路径)")
        control_layout.addWidget(self.ftp_info_label)
        
        # 状态标签
        self.status_label = QLabel("状态: 未运行")
        self.status_label.setStyleSheet("font-weight: bold;")
        control_layout.addWidget(self.status_label)
        
        # 按钮区域 - 使用水平布局
        button_layout = QHBoxLayout()
        
        # 添加测试连接按钮
        self.test_button = QPushButton("测试FTP连接")
        self.test_button.setMinimumHeight(30)
        self.test_button.clicked.connect(self.test_ftp_connection)
        button_layout.addWidget(self.test_button)
        
        # 添加开始按钮
        self.start_button = QPushButton("开始监听")
        self.start_button.setMinimumHeight(30)
        self.start_button.clicked.connect(self.start_monitoring)
        button_layout.addWidget(self.start_button)
        
        # 添加停止按钮
        self.stop_button = QPushButton("停止监听")
        self.stop_button.setMinimumHeight(30)
        self.stop_button.clicked.connect(self.stop_monitoring)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        # 添加清除日志按钮
        self.clear_log_button = QPushButton("清除日志")
        self.clear_log_button.setMinimumHeight(30)
        self.clear_log_button.clicked.connect(self.clear_log)
        button_layout.addWidget(self.clear_log_button)
        
        control_layout.addLayout(button_layout)
        
        # 下半部分日志窗口
        self.log_widget = LogWidget()
        self.logger.log_signal.connect(self.log_widget.append_log)
        
        # 添加到分割器
        splitter.addWidget(control_widget)
        splitter.addWidget(self.log_widget)
        splitter.setSizes([150, 350])  # 设置初始大小比例
        
        # 创建系统托盘图标
        self.create_tray_icon()
        
        # 监听状态
        self.is_monitoring = False
        
        # 测试线程
        self.test_thread = None
        
        # 初始日志
        self.logger.info("程序已启动，针对\"/南安/\"目录的特殊版本")
        self.logger.info("运行于 " + ("Linux系统" if IS_LINUX else "Windows系统"))
        self.logger.info("请点击\"测试FTP连接\"按钮测试连接")
    
    def update_directory_info(self):
        """更新目录信息显示"""
        if self.ftp_uploader.working_directory:
            self.ftp_info_label.setText(f"FTP服务器: {self.ftp_host}\n目录: {self.ftp_uploader.working_directory} (已验证可上传)")
        
    def clear_log(self):
        """清除日志窗口内容"""
        self.log_widget.clear()
        self.logger.info("日志已清除")
    
    def test_ftp_connection(self):
        """测试FTP连接，使用线程避免UI阻塞"""
        self.test_button.setEnabled(False)
        self.test_button.setText("正在测试连接...")
        
        # 获取测试线程
        self.test_thread = self.ftp_uploader.test_connection()
        
        # 连接线程完成信号
        def on_test_finished(success, message):
            """当测试线程完成时处理结果"""
            # 更新UI状态
            self.test_button.setText("测试FTP连接")
            self.test_button.setEnabled(True)
            
            # 显示结果
            if success:
                QMessageBox.information(self, "连接测试", message)
                # 更新FTP上传器的工作目录
                self.ftp_uploader.working_directory = self.test_thread.working_directory
                self.update_directory_info()
            else:
                QMessageBox.critical(self, "连接测试", message)
            
            # 清理线程
            self.test_thread.quit()
            self.test_thread.wait()
        
        # 连接信号
        self.test_thread.finished.connect(on_test_finished)
        
        # 启动线程
        self.test_thread.start()
    
    def create_tray_icon(self):
        # 创建托盘图标菜单
        tray_menu = QMenu()
        show_action = QAction("显示", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.close_application)
        tray_menu.addAction(quit_action)
        
        # 创建托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip("截图FTP上传工具")
        self.tray_icon.setContextMenu(tray_menu)
        
        # 设置图标并显示
        if IS_LINUX:
            # 在Linux上使用QIcon.fromTheme
            icon = QIcon.fromTheme("accessories-screenshot", QIcon.fromTheme("image"))
            if icon.isNull():
                icon = self.style().standardIcon(QStyle.SP_ComputerIcon)
        else:
            # 在Windows上使用标准图标
            icon = self.style().standardIcon(QStyle.SP_MessageBoxInformation)
            
        self.tray_icon.setIcon(icon)
        self.tray_icon.show()
    
    def start_monitoring(self):
        # 检查是否已找到工作目录
        if not self.ftp_uploader.working_directory:
            self.logger.warning("尚未找到可用的工作目录，请先测试FTP连接")
            QMessageBox.warning(self, "缺少工作目录", "请先点击\"测试FTP连接\"按钮，确认可用的上传目录。")
            return
        
        self.logger.info("开始监听Print Screen键")
        self.keyboard_listener.start_listening()
        self.is_monitoring = True
        self.status_label.setText("状态: 正在监听Print Screen键")
        self.status_label.setStyleSheet("font-weight: bold; color: green;")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.test_button.setEnabled(False)
        
        # 最小化到托盘
        self.hide()
        self.tray_icon.showMessage("截图上传工具", "程序正在后台运行，按Print Screen键上传截图", QSystemTrayIcon.Information, 2000)
    
    def stop_monitoring(self):
        self.logger.info("停止监听Print Screen键")
        self.keyboard_listener.stop_listening()
        self.is_monitoring = False
        self.status_label.setText("状态: 未运行")
        self.status_label.setStyleSheet("font-weight: bold;")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.test_button.setEnabled(True)
    
    def on_screenshot(self):
        self.logger.info("检测到截图，准备处理...")
        success, filename = self.screenshot_manager.capture_and_upload()
        if success:
            self.logger.success(f"截图已成功上传: {filename}")
            self.tray_icon.showMessage("截图已上传", f"截图已成功上传到FTP: {filename}", QSystemTrayIcon.Information, 2000)
        else:
            self.logger.error(f"截图上传失败: {filename}")
            self.tray_icon.showMessage("上传失败", f"截图上传失败: {filename}", QSystemTrayIcon.Warning, 2000)
    
    def closeEvent(self, event):
        # 拦截关闭事件，最小化到托盘而不是关闭
        if self.is_monitoring:
            event.ignore()
            self.hide()
            self.tray_icon.showMessage("截图上传工具", "程序已最小化到系统托盘", QSystemTrayIcon.Information, 2000)
        else:
            event.accept()
    
    def close_application(self):
        # 实际关闭应用程序
        self.logger.info("正在关闭程序...")
        self.stop_monitoring()
        
        # 停止并等待任何正在运行的线程
        if self.test_thread and self.test_thread.isRunning():
            self.test_thread.quit()
            self.test_thread.wait()
            
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_()) 