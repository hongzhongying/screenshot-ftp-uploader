# 截图FTP上传工具 - 南安专用版

这是一个为银河麒麟v10系统开发的截图自动上传工具。

## 功能特点

- 支持快捷键截图（Print Screen）
- 自动上传到FTP服务器
- 适配银河麒麟v10系统
- 包含所有必要依赖

## 自动构建方法

本项目使用GitHub Actions自动构建银河麒麟v10系统可用的DEB安装包。构建完成后，可以从GitHub Actions的Artifacts下载DEB包。

## 手动上传文件的步骤

如果Git推送遇到问题，可以按照以下步骤手动上传文件：

1. 运行`prepare_key_files.ps1`脚本准备所有必要文件
2. 访问 https://github.com/hongzhongying/screenshot-ftp-uploader
3. 点击"Add file" > "Upload files"按钮
4. 将`deb_build_files`目录中的以下文件上传：
   - build_kylin_package.sh
   - kylin_package.spec
   - requirements.txt
   - README_KYLIN_PACKAGING.md
   - screenshot_ftp_nanAn_kylin.py
5. 创建`.github/workflows`目录，并上传`build-deb.yml`文件
6. 提交更改，描述为"准备银河麒麟DEB构建文件"
7. 访问 https://github.com/hongzhongying/screenshot-ftp-uploader/actions
8. 在"Workflows"列表中找到"Build DEB Package"
9. 点击"Run workflow"按钮手动触发构建
10. 等待构建完成（通常需要5-10分钟）
11. 从构建页面下载生成的DEB安装包

## 安装说明

构建完成后，您可以将DEB包复制到银河麒麟v10系统，然后使用以下命令安装：

```bash
sudo dpkg -i screenshot-ftp-uploader_kylin-v10_amd64.deb
```

安装完成后，可以从应用程序菜单或桌面快捷方式启动"截图FTP上传工具"。

## 使用方法

1. 从桌面快捷方式启动程序
2. 按Print Screen键进行截图
3. 截图会自动上传到FTP服务器

## 注意事项

- 本版本包含所有必要依赖，无需网络连接即可安装
- 适配银河麒麟v10系统
- 如有问题请联系管理员 