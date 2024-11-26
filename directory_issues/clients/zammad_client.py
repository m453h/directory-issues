from zammad_py import ZammadAPI
from zammad_py.api import Resource 
from pydantic_settings import BaseSettings


class ZammadConfig(BaseSettings):
    zammad_token:str =""
    zammad_url:str="https://support.mediacloud.org/api/v1/"
    default_zammad_group:str="Users"
    default_zammad_user:str="Directory Detective"
    default_zammad_email:str="support@mediacloud.org"

config = ZammadConfig()

class Tag(Resource):
    #Quick minimal extention to the zammad api
    path_attribute = "tags"

    def tag_ticket(self, ticket_id, tag):
       
        params = {
            "item" : tag,
            "o_id" : ticket_id,
            "object" : "Ticket",
        } 
        response = self._connection.session.post(self.url + "/add", params=params)
        return self._raise_or_return_json(response)


class ZammadClient():
    def __init__(self):
        
        self.client = ZammadAPI(
                url=config.zammad_url, 
                http_token=config.zammad_token)
        self.tag_client = Tag(connection=self.client)



    def new_ticket(self,
            article_message:str,  
            ticket_title:str,
            source_id:int,
            collections:str,
            send_email:bool=False,
            tags = []):
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
        for tag in tags:
            self.tag_client.tag_ticket(response["id"], tag)
        return response

    #Set option to close an article too?
    def source_article(self, 
            article_message:str,
            article_title:str,
            source_id:int,
            collections:str,
            send_email:bool=False,
            state="open"
            ):
        """
        Update a ticket for a source with a new article, and reopen it. 
        First find the ticket (create one if it doesn't exist yet)
        Then create the article
        
        """
        #Get the id of the exiting ticket for this source:
        ticket_page = self.client.ticket.search(f"source:{source_id}")

        if len(ticket_page) == 0:
            #If there aint no ticket, make one
            return self.new_ticket(
                article_message,
                article_title,
                source_id,
                collections,
                send_email,
                ["source"]
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

        response = self.client.ticket.update(id=ticket_id, params=params)
        return response


    def collection_article(self,
            article_message:str,
            ticket_title:str,
            collection_id:int,
            send_email:bool=False):
        #Close cousin of the source_article- but we are grabbing 
        pass

    def summary_ticket(self,
            summary_message,
            summary_title,
            send_email:bool=True):
        #Haven't fully defined the functionality here, but the basic idea is to have some tickets which just 
        #record that a batch action has taken place. Toggling email functionality so that we DO notify on this 
        #but DONT on the other actions is the unique challenge.  
        pass
