import pandas as pd
import requests
import json
import time
import googletrans
import hashlib
import hmac
import base64
from PyNaver import Datalab
from datetime import datetime
from dateutil.relativedelta import relativedelta


#------------------------네이버-----------------------#
##네이버 쇼핑----------------------------
class naver_shopping:
    def __init__(self, search_term):
        self.search_term = search_term

    def get_url(self):
        url = f'https://search.shopping.naver.com/api/search/all?sort=rel&pagingIndex=1&pagingSize=40&viewType=list&productSet=total&deliveryFee=&deliveryTypeValue=&query={self.search_term}&origQuery={self.search_term}&iq=&eq=&xq='
        return url

    def get_data(self):
        response = requests.get(self.get_url())
        data = response.json()
        return data

    def get_item_data(self, items):
        item_data = []
        for item in items:

            try:
                attributeValue = item['attributeValue']
            except:
                attributeValue = '정보 없음'
            try:
                brand = item['brand']
            except:
                brand = '정보 없음'
            category1Name = item['category1Name']
            category2Name = item['category2Name']
            category3Name = item['category3Name']
            category4Name = item['category4Name']
            try:
                characterValue = item['characterValue']
            except:
                characterValue = '정보 없음'
            lowPrice = item['lowPrice']
            mobileLowPrice = item['mobileLowPrice']
            productName = item['productName']
            productTitle = item['productTitle']
            if 'adProductInfoEnabled' in list(item.keys()):
                rank = item['rank'] + '(ads)'
            else:
                rank = item['rank']
            reviewCount = item['reviewCount']
            reviewCountSum = item['reviewCountSum']
            try:
                scoreInfo = item['scoreInfo']
            except:
                scoreInfo = 0
            try:
                smryReview = item['smryReview']
            except:
                smryReview = 0
            
            item_data.append([
                                productName,
                                productTitle,
                                rank,
                                lowPrice,
                                brand,
                                category1Name,
                                category2Name,
                                category3Name,
                                category4Name,
                                characterValue,
                                mobileLowPrice,
                                reviewCount,
                                reviewCountSum,
                                scoreInfo,
                                attributeValue,
                                smryReview])
        
        return item_data

    def get_items(self):
        data = self.get_data()

        normal_items = data['shoppingResult']['products']
        ads_items = data['searchAdResult']['products']

        items = self.get_item_data(normal_items) + self.get_item_data(ads_items)        
        return items

    def to_df(self):
        
        items = self.get_items()

        df = pd.DataFrame(items, columns=['productName',
                                        'productTitle',
                                        'rank',
                                        'lowPrice',
                                        'brand',
                                        'category1Name',
                                        'category2Name',
                                        'category3Name',
                                        'category4Name',
                                        'characterValue',
                                        'mobileLowPrice',
                                        'reviewCount',
                                        'reviewCountSum',
                                        'scoreInfo',
                                        'attributeValue',
                                        'smryReview'])

        df.rename({ 'productName':'상품명',
                    'productTitle':'상품제목',
                    'rank':'순위',
                    'lowPrice':'가격(원)',
                    'brand':'브랜드',
                    'category1Name':'카테고리1',
                    'category2Name':'카테고리2',
                    'category3Name':'카테고리3',
                    'category4Name':'카테고리4',
                    'mobileLowPrice':'모바일최저가',
                    'reviewCount':'리뷰수',
                    'scoreInfo':'평점',
                    },axis=1,inplace=True)
        df['가격(원)'] = df['가격(원)'].astype(int)

        return df

##네이버 검색광고 api-----------------------------------
class Signature:

    @staticmethod
    def generate(timestamp, method, uri, secret_key):
        message = "{}.{}.{}".format(timestamp, method, uri)
        hash = hmac.new(bytes(secret_key, "utf-8"), bytes(message, "utf-8"), hashlib.sha256)

        hash.hexdigest()
        return base64.b64encode(hash.digest())


def get_header(method, uri, API_KEY, SECRET_KEY, CUSTOMER_ID):
    timestamp = str(round(time.time() * 1000))
    signature = Signature().generate(timestamp, method, uri, SECRET_KEY)
    return {'Content-Type': 'application/json; charset=UTF-8', 
            'X-Timestamp': timestamp, 'X-API-KEY': API_KEY, 
            'X-Customer': str(CUSTOMER_ID), 'X-Signature': signature}


