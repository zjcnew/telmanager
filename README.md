# telmanager
光猫管理器，获取连接、流量等信息，配合定时任务可实现自动重启设备的目的。
## 兼容设备
目前以下设备调试通过：
### 中国电信
*华为HS8145C5
*中兴ZXHN F450
## 使用方法 
1.安装Python3
2.安装库
`
pip3 install --trusted-host mirrors.aliyun.com -i http://mirrors.aliyun.com/pypi/simple/ requests lxml
`

3.下载telmanager.py脚本到本地，末尾修改参数（查阅光猫背面信息）
`
logger = Logger(sys.path[0] + '/' + 'telmanager.log') # 定义输出日志的文件
mo = MO('192.168.1.1') # 光猫地址
mo.login('useradmin', '2DJFP') # 光猫登录帐号与密码
`
4.执行脚本
`
python telmanager.py
`
5.查看日志文件内容
欢迎反馈，提供其他型号设备的测试结果。
