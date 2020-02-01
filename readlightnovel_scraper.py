import requests
import bs4
import cloudscraper
import sys
from ebooklib import epub

index_url = "https://www.readlightnovel.org/my-death-flags-show-no-sign-of-ending/chapter-111"
index_list = []
book_name = "my death flags show no sign of ending"

def remove_script_tags(soup):
    [s.extract() for s in soup(['script','ins'])]
    return soup
    
    
def get_chapter_urls(scraper):
    res = scraper.get(index_url)
    soup = bs4.BeautifulSoup(res.text, 'html.parser')
    cont = soup.find_all('ul', class_='chapter-actions')[0].find_all('select')[0].find_all('option')
    #cont = soup.find_all('div', class_ ='col-lg-12')
    #print(cont[0].attrs,cont[0].contents)
    for c in cont:
        contents = c.contents[0]
        if not c['value'][:4]=='http':
            continue
        if c.contents[0][:1]=='\n':
            contents = c.contents[0][1:]
        index_list.append({'url':c['value'],'title':contents})
        

def get_chapter_content(scraper,indx):
    print(f"extracting : title= {index_list[indx]['title']} url = {index_list[indx]['url']}")
    cont = ''
    try:
        res = scraper.get(index_list[indx]['url'])
        soup = bs4.BeautifulSoup(res.text, 'html.parser')    
        cont = soup.find_all('div', class_='desc')[0].find_all('div',class_='hidden')
        #remove_script_tags(cont)
        return str(cont)
    except Exception as e:
        print(e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print(exc_type, exc_tb.tb_lineno)
    return '<div> error </div>'
    
def get_chapters(scraper):
    for indx in range(len(index_list)):
        index_list[indx]['content'] = get_chapter_content(scraper,indx)
    

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
    print(sys.argv)
    sys.setrecursionlimit(1000000)  
    scraper = cloudscraper.create_scraper() 
    get_chapter_urls(scraper)
    get_chapters(scraper)
    print('making epub')
    make_epub()