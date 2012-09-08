import httplib
import xml.etree.ElementTree as ET
import json
from bs4 import BeautifulSoup
import urlparse
import urllib
from datetime import datetime
import http
import db
import err

android_host_https = 'play.google.com'
android_conn_https = http.get_conn_https(android_host_https)
android_headers_https = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain", "Accept-Language": "en-UK"}
android_root = 'store/apps'
android_categories = 'category/APPLICATION'
def android_https_get(url):
    global android_conn_https
    status, body, android_conn_https = http.use_httplib_https(url, 'GET', '', android_conn_https, android_host_https, android_headers_https)
    return status, body
def android_https_post(url, url_body):
    global android_conn_https
    status, body, android_conn_https = http.use_httplib_https(url, 'POST', url_body, android_conn_https, android_host_https, android_headers_https)
    print status, body
    return status, body

####################
def categories_read_main():
    global android_conn
    url = '/%s/%s'%(android_root, android_categories)
    print '** categories main %s **'%(url)
    status, body = android_https_get(url)
    if status != 200:
        raise Exception('app home https connection error: %s'%(str(status)))
    soup = BeautifulSoup(body)
    divs = soup.body.find_all(name='div', attrs={'class':'padded-content3 app-home-nav'})
    for div in divs:
        if len(div.contents) != 2:
            raise Exception('app home nav length != 2')
        h2 = div.contents[0]
        cate_group_name = h2.text.strip()
        ul = div.contents[1]
        lis = ul.find_all(name='li', attrs={'class':'category-item'})
        if len(lis) <= 0:
            raise Exception('app home nav li length <= 0')
        for li in lis:
            a = li.a
            if a == None:
                raise Exception('app home nav li a == None')
            if not a.has_key('href'):
                raise Exception('app home nav li a href has not href')
            cate_path = urlparse.urlparse(a['href']).path.strip()
            cate_name = a.text.strip()
            db.db_execute_g(db.sql_cate_insert, (cate_group_name, cate_name, cate_path, str(datetime.now())))
            cate_i = 0
            while cate_i < 504:
                db.db_execute_g(db.sql_cate_read_insert, (cate_name, cate_path, cate_i, 'topselling_free'))
                db.db_execute_g(db.sql_cate_read_insert, (cate_name, cate_path, cate_i, 'topselling_paid'))
                cate_i = cate_i + 24

def category_read_main():
    rows = db.db_get_g(db.sql_cate_read_get, ())
    for row in rows:
        cate_name = row[0]
        cate_path = row[1]
        cate_param = row[2]
        cate_type = row[3]
        try:
            category_read(cate_path, cate_name, cate_type, cate_param)
            db.db_execute_g(db.sql_cate_read_update, (cate_name, cate_path, cate_param, cate_type, ))
        except Exception as e:
            err.except_p(e)
            

def category_read(cate_path, cate_name, cate_type, cate_start):
    url = '%s/collection/%s?start=%s&num=24'%(cate_path, cate_type, cate_start)
    print '** category %s **'%(url)
    status, body = android_https_get(url)
    if status != 200:
        raise Exception('app category https connection error')
    soup = BeautifulSoup(body)
    divs = soup.find_all(name='div', attrs={'class':'snippet snippet-medium'})
    for div in divs:
        rank_divs = div.find_all(name='div', attrs={'class':'ordinal-value'})
        if len(rank_divs) != 1:
            raise Exception('category div ordinal-value len != 1')
        rank = rank_divs[0].text.strip()
        href_as = div.find_all(name='a', attrs={'class':'title'})
        if len(href_as) != 1:
            raise Exception('category div a href len != 1')
        if not href_as[0].has_key('href'):
            raise Exception('category div a href is empty')
        href = href_as[0]['href']
        href = urlparse.urlparse(href)
        href_qs = urlparse.parse_qs(href.query)
        href_path = href.path
        href_id = None
        if href_qs.has_key('id') and len(href_qs['id']) > 0:
            href_id = href_qs['id'][0]
        if href_id == None:
            raise Exception('category div a href urlparse wrong')
        app_id = href_id.strip()
        db.db_execute_g(db.sql_app_insert_with_rank, (app_id, rank))
    

def app_read_main():
    rows = db.db_get_g(db.sql_app_read_get, ())
    for row in rows:
        app_id = row[0]
        app_read(app_id)

def app_read(app_id):
    url = '/%s/details?id=%s'%(android_root, app_id)
    print '** app %s **'%(url)
    try:
        status, body = android_https_get(url)
        if status != 200:
            raise Exception('app read https connection error: %s'%(str(status)))
        soup = BeautifulSoup(body)
        app_read_banner(app_id, soup)
        app_read_tab_overview(app_id, soup)
        app_read_tab_review(app_id, soup)
        app_read_tab_permission(app_id, soup)
    except Exception as e:
        err.except_p(e)


