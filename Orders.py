import pyspark
from pyspark import SparkConf, SparkContext
from pyspark.streaming import StreamingContext
from pyspark.sql import SparkSession
from pyspark.sql import SQLContext
from pyspark.sql import HiveContext
from pyspark.sql import DataFrameWriter
from pyspark.sql import DataFrame 
from pyspark.sql.types import StringType, IntegerType, StructField, StructType, LongType, TimestampType, FloatType
import boto3
import argparse
import sys
from botocore.client import Config
import datetime
import time
from datetime import datetime, timedelta

# The 'os' library allows us to read the environment variable SPARK_HOME defined in the IDE environment
import os
import json
from collections import namedtuple
from pyspark import RDD, since, keyword_only
import re
from boto3.s3.transfer import S3Transfer, TransferConfig
import io
from io import StringIO
#import yaml
from pyspark.sql.functions import struct, collect_list, explode
import s3fs
import psycopg2

os.environ['PYSPARK_SUBMIT_ARGS'] = '--packages com.amazonaws:aws-java-sdk:1.7.4,org.apache.hadoop:hadoop-aws:2.7.2 pyspark-shell'

#sc = SparkContext()
sc= SparkContext.getOrCreate()
sqlContext = SQLContext(sc)

#sc = pyspark.SparkContext(conf = conf)
hadoop_conf = sc._jsc.hadoopConfiguration()
hadoop_conf.set("fs.s3.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
hadoop_conf.set("fs.s3a.access.key", "")
hadoop_conf.set("fs.s3a.secret.key", "")

hadoop_conf.set("fs.s3n.awsAccessKeyId", "")
hadoop_conf.set("fs.s3n.awsSecretAccessKey", "")

value={'data': {'orders': {'customers': [{'custType': '2', 'postcode': 'xyzwer', 'street4': 'Oxon', 'street1': '2 my Square',
                                          'companyName': 'You are my Hero', 'paymentTerms': '0', 'telNumber': '12345678',
                                          'street2': 'Park', 'customerid': '000001', 'country': 'GB', 'street3': 'oxford',
                                          'companycode': 'INF1', 'townCity': 'HENDON'}],
                           'order': [{'freightCharge': '0', 'shipTo': '00TX01', 'ordernumber': '5682104II1', 
                                      'currency': 'GBP', 'payer': '00TX01', 'order_items': {'order_item':
                                                                                            [{'productid': '8660626322', 'itemNumber': '1', 'netValue': '0', 'taxAmount': '0', 'quantity': '1', 'tranType': 'Z', 'unitPrice': '0'}]}, 'billDoc': '5682104II1', 'doctype': 'I', 'billTo': '00TX01', 'freightTax': '0', 'docDate': '2017-10-24', 'companycode': 'INF1'}], 'materials': {'materials': [{'formerImprint': '2ORBLANK', 'versionType': '2VEPB', 'materialNumber': '9780418028865', 'team': '2TMBHSUKOT', 'textType': '2TEBL510', 'legalOwner': '2PCUK', 'legacyDivision': '2DVHSRBKS', 'geoSplit': '2SGBHSPOS', 'title': 'My New Titles January - March 201', 'pcSG': '2GDSG00601', 'producerCode': '2PRBHSUKPOS', 'subDivision': '2SDBHSRO', 'pcUS': '2GDUS04001', 'pcUK': '2GDGB17401'}]}, 'recordCount': 1}}, 'sourceDetails': {'applicationName': 'AVENGERS', 'platform': 'ERRICSON'}, 'headers': {'id': '7199754355652186066', 'source': 'BKP', 'timestamp': '1508961644548', 'version': '1.0', 'type': 'ORDERS'}}

list= json.dumps(value)

list= json.dumps(value)
rdd = sc.parallelize([(list)])
xy = sqlContext.read.json(rdd)
df3 = xy\
.select(explode('data.orders.materials.materials'),'headers')

_materials=df3\
.withColumn('formerImprint',df3.col.formerImprint)\
.withColumn('geoSplit',df3.col.geoSplit)\
.withColumn('legacyDivision',df3.col.legacyDivision)\
.withColumn('legalOwner',df3.col.legalOwner)\
.withColumn('materialNumber',df3.col.materialNumber)\
.withColumn('pcSG',df3.col.pcSG)\
.withColumn('pcUK',df3.col.pcUK)\
.withColumn('pcUS',df3.col.pcUS)\
.withColumn('producerCode',df3.col.producerCode)\
.withColumn('subDivision',df3.col.subDivision)\
.withColumn('team',df3.col.team)\
.withColumn('textType',df3.col.textType)\
.withColumn('title',df3.col.title)\
.withColumn('versionType',df3.col.versionType)\

df1 = xy\
.select(explode('data.orders.order'),'headers')

_orders=df1\
.withColumn('doctype',df1.col.doctype)\
.withColumn('freightTax',df1.col.freightTax)\
.withColumn('ordernumber',df1.col.ordernumber)\
.withColumn('docDate',df1.col.docDate)\
.withColumn('currency',df1.col.currency)\
.withColumn('shipTo',df1.col.shipTo)\
.withColumn('billDoc',df1.col.billDoc)\
.withColumn('billTo',df1.col.billTo)\
.withColumn('companycode',df1.col.companycode)\
.withColumn('id',df1.headers)

df2 = df1\
.select(explode('col.order_items.order_item'),'headers')

_order_items_schema=df2\
.withColumn('itemNumber',df2.col.itemNumber)\
.withColumn('netValue',df2.col.netValue)\
.withColumn('productid',df2.col.productid)\
.withColumn('taxAmount',df2.col.taxAmount)\
.withColumn('quantity',df2.col.quantity)\
.withColumn('tranType',df2.col.tranType)\
.withColumn('unitPrice',df2.col.unitPrice)\
.withColumn('id',df2.headers)

_orders.createOrReplaceTempView("Order_info")
_order_items_schema.createOrReplaceTempView("Order_items")
_materials.createOrReplaceTempView("materials")

_dataframe1 = sqlContext.sql("select headers.id, cast(from_unixtime((headers.timestamp/1000)) as TIMESTAMP) as datetime,itemNumber,netValue,productid,  taxAmount,quantity,tranType,unitPrice from Order_items")
_dataframe2 = sqlContext.sql("select headers.id, cast(from_unixtime((headers.timestamp/1000)) as TIMESTAMP) as datetime,doctype, freightTax, ordernumber,docDate, currency, shipTo, billDoc,billTo,companycode from Order_info")
_dataframe3 = sqlContext.sql("select headers.id, cast(from_unixtime((headers.timestamp/1000)) as TIMESTAMP) as datetime,formerImprint,geoSplit,legacyDivision,legalOwner, materialNumber,pcSG,pcUK,pcUS,producerCode,subDivision,team,textType,title,versionType from materials")

parser = argparse.ArgumentParser()
parser.add_argument('month', type=lambda s: datetime.now().month)
args1 = parser.parse_args(['2012-09-01'])
#print (args1.month)

parser = argparse.ArgumentParser()
parser.add_argument('year', type=lambda s: datetime.now().year)
args2 = parser.parse_args(['2012-09-01'])
#print (args2.year)

parser = argparse.ArgumentParser()
parser.add_argument('date', type=lambda s: datetime.strftime(datetime.now(), "%Y-%m-%d"))
args3 = parser.parse_args(['2012-09-01'])

_Orders_url= "s3n://"+'analytics-reports-data'+'/'+'BMX_sales/output' +'/' + 'orders'+'/'+str(args2.year) + '/'+ str(args1.month) +'/' + str(args3.date) +'/'
_Order_items_url ="s3n://"+'analytics-reports-data'+'/'+'BMX_sales/output' +'/' + 'order_items'+'/'+str(args2.year) + '/'+ str(args1.month) +'/' + str(args3.date) +'/'
_materials_url="s3n://"+'analytics-reports-data'+'/'+'BMX_sales/output' +'/' + 'materials'+'/'+str(args2.year) + '/'+ str(args1.month) +'/' + str(args3.date) +'/'

_delimiter=","

df4 = xy\
.select(explode('data.orders.customers'),'headers')

_customers=df4\
.withColumn('companyName',df4.col.companyName)\
.withColumn('companycode',df4.col.companycode)\
.withColumn('country',df4.col.country)\
.withColumn('custType',df4.col.custType)\
.withColumn('customerid',df4.col.customerid)\
.withColumn('postcode',df4.col.postcode)\
.withColumn('street1',df4.col.street1)\
.withColumn('street2',df4.col.street2)\
.withColumn('street3',df4.col.street3)\
.withColumn('telNumber',df4.col.telNumber)\
.withColumn('townCity',df4.col.townCity)\

_customers.createOrReplaceTempView("customers")

_customers_url="s3n://"+'analytics-reports-data'+'/'+'BMX_sales/output' +'/' + 'customers'+'/'+str(args2.year) + '/'+ str(args1.month) +'/' + str(args3.date) +'/'

_dataframe4 = sqlContext.sql("select headers.id, cast(from_unixtime((headers.timestamp/1000)) as TIMESTAMP) as datetime,companyName,companycode,country,custType,customerid,postcode,street1,street2,street3,telNumber,townCity from customers")

_filename1=_dataframe1.coalesce(1).write.format('com.databricks.spark.csv').option('header','true').option('delimiter', _delimiter).option('parserLib', '').mode("overwrite").save(_Order_items_url)

_filename2=_dataframe2.coalesce(1).write.format('com.databricks.spark.csv').option('header','true').option('delimiter', _delimiter).option('parserLib', '').mode("overwrite").save(_Orders_url)

_filename3=_dataframe3.coalesce(1).write.format('com.databricks.spark.csv').option('header','true').option('delimiter', _delimiter).option('parserLib', '').mode("overwrite").save(_materials_url)

_filename4=_dataframe4.coalesce(1).write.format('com.databricks.spark.csv').option('header','true').option('delimiter', _delimiter).option('parserLib', '').mode("overwrite").save(_customers_url)