def naver_keyword(keyword,API_KEY, SECRET_KEY, CUSTOMER_ID):
    uri = '/keywordstool'
    method = 'GET'
    BASE_URL = 'https://api.naver.com'
    r = requests.get(BASE_URL + uri+'?hintKeywords={}&showDetail=1'.format(keyword.replace(' ','')),
                    headers=get_header(method, uri, API_KEY, SECRET_KEY, CUSTOMER_ID))
    #전체 키워드 관련 자료
    keyword_data = list(filter(lambda x:keyword.split(' ')[0] in x['relKeyword'], r.json()['keywordList']))
    #필요한 것
    ##키워드 검색량
    # print('키워드 검색량', keyword_data[0])
    keyword_search_volume = pd.DataFrame(keyword_data[0],index=[0])
    ##검색량 기준 연관키워드 검색량
    volume_by_mobile = [x for x in keyword_data if type(x['monthlyMobileQcCnt']) == int ]
    top_10_by_volume = sorted(volume_by_mobile, key = lambda x: x['monthlyMobileQcCnt'], reverse=True)
    # print('연관 키워드',top_10_by_volume[:10])
    top_10_related_keywords = pd.DataFrame.from_dict(top_10_by_volume[:10])
    #모바일/PC 검색량 비율
    #모바일 ctr, pc ctr
    keyword_search_volume.rename({'compIdx':'경쟁정도',
           'monthlyAveMobileClkCnt':'월평균클릭수_모바일',
           'monthlyAveMobileCtr':'월평균클릭률_모바일',
           'monthlyAvePcClkCnt':'월평균클릭수_PC',
           'monthlyAvePcCtr':'월평균클릭률_PC', 
           'monthlyMobileQcCnt':'월간검색수_모바일',
           'monthlyPcQcCnt': '월간검색수_PC',
           'plAvgDepth':'월평균노출광고수', 
           'relKeyword':'연관키워드'},axis=1,inplace=True)
    top_10_related_keywords.rename({'compIdx':'경쟁정도',
    'monthlyAveMobileClkCnt':'월평균클릭수_모바일',
    'monthlyAveMobileCtr':'월평균클릭률_모바일',
    'monthlyAvePcClkCnt':'월평균클릭수_PC',
    'monthlyAvePcCtr':'월평균클릭률_PC', 
    'monthlyMobileQcCnt':'월간검색수_모바일',
    'monthlyPcQcCnt': '월간검색수_PC',
    'plAvgDepth':'월평균노출광고수', 
    'relKeyword':'연관키워드'},axis=1,inplace=True)
    keyword_search_volume.drop(['경쟁정도','월평균노출광고수'], axis=1, inplace=True)
    top_10_related_keywords.drop(['경쟁정도','월평균노출광고수'], axis=1, inplace=True)
    return keyword_search_volume,top_10_related_keywords


##네이버 데이터랩 api-----------------------------------
def naver_datalab(keyword,NAVER_API_ID, NAVER_API_SECRET):
    
    # 네이버 데이터랩 API 세션 정의
    DL = Datalab(NAVER_API_ID, NAVER_API_SECRET)

    # 요청 파라미터 설정
    endDate = datetime.now().strftime("%Y-%m-%d")
    startDate = (datetime.now()-relativedelta(years=1)).strftime("%Y-%m-%d")
    timeUnit = 'month'
    device = ''
    ages = []
    gender = ''

    # 검색어 그룹 세트 등록하기
    keyword = {'keyword': {'groupName':keyword, 'keywords':[keyword]}}
    DL.add_keyword_groups(keyword['keyword'])

    # 결과 데이터를 DataFrame으로 조회하기
    df = DL.get_data(startDate, endDate, timeUnit, device, ages, gender)
    return df


#--------------쇼피--------------------

