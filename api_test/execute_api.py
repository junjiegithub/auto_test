import json

import requests
from dingtalkchatbot.chatbot import DingtalkChatbot
from flask import jsonify, flash, redirect, url_for, request, session, render_template,current_app
from base import db_test, base_set
from base.db_erp import MysqlDb



#
def login():
    login_url = base_set.login_url
    login_data = {
        "email": base_set.login_email,
        "password": base_set.login_password
    }

    header = {'Content-Type': 'application/json'}
    r = requests.post(login_url, json=login_data, headers=header)
    r = r.json()

    token = str(r['data'])
    return token

def api_list1():
    db = db_test.db_login()
    cursor = db.cursor()

    page = request.args.get('page', 1, type=int)
    per_page = 6
    offset = (page - 1) * per_page

    # 获取搜索参数
    search_app = request.args.get('search_app', '').strip()
    search_title = request.args.get('search_title', '').strip()
    search_pass = request.args.get('search_pass', '').strip()
    search_module = request.args.get('search_module', '').strip()
    search_url = request.args.get('search_url', '').strip()
    search_creat = request.args.get('search_creat', '').strip()  # 获取创建人搜索参数

    # 构建SQL查询
    sql = "SELECT * FROM test.erp_case WHERE is_del = 0 "
    count_sql = "SELECT COUNT(*) FROM test.erp_case WHERE is_del = 0"
    params = []

    if search_app:
        sql += " AND app LIKE %s"
        count_sql += " AND app LIKE %s"
        params.append(f"%{search_app}%")

    if search_title:
        sql += " AND title LIKE %s"
        count_sql += " AND title LIKE %s"
        params.append(f"%{search_title}%")

    if search_pass:
        sql += " AND pass = %s"
        count_sql += " AND pass = %s"
        params.append(search_pass)

    if search_module:
        sql += " AND module LIKE %s"
        count_sql += " AND module LIKE %s"
        params.append(f"%{search_module}%")

    if search_url:
        sql += " AND url LIKE %s"
        count_sql += " AND url LIKE %s"
        params.append(f"%{search_url}%")

    if search_creat:
        sql += " AND creat LIKE %s"
        count_sql += " AND creat LIKE %s"
        params.append(f"%{search_creat}%")

    # 在 WHERE 子句完成后再添加 ORDER BY
    sql += " ORDER BY creat_time DESC"

    # 执行查询以获取总记录数
    cursor.execute(count_sql, params)
    total_records = cursor.fetchone()[0]

    # 分页
    sql += " LIMIT %s OFFSET %s"
    params.extend([per_page, offset])

    # 执行查询以获取实际数据
    cursor.execute(sql, params)
    api = cursor.fetchall()

    cursor.close()

    # 计算总页数
    total_pages = (total_records + per_page - 1) // per_page

    # 将搜索参数传递回模板，确保搜索框中能显示之前输入的值
    return render_template('api.html',
                           api=api,
                           page=page,
                           total_pages=total_pages,
                           search_app=search_app,
                           search_title=search_title,
                           search_pass=search_pass,
                           search_module=search_module,
                           search_url=search_url,
                           search_creat=search_creat)

def api_add1():
    if request.method == 'POST':
        app_name = request.form.get('app')
        module = request.form.get('module')
        title = request.form.get('title')
        method = request.form.get('method')
        url = request.form.get('url')
        run = request.form.get('run')
        headers = request.form.get('headers')
        pre_case_id = request.form.get('pre_case_id')
        pre_fields = request.form.get('pre_fields')
        request_body = request.form.get('request_body')
        expect_result = request.form.get('expect_result', '待执行')
        assert_type = request.form.get('assert_type')
        pass_case = request.form.get('pass')
        msg = request.form.get('msg')
        remark = request.form.get('remark')

        username = session['username']
        sql = f'''SELECT * FROM `yd_authen`.`tb_user` WHERE `email` = '{username}' AND `is_delete` = '0' '''
        mydb = MysqlDb()
        user = mydb.query(sql)
        id = user[0].get('id')
        creat = user[0].get('name')
        # msg = f"用户{name},邮箱 {username} 访问了 home 页面,id是{id}"
        if pre_case_id == '':
            pre_case_id = None

        db = db_test.db_login()
        cursor = db.cursor()

        sql = """
            INSERT INTO test.erp_case (app, module, title, method, url, run, headers, pre_case_id, pre_fields, request_body, expect_result, assert_type, pass, msg, remark, creat_time, update_time, is_del,creat)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), 0,%s)
        """
        cursor.execute(sql, (
            app_name, module, title, method, url, run, headers, pre_case_id, pre_fields, request_body, expect_result,
            assert_type, pass_case, msg, remark,creat))
        db.commit()
        cursor.close()

        flash('新增用例成功！')
        return redirect(url_for('api_list'))

    return render_template('api_add.html')

