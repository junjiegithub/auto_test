import mysql
from flask import session, render_template, request, flash
from base import db_test, base_set
from base.db_erp import MysqlDb
import mysql.connector


def get_db_connection():
    return mysql.connector.connect(
        host=base_set.host,
        user=base_set.user,
        password=base_set.password,
        database=base_set.database,
        port=base_set.port,
        charset="utf8"
    )

def mysql_exec():
    username = session['username']
    return render_template('index2016.html')

def execute_sql():
    if request.method == 'GET':
        return render_template('sql_execute_form.html')

    sql_query = request.form['sql_query']
    db = get_db_connection()
    cursor = db.cursor()

    username = session['username']
    sql = f"SELECT * FROM `yd_authen`.`tb_user` WHERE `email` = '{username}' AND `is_delete` = '0'"
    mydb = MysqlDb()
    user = mydb.query(sql)
    id = user[0].get('id')
    name = user[0].get('name')
    rollback_sql = []  # 保存回滚 SQL
    msg = f"用户{name},邮箱 {username} 访问了 财务系统相关优化 页面,id是{id}，执行的sql是{sql_query}"

    try:
        db.autocommit = False  # 正确设置 autocommit 为 False

        sql_statements = sql_query.strip().split(';')
        results = []
        non_select_results = []

        for statement in sql_statements:
            statement = statement.strip()
            if not statement:
                continue

            print(f"Executing SQL: {statement}")

            # 针对 UPDATE 或 DELETE 操作生成回滚语句
            if statement.lower().startswith("update") or statement.lower().startswith("delete"):
                table_name = statement.split()[1] if statement.lower().startswith("update") else statement.split()[2]
                where_clause = statement.lower().split('where')[-1].strip()

                # 动态生成 SELECT 语句以获取回滚前的数据
                select_old_data = f"SELECT * FROM {table_name} WHERE {where_clause}"
                cursor.execute(select_old_data)
                old_data = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]

                # 为每行旧数据生成对应的 INSERT 语句
                for row in old_data:
                    values = ', '.join([f"'{str(value)}'" if value is not None else 'NULL' for value in row])
                    insert_statement = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({values});"
                    rollback_sql.append(insert_statement)

            # 处理 SELECT 操作
            if statement.lower().startswith("select"):
                cursor.execute(statement)
                result = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                results.append({"columns": columns, "rows": result})
            else:
                cursor.execute(statement)
                affected_rows = cursor.rowcount
                non_select_results.append(f"Query: '{statement}' executed successfully. Affected rows: {affected_rows}")

        db.commit()  # 提交事务

        # 生成 rollback_sql 字符串
        rollback_sql_str = '; '.join(rollback_sql)

        # 将日志信息插入到数据库中
        sql_log = '''INSERT INTO `test`.`erp_test_log`(`log_`, `rollback_sql`) VALUES (%s, %s)'''
        db1 = db_test.db_login()
        cursor_log = db1.cursor()
        cursor_log.execute(sql_log, (msg, rollback_sql_str))
        db1.commit()

        return render_template('result2016.html',
                               results=results,
                               non_select_results=non_select_results,
                               executed_sql=sql_query,
                               rollback_sql=rollback_sql_str)

    except mysql.connector.Error as e:
        db.rollback()  # 发生错误时回滚
        return f"An error occurred: {e.msg}"

    finally:
        cursor.close()
        db.close()
        cursor_log.close()


