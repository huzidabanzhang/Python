#!/usr/bin/env python
# -*- coding:UTF-8 -*-
'''
@Description:
@Author: Zpp
@Date: 2019-09-09 10:02:39
@LastEditTime : 2020-01-13 14:48:00
@LastEditors  : Zpp
'''
from flask import request
from models.base import db
from models.system import Admin, Role, Route, Menu, Interface, InitSql
from conf.setting import Config, init_route, init_menu
from sqlalchemy import text
import uuid
import datetime
import random


class AdminModel():
    def CreateDropRequest(self, isInit):
        try:
            s = db.session()

            if isInit:
                try:
                    res = s.query(InitSql).first()
                    if res.isInit:
                        return str('已经初始化~~~')
                except:
                    pass

            db.drop_all()
            db.create_all()
            password = self.__get_code()

            role_id = uuid.uuid4()
            role = Role(
                role_id=role_id, 
                name=u'超级管理员', 
                check_key='[]',
                mark=u'SYS_ADMIN'
            )
            s.add(role)
            s.commit()

            admin = Admin(
                admin_id=uuid.uuid4(),
                username=u'Admin',
                password=Config().get_md5(password),
                avatarUrl='',
                roles=[role]
            )
            s.add(admin)
            s.commit()

            self.__init_routes(init_route, '0', role_id)
            self.__init_menus(init_menu, '0', role_id)

            if not isInit:
                sql = InitSql(isInit=True)
                s.add(sql)
                s.commit()

            return {
                'username': 'Admin',
                'password': password
            }
        except Exception as e:
            print e
            return str(e.message)

    def __get_code(self):
        code_list = []
        for i in range(10):   # 0~9
            code_list.append(str(i))
        for i in range(65, 91):  # A-Z
            code_list.append(chr(i))
        for i in range(97, 123):  # a-z
            code_list.append(chr(i))
        code = random.sample(code_list, 6)  # 随机取6位数
        code_num = ''.join(code)
        return code_num

    def __init_routes(self, data, pid, role_id):
        s = db.session()
        for r in data:
            route_id = uuid.uuid4()
            route = self.__create_route(r, route_id, pid)
            s.add(route)
            s.commit()
            if r.has_key('children'):
                self.__init_routes(r['children'], route_id, role_id)

    def __init_menus(self, data, pid, role_id):
        s = db.session()
        for m in data:
            role = s.query(Role).filter(Role.role_id == role_id).first()

            menu_id = uuid.uuid4()
            menu = self.__create_menu(m, menu_id, pid)

            if m.has_key('interface'):
                interfaces = []
                for f in m['interface']:
                    interface = self.__create_interface(f, uuid.uuid4(), menu_id)
                    s.add(interface)
                    interfaces.append(interface)
                menu.interfaces = interfaces

                role_interfaces = [i for i in role.interfaces]
                role.interfaces = role_interfaces + interfaces

            s.add(menu)

            menus = [i for i in role.menus]
            menus.append(menu)
            role.menus = menus

            s.commit()
            if m.has_key('children'):
                self.__init_menus(m['children'], menu_id, role_id)

    def __create_route(self, params, route_id, pid):
        return Route(
            route_id=route_id,
            pid=pid,
            name=params['name'],
            description=params['description'],
            path=params['path'],
            component=params['component'],
            componentPath=params['componentPath'],
            cache=params['cache']
        )

    def __create_menu(self, params, menu_id, pid):
        return Menu(
            menu_id=menu_id,
            pid=pid,
            name=params['name'],
            path=params['path'],
            icon=params['icon']
        )

    def __create_interface(self, params, interface_id, menu_id):
        return Interface(
            menu_id=menu_id,
            interface_id=interface_id,
            name=params['name'],
            path=params['path'],
            method=params['method'],
            description=params['description'],
            mark=params['mark']
        )

    def QueryAdminByParamRequest(self, params, page=1, page_size=20, order_by='id'):
        '''
        管理员列表
        '''
        s = db.session()
        try:
            data = {}
            for i in ['role_id', 'isLock']:
                if params.has_key(i):
                    data[i] = params[i]

            result = Admin.query.filter_by(**data).order_by(order_by).paginate(page, page_size, error_out=False)

            return {'data': [value.to_json() for value in result.items], 'total': result.total}
        except Exception as e:
            print e
            return str(e.message)

    def CreateAdminRequest(self, params):
        '''
        新建管理员
        '''
        s = db.session()
        try:
            role = s.query(Role).filter(Role.role_id.in_(params['role_id']))

            if not role:
                return str('角色不存在')

            for i in role:
                if i.mark == 'SYS_ADMIN':
                    return str('不能设为为超级管理员')

            admin = s.query(Admin).filter(Admin.username == params['username']).first()

            if admin:
                return str('管理员已存在')

            item = Admin(
                admin_id=uuid.uuid4(),
                username=params['username'],
                password=Config().get_md5(params['password']),
                sex=int(params['sex']),
                email=params['email'],
                nickname=params['nickname'],
                avatarUrl=params['avatarUrl'],
                roles=role
            )
            s.add(item)
            s.commit()
            return True
        except Exception as e:
            s.rollback()
            print e
            return str(e.message)

    def GetAdminRequest(self, username, password):
        '''
        查询管理员
        '''
        s = db.session()
        try:
            admin = s.query(Admin).filter(Admin.username == username, Admin.password == Config().get_md5(password)).first()
            if not admin:
                return str('管理员不存在')
            if not admin.isLock:
                return str('管理员被禁用')

            data = admin.to_json()
            print data
            # route = []
            # menu = []
            # interface = []
            # role = s.query(Role).filter(Role.id == admin.role_id).first()
            # if role:
            #     for i in role.routes:
            #         item = i.to_json()
            #         if item['isLock']:
            #             route.append(item)

            #     for i in role.menus.filter(Menu.isLock == True).order_by(Menu.sort, Menu.id):
            #         menu.append(i.to_json())
            #         interfaces = s.query(Interface).filter(Interface.menu_id == i.menu_id, Interface.isLock == True).all()
            #         interface = interface + [i.to_json() for i in interfaces]

            # data['routes'] = route
            # data['menus'] = menu
            # data['interface'] = interface
            return data
        except Exception as e:
            print e
            return str(e.message)

    def ModifyAdminRequest(self, admin_id, params):
        '''
        修改管理员信息
        '''
        s = db.session()
        try:
            admin = s.query(Admin).filter(Admin.admin_id == admin_id).first()
            if not admin:
                return str('管理员不存在')
            if not admin.isLock:
                return str('管理员被禁用')
            
            role = s.query(Role).filter(Role.role_id.in_(params['role_id']))

            if not role:
                return str('角色不存在')

            for i in role:
                if i.mark == 'SYS_ADMIN':
                    return str('不能设为为超级管理员')

            AllowableFields = ['nickname', 'sex', 'role_id', 'avatarUrl', 'password', 'email']
            data = {}

            for i in params:
                if i in AllowableFields and params.has_key(i):
                    if i == 'password':
                        if params[i] != admin.password:
                            data[i] = Config().get_md5(params[i])
                    elif i == 'role_id':
                        data[i] = role
                    else:
                        data[i] = params[i]

            s.query(Admin).filter(Admin.admin_id == admin_id).update(data)
            s.commit()
            return True
        except Exception as e:
            print e
            s.rollback()
            return str(e.message)

    def LockAdminRequest(self, admin_id, isLock):
        '''
        禁用管理员
        '''
        s = db.session()
        try:
            s.query(Admin).filter(Admin.admin_id.in_(admin_id)).update({Admin.isLock: isLock}, synchronize_session=False)
            s.commit()
            return True
        except Exception as e:
            print e
            s.rollback()
            return str(e.message)