def app_read_banner(app_id, soup):
    banner_title = ''
    banner_developer_href = ''
    banner_developer_name = ''
    banner_icon_src = ''
    rating_figure = ''
    raters = ''
    price = ''
    banner_title_fa = soup.find_all(name='td', attrs={'class':'doc-banner-title-container'})
    if len(banner_title_fa) == 1:
        banner_title_f = banner_title_fa[0]
        if banner_title_f.h1 != None:
            banner_title = banner_title_f.h1.text
        if banner_title_f.a != None:
            if banner_title_f.a.has_key('href'):
                banner_developer_href = banner_title_f.a['href'].strip()
            if banner_title_f.a.text != None:
                banner_developer_name = banner_title_f.a.text.strip()
    banner_icon_fa = soup.find_all(name='div', attrs={'class':'doc-banner-icon'})
    for banner_icon in banner_icon_fa:
        if banner_icon.img != None:
            if banner_icon.img.has_key('src'):
                banner_icon_src = banner_icon.img['src'].strip()
    banner_annotation_fa = soup.find_all(name='div', attrs={'class':'badges-badge-title goog-inline-block'})
    for banner_annotation in banner_annotation_fa:
        banner_annotation_text = banner_annotation.text.strip()
        db.db_execute_g(db.sql_app_awards_insert, (app_id, banner_annotation_text))
    rating_price_fa = soup.find_all(name='td', attrs={'class':'doc-details-ratings-price'})
    if len(rating_price_fa) == 1:
        rating_fa = rating_price_fa[0].find_all(name='div', attrs={'class':'ratings goog-inline-block'})
        for rating_f in rating_fa:
            if rating_f.has_key('title'):
                rating_title = rating_f['title']
                rating_figure = rating_title.split(' ')
                if len(rating_figure) >= 2:
                    rating_figure = rating_figure[1].strip()
            if rating_f.next_sibling != None:
                raters_f = rating_f.next_sibling
                if raters_f.text != None:
                    raters = raters_f.text
                    raters = raters.replace('(', '').replace(')', '').strip()
        price_fa = rating_price_fa[0].find_all(name='span', attrs={'class':'buy-button-price'})
        for price_f in price_fa:
            price = price_f.text
            price = price.upper().replace('BUY', '').strip()
    db.db_execute_g(db.sql_app_banner_update, (banner_title, banner_icon_src, banner_developer_name, banner_developer_href, rating_figure, raters, price, app_id))
        

def app_read_tab_overview(app_id, soup):
    app_read_metadata(app_id, soup)
    app_read_overview(app_id, soup)
    app_read_screenshot(app_id, soup)
    app_read_video(app_id, soup)


def app_read_metadata(app_id, soup):
    meta_update = ''
    meta_current = ''
    meta_require = ''
    meta_install = ''
    meta_size = ''
    meta_category = ''
    meta_rating = ''
    metadata_fa = soup.find_all(name='div', attrs={'class':'doc-metadata'})
    for metadata_f in metadata_fa:
        meta_google_plus_fa = metadata_f.find_all(name='div', attrs={'class':'plus-share-container'})
        for meta_google_plus_f in meta_google_plus_fa:
            if len(meta_google_plus_f.contents)>0 and meta_google_plus_f.contents[0].has_key('href'):
                meta_google_plus_href = meta_google_plus_f.contents[0]['href'].strip()
                db.db_execute_g(db.sql_app_google_plus_insert, (app_id, meta_google_plus_href))
        meta_update_fa = metadata_f.find_all(name='dt', text='Updated:')
        if len(meta_update_fa) > 0 and meta_update_fa[0].next_sibling != None:
            meta_update_f = meta_update_fa[0].next_sibling
            if meta_update_f.time != None:
                meta_update = meta_update_f.time.text.strip()
        meta_current_fa = metadata_f.find_all(name='dt', text='Current Version:')
        if len(meta_current_fa) > 0 and meta_current_fa[0].next_sibling != None:
            meta_current_f = meta_current_fa[0].next_sibling
            meta_current = meta_current_f.text.strip()
        meta_require_fa = metadata_f.find_all(name='dt', text='Requires Android:')
        if len(meta_require_fa) > 0 and meta_require_fa[0].next_sibling != None:
            meta_require_f = meta_require_fa[0].next_sibling
            meta_require = meta_require_f.text.strip()
        meta_category_fa = metadata_f.find_all(name='dt', text='Category:')
        if len(meta_category_fa) > 0 and meta_category_fa[0].next_sibling != None:
            meta_category_f = meta_category_fa[0].next_sibling
            meta_category = meta_category_f.text.strip()
        meta_install_fa = metadata_f.find_all(name='dt', text='Installs:')
        if len(meta_install_fa) > 0 and meta_install_fa[0].next_sibling != None:
            meta_install_f = meta_install_fa[0].next_sibling
            meta_install = meta_install_f.text
            meta_install = meta_install.upper().replace('LAST 30 DAYS', '').strip()
        meta_size_fa = metadata_f.find_all(name='dt', text='Size:')
        if len(meta_size_fa) > 0 and meta_size_fa[0].next_sibling != None:
            meta_size_f = meta_size_fa[0].next_sibling
            meta_size = meta_size_f.text.strip()
        meta_rating_fa = metadata_f.find_all(name='dt', text='Content Rating:')
        if len(meta_rating_fa) > 0 and meta_rating_fa[0].next_sibling != None:
            meta_rating_f = meta_rating_fa[0].next_sibling
            meta_rating = meta_rating_f.text.strip()
    db.db_execute_g(db.sql_app_metadata_update, (meta_update, meta_current, meta_require, meta_install, meta_size, meta_category, meta_rating, app_id))
    

