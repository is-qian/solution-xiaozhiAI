import modem
import uos
import ujson as json
from usr import uuid
import uwebsocket as ws
from usr.threading import Thread, Condition
from usr.logging import getLogger
import sys_bus



logger = getLogger(__name__)


WSS_DEBUG = True
PROTOCOL_VERSION = "1"
OTA_DOWNLOAD_URL= "http://wechat-mini-static.robomon.cn//OTA/"

class OTAClient(object):
    """OTA客户端 - 获取WebSocket配置"""
    
    def __init__(self):
        self.ota_endpoint = "https://api.tenclass.net/xiaozhi/ota/"
        self.device_info = None
        self.websocket_config = None
        self.firmware_version = self._get_firmware_version()
        self.next_firmware_version = None
        self.next_firmware_url = None
        self._generate_device_info()
        
    def _generate_device_info(self):
        """生成设备信息"""
        try:
            # 获取IMEI作为设备唯一标识
            imei = modem.getDevImei()
            mac_address = self._imei_to_mac(imei)
        except Exception as e:
            logger.debug("无法获取IMEI，使用随机MAC: {}".format(repr(e)))
            mac_address = self._generate_random_mac()
            imei = "123456789012345"
        
        # 生成UUID (基于MAC地址)
        device_uuid = self._generate_uuid_from_mac(mac_address)
        
        # 生成设备hashcode
        device_hashcode = self._generate_device_hashcode(imei)
        
        # 设备信息模板
        device_info_template = {
            "version": 3,
            "language": "zh-CN",
            "flash_size": 4194304,
            "minimum_free_heap_size": 102400,
            "chip_model_name": "EC800M-CN",
            "chip_info": {
                "model": "EC800M-CN",
                "cores": 1,
                "revision": 0,
                "features": 50
            },
            "application": {
                "name": "SC-HEART-P1", 
                "version": self.firmware_version,
                "compile_time": "2024-12-19T10:30:00Z"
            },
            "board": {
                "type": "SC-HEART-P1",
                "features": {
                    "audio": True,
                    "touch": False,
                    "camera": False,
                    "battery": True,
                    "sd_card": False
                }
            }
        }
        
        # 复制设备信息模板并添加设备特定信息
        self.device_info = device_info_template.copy()
        self.device_info.update({
            "mac_address": mac_address,
            "uuid": device_uuid,
            "imei": imei,
            "hashcode": device_hashcode,
            "protocol_version": 3
        })
        
        logger.debug("设备UUID: {}".format(device_uuid))
        logger.debug("=== 设备信息详情 ===")
        logger.debug("MAC地址: {}".format(mac_address))
        logger.debug("IMEI: {}".format(imei))
        logger.debug("设备UUID: {}".format(device_uuid))
        logger.debug("设备Hashcode: {}".format(device_hashcode))
        logger.debug("固件版本: {}".format(self.firmware_version))
        logger.debug("完整设备信息: {}".format(json.dumps(self.device_info)))
        logger.debug("=== 设备信息详情结束 ===")
    
    def _get_firmware_version(self):
        """获取设备固件版本号"""
        # 使用自定义的简单版本号格式
        # 这个版本号应该与OTA服务器上的版本进行比较
        # 格式：主版本号.次版本号.修订号 (例如: 0.0.1, 1.0.0, 2.1.3)
        custom_version = "0.0.0"
        logger.debug("使用自定义固件版本: {}".format(custom_version))
        return custom_version
    
    def _imei_to_mac(self, imei):
        """将IMEI转换为MAC地址格式"""
        if not imei or len(imei) < 15:
            return self._generate_random_mac()
        
        # 取IMEI的最后12位，转换为MAC格式
        mac_part = imei[-12:]
        mac = ":".join([mac_part[i:i+2] for i in range(0, 12, 2)])
        return mac.upper()
    
    def _generate_random_mac(self):
        """生成随机MAC地址"""
        try:
            import urandom
            mac_bytes = [urandom.getrandbits(8) for _ in range(6)]
            # 确保第一个字节是偶数（单播地址）
            mac_bytes[0] &= 0xFE
            return ":".join(["{:02X}".format(b) for b in mac_bytes])
        except:
            # 如果urandom不可用，使用固定的测试MAC
            return "02:00:00:12:34:56"
    
    def _generate_uuid_from_mac(self, mac_address):
        """基于MAC地址生成UUID"""
        try:
            # 移除MAC地址中的冒号
            mac_clean = mac_address.replace(":", "").lower()
            
            try:
                import uhashlib as hashlib
            except ImportError:
                import hashlib
            
            if hashlib:
                # 使用MD5生成UUID
                md5 = hashlib.md5()
                md5.update(mac_clean.encode())
                hash_bytes = md5.digest()
                
                # 格式化为UUID格式
                try:
                    import ubinascii
                    uuid_str = ubinascii.hexlify(hash_bytes).decode()
                except ImportError:
                    import binascii as ubinascii
                    uuid_str = ubinascii.hexlify(hash_bytes).decode()
                
                formatted_uuid = "{}-{}-{}-{}-{}".format(
                    uuid_str[0:8],
                    uuid_str[8:12],
                    uuid_str[12:16],
                    uuid_str[16:20],
                    uuid_str[20:32]
                )
                return formatted_uuid
            else:
                # 如果没有hashlib，使用简单的UUID格式
                return "xiaozhi-{}-device".format(mac_clean)
        except Exception as e:
            logger.debug("UUID生成失败，使用备用方案: {}".format(repr(e)))
            return str(uuid.uuid4())
    
    def _generate_device_hashcode(self, imei):
        """生成设备hashcode"""
        try:
            try:
                import uhashlib as hashlib
            except ImportError:
                import hashlib
            
            if hashlib:
                # 计算MD5哈希
                hash_obj = hashlib.md5()
                hash_obj.update(imei.encode())
                hash_bytes = hash_obj.digest()
                
                # 转换为十六进制并取前16位
                try:
                    import ubinascii
                    hashcode = ubinascii.hexlify(hash_bytes).decode()[:16]
                except ImportError:
                    import binascii as ubinascii
                    hashcode = ubinascii.hexlify(hash_bytes).decode()[:16]
                
                return "xiaozhi_{}".format(hashcode)
            else:
                # 备用方案：使用IMEI后8位
                return "xiaozhi_{}".format(imei[-8:] if len(imei) >= 8 else imei)
                
        except Exception as e:
            logger.debug("hashcode生成失败，使用简化方法: {}".format(repr(e)))
            # 最后备用方案
            return "xiaozhi_{}".format(imei[-8:] if len(imei) >= 8 else imei)

    def _http_request(self, request):
        try:
            import usocket
            import ussl
        except ImportError:
            logger.error("QuecPython环境缺少usocket或ussl模块")
            return False
        
        url_parts = self.ota_endpoint.replace("https://", "").split("/")
        host = url_parts[0]
        path = "/" + "/".join(url_parts[1:])
            
        # 创建socket连接
        sock = usocket.socket()
        
        # DNS解析
        addr_info = usocket.getaddrinfo(host, 443)
        if not addr_info:
            raise Exception("DNS解析失败: {}".format(host))
        
        addr = addr_info[0][-1]
        logger.debug("连接地址: {}".format(addr))
        
        # 建立TCP连接
        sock.connect(addr)
        logger.debug("TCP连接成功")
        
        # 建立SSL连接
        ssl_sock = ussl.wrap_socket(sock, server_hostname=host)
        logger.debug("SSL连接成功")
        
        # 发送请求
        ssl_sock.write(request.encode())
        logger.debug("请求已发送")
        
        # 接收响应
        response_data = b''
        max_read_attempts = 50
        read_attempts = 0
        
        while read_attempts < max_read_attempts:
            try:
                chunk = ssl_sock.read(1024)
                if not chunk:
                    break
                response_data += chunk
                read_attempts += 1
                
                # 检查是否收到完整响应
                if b'\r\n\r\n' in response_data:
                    break
            except OSError:
                break
        
        ssl_sock.close()
        
        return response_data
    def get_websocket_config(self):
        """从OTA API获取WebSocket配置"""
        logger.info("正在从OTA API获取WebSocket配置...")
        
        try:
            # 第一步：调用 /xiaozhi/ota/ 获取challenge或检查注册状态
            challenge = self._get_challenge()
            if challenge is None:
                logger.error("获取challenge失败")
                return False
            
            # 检查设备是否已经注册
            if challenge == "ALREADY_REGISTERED":
                # 设备已经注册，直接获取WebSocket配置
                if hasattr(self, '_first_response') and self._first_response and "websocket" in self._first_response:
                    self.websocket_config = self._first_response["websocket"]
                    logger.info("设备已注册，获取WebSocket配置成功")
                    logger.debug("WebSocket URL: {}".format(self.websocket_config["url"]))
                    return True
                else:
                    logger.error("设备已注册但未找到WebSocket配置")
                    return False
            
            # 第二步：调用 /xiaozhi/ota/activate 激活设备
            # 必须完成激活认证，WebSocket配置才有效
            if not self._activate_device(challenge):
                logger.error("设备激活失败")
                return False
            
            # 激活成功后，从第一步响应中获取WebSocket配置
            if hasattr(self, '_first_response') and self._first_response and "websocket" in self._first_response:
                self.websocket_config = self._first_response["websocket"]
                logger.info("激活成功，获取WebSocket配置成功")
                logger.debug("WebSocket URL: {}".format(self.websocket_config["url"]))
                return True
            else:
                logger.error("激活成功但未找到WebSocket配置")
                return False
            
        except Exception as e:
            logger.error("获取WebSocket配置失败: {}".format(repr(e)))
            return False
    
    def _get_challenge(self):
        """第一步：获取challenge"""
        logger.info("正在获取challenge...")
        
        try:
            # 解析URL
            url_parts = self.ota_endpoint.replace("https://", "").split("/")
            host = url_parts[0]
            path = "/" + "/".join(url_parts[1:])
            
            # 构建请求数据 - 使用完整的设备信息
            request_data = self.device_info
            
            post_data = json.dumps(request_data)
            
            # 构建HTTP请求头
            mac_address = self.device_info.get('mac_address', '')
            device_uuid = self.device_info.get('uuid', '')
            serial_number = "JJZL_SILICORE_1_FCFCB75053D9870E"
            
            request = "POST {} HTTP/1.1\r\n".format(path)
            request += "Host: {}\r\n".format(host)
            request += "Content-Type: application/json\r\n"
            request += "Content-Length: {}\r\n".format(len(post_data))
            request += "Connection: close\r\n"
            request += "User-Agent: SC-HEART-P1/{}\r\n".format(self.firmware_version)
            request += "Accept-Language: zh-CN\r\n"
            request += "Activation-Version: 2\r\n"
            request += "Device-Id: {}\r\n".format(mac_address)
            request += "Client-Id: {}\r\n".format(device_uuid)
            request += "Serial-Number: {}\r\n".format(serial_number)
            request += "X-Device-Type: SC-HEART-P1\r\n"
            request += "X-Firmware-Version: {}\r\n".format(self.firmware_version)
            request += "X-Hardware-Version: 1.0\r\n"
            request += "X-Protocol-Version: 2\r\n"
            request += "\r\n"
            request += post_data
            
            # 打印完整的HTTP请求信息用于调试
            logger.debug("=== 第一步：获取Challenge HTTP请求详情 ===")
            logger.debug("请求URL: https://{}{}".format(host, path))
            logger.debug("请求方法: POST")
            logger.debug("请求头:")
            logger.debug("  Host: {}".format(host))
            logger.debug("  Content-Type: application/json")
            logger.debug("  Content-Length: {}".format(len(post_data)))
            logger.debug("  Connection: close")
            logger.debug("  User-Agent: SC-HEART-P1/{}".format(self.firmware_version))
            logger.debug("  Accept-Language: zh-CN")
            logger.debug("  Activation-Version: 2")
            logger.debug("  Device-Id: {}".format(mac_address))
            logger.debug("  Client-Id: {}".format(device_uuid))
            logger.debug("  Serial-Number: {}".format(serial_number))
            logger.debug("  X-Device-Type: SC-HEART-P1")
            logger.debug("  X-Firmware-Version: {}".format(self.firmware_version))
            logger.debug("  X-Hardware-Version: 1.0")
            logger.debug("  X-Protocol-Version: 2")
            logger.debug("请求体:")
            logger.debug("{}".format(post_data))
            logger.debug("=== 完整HTTP请求 ===")
            logger.debug("{}".format(request))
            logger.debug("=== 第一步请求详情结束 ===")
            
            response_data = self._http_request(request=request)
            # 解析响应
            response_str = response_data.decode('utf-8')
            logger.debug("收到响应: {} bytes".format(len(response_data)))
            
            # 分离头部和主体
            if '\r\n\r\n' not in response_str:
                raise Exception("响应格式错误")
            
            headers, body = response_str.split('\r\n\r\n', 1)
            
            # 打印响应详情
            logger.debug("=== 第一步响应详情 ===")
            logger.debug("响应头:")
            logger.debug("{}".format(headers))
            logger.debug("响应体:")
            logger.debug("{}".format(body))
            logger.debug("=== 第一步响应详情结束 ===")
            
            # 检查状态码
            lines = headers.split('\r\n')
            status_line = lines[0] if lines else ""
            
            if 'HTTP/1.1 202' in status_line:
                logger.warn("第一步请求被接受但需要等待处理")
                return None
            elif 'HTTP/1.1 200' not in status_line:
                logger.error("HTTP错误状态码: {}".format(status_line))
                raise Exception("HTTP错误: {}".format(status_line))
            
            # 解析JSON响应
            response_data = json.loads(body)
            logger.debug("JSON解析成功")
            logger.debug("第一步API响应: {}".format(response_data))
            
            # 保存第一步响应，以便后续使用
            self._first_response = response_data
            
            # 检查设备是否已经注册
            if "activation" not in response_data and "websocket" in response_data:
                logger.info("设备已经注册，直接获取WebSocket配置")
                self.next_firmware_version = response_data["firmware"].get("version")
                self.next_firmware_url = response_data["firmware"].get("url")
                logger.info("下一版本固件信息: {}:{}".format(self.next_firmware_version, self.next_firmware_url))
                return "ALREADY_REGISTERED"
            
            # 提取challenge
            if "challenge" in response_data:
                challenge = response_data["challenge"]
                logger.info("成功获取challenge: {}".format(challenge))
                return challenge
            elif "activation" in response_data and "challenge" in response_data["activation"]:
                challenge = response_data["activation"]["challenge"]
                logger.info("成功获取challenge: {}".format(challenge))
                return challenge
            else:
                logger.error("响应中没有challenge字段")
                logger.debug("可用的字段: {}".format(list(response_data.keys())))
                if "activation" in response_data:
                    logger.debug("activation字段内容: {}".format(response_data["activation"]))
                return None
                
        except Exception as e:
            logger.error("获取challenge失败: {}".format(repr(e)))
            return None
    
    def _activate_device(self, challenge):
        """第二步：激活设备"""
        try:
            import usocket
            import ussl
            import uhashlib as hashlib
            import ubinascii
        except ImportError:
            try:
                import usocket
                import ussl
                import hashlib
                import binascii as ubinascii
            except ImportError:
                logger.error("QuecPython环境缺少必要模块")
                return False
        
        logger.info("正在激活设备...")
        
        try:
            # 解析URL
            url_parts = self.ota_endpoint.replace("https://", "").split("/")
            host = url_parts[0]
            # 确保路径正确，不要重复xiaozhi
            if len(url_parts) > 1 and url_parts[1] == "xiaozhi":
                path = "/xiaozhi/ota/activate"
            else:
                path = "/" + "/".join(url_parts[1:]) + "/activate"
            
            # 生成HMAC
            mac_address = self.device_info.get('mac_address', '')
            serial_number = "JJZL_SILICORE_1_FCFCB75053D9870E"
            
            # 使用正确的license_key
            license_key = "qOUuIWRUrvn80gsDZFUDC6Jd2yeLw5sP"
            
            # 计算HMAC-SHA256
            try:
                # 尝试使用hmac模块
                import hmac as hmac_module
                hmac_instance = hmac_module.new(license_key.encode(), challenge.encode(), hashlib.sha256)
                hmac_result = ubinascii.hexlify(hmac_instance.digest()).decode()
            except Exception as e:
                # 如果hmac模块不可用，手动实现HMAC-SHA256
                logger.debug("hmac模块不可用，手动实现HMAC: {}".format(repr(e)))
                
                # 手动实现HMAC-SHA256
                key = license_key.encode()
                message = challenge.encode()
                
                # 如果key长度超过64字节，先hash
                if len(key) > 64:
                    hash_obj = hashlib.sha256()
                    hash_obj.update(key)
                    key = hash_obj.digest()
                
                # 如果key长度不足64字节，用0填充
                if len(key) < 64:
                    key = key + b'\x00' * (64 - len(key))
                
                # 计算 inner hash
                inner_key = bytes([k ^ 0x36 for k in key])  # key XOR ipad
                inner_hash = hashlib.sha256()
                inner_hash.update(inner_key)
                inner_hash.update(message)
                inner_digest = inner_hash.digest()
                
                # 计算 outer hash
                outer_key = bytes([k ^ 0x5c for k in key])  # key XOR opad
                outer_hash = hashlib.sha256()
                outer_hash.update(outer_key)
                outer_hash.update(inner_digest)
                outer_digest = outer_hash.digest()
                
                hmac_result = ubinascii.hexlify(outer_digest).decode()
            
            logger.debug("HMAC计算详情:")
            logger.debug("  license_key: {}".format(license_key))
            logger.debug("  challenge: {}".format(challenge))
            logger.debug("  hmac_result: {}".format(hmac_result))
            
            # 构建请求数据
            request_data = {
                "algorithm": "hmac-sha256",
                "serial_number": serial_number,
                "challenge": challenge,
                "hmac": hmac_result
            }
            
            post_data = json.dumps(request_data)
            
            # 构建HTTP请求头
            device_uuid = self.device_info.get('uuid', '')
            
            request = "POST {} HTTP/1.1\r\n".format(path)
            request += "Host: {}\r\n".format(host)
            request += "Content-Type: application/json\r\n"
            request += "Content-Length: {}\r\n".format(len(post_data))
            request += "Connection: close\r\n"
            request += "User-Agent: SC-HEART-P1/{}\r\n".format(self.firmware_version)
            request += "Accept-Language: zh-CN\r\n"
            request += "Activation-Version: 2\r\n"
            request += "Device-Id: {}\r\n".format(mac_address)
            request += "Client-Id: {}\r\n".format(device_uuid)
            request += "Serial-Number: {}\r\n".format(serial_number)
            request += "X-Device-Type: SC-HEART-P1\r\n"
            request += "X-Firmware-Version: {}\r\n".format(self.firmware_version)
            request += "X-Hardware-Version: 1.0\r\n"
            request += "X-Protocol-Version: 2\r\n"
            request += "\r\n"
            request += post_data
            
            # 打印完整的HTTP请求信息用于调试
            logger.debug("=== 第二步：激活设备 HTTP请求详情 ===")
            logger.debug("请求URL: https://{}{}".format(host, path))
            logger.debug("请求方法: POST")
            logger.debug("请求头:")
            logger.debug("  Host: {}".format(host))
            logger.debug("  Content-Type: application/json")
            logger.debug("  Content-Length: {}".format(len(post_data)))
            logger.debug("  Connection: close")
            logger.debug("  User-Agent: SC-HEART-P1/{}".format(self.firmware_version))
            logger.debug("  Accept-Language: zh-CN")
            logger.debug("  Activation-Version: 2")
            logger.debug("  Device-Id: {}".format(mac_address))
            logger.debug("  Client-Id: {}".format(device_uuid))
            logger.debug("  Serial-Number: {}".format(serial_number))
            logger.debug("  X-Device-Type: SC-HEART-P1")
            logger.debug("  X-Firmware-Version: {}".format(self.firmware_version))
            logger.debug("  X-Hardware-Version: 1.0")
            logger.debug("  X-Protocol-Version: 2")
            logger.debug("请求体:")
            logger.debug("{}".format(post_data))
            logger.debug("=== 完整HTTP请求 ===")
            logger.debug("{}".format(request))
            logger.debug("=== 第二步请求详情结束 ===")
            
            response_data = self._http_request(request=request)
            # 解析响应
            response_str = response_data.decode('utf-8')
            logger.debug("收到响应: {} bytes".format(len(response_data)))
            
            # 分离头部和主体
            if '\r\n\r\n' not in response_str:
                raise Exception("响应格式错误")
            
            headers, body = response_str.split('\r\n\r\n', 1)
            
            # 打印响应详情
            logger.debug("=== 第二步响应详情 ===")
            logger.debug("响应头:")
            logger.debug("{}".format(headers))
            logger.debug("响应体:")
            logger.debug("{}".format(body))
            logger.debug("=== 第二步响应详情结束 ===")
            
            # 检查状态码
            lines = headers.split('\r\n')
            status_line = lines[0] if lines else ""
            
            if 'HTTP/1.1 202' in status_line:
                logger.warn("激活请求被接受但需要等待处理")
                # 202状态码表示请求被接受，但需要等待处理
                # 根据参考代码，这应该返回ESP_ERR_TIMEOUT，但我们在这里返回True
                # 因为服务器已经接受了我们的激活请求
                logger.info("设备激活请求已被服务器接受")
                return True
            elif 'HTTP/1.1 200' not in status_line:
                logger.error("HTTP错误状态码: {}".format(status_line))
                raise Exception("HTTP错误: {}".format(status_line))
            
            # 解析JSON响应
            response_data = json.loads(body)
            logger.debug("JSON解析成功")
            logger.debug("第二步API响应: {}".format(response_data))
            
            # 激活成功，不需要从第二步响应中提取WebSocket配置
            # WebSocket配置已经在第一步响应中获取
            logger.info("设备激活成功")
            return True

        except Exception as e:
            logger.error("激活设备失败: {}".format(repr(e)))
            return False
    def _activate_device(self, challenge):
        " "
    def get_websocket_url(self):
        """获取WebSocket URL"""
        if self.websocket_config:
            return self.websocket_config["url"]
        return None
    
    def get_access_token(self):
        """获取访问令牌"""
        if self.websocket_config:
            return self.websocket_config["token"]
        return None

    def result(args):
        logger.info('download status:',args[0],'download process:',args[1])
    
    def check_firmware_update(self):
        if not self.next_firmware_version or not self.next_firmware_url:
            logger.info("没有可用的固件更新")
            return False
        logger.info("检测到新固件版本: {}，下载链接: {}".format(
            self.next_firmware_version, OTA_DOWNLOAD_URL + self.next_firmware_version + "/dfota_1.bin"))
        try:
            import fota
            import utime
            
            fota_obj = fota()
            # 由于小智只能下载一个包 所以先暂时放到这里
            res = fota_obj.httpDownload(url1=OTA_DOWNLOAD_URL + self.next_firmware_version + "/dfota_1.bin", url2=OTA_DOWNLOAD_URL + self.next_firmware_version + "/dfota_2.bin")
            if res != 0:
                logger.error("固件更新失败，返回码: {}".format(res))
                return None
            logger.info("固件更新成功")
            utime.sleep(2)
    
        except Exception as e:
            logger.error("固件下载失败: {}".format(repr(e)))
            return None

