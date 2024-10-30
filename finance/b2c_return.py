import logging
import traceback
from flask import request
import requests
from base.db_erp import MysqlDb
import json
from base import base_set
from flask import render_template

class b2c_return():
    def login(self):
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



    def b2c_returno(self):
        # 获取输入框中的数据
        input_list = request.form.get('input_list', '')

        # 将输入的字符串按照逗号分隔成列表，并去掉首尾的单引号和多余的空格
        platformNumber = [item.strip().strip("'") for item in input_list.split(',') if item.strip()]

        headers = {'Content-Type': 'application/json', 'Authorization': '{0}'.format(self.login())}
        addreturn_url = base_set.addreturn_url
        ordOrderInfoB2c = base_set.ordOrderInfoB2c
        result = []
        al_time = '%2024-09%'

        # 设置日志记录配置
        logging.basicConfig(filename='error_log.log', level=logging.ERROR,
                            format='%(asctime)s - %(levelname)s - %(message)s')

        for nunber in platformNumber:
            report_findata_sql = '''
                            SELECT
                        * 
                    FROM
                        `yd_finance`.`fn_transaction_report` 
                    WHERE
                        `time_` LIKE '{}' 
                        AND `order_id_` = '{}' 
                        AND `is_delete_` = '0' 
                        AND sku_ IS NOT NULL
                        AND sku_ !=''
                        AND `total_` < '0'
                            '''.format(al_time, nunber)
            mydb = MysqlDb()
            res_time = mydb.query(report_findata_sql)

            for product_sales_ in res_time:
                # try:
                    ordOrderInfoB2c_data = {
                        "contentType0": "2",
                        "content0": [nunber]
                    }
                    res = requests.post(ordOrderInfoB2c, headers=headers, json=ordOrderInfoB2c_data)
                    res = res.json()

                    baseCompanyId = res['data']['list'][0]['baseCompanyId']
                    basePlatformId = res['data']['list'][0]['basePlatformId']
                    anShopId = res['data']['list'][0]['anShopId']
                    baseCurrencyId = res['data']['list'][0]['baseCurrencyId']
                    wareProductSellerskuId = res['data']['list'][0]['wareProductSellerskuId']
                    wareProductSkuId = res['data']['list'][0]['wareSellerskuSkuRelVoList'][0]['wareProductSkuId']
                    tu_url = res['data']['list'][0]['wareSellerskuSkuRelVoList'][0]['url']
                    wareProductName = res['data']['list'][0]['wareSellerskuSkuRelVoList'][0]['wareProductName']
                    model = res['data']['list'][0]['wareSellerskuSkuRelVoList'][0]['model']
                    sku = res['data']['list'][0]['wareSellerskuSkuRelVoList'][0]['sku']
                    sellersku = res['data']['list'][0]['sellerSku']

                    exchangeRate_sql = '''
                                    SELECT
                            rate_ 
                        FROM
                            `yd_base`.`base_exchange_rate` 
                        WHERE
                            `org_currency_id_` = '{}' 
                            AND `effec_date_` LIKE '{}'
                                    '''.format(baseCurrencyId, al_time)

                    rate_sql = mydb.query(exchangeRate_sql)
                    rate_ = rate_sql[0].get('rate_')
                    rate_ = str(rate_)

                    time_ = product_sales_.get('time_')
                    saleAmount = product_sales_.get('product_sales_')
                    saleTax = product_sales_.get('product_sales_tax_') + product_sales_.get('shipping_credits_tax_') + \
                              product_sales_.get('giftwrap_credits_tax_')
                    withholdSaleTax = product_sales_.get('marketplace_withheld_tax_') + product_sales_.get(
                        'promotional_rebates_tax_')
                    platformPackageCost = product_sales_.get('gift_wrap_credits_')
                    commission = product_sales_.get('selling_fees_')
                    discount_cost = product_sales_.get('promotional_rebates_') + product_sales_.get(
                        'shipping_credits_')
                    lastFreight = product_sales_.get('fba_fees_')
                    totalOther = (
                            product_sales_.get('total_') - product_sales_.get('product_sales_') - product_sales_.get(
                        'product_sales_tax_') \
                            - product_sales_.get('shipping_credits_') - product_sales_.get(
                        'shipping_credits_tax_') - \
                            product_sales_.get('gift_wrap_credits_') \
                            - product_sales_.get('giftwrap_credits_tax_') - product_sales_.get(
                        'regulatory_fee_') - \
                            product_sales_.get('tax_on_regulatory_fee_') \
                            - product_sales_.get('promotional_rebates_') - product_sales_.get(
                        'marketplace_withheld_tax_') - product_sales_.get('selling_fees_') \
                            - product_sales_.get('fba_fees_'))

                    refundTotal = product_sales_.get('total_')

                    addreturn_url_data = {
                        "number": "--",
                        "platformNumber": nunber,
                        "baseCompanyId": baseCompanyId,
                        "basePlatformId": basePlatformId,
                        "anShopId": anShopId,
                        "refundTime": time_,
                        "baseCurrencyId": baseCurrencyId,
                        "exchangeRate": rate_,
                        "refundB2cDetailList": [
                            {
                                "wareProductSellerskuId": wareProductSellerskuId,
                                "operateBy": "-99999",
                                "wareProductSkuId": wareProductSkuId,
                                "url": tu_url,
                                "wareProductName": wareProductName,
                                "model": model,
                                "sku": sku,
                                "sellersku": sellersku,
                                "title": "",
                                "transportationStock": 0,
                                "amount": "1",
                                "titleEn": "En",
                                "modelNumber": '',
                                "saleAmount": saleAmount,
                                "refundTotal": refundTotal,
                                "totalOther": totalOther,
                                "saleTax": saleTax,
                                "withholdSaleTax": withholdSaleTax,
                                "firstFreight": "0",
                                "tariff": "0",
                                "platformPackageCost": platformPackageCost,
                                "discountCost": discount_cost,
                                "commission": commission,
                                "lastFreight": lastFreight,
                                "otherCost": totalOther
                            }
                        ]
                    }

                    for detail in addreturn_url_data['refundB2cDetailList']:
                        detail['saleAmount'] = float(detail['saleAmount'])
                        detail['refundTotal'] = float(detail['refundTotal'])
                        detail['totalOther'] = float(detail['totalOther'])
                        detail['saleTax'] = float(detail['saleTax'])
                        detail['withholdSaleTax'] = float(detail['withholdSaleTax'])
                        detail['platformPackageCost'] = float(detail['platformPackageCost'])
                        detail['discountCost'] = float(detail['discountCost'])
                        detail['commission'] = float(detail['commission'])
                        detail['lastFreight'] = float(detail['lastFreight'])
                        detail['otherCost'] = float(detail['otherCost'])

                        re = requests.post(addreturn_url, headers=headers, json=addreturn_url_data)
                        re = re.json()

                        if str(re['msg']) == 'success':
                            print(str(re['msg']))
                            result.append(nunber)
                        else:
                            print('生成退款单失败，失败返回原因：{}'.format(re['msg']))


        formatted_response = json.dumps(result, indent=4, ensure_ascii=False)
        # 处理后的列表（在这里你可以对数据列表进行进一步处理）
        processed_data = f"您需要生成B2C退款的平台订单号为: {platformNumber}"
        order_str = result[0] if len(result) == 1 else ','.join(result)

        formatted_response1 = platformNumber[0] if len(platformNumber) == 1 else ','.join(platformNumber)

        # 使用render_template来渲染HTML
        return render_template('b2c_returno_result.html', formatted_response1=formatted_response1, order_str=order_str)


if __name__ == '__main__':
    b2c_return1 = b2c_return().login()