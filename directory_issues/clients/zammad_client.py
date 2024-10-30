from zammad_py import ZammadAPI
from pydantic_settings import BaseSettings


class ZammadConfig(BaseSettings):
    zammad_token:str =""
    zammad_url:str="https://support.mediacloud.org/api/v1/"

config = ZammadConfig()

class ZammadClient():
    def __init__(self):
        self.client = ZammadAPI(
                url=config.zammad_url, 
                http_token=config.zammad_token)

    def source_ticket(self, source):
        ##Ideally we actually do a bunch of stuff here.
        ## Check if a ticket already exists, is it open, etc
        ## decide whether to append to it or otherwise. 
        ## Render out the content of the source
        ## make a ticket!
        pass
