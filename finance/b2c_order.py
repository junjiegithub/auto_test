from flask import request, render_template
from base.db_erp import MysqlDb


class b2c_order():
    def b2c_order_result(self):
        # 获取输入框中的数据
        input_list = request.form.get('input_list1', '')
        # print(input_list)
        result = []
        # 将输入的字符串按照逗号分隔成列表，并去掉首尾的单引号和多余的空格
        platformNumber = [item.strip().strip("'") for item in input_list.split(',') if item.strip()]
        mydb = MysqlDb()
        for nunber in platformNumber:
            count_sql=f'''
             SELECT
						COUNT(d.order_id_) AS count
            FROM
                yd_order.ord_order_info_b2c a
                LEFT JOIN yd_order.ord_order_info_b2c_detail b ON a.id_ = b.ord_order_info_b2c_id_
                LEFT JOIN yd_ware.ware_product_sellersku c ON b.ware_product_sellersku_id_ = c.id_
                LEFT JOIN yd_finance.fn_transaction_report d ON a.platform_number_ = d.order_id_ 
                AND c.seller_sku_ = d.sku_ 
                AND d.total_ > 0 
            WHERE
                a.is_delete_ = 0 
                AND b.is_delete_ = 0 
                AND c.is_delete_ = 0 
                AND d.is_delete_ = 0 
                AND a.an_shop_id_ = d.shop_id_
                AND d.time_ >= '2024-07-01 00:00:00'
                    AND a.sale_time_>='2024-07-01 00:00:00'
                    AND a.platform_number_  = '{nunber}'
                    GROUP BY d.id_,d.time_
            '''


            res_count = mydb.query(count_sql)
            count=res_count[0].get('count')
            # print(count)
            if len(res_count) > 1:
                count1 = res_count[1].get('count', 0)
            else:
                count1 = 0


            # print('count是{}，count1是{}'.format(count,count1))
            count2ced_sql = f'''
                        SELECT
            						COUNT(d.order_id_) AS count2ced
                        FROM
                            yd_order.ord_order_info_b2c a
                            LEFT JOIN yd_order.ord_order_info_b2c_detail b ON a.id_ = b.ord_order_info_b2c_id_
                            LEFT JOIN yd_ware.ware_product_sellersku c ON b.ware_product_sellersku_id_ = c.id_
                            LEFT JOIN yd_finance.fn_transaction_report d ON a.platform_number_ = d.order_id_ 
                            AND c.seller_sku_ = d.sku_ 
                            AND d.total_ > 0 
                        WHERE
                            a.is_delete_ = 0 
                            AND b.is_delete_ = 0 
                            AND c.is_delete_ = 0 
                            AND d.is_delete_ = 0 
                            AND a.an_shop_id_ = d.shop_id_
                            AND d.time_ >= '2024-09-01 00:00:00'
                                AND a.sale_time_>='2024-07-01 00:00:00'
                                AND a.platform_number_ = '{nunber}';
                        '''
            count2ced = mydb.query(count2ced_sql)
            # print(count2ced)

            count2ced_ = count2ced[0].get('count2ced')

            if  count>1 and count1 >1:
                #'302-6254652-1568314'
                spe_sql=f'''
                 SELECT
                CONCAT( 'UPDATE yd_order.ord_order_info_b2c_detail SET  settlement_time_ ="', d.time_, '"', 
                ', sale_amount_= "', d.product_sales_, '"', 
                ', withhold_sale_tax_= "', d.marketplace_withheld_tax_, '"',
                ', sale_tax_= "', d.product_sales_tax_, '"', 
                ', discount_cost_= "', d.promotional_rebates_, '"',
                ', commission_= "', d.selling_fees_, '"',
                ', last_freight_= "', d.fba_fees_, '"',
                ', other_cost_= "', d.total_ - d.product_sales_ - d.product_sales_tax_ - d.marketplace_withheld_tax_ - d.promotional_rebates_ - d.selling_fees_ - d.fba_fees_, '"',
                ', sale_total_= "', d.total_, '"',
                ' WHERE id_ = "', b.id_, '";' )  AS newsql
            FROM
                yd_order.ord_order_info_b2c a
                INNER JOIN yd_order.ord_order_info_b2c_detail b ON a.id_ = b.ord_order_info_b2c_id_
                INNER JOIN yd_ware.ware_product_sellersku c ON b.ware_product_sellersku_id_ = c.id_
                INNER JOIN  yd_finance.fn_transaction_report d ON a.platform_number_ = d.order_id_ 
                AND c.seller_sku_ = d.sku_ 
                AND d.total_ > 0 
            WHERE
                a.is_delete_ = 0 
                AND b.is_delete_ = 0 
                AND c.is_delete_ = 0 
                AND d.is_delete_ = 0 
                AND a.an_shop_id_ = d.shop_id_
                AND d.time_ >= '2024-07-01 00:00:00'
                    AND a.sale_time_>='2024-07-01 00:00:00'
                    AND a.platform_number_ ='{nunber}'
GROUP BY b.id_;
                '''

                spe_sql_res = mydb.query(spe_sql)
                # print(spe_sql_res)
                for sql2 in spe_sql_res:

                    spe_sql_res_r4 = mydb.execute(sql2['newsql'])
                    result.append(sql2)

            elif count2ced_>1:
                # print('count2ced大于2')
                sum_sql=f'''
                SELECT
    CONCAT( 'UPDATE yd_order.ord_order_info_b2c_detail SET  settlement_time_ ="', d.time_, '"', 
            ', sale_amount_= "', SUM(d.product_sales_), '"', 
            ', withhold_sale_tax_= "', SUM(d.marketplace_withheld_tax_), '"',
            ', sale_tax_= "', SUM(d.product_sales_tax_), '"', 
            ', discount_cost_= "', SUM(d.promotional_rebates_), '"',
            ', commission_= "', SUM(d.selling_fees_), '"',
            ', last_freight_= "', SUM(d.fba_fees_), '"',
            ', other_cost_= "', SUM(d.total_ - d.product_sales_ - d.product_sales_tax_ - d.marketplace_withheld_tax_ - d.promotional_rebates_ - d.selling_fees_ - d.fba_fees_), '"',
            ', sale_total_= "', SUM(d.total_), '"',
            ' WHERE id_ = "', b.id_, '";' )  AS newsql
FROM
    yd_order.ord_order_info_b2c a
    LEFT JOIN yd_order.ord_order_info_b2c_detail b ON a.id_ = b.ord_order_info_b2c_id_
    LEFT JOIN yd_ware.ware_product_sellersku c ON b.ware_product_sellersku_id_ = c.id_
    LEFT JOIN yd_finance.fn_transaction_report d ON a.platform_number_ = d.order_id_ 
        AND c.seller_sku_ = d.sku_ 
        AND d.total_ > 0 
WHERE
    a.is_delete_ = 0 
    AND b.is_delete_ = 0 
    AND c.is_delete_ = 0 
    AND d.is_delete_ = 0 
    AND a.an_shop_id_ = d.shop_id_
    AND d.time_ >= '2024-09-01 00:00:00'
    AND a.sale_time_ >= '2024-07-01 00:00:00'
    AND a.platform_number_ = '{nunber}'
GROUP BY b.id_;     
                '''
                # print(sum_sql)
                sum_count = mydb.query(sum_sql)
                # print(sum_count)
                for sql1 in sum_count:
                    # print(sql1)
                    r3 = mydb.execute(sql1['newsql'])
                    # print(sql1['newsql'])
                    # print(r3)
                    result.append(sql1)
                # sum_ = sum_count[0].get('newsql')
                # r4 = mydb.execute(sum_)
                # result.append(sum_)
            else:
                sql = f'''
                    SELECT
                a.platform_number_,
                    CONCAT( 'UPDATE yd_order.ord_order_info_b2c_detail SET  settlement_time_ ="', d.time_, '"',
                    ', sale_amount_= "', d.product_sales_, '"',
                    ', withhold_sale_tax_= "', d.marketplace_withheld_tax_, '"',
                    ', sale_tax_= "', d.product_sales_tax_, '"',
                    ', discount_cost_= "', d.promotional_rebates_, '"',
                    ', commission_= "', d.selling_fees_, '"',
                    ', last_freight_= "', d.fba_fees_, '"',
                    ', other_cost_= "', d.total_ - d.product_sales_ - d.product_sales_tax_ - d.marketplace_withheld_tax_ - d.promotional_rebates_ - d.selling_fees_ - d.fba_fees_, '"',
                    ', sale_total_= "', d.total_, '"',
                    ' WHERE id_ = "', b.id_, '";' )  AS newsql
                FROM
                    yd_order.ord_order_info_b2c a
                    LEFT JOIN yd_order.ord_order_info_b2c_detail b ON a.id_ = b.ord_order_info_b2c_id_
                    LEFT JOIN yd_ware.ware_product_sellersku c ON b.ware_product_sellersku_id_ = c.id_
                    LEFT JOIN yd_finance.fn_transaction_report d ON a.platform_number_ = d.order_id_
                    AND c.seller_sku_ = d.sku_
                    AND d.total_ > 0
                WHERE
                    a.is_delete_ = 0
                    AND b.is_delete_ = 0
                    AND c.is_delete_ = 0
                    AND d.is_delete_ = 0
                    AND a.an_shop_id_ = d.shop_id_
                    AND d.time_ >= '2024-09-01 00:00:00'
                        AND a.sale_time_>='2024-07-01 00:00:00'
                        AND a.platform_number_ = '{nunber}'
                        GROUP BY b.id_;
                    '''

                # print(sql)
                res = mydb.query(sql)
                # print(res)
                for sql1 in res:
                    # print(sql1)
                    r3 = mydb.execute(sql1['newsql'])
                    # print(sql1['newsql'])
                    # print(r3)
                    result.append(sql1)

        platformNumber = platformNumber[0] if len(platformNumber) == 1 else ','.join(platformNumber)


        return render_template('b2c_order_result.html', platformNumber=platformNumber, result=result)

if __name__ == '__main__':
    b2c_order1=b2c_order()