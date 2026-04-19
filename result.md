(.venv) root@iZ2ze24zep7yf273as5m21Z:/opt/tripweaver/frontend# journalctl -u tripweaver-backend -n 200 --no-pager | grep -Ei "amap|infocode|invalid|forbidden|key|failed"
curl -s "https://restapi.amap.com/v3/place/text?keywords=酒店&city=北京&key=你的AMAP_API_KEY"
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   13. name=回味鸭血粉丝汤(汉中门大街店) | type=餐饮服务;中餐厅;特色/地方风味餐厅 | address=莫愁湖街道汉中门大街149号 | location=118.747508,32.03829
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   14. name=凤英特色包子(兆园店) | type=餐饮服务;餐饮相关场所;餐饮相关 | address=茶南商业街兆园85号(云锦路地铁站1号口步行480米) | location=118.748088,32.031124
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   15. name=方中山胡辣汤(南京汉中路店) | type=餐饮服务;中餐厅;中餐厅 | address=汉中门大街281-6号 | location=118.736975,32.039368
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   16. name=香河肉饼(明园社区店) | type=餐饮服务;餐饮相关场所;餐饮相关 | address=福园街明园91号 | location=118.745596,32.031289
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   17. name=麦当劳(建邺吾悦广场餐厅) | type=餐饮服务;快餐厅;麦当劳 | address=新城吾悦广场负一层B1001和B1002号商铺 | location=118.735862,32.038313
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   18. name=味真馄饨(兆园西小区店) | type=餐饮服务;中餐厅;特色/地方风味餐厅 | address=兆园44号13幢103室 | location=118.74859,32.031954
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   19. name=双冰面馆(明园社区店) | type=餐饮服务;中餐厅;中餐厅 | address=茶南仁园83号(云锦路地铁站1号口步行420米) | location=118.747799,32.031703
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   20. name=徐殿高包子铺 | type=餐饮服务;餐饮相关场所;餐饮相关 | address=福园街103号(云锦路地铁站1号口步行490米) | location=118.747843,32.030903
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP request -> text params={'keywords': '南京博物院 附近 早餐', 'city': '南京', 'citylimit': 'true', 'offset': 20, 'page': 1, 'extensions': 'all'}
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP response <- text ok status=1 keys=['suggestion', 'count', 'infocode', 'pois', 'status', 'info']
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] POI results -> keywords=南京博物院 附近 早餐 city=南京 count=20
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   1. name=金原鸭血粉丝汤(中山东路店) | type=餐饮服务;中餐厅;中餐厅 | address=中山东路与李府街交叉口西60米 | location=118.823603,32.038763
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   2. name=张府园包子店(李府街店) | type=餐饮服务;中餐厅;中餐厅 | address=李府街17-1号(明故宫地铁站1号口步行430米) | location=118.823935,32.038434
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   3. name=鸡鸣汤包(后宰门店) | type=餐饮服务;中餐厅;中餐厅 | address=后宰门街25号 | location=118.821078,32.045011
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   4. name=速美特大食堂(中山东路店) | type=餐饮服务;中餐厅;中餐厅 | address=中山东路532号(南京博物院对面) | location=118.823997,32.038499
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   5. name=氾水长鱼面 | type=餐饮服务;快餐厅;快餐厅 | address=后宰门街15-9号 | location=118.822884,32.044819
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   6. name=孙记大碗皮肚面(后宰门东村84号小区店) | type=餐饮服务;中餐厅;中餐厅 | address=后宰门街80号-1号 | location=118.820718,32.045263
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   7. name=鸡鸣汤包(紫金坊中山陵店) | type=餐饮服务;餐饮相关场所;餐饮相关 | address=中山门大街9号紫金文化广场南侧A05 | location=118.834355,32.040394
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   8. name=邱成宝汤包王·鸭血粉丝(后宰门街32号小区店) | type=餐饮服务;中餐厅;中餐厅 | address=后宰门街32号后宰门街32号小区 | location=118.821998,32.045225
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   9. name=张府园大碗面(后宰门店) | type=餐饮服务;中餐厅;中餐厅 | address=后宰门街25号 | location=118.820909,32.045018
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   10. name=肯德基(中山门店) | type=餐饮服务;快餐厅;肯德基 | address=中山门大街9号苜蓿园地铁站 | location=118.834772,32.04088
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   11. name=小李汤包馆(苜蓿新苑店) | type=餐饮服务;中餐厅;中餐厅 | address=苜蓿新苑苜蓿园东街26号院 | location=118.832795,32.037748
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   12. name=襄阳牛肉面(后宰门街店) | type=餐饮服务;中餐厅;中餐厅 | address=后宰门街36号 | location=118.820744,32.045271
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   13. name=徐州第一家羊肉汤凉皮擀面皮(后宰门街店) | type=餐饮服务;中餐厅;中餐厅 | address=梅园街道后宰门街15号-2 | location=118.822489,32.044888
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   14. name=张府园包子店(清溪路店) | type=餐饮服务;中餐厅;中餐厅 | address=后宰门街15号15-14 | location=118.822924,32.044648
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   15. name=高岗里小马牛肉面(后宰门创业一条街店) | type=餐饮服务;中餐厅;中餐厅 | address=后宰门西村20号-15号 | location=118.821162,32.047729
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   16. name=新新水饺店(后宰门创业一条街店) | type=餐饮服务;中餐厅;特色/地方风味餐厅 | address=梅园新村街道后宰门西村20号东8号(五十四中学旁) | location=118.821162,32.047787
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   17. name=哈尔滨水饺(后宰门店) | type=餐饮服务;中餐厅;特色/地方风味餐厅 | address=后宰门街29号(近交通银行) | location=118.820074,32.045072
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   18. name=金陵鸭血粉丝汤包 | type=餐饮服务;中餐厅;中餐厅 | address=中山东路与清溪路交叉口东40米 | location=118.822941,32.039214
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   19. name=陈永梅汤包(后宰门创业一条街店) | type=餐饮服务;中餐厅;中餐厅 | address=后宰门西村20-38号 | location=118.821023,32.048624
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   20. name=和善园(南京后宰门店) | type=餐饮服务;餐饮相关场所;餐饮相关 | address=后宰门街东村74-5 | location=118.821322,32.04814
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP request -> text params={'keywords': '南京博物院 早餐', 'city': '南京', 'citylimit': 'true', 'offset': 20, 'page': 1, 'extensions': 'all'}
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP response <- text ok status=1 keys=['suggestion', 'count', 'infocode', 'pois', 'status', 'info']
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] POI results -> keywords=南京博物院 早餐 city=南京 count=20
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   1. name=金原鸭血粉丝汤(中山东路店) | type=餐饮服务;中餐厅;中餐厅 | address=中山东路与李府街交叉口西60米 | location=118.823603,32.038763
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   2. name=鸡鸣汤包(后宰门店) | type=餐饮服务;中餐厅;中餐厅 | address=后宰门街25号 | location=118.821078,32.045011
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   3. name=鸿福星大碗皮肚面 | type=餐饮服务;中餐厅;中餐厅 | address=后宰门街32号后宰门街32号小区 | location=118.82227,32.045191
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   4. name=鸡鸣汤包(紫金坊中山陵店) | type=餐饮服务;餐饮相关场所;餐饮相关 | address=中山门大街9号紫金文化广场南侧A05 | location=118.834355,32.040394
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   5. name=孙记大碗皮肚面(后宰门东村84号小区店) | type=餐饮服务;中餐厅;中餐厅 | address=后宰门街80号-1号 | location=118.820718,32.045263
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   6. name=氾水长鱼面 | type=餐饮服务;快餐厅;快餐厅 | address=后宰门街15-9号 | location=118.822884,32.044819
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   7. name=张府园包子店(李府街店) | type=餐饮服务;中餐厅;中餐厅 | address=李府街17-1号(明故宫地铁站1号口步行430米) | location=118.823935,32.038434
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   8. name=肯德基(中山门店) | type=餐饮服务;快餐厅;肯德基 | address=中山门大街9号苜蓿园地铁站 | location=118.834772,32.04088
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   9. name=速美特大食堂(中山东路店) | type=餐饮服务;中餐厅;中餐厅 | address=中山东路532号(南京博物院对面) | location=118.823997,32.038499
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   10. name=蟹叁寳·蟹家宴·蟹黄捞面(南京中山陵店) | type=餐饮服务;餐饮相关场所;餐饮相关 | address=中山门大街9号紫金坊小门面A01、A02商铺 | location=118.834053,32.040328
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   11. name=小李汤包馆(苜蓿新苑店) | type=餐饮服务;中餐厅;中餐厅 | address=苜蓿新苑苜蓿园东街26号院 | location=118.832795,32.037748
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   12. name=长清面馆(李府街店) | type=餐饮服务;中餐厅;中餐厅 | address=李府街南工院·金蝶大学科技园 | location=118.823909,32.038214
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   13. name=邱成宝汤包王·鸭血粉丝(后宰门街32号小区店) | type=餐饮服务;中餐厅;中餐厅 | address=后宰门街32号后宰门街32号小区 | location=118.821998,32.045225
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   14. name=张府园大碗面(后宰门店) | type=餐饮服务;中餐厅;中餐厅 | address=后宰门街25号 | location=118.820909,32.045018
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   15. name=新新水饺店(后宰门创业一条街店) | type=餐饮服务;中餐厅;特色/地方风味餐厅 | address=梅园新村街道后宰门西村20号东8号(五十四中学旁) | location=118.821162,32.047787
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   16. name=高岗里小马牛肉面(后宰门创业一条街店) | type=餐饮服务;中餐厅;中餐厅 | address=后宰门西村20号-15号 | location=118.821162,32.047729
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   17. name=西安瓦罐面(后宰门店) | type=餐饮服务;中餐厅;中餐厅 | address=清溪路后宰门25号 | location=118.82092,32.045018
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   18. name=襄阳牛肉面(后宰门街店) | type=餐饮服务;中餐厅;中餐厅 | address=后宰门街36号 | location=118.820744,32.045271
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   19. name=陈永梅汤包(后宰门创业一条街店) | type=餐饮服务;中餐厅;中餐厅 | address=后宰门西村20-38号 | location=118.821023,32.048624
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   20. name=徐州第一家羊肉汤凉皮擀面皮(后宰门街店) | type=餐饮服务;中餐厅;中餐厅 | address=梅园街道后宰门街15号-2 | location=118.822489,32.044888
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP request -> text params={'keywords': '侵华日军南京大屠杀遇难同胞纪念馆 附近 午餐', 'city': '南京', 'citylimit': 'true', 'offset': 20, 'page': 1, 'extensions': 'all'}
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP response <- text failed info=CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] search_poi failed via HTTP: text: CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: Meal candidate query failed city=南京 meal_type=lunch query=侵华日军南京大屠杀遇难同胞纪念馆 附近 午餐 error=AMap search_poi failed via HTTP: text: CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP request -> text params={'keywords': '侵华日军南京大屠杀遇难同胞纪念馆 午餐', 'city': '南京', 'citylimit': 'true', 'offset': 20, 'page': 1, 'extensions': 'all'}
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP response <- text failed info=CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] search_poi failed via HTTP: text: CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: Meal candidate query failed city=南京 meal_type=lunch query=侵华日军南京大屠杀遇难同胞纪念馆 午餐 error=AMap search_poi failed via HTTP: text: CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP request -> text params={'keywords': '侵华日军南京大屠杀遇难同胞纪念馆 附近 中餐', 'city': '南京', 'citylimit': 'true', 'offset': 20, 'page': 1, 'extensions': 'all'}
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP response <- text failed info=CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] search_poi failed via HTTP: text: CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: Meal candidate query failed city=南京 meal_type=lunch query=侵华日军南京大屠杀遇难同胞纪念馆 附近 中餐 error=AMap search_poi failed via HTTP: text: CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP request -> text params={'keywords': '侵华日军南京大屠杀遇难同胞纪念馆 中餐', 'city': '南京', 'citylimit': 'true', 'offset': 20, 'page': 1, 'extensions': 'all'}
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP response <- text failed info=CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] search_poi failed via HTTP: text: CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: Meal candidate query failed city=南京 meal_type=lunch query=侵华日军南京大屠杀遇难同胞纪念馆 中餐 error=AMap search_poi failed via HTTP: text: CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP request -> text params={'keywords': '侵华日军南京大屠杀遇难同胞纪念馆 附近 简餐', 'city': '南京', 'citylimit': 'true', 'offset': 20, 'page': 1, 'extensions': 'all'}
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP response <- text failed info=CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] search_poi failed via HTTP: text: CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: Meal candidate query failed city=南京 meal_type=lunch query=侵华日军南京大屠杀遇难同胞纪念馆 附近 简餐 error=AMap search_poi failed via HTTP: text: CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP request -> text params={'keywords': '侵华日军南京大屠杀遇难同胞纪念馆 简餐', 'city': '南京', 'citylimit': 'true', 'offset': 20, 'page': 1, 'extensions': 'all'}
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP response <- text failed info=CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] search_poi failed via HTTP: text: CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: Meal candidate query failed city=南京 meal_type=lunch query=侵华日军南京大屠杀遇难同胞纪念馆 简餐 error=AMap search_poi failed via HTTP: text: CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP request -> text params={'keywords': '南京博物院 附近 午餐', 'city': '南京', 'citylimit': 'true', 'offset': 20, 'page': 1, 'extensions': 'all'}
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP response <- text failed info=CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] search_poi failed via HTTP: text: CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: Meal candidate query failed city=南京 meal_type=lunch query=南京博物院 附近 午餐 error=AMap search_poi failed via HTTP: text: CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP request -> text params={'keywords': '南京博物院 午餐', 'city': '南京', 'citylimit': 'true', 'offset': 20, 'page': 1, 'extensions': 'all'}
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP response <- text failed info=CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] search_poi failed via HTTP: text: CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: Meal candidate query failed city=南京 meal_type=lunch query=南京博物院 午餐 error=AMap search_poi failed via HTTP: text: CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:33 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP request -> text params={'keywords': '侵华日军南京大屠杀遇难同胞纪念馆 附近 晚餐', 'city': '南京', 'citylimit': 'true', 'offset': 20, 'page': 1, 'extensions': 'all'}
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP response <- text failed info=CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] search_poi failed via HTTP: text: CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: Meal candidate query failed city=南京 meal_type=dinner query=侵华日军南京大屠杀遇难同胞纪念馆 附近 晚餐 error=AMap search_poi failed via HTTP: text: CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP request -> text params={'keywords': '侵华日军南京大屠杀遇难同胞纪念馆 晚餐', 'city': '南京', 'citylimit': 'true', 'offset': 20, 'page': 1, 'extensions': 'all'}
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP response <- text ok status=1 keys=['suggestion', 'count', 'infocode', 'pois', 'status', 'info']
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] POI results -> keywords=侵华日军南京大屠杀遇难同胞纪念馆 晚餐 city=南京 count=5
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   1. name=南京古南都饭店 | type=住宿服务;宾馆酒店;五星级宾馆|餐饮服务;餐饮相关场所;餐饮相关 | address=广州路208号 | location=118.773523,32.051469
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   2. name=古南都饭店遂心遂意自助餐 | type=餐饮服务;外国餐厅;西餐厅(综合风味) | address=广州路208号古南都饭店1层(近五台山体育中心) | location=118.77345,32.051618
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   3. name=大成小火锅(南京环宇城店) | type=餐饮服务;中餐厅;火锅店 | address=清凉门大街1号南京环宇城负1层B113-2号 | location=118.752315,32.044437
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   4. name=鸭得堡石鼓路店 | type=餐饮服务;餐饮相关场所;餐饮相关 | address=石鼓路121号 | location=118.777643,32.040712
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   5. name=古南都饭店·那古野日本料理 | type=餐饮服务;外国餐厅;日本料理 | address=广州路208号南京古南都饭店4楼 | location=118.773434,32.051565
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP request -> text params={'keywords': '侵华日军南京大屠杀遇难同胞纪念馆 附近 本地菜', 'city': '南京', 'citylimit': 'true', 'offset': 20, 'page': 1, 'extensions': 'all'}
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP response <- text ok status=1 keys=['suggestion', 'count', 'infocode', 'pois', 'status', 'info']
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] POI results -> keywords=侵华日军南京大屠杀遇难同胞纪念馆 附近 本地菜 city=南京 count=20
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   1. name=艺味深尝(水西门大街店) | type=餐饮服务;中餐厅;中餐厅 | address=云锦路38号万达东坊7栋1层底商 | location=118.743818,32.033271
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   2. name=玲珑菜馆·南京菜 | type=餐饮服务;中餐厅;中餐厅 | address=湛江路牡丹里16-8号 | location=118.744021,32.039735
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   3. name=小厨娘臻选(云锦博物馆建邺吾悦店) | type=餐饮服务;中餐厅;中餐厅 | address=汉中门大街299号建业吾悦广场5楼 | location=118.735845,32.037628
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   4. name=宴南春(湖南菜馆) | type=餐饮服务;中餐厅;湖南菜(湘菜) | address=水西门大街362-1号 | location=118.748777,32.035077
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   5. name=富临轩私房菜(集庆门大街店) | type=餐饮服务;中餐厅;江苏菜 | address=集庆门大街188号(凤栖路侧) | location=118.744289,32.029281
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   6. name=Gulee古力丘食·烟火新疆菜 | type=餐饮服务;中餐厅;中餐厅 | address=江东中路68号1幢225-227室 | location=118.734903,32.036598
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   7. name=锅立方·开心牛蛙厂(河西直营店) | type=餐饮服务;中餐厅;中餐厅 | address=万达西地二街区214-6号 | location=118.736621,32.029567
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   8. name=薄利土菜馆(福园小区店) | type=餐饮服务;中餐厅;中餐厅 | address=茶南福园街71号 | location=118.747117,32.030782
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   9. name=吉记老七家湾牛肉锅贴 | type=餐饮服务;中餐厅;中餐厅 | address=兆园65号22幢102室 | location=118.7487,32.030605
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   10. name=张记龙虾(湖西街店) | type=餐饮服务;中餐厅;特色/地方风味餐厅|餐饮服务;中餐厅;火锅店 | address=莫愁湖街道湖西街1-5号(美高美大厦斜对面) | location=118.751862,32.032816
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   11. name=齐飞阁·私房菜(建业吾悦店) | type=餐饮服务;餐饮相关场所;餐饮相关 | address=吾悦广场悦街4楼406 | location=118.736567,32.03648
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   12. name=妈妈拿手菜 | type=餐饮服务;餐饮相关场所;餐饮相关 | address=凤凰西街307号 | location=118.744672,32.040856
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   13. name=小城味到·湘野菜(茶南店) | type=餐饮服务;中餐厅;湖南菜(湘菜) | address=福园街85号 | location=118.746681,32.03086
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   14. name=拿手菜·胖厨子 | type=餐饮服务;中餐厅;中餐厅 | address=湖西街14号 | location=118.750753,32.031146
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   15. name=福满锅东北铁锅炖(万达广场东坊店) | type=餐饮服务;中餐厅;东北菜 | address=云锦路70号 | location=118.743573,32.032151
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   16. name=喝断片玛陆弯东北烧烤(凤栖苑小区店) | type=餐饮服务;中餐厅;特色/地方风味餐厅 | address=云锦路75号之7号 | location=118.743847,32.030582
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   17. name=贰号院子(湛江路店) | type=餐饮服务;餐饮相关场所;餐饮相关 | address=云锦路牡丹里16-1号 | location=118.744066,32.039438
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   18. name=清真安乐园菜馆(茶南店) | type=餐饮服务;中餐厅;清真菜馆 | address=水西门大街拓园95号(近云锦路地铁站) | location=118.747764,32.033392
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   19. name=盆钵满东北地炉烤肉(云锦路店) | type=餐饮服务;餐饮相关场所;餐饮相关 | address=云锦路92-8号(集庆门大街地铁站1号口步行380米) | location=118.742891,32.029493
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP]   20. name=好记·金陵宴(建邺吾悦店) | type=餐饮服务;餐饮相关场所;餐饮相关 | address=汉中门大街299号吾悦广场5楼Z11号商铺 | location=118.73597,32.037663
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP request -> text params={'keywords': '侵华日军南京大屠杀遇难同胞纪念馆 本地菜', 'city': '南京', 'citylimit': 'true', 'offset': 20, 'page': 1, 'extensions': 'all'}
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP response <- text failed info=CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] search_poi failed via HTTP: text: CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: Meal candidate query failed city=南京 meal_type=dinner query=侵华日军南京大屠杀遇难同胞纪念馆 本地菜 error=AMap search_poi failed via HTTP: text: CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP request -> text params={'keywords': '侵华日军南京大屠杀遇难同胞纪念馆 附近 餐馆', 'city': '南京', 'citylimit': 'true', 'offset': 20, 'page': 1, 'extensions': 'all'}
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP response <- text failed info=CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] search_poi failed via HTTP: text: CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: Meal candidate query failed city=南京 meal_type=dinner query=侵华日军南京大屠杀遇难同胞纪念馆 附近 餐馆 error=AMap search_poi failed via HTTP: text: CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP request -> text params={'keywords': '侵华日军南京大屠杀遇难同胞纪念馆 餐馆', 'city': '南京', 'citylimit': 'true', 'offset': 20, 'page': 1, 'extensions': 'all'}
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP response <- text failed info=CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] search_poi failed via HTTP: text: CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: Meal candidate query failed city=南京 meal_type=dinner query=侵华日军南京大屠杀遇难同胞纪念馆 餐馆 error=AMap search_poi failed via HTTP: text: CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP request -> text params={'keywords': '南京博物院 附近 晚餐', 'city': '南京', 'citylimit': 'true', 'offset': 20, 'page': 1, 'extensions': 'all'}
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP response <- text failed info=CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] search_poi failed via HTTP: text: CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: Meal candidate query failed city=南京 meal_type=dinner query=南京博物院 附近 晚餐 error=AMap search_poi failed via HTTP: text: CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP request -> text params={'keywords': '南京博物院 晚餐', 'city': '南京', 'citylimit': 'true', 'offset': 20, 'page': 1, 'extensions': 'all'}
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP response <- text failed info=CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] search_poi failed via HTTP: text: CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:34 iZ2ze24zep7yf273as5m21Z python[10255]: Meal candidate query failed city=南京 meal_type=dinner query=南京博物院 晚餐 error=AMap search_poi failed via HTTP: text: CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:36 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP request -> detail params={'id': 'B001905N9D', 'extensions': 'all'}
Apr 19 21:41:36 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP response <- detail ok status=1 keys=['count', 'infocode', 'pois', 'status', 'info']
Apr 19 21:41:36 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] POI detail -> id=B001905N9D | name=侵华日军南京大屠杀遇难同胞纪念馆 | type=风景名胜;风景名胜;纪念馆 | address=水西门大街418号 | location=118.742372,32.035217
Apr 19 21:41:36 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP request -> detail params={'id': 'B001907TGR', 'extensions': 'all'}
Apr 19 21:41:36 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP response <- detail ok status=1 keys=['count', 'infocode', 'pois', 'status', 'info']
Apr 19 21:41:36 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] POI detail -> id=B001907TGR | name=南京博物院 | type=科教文化服务;博物馆;博物馆 | address=中山东路321号 | location=118.825064,32.040802
Apr 19 21:41:36 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP request -> detail params={'id': 'B0019135C5', 'extensions': 'all'}
Apr 19 21:41:36 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP response <- detail ok status=1 keys=['count', 'infocode', 'pois', 'status', 'info']
Apr 19 21:41:36 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] POI detail -> id=B0019135C5 | name=六朝博物馆 | type=科教文化服务;博物馆;博物馆 | address=长江路302号 | location=118.799124,32.042840
Apr 19 21:41:36 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP request -> geo params={'address': '水西门大街418号', 'city': '南京'}
Apr 19 21:41:36 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP response <- geo ok status=1 keys=['status', 'info', infocode', 'count', 'geocodes']
Apr 19 21:41:36 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP request -> geo params={'address': '中山东路321号', 'city': '南京'}
Apr 19 21:41:36 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP response <- geo ok status=1 keys=['status', 'info', infocode', 'count', 'geocodes']
Apr 19 21:41:36 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP request -> integrated params={'origin': '118.742868,32.035214', 'destination': '118.824899,32.040449', 'city': '南京', 'cityd': '南京', 'extensions': 'base'}
Apr 19 21:41:36 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP response <- integrated ok status=1 keys=['status', 'info', 'infocode', 'count', 'route']
Apr 19 21:41:36 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] Route result -> type=transit | origin=水西门大街418号 | destination=中山东路321号 | distance=8849.0 | duration=2393 | description=transit cost 3.0
Apr 19 21:41:36 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP request -> geo params={'address': '中山东路321号', 'city': '南京'}
Apr 19 21:41:36 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP response <- geo ok status=1 keys=['status', 'info', infocode', 'count', 'geocodes']
Apr 19 21:41:36 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP request -> geo params={'address': '长江路302号', 'city': '南京'}
Apr 19 21:41:36 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP response <- geo failed info=CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:36 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] plan_route[transit] failed via HTTP: geo: CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:36 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP request -> geo params={'address': '南京', 'city': '南京'}
Apr 19 21:41:36 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP response <- geo failed info=CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:36 iZ2ze24zep7yf273as5m21Z python[10255]: AMap city geocode failed for candidate=南京: geo: CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:36 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP request -> geo params={'address': '南京市', 'city': '南京市'}
Apr 19 21:41:36 iZ2ze24zep7yf273as5m21Z python[10255]: [AMAP] HTTP response <- geo failed info=CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:36 iZ2ze24zep7yf273as5m21Z python[10255]: AMap city geocode failed for candidate=南京市: geo: CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:36 iZ2ze24zep7yf273as5m21Z python[10255]: Trip history geocode failed: geo: CUQPS_HAS_EXCEEDED_THE_LIMIT
Apr 19 21:41:36 iZ2ze24zep7yf273as5m21Z python[10255]: [API] POST /api/trip/plan -> 200 body={"success":true,"message":"Trip plan generated successfully","data":{"city":"南京","start_date":"2026-04-19","end_date":"2026-04-19","days":[{"date":"2026-04-19","day_index":0,"description":"第 1 天围绕 南京 的核心点位展开，整体安排以顺路、舒适、便于衔接为主。","transportation":"Public Transit","transportation_detail":"当天以 Public Transit 为主，优先按景点顺路原则串联 侵华日军南京大屠杀遇难同胞纪念馆、南京博物院、六朝博物馆，减少往返折返时间，结束后回到 南京交通便利经济酒店 附近休息。","transportation_cost":18,"accommodation":"南京交通便利经济酒店","hotel":{"name":"南京交通便利经济酒店","address":"建议选择南京核心商圈、地铁站或主要景区之间的住宿区域","location":null,"price_range":"low","rating":"待查询","distance":"以实际预订平台为准","type":"经济型酒店","estimated_cost":280,"photos":[],"image_url":null,"image_source":null,"image_status":null,"map_image_url":null},"attractions":[{"name":"侵华日军南京大屠杀遇难同胞纪念馆","address":"水西门大街418号","location":{"longitude":118.742372,"latitude":32.035217},"visit_duration":180,"description":"侵华日军南京大屠杀遇难同胞纪念馆，位于水西门大街418号，适合作为风景名胜类行程候选。","category":"风景名胜","rating":null,"photos":["http://store.is.autonavi.com/showpic/5bece6e3e3e4e0203fe0f2962394a46d","http://store.is.autonavi.com/showpic/d2f67f0758f4efb5379786f13e850d67","http://store.is.autonavi.com/showpic/d8f6f9f39a9fc0c5b52d5377027f88a0"],"poi_id":"B001905N9D","image_url":"http://store.is.autonavi.com/showpic/5bece6e3e3e4e0203fe0f2962394a46d","image_source":"amap","image_status":"ok","map_image_url":"https://restapiamap.com/v3/staticmap?key=e06c2050ba88b12cff51e181c7ebe69c&zoom=12&size=750%2A420&scale=2&markers=mid%2C0xFF6B35%2C1%3A118.742372%2C32.035217","ticket_price":40},{"name":"南京博物院","address":"中山东路321号","location":{"longitude":118.825064,"latitude":32.040802},"visit_duration":180,"description":"南京博物院位于 中山东路321号，适合作为当天重点游览内容。这里通常能看到城市代表性的景观、历史文化或休闲体验内容，适合安排约 180 分钟停留。建议优先关注最有代表性的区域，并结合当天客流和天气情况安排拍照、步行和休息节奏。","category":"科教文化服务","rating":null,"photos":["http://store.is.autonavi.com/showpic/6d9679442d9f514b78d55213b43d9417","http://store.is.autonavi.com/showpic/7b34bad405cc8c519b800c910b2369fa","http://store.is.autonavi.com/showpic/5ea532a7b89f4327791e2e599d253e0f"],"poi_id":"B001907TGR","image_url":"http://store.is.autonavi.com/showpic/6d9679442d9f514b78d55213b43d9417","image_source":"amap","image_status":"ok","map_image_url":"https://restapi.amap.com/v3/staticmap?key=e06c2050ba88b12cff51e181c7ebe69c&zoom=12&size=750%2A420&scale=2&markers=mid%2C0xFF6B35%2C2%3A118.825064%2C32.040802","ticket_price":40},{"name":"六朝博物馆","address":"长江路302号","location":{"longitude":118.799124,"latitude":32.04284},"visit_duration":180,"description":"六朝博物馆位于 长江路302号，适合作为当天重点游览内容。这里通常能看到城市代表性的景观、历史文化或休闲体验内容，适合安排约 180 分钟停留。建议优先关注最有代表性的区域，并结合当天客流和天气情况安排拍照、步行和休息节奏。","category":"科教文化服务","rating":null,"photos":["http://store.is.autonavi.com/showpic/de50004f8b367977e4d6a3543890a578","http://store.is.autonavi.com/showpic/ef1f42546503d045bb5295085b44f8cb","http://store.is.autonavi.com/showpic/560ad5f0dd0d31b0d2cbfb4cab9fb487"],"poi_id":"B0019135C5","image_url":"http://store.is.autonavi.com/showpic/de50004f8b367977e4d6a3543890a578","image_source":"amap","image_status":"ok","map_image_url":"https://restapi.amap.com/v3/staticmap?key=e06c2050ba88b12cff51e181c7ebe69c&zoom=12&size=750%2A420&scale=2&markers=mid%2C0xFF6B35%2C3%3A118.799124%2C32.04284","ticket_price":40}],"meals":[{"type":"breakfast","name":"有盐有味小吃(银河湾·福苑店)","address":"福园街109-4号","location":{"longitude":118.743165,"latitude":32.031502},"description":"早餐建议在 有盐有味小吃(银河湾·福苑店) 用餐，可考虑点 主食搭配蛋白和热饮。地点在 福园街109-4号，店型偏中餐厅，出餐通常更快，方便上午准时开始行程。","estimated_cost":15},{"type":"lunch","name":"热汤面配小炒和米饭","address":null,"location":null,"description":"午餐建议点热汤面、小炒和米饭，吃什么明确，也方便继续下午行程。","estimated_cost":30},{"type":"dinner","name":"南京古南都饭店","address":"广州路208号","location":{"longitude":118.773523,"latitude":32.051469},"description":"晚餐建议在 南京古南都饭店 用餐，可考虑点 店内招牌主菜配时蔬和主食。地点在 广州路208号，店型偏餐饮相关场所、餐饮相关，收尾节奏更从容，适合一天结束后放松休息。","estimated_cost":50}],"route_summary":"侵华日军南京大屠杀遇难同胞纪念馆 到 南京博物院 约 8.8 公里，预计 39 分钟","route_map_url":"https://restapi.amap.com/v3/staticmap?key=e06c2050ba88b12cff51e181c7ebe69c&zoom=12&size=750%2A420&sc...<truncated>
Apr 19 21:41:39 iZ2ze24zep7yf273as5m21Z python[10256]: AMap key configured: yes
Apr 19 21:41:39 iZ2ze24zep7yf273as5m21Z python[10256]: AMap provider: http
Apr 19 21:41:39 iZ2ze24zep7yf273as5m21Z python[10256]: AMap HTTP timeout: 10.0
Apr 19 21:41:39 iZ2ze24zep7yf273as5m21Z python[10256]: LLM key configured: yes
Apr 19 21:41:39 iZ2ze24zep7yf273as5m21Z python[10256]: [AMAP] HTTP request -> integrated params={'origin': '118.742372,32.035217', 'destination': '118.825064,32.040802', 'city': '南京', 'cityd': '南京', 'extensions': 'all'}
Apr 19 21:41:40 iZ2ze24zep7yf273as5m21Z python[10256]: [AMAP] HTTP response <- integrated ok status=1 keys=['status', 'info', 'infocode', 'count', 'route']
Apr 19 21:41:40 iZ2ze24zep7yf273as5m21Z python[10256]: [AMAP] HTTP request -> integrated params={'origin': '118.825064,32.040802', 'destination': '118.799124,32.04284', 'city': '南京', 'cityd': '南京', 'extensions': 'all'}
Apr 19 21:41:40 iZ2ze24zep7yf273as5m21Z python[10256]: [AMAP] HTTP response <- integrated ok status=1 keys=['status', 'info', 'infocode', 'count', 'route']
{"status":"0","info":"INVALID_USER_KEY","infocode":"10001"}(.venv) root@iZ2ze24zep7yf273as5m21Z:/opt/tripweaver/frontend#




VITE_AMAP_WEB_KEY=e06c2050ba88b12cff51e181c7ebe69c
# Only needed if you later enable AMap JS map rendering in the browser.
VITE_AMAP_WEB_JS_KEY=e06c2050ba88b12cff51e181c7ebe69c

sed -i 's/^AMAP_API_KEY=.*/AMAP_API_KEY=e06c2050ba88b12cff51e181c7ebe69c/' /opt/tripweaver/backend/.env
