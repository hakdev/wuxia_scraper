import asyncio
from playwright.async_api import async_playwright, Playwright,expect
import requests
from IPython.core.display import display, HTML
from bs4 import BeautifulSoup
display(HTML("<style>.container { width:100% !important; }</style>"))
from IPython.display import clear_output


class OpenAiAuto():
    chat_url = "https://chat.openai.com/chat"
    _session_token = None
    p=None
    browser = None
    context=None
    page=None
    _domain= ".chatgpt.com"
    _cookie_name = "__Secure-next-auth.session-token"
    
    _request_log=[]
    _converstaion_id=''
    _data_message_id=''
    
    def log_requests(self,i):
        try:
            if  'conversation' in i.url and i.method=='POST':
                self._request_log.append(i)
                post_data_json = i.post_data_json
                if None==i.post_data_json:
                    return                
                #if post_data_json is not None and 'conversation_id' in post_data_json:
                #    self._converstaion_id = post_data_json['conversation_id']
                #print('conversation',self._converstaion_id)
                if 'messages' in post_data_json:
                    messages = post_data_json['messages']
                    filt_messages=[i for i in messages if 'id' in i]
                    if len(filt_messages)>0:
                        self._data_message_id=filt_messages[-1]['id']
                        #print('data_message_id',self._data_message_id)
        except Exception as e:
            print("Exception occured",i)
            print(e)

    def __init__(self):
        print()
        
    @classmethod
    async def start(cls, session_token=None,converstaion_id=None):
        self = cls()
        self._session_token = session_token
        self._converstaion_id=converstaion_id
        #print("intialized",self._session_token)
        try:
            await self.login()
        except Exception as e:
            await self.stop()
            raise e
        return self
        
    async def set_session_token(self):
        #print(type(self._session_token),self._session_token)
        cookie = {"domain": OpenAiAuto._domain,"path": "/","name": OpenAiAuto._cookie_name,"value": self._session_token,"httpOnly": True,"secure": True,}
        await self.context.add_cookies([cookie])
        
    async def save_session_token(self):
        cookie_list = [i for i in await self.context.cookies() if i['name']==OpenAiAuto._cookie_name and i['domain']==OpenAiAuto._domain]
        if len(cookie_list)>0 and 'value' in cookie_list[-1]:
            self._session_token = cookie_list[-1]['value']
        
    async def check_login(self):
        login_buttons = await self.page.get_by_test_id('login-button').count()
        profile_buttons = await self.page.get_by_test_id('profile-button').count()
        if login_buttons==0 and profile_buttons==1:
            return True
        else:
            return False
        
    async def manual_login(self):
        await self.page.get_by_test_id('login-button').click()
        await expect(self.page.get_by_test_id('profile-button')).to_have_count(1,timeout=500000)
        
    async def stop(self):
        print("Stop called")
        if self.page is not None:
            await self.page.close()
            print("page closed")
            self.page = None
        if self.p is not None:
            await self.p.stop()
            print("playwright stopped")
            self.p = None
            
    async def state_session_check(self):
        if not await self.check_login():
            await self.login()
            
    def get_chat_url(self):
        if self._converstaion_id is None or self._converstaion_id=='':
            url= self.chat_url
        else:
            url= 'https://chatgpt.com/c/'+self._converstaion_id
        print("open url:"+url)
        return url
        
        
    async def login(self):
        await self.stop()
            
        self.p = await async_playwright().start()  
        self.browser = await self.p.firefox.launch(headless=False, devtools=True)
        self.context = await self.browser.new_context()
        #await p.stop()
        if self._session_token is not None:
            await self.set_session_token()
        
        self.page = await self.context.new_page()
        self.page.on("request", lambda request: self.log_requests(request))
        await self.page.goto(self.get_chat_url())
        await self.page.wait_for_load_state("networkidle")
        if not await self.check_login():
            await self.manual_login()
            await self.save_session_token()
        else:
            await self.save_session_token()
            
    async def show_output(self,show_question=False,show_all=False,clear_all=True):
        content = await self.page.content()
        soup = BeautifulSoup(content, 'html.parser')

        all_messages=[i for i in soup.select('div[data-message-id]')]

        limit_indx = -1 if show_all else len(all_messages)-2 if show_question else len(all_messages)-1
        if clear_all:
            clear_output(wait=True)

        for indx,message in enumerate(all_messages):
            if indx<limit_indx:
                continue
            [elem.extract() for elem in message.find_all('button')]
            display(HTML((message.decode_contents()+'<br/>')))
            if indx%2!=0:
                display(HTML(' <hr style="height:2px;border-width:0;color:red;background-color:red"> '))
            else:
                display(HTML(' <hr style="height:0.5px;border-width:0;color:gray;background-color:gray"> '))
        
    def set_conversation_id(self):
        if 'https://chatgpt.com/c/' in self.page.url and len(self.page.url)==58:
            self._converstaion_id = self.page.url[22:]

        
    async def send_message(self,msg,clear_all=True,show_question=False,show_all=False):
        await self.state_session_check()
        await self.page.locator("#prompt-textarea").fill(msg)
        await self.page.get_by_test_id("send-button").click()
        await self.page.wait_for_timeout(2000)
        await self.page.wait_for_load_state("networkidle")
        await expect(self.page.locator('div.result-streaming')).to_have_count(0,timeout=500000)
        self.set_conversation_id()
        await self.show_output(show_question,show_all,clear_all)



###
#await ai.stop()
# try:
#     save_session_id
#     if ai is not None:
#         print("Saving")
#         save_converstaion_id=ai._converstaion_id
#         save_session_id=ai._session_token
#         await ai.stop()
#     else:
#         save_converstaion_id=None
#         save_session_id=None
# except NameError:
#     save_converstaion_id=None
#     save_session_id=None
#     ai=None
# ai = await OpenAiAuto.start(save_session_id,save_converstaion_id)
# print(ai._converstaion_id)