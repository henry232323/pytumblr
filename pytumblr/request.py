from urllib.parse import parse_qsl, urlencode
import time
import asyncio
from hashlib import sha1

from aioauth_client import OAuth1Client, HmacSha1Signature
from aioauth_client import RANDOM as random


class TumblrRequest(OAuth1Client):
    """
    A simple request object that lets us query the Tumblr API
    """

    __version = "0.0.1"
    host: str = ""
    headers: dict = None
    loop: asyncio.AbstractEventLoop

    def __init__(self,
                 loop: asyncio.AbstractEventLoop,
                 consumer_key: str,
                 consumer_secret: str,
                 oauth_token: str=None,
                 oauth_secret: str=None,
                 host="https://api.tumblr.com",
                 access_token_url="https://api.tumblr.com/access_token",
                 request_token_url="https://www.tumblr.com/oauth/request_token",
                 authorize_url="https:/f/www.tumblr.com/oauth/authorize",
                 headers=None):
        super(__class__, self).__init__(consumer_key=consumer_key,
                                        consumer_secret=consumer_secret,
                                        base_url=host,
                                        access_token_url=access_token_url,
                                        oauth_token=oauth_token,
                                        oauth_token_secret=oauth_secret,
                                        signature=HmacSha1Signature(),
                                        request_token_url=request_token_url,
                                        authorize_url=authorize_url)

        if headers is None:
            headers = {}

        self.loop = loop
        self.host = host
        self.headers = {
            "User-Agent": "apytumblr/" + self.__version
        }
        self.headers.update(headers)

    async def get(self, url: str, params: dict) -> dict:
        """
        Issues a GET request against the API, properly formatting the params
        :param url: a string, the url you are requesting
        :param params: a dict, the key-value of all the paramaters needed
                       in the request
        :returns: a dict parsed of the JSON response
        """
        url = self.host + url
        if params:
            url = url + "?" + urlencode(params)

        resp = await self.request("GET", url, headers=self.headers)

        return await resp.json()

    async def post(self, url: str, params: dict=None, files: list=None):
        """
        Issues a POST request against the API, allows for multipart data uploads
        :param url: a string, the url you are requesting
        :param params: a dict, the key-value of all the parameters needed
                       in the request
        :param files: a list, the list of tuples of files
        :returns: a dict parsed of the JSON response
        """
        url = self.host + url
        if params is None:
            params = {}
        if files is None:
            files = []

        if files:
            return await self.post_multipart(url, params, files)
        else:
            resp = await self.request(url=url, method="POST", body=urlencode(params), headers=self.headers)
            return await resp.json()

    async def post_multipart(self, url: str, params: dict, files: list):
        """
        Generates and issues a multipart request for data files
        :param url: a string, the url you are requesting
        :param params: a dict, a key-value of all the parameters
        :param files:  a list, the list of tuples for your data
        :returns: a dict parsed from the JSON response
        """
        #  combine the parameters with the generated oauth params
        params = dict(params.items() + self.generate_oauth_params().items())
        faux_req = self.request(method="POST", url=url, parameters=params)
        params = dict(parse_qsl(faux_req.to_postdata()))

        content_type, body = self.encode_multipart_formdata(params, files)
        headers = {'Content-Type': content_type, 'Content-Length': str(len(body))}

        #  Do a bytearray of the body and everything seems ok
        r = await self.request(url=url, method="POST", body=bytearray(body), headers=headers)
        return await r.json()

    @staticmethod
    def encode_multipart_formdata(fields: dict, files: list):
        """
        Properly encodes the multipart body of the request
        :param fields: a dict, the parameters used in the request
        :param files:  a list of tuples containing information about the files
        :returns: the content for the body and the content-type value
        """
        import mimetypes
        from email.generator import _make_boundary
        BOUNDARY = _make_boundary()
        CRLF = '\r\n'
        L = []
        for (key, value) in fields.items():
            L.append('--' + BOUNDARY)
            L.append('Content-Disposition: form-data; name="{0}"'.format(key))
            L.append('')
            L.append(value)
        for (key, filename, value) in files:
            L.append('--' + BOUNDARY)
            L.append('Content-Disposition: form-data; name="{0}"; filename="{1}"'.format(key, filename))
            L.append('Content-Type: {0}'.format(mimetypes.guess_type(filename)[0] or 'application/octet-stream'))
            L.append('Content-Transfer-Encoding: binary')
            L.append('')
            L.append(value)
        L.append('--' + BOUNDARY + '--')
        L.append('')
        body = CRLF.join(L)
        content_type = 'multipart/form-data; boundary={0}'.format(BOUNDARY)
        return content_type, body

    def generate_oauth_params(self) -> dict:
        """
        Generates the oauth parameters needed for multipart/form requests
        :returns: a dictionary of the proper headers that can be used
                  in the request
        """
        params = {
            'oauth_version': "1.0",
            'oauth_nonce': sha1(str(random()).encode('ascii')).hexdigest(),
            'oauth_timestamp': int(time.time()),
            'oauth_token': self.oauth_token,
            'oauth_consumer_key': self.consumer_key
        }
        return params
