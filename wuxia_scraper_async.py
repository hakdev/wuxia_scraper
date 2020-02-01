import aiohttp
import asyncio
import ssl
import bs4
from ebooklib import epub
import requests
import sys

index_url = "https://m.wuxiaworld.co/The-Grandmaster-Strategist/all.html"
index_list = []
book_name = "The Grand Master Strategist"

def remove_script_tags(soup):
    [s.extract() for s in soup(['script','ins'])]
    return soup


def get_chapter_data(res):
    soup = bs4.BeautifulSoup(res, 'html.parser')
    return str(remove_script_tags(soup.find('div', id='chaptercontent')))
    
    
def get_chapter_urls():
    res = requests.get(index_url)
    soup = bs4.BeautifulSoup(res.text, 'html.parser')
    cont = soup.find_all('div', id='chapterlist')[0]
    for indx in cont.find_all('a'):
        if len(indx) == 0:
            continue
        if not indx['href'].endswith('.html'):
            continue
        index_list.append({'url':indx['href'],'title':indx.contents[0]})
        

def construct_url(first, last):
    return first + '/' + last 
    
 
def get_root_url():
    return index_url[:index_url.rfind('/')]
    
    
async def fetch(session, indx):
    url = construct_url(get_root_url(),index_list[indx]['url'])
    print(f"[{indx}] - started")
    async with session.get(url) as response:
        if response.status != 200:
            return
            #response.raise_for_status()
        chapter_html = await response.text()
        index_list[indx]['content'] = get_chapter_data(chapter_html)
        print(f"[{indx}] - ended")
        
    
async def fetch_all(session):
    tasks = []
    for i in range(len(index_list)):
        # task = asyncio.create_task(fetch(session,i))
        task = asyncio.ensure_future(fetch(session,i))
        tasks.append(task)
    await asyncio.gather(*tasks)
    
 
async def main():
    async with aiohttp.ClientSession() as session:
        await fetch_all(session)
        

def make_epub():
    book = epub.EpubBook()

    book.set_identifier('id1232132')
    book.set_title(book_name)
    book.set_language('en')

    book.add_author('x')

    book.toc = []
    book.spine =['nav']

    for indx in range(len(index_list)):
        xtitle= index_list[indx]['title']
        xfile_name=f'Chapter{indx+1}.xhtml'
        c1 = epub.EpubHtml(title=xtitle, file_name=xfile_name, lang='hr')
        c1.content=str(index_list[indx]['content'])
        book.add_item(c1)
        book.toc.append(epub.Link(xfile_name, xtitle, xtitle))
        book.spine.append(c1)

    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    style = 'BODY {color: white;}'
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    epub.write_epub(book_name + '.epub', book, {})
    
 
if __name__ == '__main__':
    if len(sys.argv) == 3:
        index_url = sys.argv[1]
        book_name = sys.argv[2]
    get_chapter_urls()
    #asyncio.run(main())
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(main())
    loop.run_until_complete(future)
    print('making epub')
    make_epub()