def rollback_changes():
    db = get_db_connection()
    cursor = db.cursor()

    rollback_sql = request.form['rollback_sql'].split(';')

    # 初始化用于存储回滚前数据的变量
    before_rollback_data = {}
    after_rollback_data = {}
    table_names_with_conditions = {}  # 用于存储表名和对应的 WHERE 子句
    table_name = None  # 初始化 table_name

    try:
        # 动态生成获取回滚前数据的查询语句
        for statement in rollback_sql:
            statement = statement.strip()
            if not statement:
                continue

            print(f"Processing statement: {statement}")

            # 解析表名和 WHERE 子句
            if "INSERT INTO" in statement or "UPDATE" in statement or "DELETE" in statement:
                if "INSERT INTO" in statement:
                    table_name = statement.split()[2]  # 获取表名
                    # 从 INSERT 语句中获取主键的列和值
                    columns_part = statement.split('(', 1)[1].split(')')[0]  # 获取列名部分
                    values_part = statement.split('VALUES', 1)[1].strip().split('(', 1)[1].split(')')[0]  # 获取值部分
                    columns = [col.strip() for col in columns_part.split(',')]
                    values = [val.strip().strip("'") for val in values_part.split(',')]

                    # 找到主键列的位置，并获取主键值
                    primary_key_column = 'id_'  # 假设主键是 'id_'，根据表结构需要调整
                    if primary_key_column in columns:
                        primary_key_value = values[columns.index(primary_key_column)]

                        # 生成删除现有主键记录的 SQL
                        delete_existing_record = f"DELETE FROM {table_name} WHERE {primary_key_column} = '{primary_key_value}'"
                        print(f"Deleting existing record with SQL: {delete_existing_record}")
                        cursor.execute(delete_existing_record)

                elif "UPDATE" in statement:
                    table_name = statement.split()[1]
                elif "DELETE" in statement:
                    table_name = statement.split()[2]

                print(f"Detected table: {table_name}")

                # 只有在 UPDATE 或 DELETE 操作中，我们才需要 WHERE 子句
                if "UPDATE" in statement or "DELETE" in statement:
                    if "WHERE" in statement.upper():
                        where_clause = statement.split("WHERE", 1)[1].strip()  # 获取 WHERE 子句
                        table_names_with_conditions[table_name] = where_clause
                        print(f"WHERE clause detected: {where_clause}")

                        # 动态构建回滚前查询 SQL，只选择当前表的相关列
                        select_old_data = f"SELECT * FROM {table_name} WHERE {where_clause}"
                        print(f"Executing SELECT for before rollback: {select_old_data}")
                        cursor.execute(select_old_data)
                        data = cursor.fetchall()
                        columns = [desc[0] for desc in cursor.description]

                        if data:
                            print(f"Data found before rollback: {data}")
                            before_rollback_data[table_name] = {"columns": columns, "rows": data}
                        else:
                            print("No data found before rollback.")

        # 设置 autocommit 为 False，开始执行回滚操作
        db.autocommit = False

        # 执行所有回滚的 INSERT 语句
        for statement in rollback_sql:
            statement = statement.strip()
            if statement:
                print(f"Rolling back with SQL: {statement}")
                cursor.execute(statement)

                # 验证回滚后数据是否恢复
                if table_name:  # 确保 table_name 存在
                    # 确保这里的列名是当前表的实际列名，而不是其他表的列名
                    if "id_" in columns:  # 确保表中有主键列 id_
                        select_query_after_rollback = f"SELECT * FROM {table_name} WHERE `id_` = '{primary_key_value}'"
                        cursor.execute(select_query_after_rollback)
                        rolled_back_data = cursor.fetchall()
                        columns = [desc[0] for desc in cursor.description]
                        print(f"Data after rollback: {rolled_back_data}")
                        if rolled_back_data:
                            after_rollback_data[table_name] = {"columns": columns, "rows": rolled_back_data}

        db.commit()  # 提交事务以执行回滚操作

        # 获取回滚后的数据，只查询符合 WHERE 条件的行
        for table_name, where_clause in table_names_with_conditions.items():
            select_new_data = f"SELECT * FROM {table_name} WHERE {where_clause}"
            print(f"Executing SELECT for after rollback: {select_new_data}")
            cursor.execute(select_new_data)
            data = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]

            if data:
                print(f"Data found after rollback: {data}")
                after_rollback_data[table_name] = {"columns": columns, "rows": data}
            else:
                print("No data found after rollback.")

        # 渲染回滚前后的数据
        flash('回滚成功！', 'success')
        return render_template('rollback_result.html',
                               before_rollback=before_rollback_data,
                               after_rollback=after_rollback_data)

    except mysql.connector.Error as e:
        db.rollback()  # 发生错误时回滚事务
        print(f"回滚失败：{e.msg}")
        flash(f"回滚失败：{e.msg}", 'danger')
        return "回滚失败"  # 或者返回一个错误页面

    finally:
        # 打印调试信息
        print("Before Rollback Data:", before_rollback_data)
        print("After Rollback Data:", after_rollback_data)

        cursor.close()
        db.close()
