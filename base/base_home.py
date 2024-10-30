import hashlib

from flask import request, session, flash, redirect, url_for, render_template

from base import db_test
from base.db_erp import MysqlDb


def login1():
    """Log in a registered user by adding the user id to the session."""
    if request.method == "POST":
        # 客户端在 login 页面发起的 POST 请求
        username = request.form["username"]
        password = request.form["password"]

        md5_hash = hashlib.md5(password.encode())
        password = md5_hash.hexdigest()

        # 获取数据库连接
        mydb = MysqlDb()

        # SQL 查询语句
        check_sql = f"SELECT * FROM `yd_authen`.`tb_user` WHERE `email` ='{username}' AND `password` = '{password}'"

        # 查询用户是否存在且密码正确
        user = mydb.query(check_sql)

        if user:
            # 登录成功，将用户信息存入 session
            session['username'] = username
            flash('登录成功', 'success')
            sql = f'''SELECT * FROM `yd_authen`.`tb_user` WHERE `email` = '{username}' AND `is_delete` = '0' '''
            mydb = MysqlDb()
            user = mydb.query(sql)
            id = user[0].get('id')
            name = user[0].get('name')
            msg = f"用户{name},邮箱 {username} 登录成功,id是{id}"
            sql_log = f"INSERT INTO `test`.`erp_test_log`(`log_`) VALUES ('{msg}')"
            db1 = db_test.db_login()
            cursor = db1.cursor()
            cursor.execute(sql_log)
            db1.commit()
            cursor.close()
            return redirect(url_for('home'))
        else:
            # 登录失败，返回提示信息
            flash('用户名或密码不对,请重新输入', 'danger')
            return render_template("login.html")

    # 对于 GET 请求，直接渲染登录页面
    return render_template("login.html")
