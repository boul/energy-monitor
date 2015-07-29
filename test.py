__author__ = 'rkuipers'

import urllib2



class myHTTPDigestAuthHandler(urllib2.HTTPDigestAuthHandler):

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
            raise urllib2.HTTPError(req.get_full_url(), 401, "digest auth failed",
                            headers, None)
        else:
            self.retried += 1
        if authreq:
            scheme = authreq.split()[0]
            if scheme.lower() == 'x-digest':
                return self.retry_http_digest_auth(req, authreq)


#Define Useful Variables

url = 'http://10.0.3.54/v1/feeds'
username = 'guest'
password = 'NIQ2y(iL'
realm = 'registered_user@power-one.com'

# Begin Making connection

# Create a Handler -- Also could be where the error lies
passman = urllib2.HTTPPasswordMgr()

passman.add_password(realm, url, username, password)

handler = myHTTPDigestAuthHandler(passman)
#handler.add_password(realm, url, username, password)

# Create an Opener

opener = urllib2.build_opener(handler,urllib2.HTTPHandler(debuglevel=1))
urllib2.install_opener(opener)
page_content = urllib2.urlopen(url)

print(page_content.read())


