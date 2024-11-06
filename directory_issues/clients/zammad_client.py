from zammad_py import ZammadAPI
from pydantic_settings import BaseSettings


class ZammadConfig(BaseSettings):
    zammad_token:str =""
    zammad_url:str="https://support.mediacloud.org/api/v1/"
    default_zammad_group:str="Users"
    default_zammad_user:str="Directory Detective"
    default_zammad_email:str="support@mediacloud.org"

config = ZammadConfig()

class ZammadClient():
    def __init__(self):
        print(config)
        self.client = ZammadAPI(
                url=config.zammad_url, 
                http_token=config.zammad_token)

    def source_ticket(self,
            article_message:str,  
            ticket_title:str,
            source_id:int,
            collections:list=[]):
        """
        Create a new ticket for a source
        """
        collections = ",".join(str(i) for i in collections)
        params = {
            "title": ticket_title,
            "group": config.default_zammad_group,
            "customer": config.default_zammad_email,
            "source": source_id,
            "collections":collections, 
            "article": {
                "subject": ticket_title,
                "body": article_message,
                "type": "note",
                "content_type":"text/html",
                "internal": False
            }
        }

        response = self.client.ticket.create(params=params)
        return response

    ##Ideally we actually do a bunch of stuff here.
    ## Check if a ticket already exists, is it open, etc
    ## decide whether to append to it or otherwise. 
    ## Render out the content of the source
    ## make a ticket!