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
            collections:str,
            send_email:bool=False):
        """
        Create a new ticket for a source
        #NB: source_article should be preferred when generating issues
        # rather than proliferating tickets, keep successive updates in the same ticket
        # at least for now
        """
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
            },
            "send_email":send_email
        }

        response = self.client.ticket.create(params=params)
        return response

    def source_article(self, 
            article_message:str,
            article_title:str,
            source_id:int,
            collections:str,
            send_email:bool=False,
            state="open"
            ):

        #Get the id of the exiting ticket for this source:
        ticket_page = self.client.ticket.search(f"source:{source_id}")
        if len(ticket_page) == 0:
            #If there aint no ticket, make one
            return self.source_ticket(
                article_message,
                article_title,
                source_id,
                collections,
                send_email
                )

        ticket_id = ticket_page[0]['id']

        params = {
            "collections":collections, 
            "article": {
                "subject": article_title,
                "body": article_message,
                "type": "note",
                "content_type":"text/html",
                "internal": False
            },
            "state":state, #Always open tickets when adding issues
            "send_email":send_email
        }
        return self.client.ticket.update(id=ticket_id, params=params)


    #The only real difference would be the hard-coded tags, so maybe this is redundant?
    #Gotta demonstrate how the tags thing work still anyway. 
    def collection_ticket(self,
        article_message:str,
        ticket_title:str,
        collection_id:int,
        send_email:bool=False):
        pass

