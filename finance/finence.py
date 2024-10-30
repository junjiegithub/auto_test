from flask import session, render_template

from base import db_test
from base.db_erp import MysqlDb
from finance.b2c_order import b2c_order
from finance.b2c_return import b2c_return


def index():
    username = session['username']
    sql = f'''SELECT * FROM `yd_authen`.`tb_user` WHERE `email` = '{username}' AND `is_delete` = '0' '''
    mydb = MysqlDb()
    user = mydb.query(sql)
    id = user[0].get('id')
    name = user[0].get('name')
    msg = f"用户{name},邮箱 {username} 访问了 财务系统相关优化 页面,id是{id}"
    sql_log = f"INSERT INTO `test`.`erp_test_log`(`log_`) VALUES ('{msg}')"
    db1 = db_test.db_login()
    cursor = db1.cursor()
    cursor.execute(sql_log)
    db1.commit()
    cursor.close()
    return render_template("finence.html")


def process():
    b2c_return1 = b2c_return()
    b2c_return2 = b2c_return1.b2c_returno()
    username = session['username']
    sql = f'''SELECT * FROM `yd_authen`.`tb_user` WHERE `email` = '{username}' AND `is_delete` = '0' '''
    mydb = MysqlDb()
    user = mydb.query(sql)
    id = user[0].get('id')
    name = user[0].get('name')
    msg = f"用户{name},邮箱 {username}请求了补偿生成B2C退款页面,id是{id}，详情是{b2c_return2}"
    sql_log = f'''INSERT INTO `test`.`erp_test_log`(`log_`) VALUES ('{msg}')'''
    db1 = db_test.db_login()
    cursor = db1.cursor()
    cursor.execute(sql_log)
    db1.commit()
    cursor.close()
    return b2c_return2


def fin_b2c():
    b2c_order1 = b2c_order()
    b2c_order2 = b2c_order1.b2c_order_result()
    username = session['username']
    sql = f'''SELECT * FROM `yd_authen`.`tb_user` WHERE `email` = '{username}' AND `is_delete` = '0' '''
    mydb = MysqlDb()
    user = mydb.query(sql)
    id = user[0].get('id')
    name = user[0].get('name')
    msg = f"用户{name},邮箱 {username}请求了B2C结算功能,id是{id}，详情是{b2c_order2}"
    sql_log = f'''INSERT INTO `test`.`erp_test_log`(`log_`) VALUES ('{msg}')'''
    db1 = db_test.db_login()
    cursor = db1.cursor()
    cursor.execute(sql_log)
    db1.commit()
    cursor.close()
    return b2c_order2