def app_read_overview(app_id, soup):
    desc = ''
    developer_website = ''
    developer_email = ''
    developer_privacy = ''
    overview_fa = soup.find_all(name='div', attrs={'class':'doc-overview'})
    for overview_f in overview_fa:
        desc_fa = overview_f.find_all(name='div', attrs={'id':'doc-original-text'})
        for desc_f in desc_fa:
            desc = desc_f.text.strip()
        developer_website_fa = overview_f.find_all(name='a', text="Visit Developer's Website")
        for developer_website_f in developer_website_fa:
            if developer_website_f.has_key('href'):
                developer_website = developer_website_f['href'].strip()
        developer_email_fa = overview_f.find_all(name='a', text='Email Developer')
        for developer_email_f in developer_email_fa:
            if developer_email_f.has_key('href'):
                developer_email = developer_email_f['href']
                developer_email = developer_email.replace('mailto:', '').strip()
        developer_privacy_fa = overview_f.find_all(name='a', text='Privacy Policy')
        for developer_privacy_f in developer_privacy_fa:
            if developer_privacy_f.has_key('href'):
                developer_privacy = developer_privacy_f['href'].strip()
    db.db_execute_g(db.sql_app_overview_update, (desc, developer_website, developer_email, developer_privacy, app_id))

def app_read_screenshot(app_id, soup):
    screenshots_fa = soup.find_all(name='div', attrs={'class':'doc-overview-screenshots'})
    for screenshots_f in screenshots_fa:
        screenshot_fa = screenshots_f.find_all(name='img', attrs={'itemprop':'screenshots'})
        for screenshot_f in screenshot_fa:
            if screenshot_f.has_key('src'):
                screenshot = screenshot_f['src'].strip()
                db.db_execute_g(db.sql_app_screenshot_insert, (app_id, screenshot))

def app_read_video(app_id, soup):
    videos_fa = soup.find_all(name='div', attrs={'class':'doc-overview-videos'})
    for videos_f in videos_fa:
        video_fa = videos_f.find_all(name='param', attrs={'name':'movie'})
        for video_f in video_fa:
            if video_f.has_key('value'):
                video = video_f['value'].strip()
                db.db_execute_g(db.sql_app_video_insert, (app_id, video))

def app_read_tab_review(app_id, soup): ## needs to work out
    rating_0 = ''
    rating_1 = ''
    rating_2 = ''
    rating_3 = ''
    rating_4 = ''
    rating_5 = ''
    tab_review = soup.find_all(name='div', attrs={'class':'doc-reviews padded-content2'})
    if len(tab_review) <= 0:
        raise Exception('app tab review len <= 0')
    tab_review = tab_review[0]
    review_head_fa = tab_review.find_all(name='div', attrs={'class':'reviews-heading-container'})
    for review_head_f in review_head_fa:
        user_rating_fa = review_head_f.find_all(name='div', attrs={'class':'user-ratings'})
        if len(user_rating_fa) <= 0:
            raise Exception('app tab review user rating len <= 0')
        user_rating_fa = user_rating_fa[0]
        rating_tr_fa = user_rating_fa.find_all(name='span', attrs={'class':'histogram-label'})
        for rating_tr_f in rating_tr_fa:
            rating_star = rating_figure = 'None'
            if rating_tr_f.has_key('data-rating'):
                rating_star = rating_tr_f['data-rating'].strip()
            if rating_tr_f.parent != None and rating_tr_f.parent.next_sibling != None:
                rating_figure = rating_tr_f.parent.next_sibling
                rating_figure = rating_figure.text.strip()
            if rating_star == '0':
                rating_0 = rating_figure
            if rating_star == '1':
                rating_1 = rating_figure
            if rating_star == '2':
                rating_2 = rating_figure
            if rating_star == '3':
                rating_3 = rating_figure
            if rating_star == '4':
                rating_4 = rating_figure
            if rating_star == '5':
                rating_5 = rating_figure
    db.db_execute_g(db.sql_app_rating_update, (rating_0, rating_1, rating_2, rating_3, rating_4, rating_5, app_id))

