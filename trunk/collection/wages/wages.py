#!/usr/bin/env python
# -*- coding:UTF-8 -*-
'''
@Description: 工资记录控制器
@Author: Zpp
@Date: 2020-04-10 13:30:34
@LastEditors: Zpp
@LastEditTime: 2020-04-10 14:09:03
'''
from flask import request
from models import db
from models.wages import Wages
from sqlalchemy import text
from conf.setting import excel_dir
import logging
import xlwings as xw
import uuid
import time
import os
import datetime
import json


class WagesModel():
    def QueryWagesByParamRequest(self, params, page=1, page_size=20, order_by='id'):
        '''
        工资列表
        '''
        s = db.session()
        try:
            data = {}
            for i in ['payment_time']:
                if params.has_key(i):
                    data[i] = params[i]

            result = Wages.query.filter_by(**data).filter(
                Wages.company.like('%' + params['company'] + '%') if params.has_key('company') else text(''),
                Wages.name.like('%' + params['name'] + '%') if params.has_key('name') else text('')
            ).order_by(order_by).paginate(page, page_size, error_out=False)

            return {'data': [value.to_json() for value in result.items], 'total': result.total}
        except Exception as e:
            print e
            logging.info('-------获取工资列表失败%s' % e)
            return str('获取工资列表失败')

    def GetWagesRequest(self, params, page=1, page_size=20):
        '''
        获取个人工资列表
        '''
        s = db.session()
        try:
            data = {
                'id_card': params['id_card'],
                'phone': params['phone']
            }

            result = Wages.query.filter_by(**data).order_by('id').paginate(page, page_size, error_out=False)

            return {'data': [value.to_json() for value in result.items], 'total': result.total}
        except Exception as e:
            print e
            logging.info('-------获取个人工资失败%s' % e)
            return str('获取个人工资失败')

    @staticmethod
    def allowed_file(file):
        ALLOWED_EXTENSIONS = set(['xls', 'xlsx'])

        return '.' in file and file.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    def ImportWagesRequest(self, file, payment_time):
        '''
        导入工资记录
        '''
        s = db.session()
        filename = file.filename

        ary = filename.split('.')
        count = len(ary)
        ext = ary[count - 1] if count > 1 else ''
        if not self.allowed_file(filename):
            return str('请上传Excel文件')

        file.seek(0)
        fn = '/' + str(time.strftime('%Y/%m/%d'))
        if not os.path.exists(excel_dir + fn):
            os.makedirs(excel_dir + fn)
        path = fn + '/' + str(uuid.uuid1()) + '.' + ext
        file.save(excel_dir + path)

        import pythoncom
        pythoncom.CoInitialize()

        xw_app = xw.App(visible=False, add_book=False)
        wb = xw_app.books.open(excel_dir + path)

        params = []

        for sheet in wb.sheets:
            # 读取所有内容
            data = sheet.range('A1').expand().value

            fileds = [u'公司', u'姓名', u'身份证', u'电话']
            for i in data:
                if i[0] == u'公司':
                    item = i
                else:
                    d = {
                        'value': {}
                    }
                    for index, j in enumerate(item):
                        if j:
                            if j.replace(" ", "") in fileds:
                                d[j.replace(" ", "")] = i[index] if type(i[index]) != float else int(i[index])
                            else:
                                d['value'][j] = str(i[index]) if not type(i[index]).__name__ == 'datetime' else i[index].strftime('%Y-%m-%d')
                    params.append(d)
        print len(params)
        case = []
        for i in params:
            if i.has_key(u'公司') and i.has_key(u'姓名') and i.has_key(u'身份证') and i.has_key(u'电话'):
                case.append(Wages(
                    wages_id=uuid.uuid4(),
                    company=i[u'公司'],
                    name=i[u'姓名'],
                    id_card=i[u'身份证'],
                    phone=int(i[u'电话']),
                    wages=json.dumps(i['value']),
                    payment_time=payment_time
                ))
            else: 
                print i
        s.add_all(case)
        s.commit()
        return True
