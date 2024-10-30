from flask import Flask, render_template, session, request, flash, redirect, url_for     #引用，创建和管理Flask应用
from base import db_test, base_home, mysql_exce   #存放基础功能和配置文件
from finance import finence   #业务功能，做财务结算使用，主要是ToB结算，和退款数据生成
from api_test import  execute_api   #核心业务功能，自动化测试用例的管理
import os    #与操作系统进行交互，主要用户处理文件，路径，环境变量以及执行系统命令
import openpyxl   #用来处理excel表格
from werkzeug.utils import secure_filename  #防止路径注入攻击，减少文件名相关的错误，
import logging    #输出日志，DEBUG，INFO，WARNING，ERROR，CRITICAL
from apscheduler.schedulers.background import BackgroundScheduler  # Python 定时任务调度器，BackgroundScheduler它的任务是在后台运行调度的作业，允许程序继续执行其他操作。由于它在后台运行，因此不会阻塞主线程
import atexit   #专门清理程序退出关闭的，例如定时调度停止，数据库连接关闭，文件关闭，确保资源释放
from sqlalchemy import create_engine, func  #创建数据库连接引擎，使用内置func来执行聚合函数
from sqlalchemy.orm import sessionmaker, scoped_session  #创建数据库会话，每个线程都有自己的会话，防止并发
from sqlalchemy.ext.declarative import declarative_base  #定义类映射数据库表字段，使用模型类做增删改查
from sqlalchemy import Column, Integer, String, DateTime, Text  #处理数据库表结构映射
import matplotlib.pyplot as plt  #用于统计分析或数据可视化，例如各种饼状图,柱状图
from sqlalchemy.orm import declarative_base  # 修复警告

# 初始化 Flask 应用
app = Flask(__name__)

# 设置 session 的密钥，用于加密 session 数据
app.secret_key = 'xxxsec'

# 定义允许上传的文件扩展名
ALLOWED_EXTENSIONS = {'xlsx'}

# 设置文件上传的路径
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 设置日志级别为 DEBUG，确保所有日志都输出到控制台
# logging.basicConfig(filename='app.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
logging.basicConfig(level=logging.DEBUG)


# 定义定时任务执行的函数
def scheduled_execute_api_test():
    with app.app_context():  # 创建应用上下文，用于定时任务的执行
        logging.info("定时执行API测试项目。")
        try:
            Execute_api_test_project()  # 调用执行 API 测试项目的函数
        except Exception as e:
            logging.error(f"Error executing scheduled API test: {e}")


# 设置定时任务调度器
scheduler = BackgroundScheduler()

# 添加定时任务：每 60 分钟（1小时）执行一次 scheduled_execute_api_test 函数
scheduler.add_job(func=scheduled_execute_api_test, trigger="interval", minutes=60)

# 启动调度器
scheduler.start()

# 应用关闭时，关闭调度器，确保应用停止时定时任务也终止
atexit.register(lambda: scheduler.shutdown())

# 全局的 session 校验逻辑，排除对登录页和静态资源的校验
@app.before_request
def check_login():
    if request.endpoint == 'login' or request.endpoint == 'static':
        return  # 如果是登录或静态资源请求，跳过校验
    if 'username' not in session:  # 如果用户未登录，重定向至登录页面
        flash('登录失效,请重新登录！', 'danger')
        return redirect(url_for('login'))

# 登录路由处理，GET 和 POST 方法均支持
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    return base_home.login1()  # 使用 base_home 模块中的 login1 函数处理

# 首页路由，处理 GET 和 POST 请求
@app.route('/home/', methods=["GET", "POST"])
@app.route('/home', methods=["GET", "POST"])
def home():
    return render_template('index.html')  # 渲染主页模板

# 财务模块的主页面，处理 GET 和 POST 请求
@app.route('/finence', methods=["GET", "POST"])
def index():
    return finence.index()  # 调用 finence 模块中的 index 函数

# 财务处理的路由，处理 POST 请求
@app.route('/process', methods=['POST'])
def process():
    return finence.process()  # 调用 finence 模块中的 process 函数

# 财务 B2C 处理的路由，处理 POST 请求
@app.route('/fin_b2c', methods=['POST'])
def fin_b2c():
    return finence.fin_b2c()  # 调用 finence 模块中的 fin_b2c 函数

# 显示基础页面，处理 GET 和 POST 请求
@app.route('/home/base', methods=['GET', 'POST'])
def home_base():
    return render_template('home_base.html')

# MySQL 执行页面，处理 GET 请求
@app.route('/home/mysql', methods=['GET'])
@app.route('/home/mysql/', methods=['GET'])
def mysql_exec():
    return mysql_exce.mysql_exec()  # 调用 mysql_exce 模块中的 mysql_exec 函数

# 执行 SQL 页面，处理 GET 和 POST 请求
@app.route('/home/mysql/execute', methods=['GET', 'POST'])
def execute_sql():
    return mysql_exce.execute_sql()  # 调用 mysql_exce 模块中的 execute_sql 函数

