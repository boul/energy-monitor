import urllib2
import json
import logging
import socket
__author__ = 'rkuipers'


# Super this because the logger returns non-standard digest header: x-Digest
class MyHTTPDigestAuthHandler(urllib2.HTTPDigestAuthHandler):

    def retry_http_digest_auth(self, req, auth):
        token, challenge = auth.split(' ', 1)
        chal = urllib2.parse_keqv_list(urllib2.parse_http_list(challenge))
        auth = self.get_authorization(req, chal)
        if auth:

            auth_val = 'X-Digest %s' % auth
            if req.headers.get(self.auth_header, None) == auth_val:
                return None
            req.add_unredirected_header(self.auth_header, auth_val)
            resp = self.parent.open(req, timeout=req.timeout)
            return resp

    def http_error_auth_reqed(self, auth_header, host, req, headers):
        authreq = headers.get(auth_header, None)
        if self.retried > 5:
            # Don't fail endlessly - if we failed once, we'll probably
            # fail a second time. Hm. Unless the Password Manager is
            # prompting for the information. Crap. This isn't great
            # but it's better than the current 'repeat until recursion
            # depth exceeded' approach <wink>
            raise urllib2.HTTPError(req.get_full_url(), 401,
                                    "digest auth failed",
                                    headers, None)
        else:
            self.retried += 1
        if authreq:
            scheme = authreq.split()[0]
            if scheme.lower() == 'x-digest':
                return self.retry_http_digest_auth(req, authreq)


class Vsn300Reader():

    def __init__(self, host, user, password, inverter_id, simulate=False):
        
        self.host = host
        self.user = user
        self.password = password
        self.realm = 'registered_user@power-one.com'
        self.inverter_id = inverter_id
        self.simulate = simulate

        self.logger = logging.getLogger(__name__)

    def get_last_stats(self):
        url = "http://" + self.host + "/v1/feeds/"

        passman = urllib2.HTTPPasswordMgr()
        passman.add_password(self.realm, url, self.user, self.password)
        handler = MyHTTPDigestAuthHandler(passman)
        device_path = "ser4:" + self.inverter_id
        stats = dict()

        self.logger.info("Getting VSN300 stats from: {0}".format(url))

        if self.simulate:
            self.logger.warning("RUNNING IN SIMULATION MODE!!!")
            parsed_json = json.loads(open('vsn300.json').read())
        else:

            try:
                opener = urllib2.build_opener(handler)
                urllib2.install_opener(opener)
                json_response = urllib2.urlopen(url, timeout=10)
                parsed_json = json.load(json_response)
            except Exception as e:
                self.logger.error(e)
                return

        path = parsed_json['feeds'][device_path]['datastreams']

        for k, v in path.iteritems():

                self.logger.info(
                    str(k) + " - " + str(v['description']) + " - " +
                    str(v['data'][9]['value']))

                stats[k] = v['data'][9]['value']

        self.logger.debug(stats)

        return stats
