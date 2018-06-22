from bs4 import BeautifulSoup
from selenium import webdriver
from threading import Thread
from stem import Signal
from stem.control import Controller
from http import cookiejar
import threading
import requests
import time
import json
import queue
import random
import os
import redis
import sched


USER_AGENTS = [
    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; \
        SV1; AcooBrowser; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Acoo Browser; \
        SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)",
    "Mozilla/4.0 (compatible; MSIE 7.0; AOL 9.5; AOLBuild 4337.35; \
        Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
    "Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)",
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64;\
        Trident/5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; \
        .NET CLR 2.0.50727; Media Center PC 6.0)",
    "Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; \
        WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; \
        .NET CLR 3.0.30729; .NET CLR 1.0.3705; .NET CLR 1.1.4322)",
    "Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.2; .NET CLR 1.1.4322;\
        .NET CLR 2.0.50727; InfoPath.2; .NET CLR 3.0.04506.30)",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN) AppleWebKit/523.15 \
        (KHTML, like Gecko, Safari/419.3) Arora/0.3 (Change: 287 c9dfb30)",
    "Mozilla/5.0 (X11; U; Linux; en-US) AppleWebKit/527+ (KHTML,\
        like Gecko, Safari/419.3) Arora/0.6",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.\
        2pre) Gecko/20070215 K-Ninja/2.1.1",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9)\
        Gecko/20080705 Firefox/3.0 Kapiko/3.0",
    "Mozilla/5.0 (X11; Linux i686; U;) Gecko/20070322 Kazehakase/0.4.5",
    "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.8) \
        Gecko Fedora/1.9.0.8-1.fc10 Kazehakase/0.5.6",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11\
        (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/535.20\
         (KHTML, like Gecko) Chrome/19.0.1036.7 Safari/535.20",
    "Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; fr) Presto/2.9.168 Version/11.52",
]    


class BlockCookie(cookiejar.CookiePolicy):
    # disable cookie
    return_ok = set_ok = lambda self, *args, ** kwargs : False
    domain_return_ok = path_return_ok = return_ok
    netscape = True
    rfc2965 = hide_cookie2 = False

class MovieThread(Thread):

    def __init__(self,threadpool,t_num):
        Thread.__init__(self)
        self.threadpool = threadpool
        self.t_num = t_num
        self.proxies = {'http':'http://127.0.0.1:8123'}
        self.params = {'sort':'T','range':'0,10'}
        self.headers = {
            'Accept':'text/html,application/xhtml+xml,\
                application/xml;q=0.9,*/*;q=0.8',
            'Accept-Encoding':'gzip, deflate, br',
            'Cache-Control':'max-age=0',
            'Connection':'keep-alive',
            'Host':'movie.douban.com',
            'User-Agent':"Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; \
                SV1; AcooBrowser; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
        }
        self.STOP = False
        self.DATA = []
        self.url = 'https://movie.douban.com/j/new_search_subjects'
    
    def run(self):
       
        self.__getTask()
        print('-----------'+self.params['genres']+'-----------')
        while True:
            
            self.headers['User-Agent'] = random.choice(USER_AGENTS)
            session = requests.Session()
            session.cookie.set_policy(BlockCookie())
            r = session.get(url=self.url,params=self.params,
                    headers=self.headers,proxies=self.proxies)
            datas = r.json()
            print("current thread :",self.t_num)
            print("GET {0} {1} {2} -> start {3}".format(
                self.params['tags'],self.params['genres'],
                self.params['countries'],self.params['start'])
            )

            if len(datas['data']) == 0:
                # write to redis
                self.__sortData()
                if not self.__getTask():
                    break
                else:
                    continue
            # Lock.acquire()
            if r.url.find('https://movie.douban.com/j/') == -1:
                break
            for data in datas['data']:
                data['genres'] = self.params['genres']
                data['tags'] = self.params['tags']
                data['countries'] = self.params['countries']
                self.DATA.append(data)
            time.sleep(0.5)
            self.__nextPage()
            # Lock.release()

    def __getTask(self):
        self.threadpool.changeTorIP()
        t_params = self.threadpool.nextTask()
        if not t_params:
            return t_params
        else:
            self.params.update(t_params)
            self.params['start'] = str(0)
            return 1
    
    def __nextPage(self):
        self.params['start'] = str(int(self.params['start'])+20)

    def __sortData(self):
        rdpool = self.threadpool.redis_pool
        rdc = redis.StrictRedis(connection_pool=rdpool)
        for data in self.DATA:
            rdc.lpush('movie:items',str(data))
        print('add data to redisDB ... finish')

    # def __getProxy(self):
    #     pass