def app_read_tab_permission(app_id, soup):
    perm_group_title = ''
    tab_permissions_fa = soup.find_all(name='div', attrs={'class':'doc-specs padded-content2'})
    if len(tab_permissions_fa) <= 0:
        raise Exception('app tab permission len <= 0')
    tab_permissions_fa = tab_permissions_fa[0]
    perm_fa = tab_permissions_fa.find_all(name='li', attrs={'class':'doc-permission-group'})
    for perm_f in perm_fa:
        for pc in perm_f.contents:
            if pc.has_key('class'):
                pcc = pc['class']
                if 'doc-permission-group-title' in pcc:
                    perm_group_title = pc.text.strip()
                if 'doc-permission-description' in pcc:
                    perm_each_desc = pc.text.strip()
                    db.db_execute_g(db.sql_app_perm_insert, (app_id, perm_group_title, perm_each_desc))



######



### read review:     #db.db_execute_g(db.sql_app_review_ in ajax

import urllib2
import urllib
import json
def post(url, data):
    data = urllib.urlencode(data)
    req = urllib2.Request(url=url, data=data)
    f = urllib2.urlopen(req)
    b = f.read()
    b = b.replace(")]}'", '')
    #print b
    j = json.loads(b)
    print json.dumps(j, indent=2)
def post_t():
    url = 'https://play.google.com/store/getreviews'
    data = {
        'id':'com.bfs.ninjump', #'com.rovio.angrybirds', #'com.tencent.mm',
        'reviewSortOrder':'0',
        'reviewType':'1',
        'pageNum':'40', # 450 is the max number i can get
        }
    post(url, data)
    
def http_post(host, url, params, headers):
    conn = httplib.HTTPSConnection(host=host)
    conn.request(method='POST', url=url, body=params, headers=headers)
    resp = conn.getresponse()
    status = resp.status
    body = resp.read()
    print status
    print body

def post_test():
    url = '/store/getreviews'
    params = {
        'id':'com.bfs.ninjump', #'com.rovio.angrybirds', #'com.tencent.mm',
        'reviewSortOrder':'0',
        'reviewType':'1',
        'pageNum':'40', # 450 is the max number i can get
        }
    params = urllib.urlencode(params)
    print params
    android_https_post(url, params)


if __name__ == '__main__':
    db.db_init()
    #categories_read_main()
    #category_read_main()
    app_read_main()
    #a = httplib.HTTPSConnection('')
    '''
    url = 'https://play.google.com/store/getreviews'
    data = {
        'id':'com.bfs.ninjump', #'com.rovio.angrybirds', #'com.tencent.mm',
        'reviewSortOrder':'0',
        'reviewType':'1',
        'pageNum':'450', # 450 is the max number i can get
        }
    post(url, data)
    print "+++++++++++++++++++++"
    '''
    '''
    url = '/store/apps/category/ARCADE/collection/topselling_paid'
    params = {
        'start':'24',
        'num':'24',
        }
    params = urllib.urlencode(params)
    http_post(host, url, params, headers)
    print "+++++++++++++++++++++"
    url = 'https://play.google.com/store/apps/category/ARCADE/collection/topselling_paid'
    params = {
        'start':'24',
        'num':'24',
        }
    post(url, params)
    '''


            #category_read(cate_path, cate_name)
            #break
        #break


'''
    cate_type = 'topselling_free'
    category_read_base(cate_path, cate_name, cate_type)
    cate_type = 'topselling_paid'
    category_read_base(cate_path, cate_name, cate_type)
'''
'''
def category_read_base(cate_path, cate_name, cate_type):
    cate_start = 0
    i = 0
    status = 200
    while status != 403:
         status, cate_current = category_read_loop(cate_path, cate_name, cate_type, cate_start)
         #print status, cate_start, cate_current
         i = i + 1
         cate_start = cate_start + 24
         break
    print status, cate_start, cate_current, cate_path
'''


# google plus share
'https://plusone.google.com/u/0/_/+1/fastbutton?url=https%3A%2F%2Fmarket.android.com%2Fdetails%3Fid%3Dcom.rovio.angrybirds'


    #review_content_fa = tab_review.find_all(name='div', attrs={'class':'doc-user-reviews-list'})
    #review_content_fa = tab_review.find_all(name='div', attrs={'class':'doc-user-reviews-page num-pagination-page'})
    #review_content_fa = tab_review.find_all(name='div', attrs={'class':'doc-reviews-container'})
    #for review_content_f in review_content_fa:
        #print review_content_f.prettify()
    #    print '=========='
    ############# how to get review all out? need to look at the javascript 