class JsonMessage(object):

    def __init__(self, kwargs):
        self.kwargs = kwargs
    
    def __str__(self):
        return str(self.kwargs)
    
    def to_bytes(self):
        return json.dumps(self.kwargs)
    
    @classmethod
    def from_bytes(cls, data):
        return cls(json.loads(data))

    def __getitem__(self, key):
        return self.kwargs[key]


class RespHelper(Condition):

    def __init__(self):
        self.__ack_items = {}
        super().__init__()

    def get(self, request, timeout=None):
        """accept a request and return response matched or none"""
        self.__ack_items[request] = None
        self.wait_for(lambda: self.__ack_items[request] is not None, timeout=timeout)
        return self.__ack_items.pop(request)

    def put(self, response):
        """accept a response and match it with request if possible"""
        for request in self.__ack_items.keys():
            if not self.validate(request, response):
                continue
            self.__ack_items[request] = response
            self.notify_all()
            break

    @staticmethod
    def validate(request, response):
        return request["type"] == response["type"]


class WebSocketClient(object):

    def __init__(self, debug=WSS_DEBUG):
        self.debug = debug
        self.ota_client = OTAClient()
        self.host = None
        self.access_token = None
        self.__resp_helper = RespHelper()
        self.__recv_thread = None
        self.__audio_message_handler = None
        self.__json_message_handler = None
        
        # 初始化时获取配置
        self._initialize_config()
    
    def _initialize_config(self):
        """初始化WebSocket配置"""
        if self.ota_client.get_websocket_config():
            self.host = self.ota_client.get_websocket_url()
            self.access_token = self.ota_client.get_access_token()
            self.ota_client.check_firmware_update()
            logger.info("WebSocket配置初始化成功")
        else:
            logger.error("WebSocket配置初始化失败")
            raise RuntimeError("无法获取WebSocket配置")
    
    def __str__(self):
        return "{}(host=\"{}\")".format(type(self).__name__, self.host)

    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, *args, **kwargs):
        return self.disconnect()

    def set_callback(self, audio_message_handler=None, json_message_handler=None):
        if audio_message_handler is not None and callable(audio_message_handler):
            self.__audio_message_handler = audio_message_handler
        else:
            raise TypeError("audio_message_handler must be callable")
        
        if json_message_handler is not None and callable(json_message_handler):
            self.__json_message_handler = json_message_handler
        else:
            raise TypeError("json_message_handler must be callable")
        
    def get_mac_address(self):
        """获取设备MAC地址"""
        return self.ota_client.device_info.get('mac_address', '64:e8:33:48:ec:c0')

    def generate_uuid(self):
        """获取设备UUID（与OTA客户端保持一致）"""
        return self.ota_client.device_info.get('uuid', str(uuid.uuid4()))

    @property
    def cli(self):
        __client__ = getattr(self, "__client__", None)
        if __client__ is None:
            raise RuntimeError("{} not connected".format(self))
        return __client__

    def is_state_ok(self):
        return self.cli.sock.getsocketsta() == 4
    
    def disconnect(self):
        """disconnect websocket"""
        __client__ = getattr(self, "__client__", None)
        if __client__ is not None:
            __client__.close()
            del self.__client__
        if self.__recv_thread is not None:
            self.__recv_thread.join()
            self.__recv_thread = None

    def connect(self):
        """connect websocket"""
        if not self.host or not self.access_token:
            raise RuntimeError("WebSocket配置未初始化")
            
        __client__ = ws.Client.connect(
            self.host, 
            headers={
                "Authorization": "Bearer {}".format(self.access_token),
                "Protocol-Version": PROTOCOL_VERSION,
                "Device-Id": self.get_mac_address(),
                "Client-Id": self.generate_uuid()
            }, 
            debug=self.debug
        )

        try:
            self.__recv_thread = Thread(target=self.__recv_thread_worker)
            self.__recv_thread.start(stack_size=64)
        except Exception as e:
            __client__.close()
            logger.error("{} connect failed, Exception details: {}".format(self, repr(e)))
        else:
            setattr(self, "__client__", __client__)
            return __client__

    def __recv_thread_worker(self):
        while True:
            try:
                raw = self.recv()
            except Exception as e:
                logger.info("{} recv thread break, Exception details: {}".format(self, repr(e)))
                break
            
            if raw is None or raw == "":
                logger.info("{} recv thread break, Exception details: read none bytes, websocket disconnect".format(self))
                break
            
            try:
                m = JsonMessage.from_bytes(raw)
            except Exception as e:
                self.__handle_audio_message(raw)
            else:
                if m["type"] == "hello":
                    with self.__resp_helper:
                        self.__resp_helper.put(m)
                else:
                    self.__handle_json_message(m)

    def __handle_audio_message(self, raw):
        if self.__audio_message_handler is None:
            logger.warn("audio message handler is None, did you forget to set it?")
            return
        try:
            self.__audio_message_handler(raw)
        except Exception as e:
            logger.error("{} handle audio message failed, Exception details: {}".format(self, repr(e)))
    
    def __handle_json_message(self, msg):
        if self.__json_message_handler is None:
            logger.warn("json message handler is None, did you forget to set it?")
            return
        try:
            self.__json_message_handler(msg)
        except Exception as e:
            logger.debug("{} handle json message failed, Exception details: {}".format(self, repr(e)))
            
    # def topic(text_value):
        
            
    def send(self, data):
        """send data to server"""
        # logger.debug("send data: ", data)
        self.cli.send(data)

    def recv(self):
        """receive data from server, return None or "" means disconnection"""
        data = self.cli.recv()
        if type(data) == str:
            data_dict = json.loads(data)
            text_value = data_dict.get("text")
            
            # 对比 text_value 和上次的值是否相同
            if text_value != self.__last_text_value and text_value is not None:
                print(text_value)  # 仅在不同时打印
                self.__last_text_value = text_value  # 更新为最新的 text_value
        # logger.debug("recv data: ", data)
        return data



    def hello(self):
        req = JsonMessage(
            {
                "type": "hello",
                "version": 1,
                "transport": "websocket",
                "audio_params": {
                    "format": "opus",
                    "sample_rate": 16000,
                    "channels": 1,
                    "frame_duration": 100
                },
                "features": {
                    "consistent_sample_rate": True
                }
            }
        )
        with self.__resp_helper:
            self.send(req.to_bytes())
            resp = self.__resp_helper.get(req, timeout=10)
            # {'transport': 'websocket', 'type': 'hello', 'session_id': 'd2091edb', 'audio_params': {'frame_duration': 60, 'channels': 1, 'format': 'opus', 'sample_rate': 24000}, 'version': 1}
            # logger.debug("hello resp: ", resp)
            return resp

    def listen(self, state, mode="auto", session_id=""):
        with self.__resp_helper:
            self.send(
                JsonMessage(
                    {
                        "session_id": session_id,  # Websocket协议不返回 session_id，所以消息中的会话ID可设置为空
                        "type": "listen",
                        "state": state,  # "start": 开始识别; "stop": 停止识别; "detect": 唤醒词检测
                        "mode": mode  # "auto": 自动停止; "manual": 手动停止; "realtime": 持续监听
                    }
                ).to_bytes()
            )
    
    def wakeword_detected(self, wakeword, session_id=""):
        with self.__resp_helper:
            self.send(
                JsonMessage(
                    {
                        "session_id": session_id,
                        "type": "listen",
                        "state": "detect",
                        "text": wakeword  # 唤醒词
                    }
                ).to_bytes()
            )
    
    def abort(self, session_id="", reason=""):
        with self.__resp_helper:
            self.send(
                JsonMessage(
                    {
                        "session_id": session_id,
                        "type": "abort",
                        "reason": reason
                    }
                ).to_bytes()
            )

    def report_iot_descriptors(self, descriptors, session_id=""):
        with self.__resp_helper:
            self.send(
                JsonMessage(
                    {
                        "session_id": session_id,
                        "type": "iot",
                        "descriptors": descriptors
                    }
                ).to_bytes()
            )

    def report_iot_states(self, states, session_id=""):
        with self.__resp_helper:
            self.send(
                JsonMessage(
                    {
                        "session_id": session_id,
                        "type": "iot",
                        "states": states
                    }
                ).to_bytes()
            )