# 回滚 MySQL 更改的路由，处理 POST 请求
@app.route('/home/mysql/rollback', methods=['POST'])
def rollback_changes():
    return mysql_exce.rollback_changes()  # 调用 mysql_exce 模块中的 rollback_changes 函数

# 判断上传的文件是否符合允许的扩展名
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# API 导入接口，处理 POST 请求，文件上传和处理
@app.route('/api/import', methods=['POST'])
def api_import():
    app.logger.debug('进入文件上传处理')

    if 'file' not in request.files:  # 如果请求中没有文件，报错并重定向
        flash('没有选择文件', 'error')
        app.logger.error('没有文件上传')
        return redirect(url_for('api_list'))

    file = request.files['file']

    if file and allowed_file(file.filename):  # 如果文件存在且是允许的类型
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])  # 如果上传目录不存在，创建目录

        filename = secure_filename(file.filename)  # 获取安全文件名
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)  # 保存文件到指定路径
        app.logger.debug(f'保存文件到路径: {file_path}')
        file.save(file_path)  # 保存文件

        try:
            wb = openpyxl.load_workbook(file_path)  # 打开上传的 Excel 文件
            sheet = wb.active  # 读取第一个工作表
            db = db_test.db_login()  # 连接数据库
            cursor = db.cursor()

            for row in sheet.iter_rows(min_row=2, values_only=True):  # 从第二行开始读取数据
                # 提取数据并进行数据库插入操作
                app_name, module, title, method, url, run, headers, pre_case_id, pre_fields, request_body, expect_result, assert_type, pass_case, msg, remark = row
                app.logger.debug(f'导入数据: {row}')
                pre_case_id = pre_case_id if pre_case_id != '' else None

                sql = """
                    INSERT INTO test.erp_case (app, module, title, method, url, run, headers, pre_case_id, pre_fields, request_body, expect_result, assert_type, pass, msg, remark, creat_time, update_time, is_del)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), 0)
                """
                # 执行 SQL 语句
                cursor.execute(sql, (
                    app_name, module, title, method, url, run, headers, pre_case_id, pre_fields, request_body,
                    expect_result, assert_type, pass_case, msg, remark
                ))

            db.commit()  # 提交事务
            cursor.close()
            flash('批量导入成功！', 'success')
            app.logger.debug('批量导入成功')
        except Exception as e:
            db.rollback()  # 出错时回滚事务
            error_message = f'批量导入失败：{str(e)}'
            app.logger.error(error_message)
            flash(error_message, 'error')
        finally:
            if os.path.exists(file_path):  # 删除临时文件
                os.remove(file_path)

        return redirect(url_for('api_list'))  # 成功后重定向至 API 列表页面

    flash('上传文件格式不支持，仅支持 .xlsx 格式', 'error')
    app.logger.error('上传文件格式不支持')
    return redirect(url_for('api_list'))  # 上传文件格式错误时的处理

# API 列表页面，处理 GET 请求
@app.route('/api', methods=['GET'])
def api_list():
    return execute_api.api_list1()  # 调用 execute_api 模块中的 api_list1 函数

# 添加新 API，处理 GET 和 POST 请求
@app.route('/api/new', methods=['GET', 'POST'])
def api_add():
    return execute_api.api_add1()  # 调用 execute_api 模块中的 api_add1 函数

# 编辑 API，处理 GET 和 POST 请求，传递 API 的 id
@app.route('/api/edit/<int:id>', methods=['GET', 'POST'])
def api_edit(id):
    return execute_api.api_edit1(id=id)  # 调用 execute_api 模块中的 api_edit1 函数

# 删除 API，处理 POST 请求
@app.route('/api/delete/<int:id>', methods=['POST'])
def api_delete(id):
    return execute_api.api_delete1(id=id)  # 调用 execute_api 模块中的 api_delete1 函数

# 执行 API 测试项目，处理 GET 请求
@app.route('/api/excute', methods=['GET'])
def Execute_api_test_project():
    return execute_api.Execute_api_test_project1()  # 调用 execute_api 模块中的 Execute_api_test_project1 函数

# SQLAlchemy 配置，创建数据库连接（根据具体数据库配置）
DATABASE_URI = 'mysql+pymysql://xxxx'
engine = create_engine(DATABASE_URI)

# 使用 scoped_session 管理 session，确保线程安全
session_factory = sessionmaker(bind=engine)
db_session = scoped_session(session_factory)

# 声明数据库模型基类
Base = declarative_base()

