FTP Readme

作者：沈洪斌
博客：http://www.cnblogs.com/vincenshen/

程序介绍：
	使用docopt第三方库来解析参数
	实现登录md5加密认证
	实现查看文件列表
	实现文件下载
	实现文件上传
	打印进度条
	文件一致性校验（未实现）
	磁盘配额（未实现）
	断点续传（未实现）
	
程序目录结构：

	FTPServer #FTPserver程序主目录
	│
	├──bin
	│   ├── Server.py  #FTPserver启动接口
	│
	├──conf
	│   ├── settings.py # 配置文件
	│   ├── accounts.cfg # 用户账号配置文件
	│	
  	├──core
	│   ├── ftpserver.py  #主逻辑功能程序
	│   ├── main.py # 启动参数解析，启动多线程
  	│
	├──home # 用户FTP根目录



注意事项：
	程序使用了第三方库 docopt 0.6.2
	该程序使用python3版本编写，不兼容python2版本
	
使用方法：
	启动服务端：pyhton bin/Server.py  runserver -s ip -p port
	启动客户端：pyhton bin/Client.py -s ip -p port
	

版本：
     1.1
	
	
更新日志：
     v1.0 2017.03.9
     v1.1 2017.03.16
	
	
