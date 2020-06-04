#!/usr/bin/env python
# -*- coding:UTF-8 -*-
'''
@Description: API蓝图初始化注册
@Author: Zpp
@Date: 2019-09-04 10:23:46
@LastEditTime: 2020-06-04 15:22:23
@LastEditors: Zpp
'''
from .v1.admin import route_admin
from .v1.menu import route_menu
from .v1.role import route_role
from .v1.interface import route_interface
from .v1.document import route_document
from .v1.folder import route_folder
from .v1.log import route_log
from .v1.base import route_base

from flask import current_app, session, make_response, request
from libs.code import ResultDeal, GetTimestamp
from models import db
from models.system import InitSql
from datetime import datetime
import time


def init_app(app):
    @app.before_first_request
    def before_first_request():
        # 运行检查是否存在数据表
        session['requestTime'] = GetTimestamp()
        try:
            # 创建数据表
            db.create_all()
            s = db.session()
            res = s.query(InitSql).first()
            if not res:
                s.add(InitSql(is_init=False))
                s.commit()
        except:
            return ResultDeal(code=-1, msg=u'数据库未连接错误或者出现错误')

    @app.before_request
    def handel_before_request():
        session['requestTime'] = GetTimestamp()

    @app.teardown_request
    def handel_teardown_request(response):
        if response:
            db.session.close()

    @app.after_request
    def handel_after_request(resp):
        """
        #请求钩子，在所有的请求发生后执行，加入headers
        :param resp:
        :return:
        """
        resp = make_response(resp)
        allow_address = ['http://localhost:5001', 'https://test.ig132n.cn']
        origin = request.headers['Origin'] if request.headers.has_key('Origin') else None
        if origin in allow_address:
            resp.headers['Access-Control-Allow-Origin'] = request.headers['Origin']
            resp.headers['Access-Control-Allow-Methods'] = 'GET, POST'
            resp.headers['Access-Control-Allow-Headers'] = 'x-requested-with,content-type,Authorization,isCheck,Origin, isGet'
            resp.headers['Access-Control-Allow-Credentials'] = 'true'

        return resp

    @app.errorhandler(401)
    def handle_401_error(error):
        return ResultDeal(code=401, msg=u'登录认证失效，请重新登录')

    @app.errorhandler(403)
    def handle_403_error(error):
        return ResultDeal(code=403, msg=u'您没有访问权限')

    @app.errorhandler(404)
    def handle_404_error(error):
        return ResultDeal(code=404, msg=u'文件或者页面不存在')

    @app.errorhandler(405)
    def handle_404_error(error):
        return ResultDeal(code=405, msg=u'方法不被允许')

    @app.errorhandler(500)
    def handle_500_error(error):
        return ResultDeal(code=500, msg=u'服务器错误 %s' % error)

    @app.route('/favicon.ico')
    def favicon():
        return current_app.send_static_file('favicon.ico')

    app.register_blueprint(route_admin)
    app.register_blueprint(route_menu)
    app.register_blueprint(route_role)
    app.register_blueprint(route_interface)
    app.register_blueprint(route_document)
    app.register_blueprint(route_folder)
    app.register_blueprint(route_log)
    app.register_blueprint(route_base)