# 定义 ERPCase 模型（对应数据库中的 erp_case 表）
class ERPCase(Base):
    __tablename__ = 'erp_case'

    # 定义表中的列
    id = Column(Integer, primary_key=True)
    app = Column(String(128))
    module = Column(String(128))
    title = Column(String(128))
    method = Column(String(128))
    url = Column(String(128))
    run = Column(String(32))
    headers = Column(String(128))
    pre_case_id = Column(String(128))
    pre_fields = Column(String(128))
    request_body = Column(String(1024))
    expect_result = Column(String(1024))
    assert_type = Column(String(64))
    pass_status = Column(String(64), name='pass')  # pass 状态
    msg = Column(Text)
    update_time = Column(DateTime)
    creat_time = Column(DateTime)
    remark = Column(String(255))
    is_del = Column(Integer)
    creat = Column(String(255))
    update = Column(String(255))

# 获取测试用例统计数据
def get_case_statistics():
    db_session.expire_all()  # 刷新 session，确保获取最新数据

    # 查询总测试用例数量，排除 is_del = 1 的测试用例
    total_cases = db_session.query(func.count(ERPCase.id)).filter(ERPCase.is_del == 0).scalar()

    # 查询不同应用的数量
    total_apps = db_session.query(func.count(func.distinct(ERPCase.app))).filter(ERPCase.is_del == 0).scalar()

    # 按 app 和 module 分组，查询每个模块的测试用例数量
    modules_per_app = db_session.query(
        ERPCase.app, ERPCase.module, func.count(ERPCase.id).label('case_count')
    ).filter(ERPCase.is_del == 0).group_by(ERPCase.app, ERPCase.module).all()

    # 查询各状态（通过、待执行、失败）的测试用例数量
    passed_cases = db_session.query(func.count(ERPCase.id)).filter(ERPCase.pass_status == '通过', ERPCase.is_del == 0).scalar()
    pending_cases = db_session.query(func.count(ERPCase.id)).filter(ERPCase.pass_status == '待执行', ERPCase.is_del == 0).scalar()
    to_execute_cases = db_session.query(func.count(ERPCase.id)).filter(ERPCase.pass_status == '失败', ERPCase.is_del == 0).scalar()

    # 按创建人分组，查询每个创建人的测试用例数量
    cases_per_creator = db_session.query(ERPCase.creat, func.count(ERPCase.id)).filter(ERPCase.is_del == 0).group_by(ERPCase.creat).all()

    return {
        'total_cases': total_cases,  # 总测试用例数
        'total_apps': total_apps,  # 不同应用的数量
        'modules_per_app': modules_per_app,  # 每个模块的测试用例数量
        'passed_cases': passed_cases,  # 通过的测试用例数
        'pending_cases': pending_cases,  # 待执行的测试用例数
        'to_execute_cases': to_execute_cases,  # 失败的测试用例数
        'cases_per_creator': cases_per_creator  # 每个创建人的测试用例数量
    }

# 生成统计图表（饼状图和条形图）
def generate_charts(statistics):
    # 生成饼状图（测试用例状态分布）
    labels = ['通过', '待执行', '失败']
    sizes = [statistics['passed_cases'], statistics['pending_cases'], statistics['to_execute_cases']]
    plt.figure(figsize=(6, 6))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)  # 设置图表样式
    plt.title('测试用例状态分布')  # 设置图表标题
    pie_chart_path = 'static/pie_chart.png'  # 保存饼状图路径
    plt.savefig(pie_chart_path)  # 保存饼状图到文件
    plt.close()  # 关闭图表

    # 生成条形图（每个创建人的测试用例数）
    creators = [creator for creator, count in statistics['cases_per_creator']]
    case_counts = [count for creator, count in statistics['cases_per_creator']]
    plt.figure(figsize=(10, 6))
    plt.bar(creators, case_counts)  # 创建条形图
    plt.xlabel('创建人')  # 设置 X 轴标签
    plt.ylabel('测试用例数')  # 设置 Y 轴标签
    plt.title('每个创建人的测试用例数量')  # 设置图表标题
    plt.xticks(rotation=45, ha='right')  # 旋转 X 轴刻度
    bar_chart_path = 'static/bar_chart.png'  # 保存条形图路径
    plt.savefig(bar_chart_path)  # 保存条形图到文件
    plt.close()  # 关闭图表

    return pie_chart_path, bar_chart_path  # 返回图表路径

# 统计报表页面，展示统计结果
@app.route('/report', methods=['GET'])
def report():
    statistics = get_case_statistics()  # 获取统计数据
    pie_chart, bar_chart = generate_charts(statistics)  # 生成图表

    return render_template('report.html', statistics=statistics, pie_chart=pie_chart, bar_chart=bar_chart)  # 渲染报表页面

# 禁用缓存，确保每次加载页面时都是最新的内容
@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

# 应用上下文关闭时，关闭 session
@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()  # 移除 scoped_session

# 主程序入口
if __name__ == '__main__':
    if not os.path.exists('static'):
        os.makedirs('static')  # 确保静态目录存在，用于保存图表
    app.run(debug=True, host='0.0.0.0', port=666)  # 启动应用，监听端口 666