def api_edit1(id):
    db = db_test.db_login()
    cursor = db.cursor()

    if request.method == 'POST':
        app_name = request.form.get('app')
        module = request.form.get('module')
        title = request.form.get('title')
        method = request.form.get('method')
        url = request.form.get('url')
        run = request.form.get('run')
        headers = request.form.get('headers')
        pre_case_id = request.form.get('pre_case_id')
        pre_fields = request.form.get('pre_fields')
        request_body = request.form.get('request_body')
        expect_result = request.form.get('expect_result')
        assert_type = request.form.get('assert_type')
        pass_case = request.form.get('pass')
        msg = request.form.get('msg')
        remark = request.form.get('remark')

        if not pre_case_id or pre_case_id == '':
            pre_case_id = 0

        username = session['username']
        sql = f'''SELECT * FROM `yd_authen`.`tb_user` WHERE `email` = '{username}' AND `is_delete` = '0' '''
        mydb = MysqlDb()
        user = mydb.query(sql)
        update = user[0].get('name')
        sql = """
            UPDATE test.erp_case 
            SET app=%s, module=%s, title=%s, method=%s, url=%s, run=%s, headers=%s, pre_case_id=%s, pre_fields=%s, 
                request_body=%s, expect_result=%s, assert_type=%s, pass=%s, msg=%s, remark=%s, update_time=NOW() ,`update`=%s
            WHERE id=%s
        """

        cursor.execute(sql, (
            app_name, module, title, method, url, run, headers, pre_case_id, pre_fields, request_body,
            expect_result, assert_type, pass_case, msg, remark, update,id))
        db.commit()
        cursor.close()

        flash('编辑用例成功！')
        return redirect(url_for('api_list'))

    cursor.execute("SELECT * FROM test.erp_case WHERE id=%s", (id,))
    api_case = cursor.fetchone()
    cursor.close()

    return render_template('api_edit2.html', api_case=api_case)


def api_delete1(id):
    db = db_test.db_login()
    cursor = db.cursor()

    sql = "UPDATE test.erp_case SET is_del=1, update_time=NOW() WHERE id=%s"

    try:
        cursor.execute(sql, (id,))
        db.commit()
        flash('删除案例成功！')
    except Exception as e:
        db.rollback()
        flash(f'删除案例失败: {str(e)}')
    finally:
        cursor.close()

    return redirect(url_for('api_list'))



def Execute_api_test_project1():
    try:
        # 确保在 Flask 应用上下文中执行
        with current_app.app_context():
            db = db_test.db_login()  # 假设此方法存在并返回数据库连接
            cursor = db.cursor()

            # 清空通过状态
            cursor.execute("UPDATE `test`.`erp_case` SET `pass` = '待执行'")
            db.commit()

            # 获取所有测试用例
            cursor.execute('SELECT * FROM test.erp_case WHERE is_del = 0 and run = "是" ')
            api = cursor.fetchall()

            # 获取 token 和请求头
            token = login()
            headers = {'Content-Type': 'application/json', 'Authorization': f'{token}'}
            headers_en={'Content-Type': 'application/json', 'Authorization': f'{token}', "erp-language": 'en'}

            # 获取主机地址
            host_sql = "SELECT * FROM `test`.`config` WHERE `dict_key` = 'host' AND `is_del` = '0'"
            cursor.execute(host_sql)
            ress = cursor.fetchall()
            host = '{}'.format(ress[0][3])

            success_count = 0
            failure_count = 0

            # 遍历每个测试用例并执行 API 调用
            for entry in api:
                id = entry[0]  # 测试用例ID
                method = entry[4]  # 请求方法
                url = entry[5]  # 请求URL
                data = json.loads(entry[10])  # 请求数据

                try:
                    if method == 'POST':
                        # 发送 POST 请求
                        r = requests.post(url=host + url, json=data, headers=headers)
                        r_en = requests.post(url=host + url, json=data, headers=headers_en)
                        response_data = r.json()
                        response_data_en = r_en.json()

                        # 处理响应，根据 code 判断成功与否
                        if str(response_data.get('code')) == '200' and str(response_data_en.get('code')) =='200':
                            success_count += 1
                            sql = "UPDATE test.erp_case SET pass='通过', msg='测试通过,默认不打印响应信息', update_time=NOW() WHERE id=%s"
                            cursor.execute(sql, (id,))
                        elif str(response_data.get('code')) == '200' and str(response_data_en.get('code')) !='200':
                            failure_count += 1
                            sql = "UPDATE test.erp_case SET pass='失败', msg=%s, remark='英文版此接口报错',update_time=NOW() WHERE id=%s"
                            cursor.execute(sql, (json.dumps(response_data_en), id))
                        else:
                            failure_count += 1
                            sql = "UPDATE test.erp_case SET pass='失败', msg=%s, remark='中文版此接口报错',update_time=NOW() WHERE id=%s"
                            cursor.execute(sql, (json.dumps(response_data), id))

                        # 提交数据库更新
                        db.commit()

                except Exception as e:
                    failure_count += 1
                    print(f"处理测试用例 {id} 时出错: {e}")

            # 查询所有失败的测试用例
            msg = "SELECT * FROM test.erp_case WHERE pass='失败' AND is_del = 0"
            cursor.execute(msg)
            msg2 = cursor.fetchall()

            # 将失败用例转换为字符串并通过钉钉机器人发送
            if msg2:  # 确保有失败的测试用例才发送
                failure_messages = "\n".join([str(case) for case in msg2])
                bot = DingtalkChatbot(
                    "https://oapi.dingtalk.com/robot/send?access_token=xxxxxxx",
                    secret='SECxxxxxxx'
                )
                bot.send_text(f"以下测试用例执行失败:\n{failure_messages}")

            cursor.close()
            db.close()

            return jsonify({
                'message': f'批量执行完成，成功: {success_count}，失败: {failure_count}'
            })
    except Exception as e:
        print(f"Execute_api_test_project 执行时出错: {e}")
        return jsonify({'error': '服务器内部错误'}), 500