class ThreadPool(object):

    def __init__(self,thread_max=4):
        self.task_queue = queue.Queue()
        self.thread_max = thread_max
        self.threads = []
        self.redis_pool = redis.ConnectionPool(host='127.0.0.1',
            port=6379,password='redispassword')
        self.proxies_pool = []

    
    def __initTaskQueue(self):
        with open('./task_queue.json','r') as out:
            params_list = json.load(out)
            for params in params_list[1:]:
                self.task_queue.put(params)

    def __init_threads(self,threadpool):
        
        for i in range(self.thread_max):
            self.threads.append(MovieThread(threadpool,i))
            print('create thread ',i)

    def start_thread(self,threadpool):
        self.__initTaskQueue()
        self.__init_threads(threadpool)
        
        for t in self.threads:
            t.start()

        for t in self.threads:
            t.join()

    def nextTask(self):
        try:
            params = self.task_queue.get(block=0)
            return params
        except Exception:
            return None

    def write_data(self):
        with open('./dataset.json','a') as out:
            for data in self.DATASET:
                json.dump(data,out,indent='\t')

    def changeTorIP(self):
    	# change tor identity but not really change IP addr
        with Controller.from_port(port=9051) as controller:
            controller.authenticate(password='manhand')
            # socks.setdefaultproxy(proxy_type=socks.PROXY_TYPE_SOCKS5,
            #     addr='127.0.0.1',port=9050)
            # socks.socket = socks.socksocket
            controller.signal(Signal.HUP) # NEWNYM
            controller.close()
        ip = requests.get('http://httpbin.org/ip',
            proxies={'http':'127.0.0.1:8123'})
        print('tor change identify {0}'.format(ip.text))

    # def getNewIP(self,url):
    #         parmas = {'num':str(self.thread_max+2)}
    #         proxies = requests.get(url,parmas).text.split("\r\n")
    #         for proxy in proxies:
    #             self.proxies_pool.append[proxy]

def combine_tags(url):
	# make a task_queue from https://movie.douban.com/tag
    browser = webdriver.PhantomJS()
    browser.get(url)
    result = browser.find_elements_by_css_selector(
        'div.tags ul.category li span.tag')
    tags_list = []
    genres_list = []
    countries_list = []
    catecories = []
    for r in result:
        catecories.append(r.text)
    tags_list = catecories[1:7]
    genres_list = catecories[8:29]
    countries_list = catecories[30:51]
    print('tags:',tags_list)
    print('genres:',genres_list)
    print('countries:',countries_list)
    combine_strs = []
    combine_list = []
    for tag in tags_list:
        for genres in genres_list:
            for country in countries_list:
                task = {}
                task['tags'] = tag
                task['genres'] = genres
                task['countries'] = country
                combine_list.append(task)
    
    # output thread task to json file
    with open('./task_queue.json','a') as f:
        json.load(combine_list,f)



# SCHEDULE = sched.scheduler(time.time, time.sleep)
# def timer_handle(sec):
#     SCHEDULE.enter(sec, random.randint(0,2), 
#         timer_handle, (sec,))
#     getNewIP()



if __name__ == '__main__':
    # combine_tags('https://movie.douban.com/tag/#/')  
    thread_pool = ThreadPool(thread_max=3)
    thread_pool.start_thread(thread_pool)
