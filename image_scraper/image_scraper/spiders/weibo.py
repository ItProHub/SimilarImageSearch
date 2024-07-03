import os
import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from scrapy.crawler import CrawlerProcess
from scrapy.http import Request
import re  # 确保导入 re 模块

class WeiboSpider(scrapy.Spider):
    name = 'weibo'
    start_urls = ['https://m.weibo.cn']  # 替换为你要爬取的目标用户的微博URL

    def __init__(self, *args, **kwargs):
        super(WeiboSpider, self).__init__(*args, **kwargs)
        # 配置Selenium的ChromeDriver
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 无头模式运行，不打开浏览器界面
        chrome_service = Service('D:\\Program Files\\chromedriver\\chromedriver.exe')
        self.driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

    def parse(self, response):
        # 使用Selenium加载页面
        self.driver.get(response.url)
        # 等待JavaScript加载完成（这里需要根据你的实际情况调整等待时间或方式）
        self.driver.implicitly_wait(10)  # 隐式等待最多10秒
        
        # 创建 images 目录
        images_dir = 'images'
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)
        
        # 提取图片URL或进行其他操作...
        # 这里只是一个示例，你需要根据微博页面的实际结构来定位图片元素
        images = self.driver.find_elements('tag name', 'img')
        for image in images:
            image_url = image.get_attribute('src')
            if image_url:
                yield Request(image_url, callback=self.save_image)

        # 关闭Selenium的ChromeDriver
        self.driver.quit()

    def save_image(self, response):
        # 保存图片到本地
        images_dir = 'images/unclip'
        image_filename = self.clean_filename(response.url.split('/')[-1])
        self.log(f'Cleaned filename: {image_filename}')  # 添加调试信息
        image_path = os.path.join(images_dir, image_filename)
        with open(image_path, 'wb') as image_file:
            image_file.write(response.body)
        self.log(f'Saved image {image_path}')

    def clean_filename(self, filename):
        # 添加调试信息
        self.log(f'Original filename: {filename}')
        # 确保传入的是字符串
        if not isinstance(filename, str):
            filename = str(filename)
        # 移除文件名中的无效字符
        return re.sub(r'[<>:"/\\|?*]', '', filename)

