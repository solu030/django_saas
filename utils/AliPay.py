import json
import datetime
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
from urllib.parse import quote_plus,urlparse,parse_qs
from base64 import decodebytes,encodebytes
from django_saas import settings
class AliPay():
    def __init__(self):
        self.app_id = settings.ALI_APPID
        self.gate_way = settings.ALI_GATEWAY
        self.return_url = settings.ALI_RETURN_URL
        self.notify_url = settings.ALI_NOTIFY_URL
        with open(settings.ALI_PRI_KEY_PATH) as fp:
            self.private_key = RSA.importKey(fp.read())
        with open(settings.ALI_PUB_KEY_PATH) as fp:
            self.public_key = RSA.importKey(fp.read())

    def direct_pay(self,subject,out_trade_no,total_amount):
        params = {
            'app_id':self.app_id,
            'method': 'alipay.trade.page.pay',
            'format': "JSON",
            'return_url': self.return_url,
            'notify_url': self.notify_url,
            'charset': 'utf-8',
            'sign_type': 'RSA2',
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'version': "1.0",
            'biz_content': json.dumps({
                "out_trade_no": out_trade_no,
                "product_code": "FAST_INSTANT_TRADE_PAY",
                "total_amount": total_amount,
                "subject": subject
            },separators=(",",":"))
        }
        unsigned_string = "&".join(["{0}={1}".format(k,params[k]) for k in sorted(params)])
        signer = PKCS1_v1_5.new(self.private_key)
        signature = signer.sign(SHA256.new(unsigned_string.encode("utf-8")))
        sign_string = encodebytes(signature).decode("utf-8").replace("\n","")
        result = "&".join(["{0}={1}".format(k,quote_plus(params[k])) for k in sorted(params)])
        result = result + "&sign=" + quote_plus(sign_string)
        pay_url = "{}?{}".format(settings.ALI_GATEWAY, result)
        return pay_url

    def ordered_data(self, data):
        complex_keys = []
        for k,v in data.items():
            if isinstance(v, dict):
                complex_keys.append(k)
        for k in complex_keys:
            data[k] = json.dumps(data[k],separators=(",",":"))
        return sorted([(k,v) for k,v in data.items()])

    def _verify(self,raw_content,signature):
        key = self.public_key
        signer = PKCS1_v1_5.new(key)
        digest = SHA256.new()
        digest.update(raw_content.encode('utf-8'))
        if signer.verify(digest,decodebytes(signature.encode('utf-8'))):
            return True
        return False
    def verify(self,data,signature):
        if "sign_type" in data:
            sign_type = data.pop("sign_type")
        unsigned_items = self.ordered_data(data)
        message = "&".join(u"{}={}".format(k,v) for k,v in unsigned_items)
        return self._verify(message,signature)