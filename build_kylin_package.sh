#!/bin/bash

# 设置变量
APP_NAME="screenshot-ftp-uploader"
APP_VERSION="1.0.0"
APP_DESCRIPTION="截图FTP上传工具 - 南安专用版"
MAINTAINER="Admin <admin@example.com>"
ARCHITECTURE="amd64"

# 清理旧的构建目录
rm -rf build/ dist/
rm -rf deb_dist/

# 使用PyInstaller构建Linux可执行文件
python -m PyInstaller --clean --noconfirm --log-level=INFO \
    --add-data="README_KYLIN_PACKAGING.md:." \
    --name="截图FTP上传工具" \
    --onefile \
    --windowed \
    screenshot_ftp_nanAn_kylin.py

# 创建deb包目录结构
mkdir -p deb_dist/$APP_NAME/DEBIAN
mkdir -p deb_dist/$APP_NAME/usr/local/bin
mkdir -p deb_dist/$APP_NAME/usr/share/applications
mkdir -p deb_dist/$APP_NAME/usr/share/pixmaps

# 复制可执行文件
cp dist/截图FTP上传工具 deb_dist/$APP_NAME/usr/local/bin/screenshot-ftp-uploader

# 创建桌面快捷方式
cat > deb_dist/$APP_NAME/usr/share/applications/$APP_NAME.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=截图FTP上传工具
Comment=截图FTP上传工具 - 南安专用版
Exec=/usr/local/bin/screenshot-ftp-uploader
Icon=screenshot-ftp-uploader
Terminal=false
Categories=Utility;
EOF

# 创建简单的图标 - 尝试创建一个基本的PNG图标
mkdir -p icon_temp
convert -size 128x128 xc:transparent \
    -fill "#2196F3" -draw "circle 64,64 64,32" \
    -fill white -draw "polygon 40,40 40,88 88,64" \
    icon_temp/screenshot-ftp-uploader.png

# 如果convert命令不可用，则创建一个简单的占位符图标
if [ ! -f icon_temp/screenshot-ftp-uploader.png ]; then
    echo "P3" > icon_temp/screenshot-ftp-uploader.ppm
    echo "16 16" >> icon_temp/screenshot-ftp-uploader.ppm
    echo "255" >> icon_temp/screenshot-ftp-uploader.ppm
    for i in {1..256}; do
        echo "0 0 255" >> icon_temp/screenshot-ftp-uploader.ppm
    done
    mv icon_temp/screenshot-ftp-uploader.ppm deb_dist/$APP_NAME/usr/share/pixmaps/screenshot-ftp-uploader.xpm
else
    cp icon_temp/screenshot-ftp-uploader.png deb_dist/$APP_NAME/usr/share/pixmaps/screenshot-ftp-uploader.png
    ln -s /usr/share/pixmaps/screenshot-ftp-uploader.png deb_dist/$APP_NAME/usr/share/pixmaps/screenshot-ftp-uploader.xpm
fi

# 清理临时图标目录
rm -rf icon_temp

# 创建控制文件
cat > deb_dist/$APP_NAME/DEBIAN/control << EOF
Package: $APP_NAME
Version: $APP_VERSION
Section: utils
Priority: optional
Architecture: $ARCHITECTURE
Maintainer: $MAINTAINER
Depends: libc6, libx11-6, libxcb1, libxau6
Recommends: libqt5core5a, libqt5gui5, libqt5widgets5
Description: $APP_DESCRIPTION
 此应用程序可以捕获屏幕截图并自动上传到FTP服务器。
 按Print Screen键会自动捕获并上传截图。
 专为银河麒麟v10系统优化的南安专用版。
EOF

# 创建postinst脚本，确保执行权限
cat > deb_dist/$APP_NAME/DEBIAN/postinst << EOF
#!/bin/bash
chmod +x /usr/local/bin/screenshot-ftp-uploader

# 创建桌面快捷方式
if [ -d /home ]; then
  for USER_HOME in /home/*; do
    if [ -d "\$USER_HOME/Desktop" ]; then
      cp /usr/share/applications/$APP_NAME.desktop "\$USER_HOME/Desktop/"
      chmod +x "\$USER_HOME/Desktop/$APP_NAME.desktop"
      chown \$(stat -c "%U:%G" "\$USER_HOME") "\$USER_HOME/Desktop/$APP_NAME.desktop"
    fi
  done
fi

exit 0
EOF
chmod +x deb_dist/$APP_NAME/DEBIAN/postinst

# 创建postrm脚本，清理
cat > deb_dist/$APP_NAME/DEBIAN/postrm << EOF
#!/bin/bash
# 删除桌面快捷方式
if [ -d /home ]; then
  for USER_HOME in /home/*; do
    if [ -f "\$USER_HOME/Desktop/$APP_NAME.desktop" ]; then
      rm -f "\$USER_HOME/Desktop/$APP_NAME.desktop"
    fi
  done
fi

exit 0
EOF
chmod +x deb_dist/$APP_NAME/DEBIAN/postrm

# 构建deb包
cd deb_dist
dpkg-deb --build $APP_NAME

# 移动deb包到项目根目录
mv $APP_NAME.deb ../screenshot-ftp-uploader_kylin-v10_amd64.deb

echo "构建完成! 生成的deb包: screenshot-ftp-uploader_kylin-v10_amd64.deb" 