class shopee_shopping:
    def __init__(self, search_term):
        self.search_term = search_term

    def get_url(self):
        url = f'https://shopee.com.my/api/v4/search/search_items?by=sales&keyword={self.search_term}&limit=60&newest=0&order=desc&page_type=search&scenario=PAGE_GLOBAL_SEARCH&version=2'
        return url

    def get_data(self):
        response = requests.get(self.get_url())
        data = response.json()
        return data

    def get_item_data(self, items):
        item_data = []
        for item in items:

            name = item['item_basic']['name']

            monthly_sold = item['item_basic']['sold']
            total_sold = item['item_basic']['historical_sold']

            item_rating = item['item_basic']['item_rating']

            rating = item_rating['rating_star']
            rcount = item_rating['rating_count'][0]
            rcount_1 = item_rating['rating_count'][1]
            rcount_2 = item_rating['rating_count'][2]
            rcount_3 = item_rating['rating_count'][3]
            rcount_4 = item_rating['rating_count'][4]
            rcount_5 = item_rating['rating_count'][5]
            rcount_with_context = item_rating['rcount_with_context']
            rcount_with_image = item_rating['rcount_with_image']
            likes = item['item_basic']['liked_count']

            price = float(item['item_basic']['price'] / 100000)
            #price_before_discount = float(item['item_basic']['price_before_discount'] / 100000)
            price_max = float(item['item_basic']['price_max'] / 100000)
            #price_max_before_discount = float(item['item_basic']['price_max_before_discount'] / 100000)
            price_min = float(item['item_basic']['price_min'] / 100000)
            #price_min_before_discount = float(item['item_basic']['price_min_before_discount'] / 100000)
            discount = float(item['item_basic']['raw_discount'] / 100)
            shop_location = item['item_basic']['shop_location']
            search_item_tracking = json.loads(item['search_item_tracking'])
            is_ads = search_item_tracking['is_ads']

            item_data.append([is_ads,
                            name,
                            monthly_sold,
                            total_sold,
                            rating,
                            rcount,
                            rcount_1,
                            rcount_2,
                            rcount_3,
                            rcount_4,
                            rcount_5,
                            rcount_with_context,
                            rcount_with_image,
                            likes,
                            price,
                            #price_before_discount,
                            price_max,
                            #price_max_before_discount,
                            price_min,
                            #price_min_before_discount,
                            discount,
                            shop_location])

        return item_data

    def get_items(self):
        data = self.get_data()
        items = self.get_item_data(data['items'])
        return items

    def to_df(self):
        
        items = self.get_items()

        df = pd.DataFrame(items, columns=[
                                'is_ads',
                                'name',
                                'monthly_sold',
                                'total_sold',
                                'rating',
                                'rcount',
                                'rcount_1',
                                'rcount_2',
                                'rcount_3',
                                'rcount_4',
                                'rcount_5',
                                'rcount_with_context',
                                'rcount_with_image',
                                'likes',
                                'price',
                                #'price_before_discount',
                                'price_max',
                                #'price_max_before_discount',
                                'price_min',
                                #'price_min_before_discount',
                                'discount',
                                'shop_location'])

        df.sort_values(by='monthly_sold', ascending=False, inplace=True)

        df.rename({ 'is_ads':'광고여부',
                    'name':'상품명',
                    'monthly_sold':'판매량(월 평균)',
                    'total_sold':'누적판매량',
                    'rating':'평점',
                    'rcount':'평가수',
                    'price':'가격(RM)',
                    'price_max':'최고가',
                    'price_min':'최저가',
                    'discount':'할인율',
                    'shop_location':'지역'
                    },axis=1,inplace=True)
        df['가격(RM)'] = df['가격(RM)'].astype(int)
        return df


#----------------------구글 api------------------------


if __name__ == "__main__":
    search_term = input('검색할 키워드를 입력하세요')

    start = time.time()
    
    #키워드 번역
    #pip install googletrans==4.0.0-rc1
    translator = googletrans.Translator()
    search_term_en = str(translator.translate(search_term, src='ko', dest='en').text)
    
    naver_shopping_result = naver_shopping(search_term).to_df()
    shopee_shopping_result = shopee_shopping(search_term_en).to_df()

    end = time.time()

    print('걸린 수집 시간 : ', end - start)
    print(naver_shopping_result,shopee_shopping_result)
