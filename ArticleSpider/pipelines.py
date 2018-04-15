# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import codecs
import json


from scrapy.pipelines.images import ImagesPipeline
from scrapy.exporters import JsonItemExporter
from twisted.enterprise import adbapi

import MySQLdb
import MySQLdb.cursors

class ArticlespiderPipeline(object):
    def process_item(self, item, spider):
        return item


class JsonWithEncodingPipeline(object):
    # 自定义json文件的导出
    def __init__(self):
        self.file = codecs.open('article.json', 'w', encoding="utf-8")

    def process_item(self, item, spider):
        lines = json.dumps(dict(item), ensure_ascii=False) + "\n"
        self.file.write(lines)
        return item

    def sider_closed(self):
        self.file.close()


class JsonExporterPipeline(object):
    # 调用scrapy提供的json export导出json文件

    def __init__(self):
        self.file = open('articleexport.json', 'wb')
        self.exporte = JsonItemExporter(self.file, encoding='utf-8', ensure_ascii=False)
        self.exporte.start_exporting()

    def close_spdier(self, spider):
        self.exporte.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        self.exporte.export_item(item)
        return item


class ArticleImagePipeline(ImagesPipeline):
    def item_completed(self, results, item, info):
        for ok, value in results:
            image_file_path = value["path"]
            item["front_image_path"] = image_file_path

        return item


class MysqlPipline(object):
    def __init__(self):
        self.conn = MySQLdb.connect('127.0.0.1', 'root', '123456', 'article_spider', charset="utf8", use_unicode=True)
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        insert_sql = """
            insert into message(title, url, create_date, fav_nums, url_object_id)
            VALUES (%s,%s,%s,%s,%s)
            """
        self.cursor.execute(insert_sql,
                            (item['title'], item['url'], item['create_date'], item['fav_nums'], item['url_object_id']))
        self.conn.commit()


class MysqlTwistedPipline(object):
    def __init__(self, dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls, settings):
        #将数据库连接参数转为dict，方便使用
        dbparms = dict(
            host=settings['MYSQL_HOST'],
            db=settings['MYSQL_DBNAME'],
            user=settings['MYSQL_USER'],
            passwd=settings['MYSQL_PASSWORD'],
            charset='utf8',
            cursorclass=MySQLdb.cursors.DictCursor,
            use_unicode=True
        )
        dbpool = adbapi.ConnectionPool("MySQLdb", **dbparms)
        return cls(dbpool)

    def process_item(self, item, spider):
        # 使用twisted将mysql插入变成异步执行
        query = self.dbpool.runInteraction(self.do_insert, item)
        query.addErrback(self.handle_error)

    def handle_error(self, failure):
        # 处理异步插入的异常
        print(failure)

    def do_insert(self, cursor, item):
        # 执行具体的插入
        insert_sql = """
                    insert into message(title, url, create_date, fav_nums, url_object_id)
                    VALUES (%s,%s,%s,%s,%s)
                    """
        cursor.execute(insert_sql,
                       (item['title'], item['url'], item['create_date'], item['fav_nums'], item['url_object_id']))
