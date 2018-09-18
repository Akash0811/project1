from string import Template
import oauth2 as oauth
import urllib.parse
import urllib
import time
import xml.dom.minidom
import sys, getopt
import requests

url = 'http://www.goodreads.com'

target_list = 'holding'

auth={
"KEY": "v3M2y9O0fY6so6oqGoF4pA",
"SECRET": "C0sDvX8UAZFOVVq2tRwHcJO4o8WriTMoEbvjE4IV5A"
}

consumer = oauth.Consumer(key=auth["KEY"],
                          secret=auth["SECRET"])

token = oauth.Token('oauth token key',
                    'oauth token secret')

client = oauth.Client(consumer, token)

def getUserId():
    response, content = client.request('%s/api/auth_user' % url,'GET')
    if response['status'] != '200':
        raise Exception('Cannot fetch resource: %s' % response['status'])
#    else:
#        print 'User loaded.'

    userxml = xml.dom.minidom.parseString(content)
    user_id = userxml.getElementsByTagName('user')[0].attributes['id'].value
    return str(user_id)
res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": auth["KEY"], "isbns": "1416949658"})
x = res.json()
print(x["books"][0]["id"])
