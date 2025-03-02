# 本项目方法已失效，停止更新 2025.03.02

# DingTalk-Live-Playback-Download-Tool
钉钉直播回放下载工具，使用钉钉分享链接一键下载钉钉直播回放视频，现已支持批量下载
![image](https://github.com/user-attachments/assets/0de8822a-fe81-4726-b8fb-8540b9197908)


## 使用方法
- 直接运行 DingTalk-Live-Playback-Download-Tool.exe
- 选择下载方式、保存方式和浏览器后，等待浏览器自动打开
- 首次运行，浏览器加载可能较慢，因为程序在自动下载并载入Webdriver，需耐心等待
- 浏览器打开后，登录钉钉账号，等待页面加载完毕
- 回到程序界面，点击回车即可开始下载

## 批量下载模式
- 将需要下载的钉钉直播分享链接保存至一个CSV或者EXCEL表格，一个单元格放一个链接，不要放在首行
- 运行 DingTalk-Live-Playback-Download-Tool.exe，选择批量下载模式
- 手动输入保存有钉钉直播分享链接表格的路径或者直接将表格文件拖进窗口
- 选择保存方式和浏览器后，等待浏览器自动打开
- 浏览器打开后，登录钉钉账号，等待页面加载完毕
- 回到程序界面，点击回车即可开始批量下载
  

![image](https://github.com/user-attachments/assets/e7b9d376-0814-4649-a334-422deb8cc2b3)

![image](https://github.com/user-attachments/assets/59b7c2e1-a29b-480f-9377-80fc2b6890c2)



## 使用的工具

本项目使用了以下第三方工具：

- [N_m3u8DL-RE](https://github.com/nilaoda/N_m3u8DL-RE)：一个跨平台的DASH/HLS/MSS下载工具，支持点播和直播（DASH/HLS）视频下载。
- [FFmpeg](https://ffmpeg.org/)：一个开源的音视频处理工具，支持多种格式的转换、录制和流媒体处理。
