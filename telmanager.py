# -*- coding: utf-8 -*-

import re
import sys
import math
import time
import random
import requests
import logging
import logging.handlers
from lxml import html

class Logger(object):

    def __init__(self, logfile):

        self.logger = logging.getLogger(__name__)
        self.handler = logging.handlers.RotatingFileHandler(logfile, maxBytes=1024 * 400, backupCount=5, encoding='utf-8', delay=False)
        self.handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.handler.setLevel(logging.DEBUG)
        self.logger.addHandler(self.handler)

    def info(self, msg):

        self.logger.setLevel(logging.INFO)
        self.logger.info(msg)
        self.handler.flush()

    def error(self, msg):

        self.logger.setLevel(logging.ERROR)
        self.logger.error(msg)
        self.handler.flush()

    def end(self):

        self.handler.close()
        self.logger.removeHandler(self.handler)


class MO:

    def __init__(self, ip):

        self.address = ip
        self.session = requests.Session()
        self.timeout = 30

    def convert_time(self, sec):

        """
        秒智能换算
        :param sec: 时间秒，int类型
        :return: 7 小时 5 分钟 22 秒
        """
        year = 365 * 24 * 60 * 60
        month = 30 * 24 * 60 * 60
        day = 24 * 60 * 60
        hour = 60 * 60
        min = 60
        if sec < 60:
            return '%d 秒' % math.ceil(sec)
        elif sec > year:
            years = divmod(sec, year)
            return '%d 年 %s' % (int(years[0]), self.convert_time(years[1]))
        elif sec > month:
            months = divmod(sec, month)
            return '%d 个月 %s' % (int(months[0]), self.convert_time(months[1]))
        elif sec > day:
            days = divmod(sec, day)
            return '%d 天 %s' % (int(days[0]), self.convert_time(days[1]))
        elif sec > hour:
            hours = divmod(sec, hour)
            return '%d 小时 %s' % (int(hours[0]), self.convert_time(hours[1]))
        else:
            mins = divmod(sec, min)
            return '%d 分钟 %d 秒' % (int(mins[0]), math.ceil(mins[1]))

    def convert_flow(self, flow_b):

        """
        流量智能换算
        :param size: 单位字节B int类型，支持正负数。
        :return: 2.00 G
        """

        if not flow_b:
            return 0
        flow_b = int(flow_b)
        flow_b_abs = abs(flow_b)
        flow_kb = flow_b_abs / 1024
        if flow_kb < 1:
            return '%s' % (0 - flow_b_abs if flow_b < 0 else flow_b_abs)
        flow_mb = flow_kb / 1024
        if flow_mb < 1:
            return '%.2fK' % (0 - flow_kb if flow_b < 0 else flow_kb)
        flow_gb = flow_mb / 1024
        if flow_gb < 1:
            return '%.2fM' % (0 - flow_mb if flow_b < 0 else flow_mb)
        flow_tb = flow_gb / 1024
        if flow_tb < 1:
            return '%.2fG' % (0 - flow_gb if flow_b < 0 else flow_gb)
        flow_pb = flow_tb / 1024
        if flow_pb < 1:
            return '%.2fT' % (0 - flow_tb if flow_b < 0 else flow_tb)
        flow_eb = flow_pb / 1024
        if flow_eb < 1:
            return '%.2fP' % (0 - flow_pb if flow_b < 0 else flow_pb)
        flow_zb = flow_eb / 1024
        if flow_zb < 1:
            return '%.2fE' % (0 - flow_eb if flow_b < 0 else flow_eb)
        flow_yb = flow_zb / 1024
        if flow_yb < 1:
            return '%.2fZ' % (0 - flow_zb if flow_b < 0 else flow_zb)
        flow_bb = flow_yb / 1024
        if flow_bb < 1:
            return '%.2fY' % (0 - flow_yb if flow_b < 0 else flow_yb)
        return 'Too large!'

    def login(self, usr, pwd, ttl=2):

        """
        登录
        :param usr: 光猫登录帐号
        :param pwd: 光猫登录密码
        """

        url = 'http://{}/cgi-bin/luci'.format(self.address)
        data = {'username': usr, 'psd': pwd}
        try:
            r = self.session.post(url, data, timeout=self.timeout, allow_redirects=True)
            r.encoding = 'utf-8'
            if self.session.cookies.get(name='sysauth'):
                logger.info('登录光猫 %s 成功~' % self.address)
                token = re.findall('token:\s*\'(.*?)\'', r.text, flags=re.S)
                if token:
                    self.token = token[0]
                    return
                else:
                    raise Exception('登录后获取token失败，返回：%s！' % r.text)
            h = html.fromstring(r.text)
            error_text = h.xpath('string(//form[@id="login_form"]/div[@class="login-input"]/div[last()]/font)')
            if '密码错误' in error_text:
                raise Exception(error_text)
            else:
                raise Exception('登录光猫设备返回异常：%s' % r.text)
        except requests.exceptions.RequestException as e:
            if ttl != 0:
                ttl -= 1
                return self.login(usr, pwd, ttl)
            raise Exception('登录光猫设备请求失败，%s！' % e)

    def get_gwinfo(self, ttl=2):

        """
        获取设备信息
        """

        url = 'http://{}/cgi-bin/luci/admin/settings/gwinfo?get=all&_={}'.format(self.address, random.random())
        try:
            r = self.session.get(url, timeout=self.timeout)
            r.encoding = 'utf-8'
            res = r.json()
            logger.info('光猫设备类型：%s，产品型号：%s，序列号：%s，MAC地址：%s，Wi-Fi状态：%s，2.4Ghz Wi-Fi名称：%s，5Ghz Wi-Fi名称：%s，固件版本：%s，上网帐号：%s，WAN口ipv4：%s，WAN口ipv6：%s。' % (
                res['DevType'],
                res['ProductCls'],
                res['ProductSN'],
                res['MAC'],
                '开启' if res['wifiOnOff'] else '关闭',
                res['ssid2g'],
                res['ssid5g'],
                res['SWVer'],
                res['wanAcnt'],
                res['WANIP'],
                res['WANIPv6']
            ))
        except requests.exceptions.RequestException as e:
            if ttl != 0:
                ttl -= 1
                return self.get_allinfo(ttl)
            logger.error('获取设备信息请求失败，%s！' % e)

    def get_allinfo(self, ttl=2):

        """
        获取所有信息
        """

        url = 'http://{}/cgi-bin/luci/admin/allInfo?_={}'.format(self.address, random.random())
        try:
            r = self.session.get(url, timeout=self.timeout)
            r.encoding = 'utf-8'
            res = r.json()
            logger.info('WAN口连接状态：%s，联网时间：%s。有线端 %s 台设备，上传速度 %sb/s，下载速度 %sb/s；无线端 %s 台设备，上传速度 %sb/s，下载速度 %sb/s。' % (
                res['wanConnect'],
                self.convert_time(res['wanUpTime']),
                res.get('wcount'),
                self.convert_flow(res.get('tWUp')),
                self.convert_flow(res.get('tWDown')),
                res.get('wlcount'),
                self.convert_flow(res.get('tWlUp')),
                self.convert_flow(res.get('tWlDown'))
            ))
            logger.info('LAN口接入设备有：')
            for i in range(1, res['wcount'] + 1):
                key = 'pc%s' % i
                logger.info('设备%s，品牌 %s，设备名称 %s，在线时间 %s，型号 %s，类型 %s，IP地址 %s，上传速度 %sb/s，下载速度 %sb/s；' % (
                    i,
                    res[key]['brand'],
                    res[key]['devName'],
                    self.convert_time(res[key]['onlineTime']),
                    res[key]['model'],
                    res[key]['type'],
                    res[key]['ip'],
                    self.convert_flow(res[key]['upSpeed']),
                    self.convert_flow(res[key]['downSpeed']))
                )
        except requests.exceptions.RequestException as e:
            if ttl != 0:
                ttl -= 1
                return self.get_allinfo(ttl)
            logger.error('获取接口信息请求失败，%s！' % e)

    def restart(self, ttl=2):

        """
        重启设备
        """

        url = 'http://{}/cgi-bin/luci/admin/reboot'.format(self.address)
        data = {'token': self.token}
        try:
            r = self.session.post(url, data, timeout=self.timeout)
            if r.status_code == 200:
                logger.info('重启设备成功~')
            else:
                if ttl != 0:
                    ttl -= 1
                    return self.restart(ttl)
                logger.error('重启设备失败，%s！' % r.status_code)
        except requests.exceptions.RequestException as e:
            if ttl != 0:
                ttl -= 1
                return self.restart(ttl)
            logger.error('重启设备请求失败，%s！' % e)

if __name__ == '__main__':

    logger = Logger(sys.path[0] + '/' + 'telmanager.log') # 定义输出日志的文件
    mo = MO('192.168.1.1') # 光猫地址
    mo.login('useradmin', '2DJFP') # 光猫登录帐号与密码
    time.sleep(3)
    mo.get_gwinfo()
    mo.get_allinfo()
    mo.restart()
    logger.end()
