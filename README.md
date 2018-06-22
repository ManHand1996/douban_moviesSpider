#### 使用Python3.5多线程 + Redis + Tor代理爬取豆瓣电影  
> Tor安装配置和转换http代理 [参考](http://www.manhand.top/15/article_detail)


- 获取tag,countries,genres 的组合作为请求API的参数 https://movie.douban.com/tag  

- 找到电影信息请求的API：https://movie.douban.com/j/new_search_subjects  
```
params={'sort':'T','range':'0,10'
      'tags':'',countries:'',genres:''
}
```

- 返回json格式数据内容：  
```
{
  "directors":["弗兰克·德拉邦特"],
  "rate":"9.6",
  "cover_x":2000,
  "star":"50",
  "title":"肖申克的救赎",
  "url":"https:\/\/movie.douban.com\/subject\/1292052\/",
  "casts":["蒂姆·罗宾斯","摩根·弗里曼","鲍勃·冈顿","威廉姆·赛德勒","克兰西·布朗"],
  "cover":"https://img3.doubanio.com\/view\/photo\/s_ratio_poster\/public\/p480747492.jpg",
  "id":"1292052",
  "cover_y":2963
}
```

若想获取完整电影数据可以根据返回的url进行爬取
