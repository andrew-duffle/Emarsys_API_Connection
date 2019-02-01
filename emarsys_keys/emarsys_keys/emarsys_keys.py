import base64
import datetime, time
import hashlib
import random
import requests
import pytz
from urllib.parse import urljoin

try:
    import simplejson as json
    assert json  # Silence potential warnings from static analysis tools
except ImportError:
    import json

import hashlib

print("Hello")


#API connection class. Conection keys are only valid for 5 minutes. Pass the endpoint and payload when called
class API_Connect:
    def makeKey(self,EP,PL):
        self.secret='[YOUR SECRECT GENERATED FROM THE PLATFORM]'
        self.EMARSYS_URI = 'https://api.emarsys.net/api/v2/'#'https://api.emarsys.net/'
        self.username='[YOUR PLATFORM USER NAME]'
        #self.endpoint= 'filter/12067/contacts/data?fields=3&offset=0&limit=800'   #'filter/12067/contacts'#'settings'   'contactlist/724031006/contacts/data?fields=3&offset=0&limit=10'


        self.t=datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
        self.tOffset=self.t+datetime.timedelta(hours=0)
        self.created=self.tOffset.isoformat()
        self.nonce=hashlib.md5(str(random.getrandbits(16)).encode('utf-8')).hexdigest() #might need to be 128
        self.password_digest=''.join((self.nonce,self.created,self.secret)).encode('utf-8')
        self.password_digest=hashlib.sha1(self.password_digest).hexdigest().encode('utf-8')
        self.password_digest=bytes.decode(base64.b64encode(self.password_digest))

        self.wsse_header = ','.join(
                (
                    'UsernameToken Username="{}"'.format(self.username),
                    'PasswordDigest="{}"'.format(self.password_digest),
                    'Nonce="{}"'.format(self.nonce),
                    'Created="{}"'.format(self.created),
                )
            )
        self.http_headers = {
                'X-WSSE': self.wsse_header,
                'Content-Type': 'application/json',
                #**other_http_headers,
            }

        self.url = urljoin(self.EMARSYS_URI, EP)

        self.payload = PL#"{\"key\":\"limit\",\"value\":\"1000\"}"

        return [self.url,self.payload,self.http_headers]

#-----------------------------------------------------------------------------------------
#Make request for users in the segment missing ID's. Check every 30 seconds for response
# try upto 10 times. Limit of 1000
Request_Variables= API_Connect().makeKey('filter/[ID OF THE SEGMENT YOU ARE LOOKING FOR]/contacts/data?fields=3&offset=0&limit=1000',{})
List_of_Users=[]
response=requests.request('GET',Request_Variables[0],data=Request_Variables[1] ,headers=Request_Variables[2])
json_data = json.loads(response.text)
List_of_Users=json_data["data"]

attempts=0

while (len(List_of_Users)==0) and (attempts<10):
    try:

        response=requests.request('GET',Request_Variables[0],data=Request_Variables[1] ,headers=Request_Variables[2])
        json_data = json.loads(response.text)
        List_of_Users=json_data["data"]
        attempts=attempts+1
        print("delay 30 seconds")
        time.sleep(30)

    except:
        pass


t=json.dumps(List_of_Users)
#List_of_Users
print("Got a list")
#-----------------------------------------------------------------------------------
#Make request for email addresses based on the ID's in the segment returned.

built_PL="{\"keyId\":\"id\",\"keyValues\":"+t+",\"fields\":[\"3\"]}"
Request_Variables= API_Connect().makeKey('contact/getdata',built_PL)
response=requests.request('POST',Request_Variables[0],data=Request_Variables[1],headers=Request_Variables[2])

json_data = json.loads(response.text)


em_ids=[]
email_to_hash=[]

for i in json_data['data']['result']:
    email_to_hash.append(i['3'])
    em_ids.append(int(i['id']))

#print(email_to_hash)

#json_data['data']['result']
#print(em_ids)
#--------------------------------------------------------------------
#create the sha256 hash for all the emails

hashes=[]

for email in email_to_hash:
    hashes.append(hashlib.sha256((''.join(email.split()).lower()).encode('utf-8')).hexdigest())
#----------------------------------------------------------------------
#Push back to emarsys based on ID and setting field 4554
#Not working
ids_hashes=[{'id': i, "[ID OF FIELD YOU ARE UPDATING]": h} for i,h in zip(em_ids,hashes)]
updates=json.dumps(ids_hashes)

#I get response 200 but i cant see where it posted on the customer record

built_PL="{\"key_id\":\"id\",\"contacts\":"+updates+"}"
Request_Variables= API_Connect().makeKey('contact',built_PL)
requests.request('PUT',Request_Variables[0],data=Request_Variables[1],headers=Request_Variables[2])

print(email_to_hash)
