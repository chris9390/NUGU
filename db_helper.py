import time
import pymysql



class DB_Helper:
    def __init__(self, conn):
        self.conn = conn
        self.print_sql_len = 200

    def now(self):
        return time.strftime('%Y-%m-%d %H:%M:%S')


    def print_sql(self, sql):
        if len(sql) >= self.print_sql_len:
            sql_print = sql[:self.print_sql_len] + '...'
        else:
            sql_print = sql

        print("SQL:", sql_print)


    def reconnect(self):
        self.conn = pymysql.connect(host='163.239.169.54',
                                    port=3306,
                                    user='s20131533',
                                    passwd='s20131533',
                                    db='slu_corpus',
                                    charset='utf8',
                                    cursorclass=pymysql.cursors.DictCursor)





    # ===============================================================================================
    # ===============================================================================================
    # ===============================================================================================
    # ===============================================================================================
    # ===============================================================================================
    # ===============================================================================================

    def insert_new_article(self, id, url, title):
        c = self.conn.cursor()

        sql = "INSERT INTO ArticleTable (article_id, article_url, article_title) VALUES ('%s', '%s', '%s')" % (id, url, title)

        self.print_sql(sql)

        c.execute(sql)
        self.conn.commit()

        print("Number of rows inserted: %d" % c.rowcount)

        c.close()


    def insert_new_text(self, dict):
        c = self.conn.cursor()

        sql = "INSERT INTO SentenceTable (sent_id, sent_original, sent_is_added, ArticleTable_article_id) " \
              "VALUES ('%s', '%s', '%s', '%s')" % (dict['sent_id'], dict['sent_original'], dict['sent_is_added'], dict['ArticleTable_article_id'])

        self.print_sql(sql)


        c.execute(sql)
        self.conn.commit()

        print("Number of rows inserted: %d" % c.rowcount)

        c.close()


    def insert_user_info(self, user_info):
        c = self.conn.cursor()

        sql = "INSERT INTO users (user_id, user_pw, user_name, user_birth, user_gender, user_email) " \
              "VALUES ('%s', '%s', '%s', '%s', '%s', '%s')" % (user_info['user_id'], user_info['user_pw'], user_info['user_name'], user_info['user_birth'], user_info['user_gender'], user_info['user_email'])

        self.print_sql(sql)

        c.execute(sql)
        self.conn.commit()
        print("Number of rows inserted: %d" % c.rowcount)

        c.close()


    # ===============================================================================================


    def total_count_text_search(self, text, inc_num):
        c = self.conn.cursor()

        # 숫자 미포함
        if inc_num == '0':
            regex_req = " AND ((sent_original NOT REGEXP '[0-9]' AND sent_confirm = 0) OR (sent_converted NOT REGEXP '[0-9]' AND sent_confirm = 1))"
        # 숫자 포함
        elif inc_num == '1':
            regex_req = " AND ((sent_original REGEXP '[0-9]' AND sent_confirm = 0) OR (sent_converted REGEXP '[0-9]' AND sent_confirm = 1))"
        # 모두
        else:
            regex_req = ""



        sql = "SELECT count(*) as total_count FROM SentenceTable" \
              " WHERE ((sent_original LIKE '%%%s%%' AND sent_confirm = 0) OR (sent_original LIKE '%%%s%%' AND sent_confirm = 1))" % (text, text)
        sql += regex_req


        c.execute(sql)

        total_count = c.fetchone()['total_count']
        c.close()
        return total_count


    def total_count_clicked_article(self, id, inc_num):
        c = self.conn.cursor()


        # 숫자 미포함
        if inc_num == '0':
            regex_req = " AND ((sent_original NOT REGEXP '[0-9]' AND sent_confirm = 0) OR (sent_converted NOT REGEXP '[0-9]' AND sent_confirm = 1))"
        # 숫자 포함
        elif inc_num == '1':
            regex_req = " AND ((sent_original REGEXP '[0-9]' AND sent_confirm = 0) OR (sent_converted REGEXP '[0-9]' AND sent_confirm = 1))"
        # 모두
        else:
            regex_req = ""


        sql = "SELECT COUNT(*) as total_count FROM SentenceTable WHERE ArticleTable_article_id = %s" % id
        sql += regex_req


        c.execute(sql)

        total_count = c.fetchone()['total_count']
        c.close()
        return total_count


    def total_count_clicked_search(self, id, text, inc_num):
        c = self.conn.cursor()

        # 숫자 미포함
        if inc_num == '0':
            regex_req = " AND ((sent_original NOT REGEXP '[0-9]' AND sent_confirm = 0) OR (sent_converted NOT REGEXP '[0-9]' AND sent_confirm = 1))"
        # 숫자 포함
        elif inc_num == '1':
            regex_req = " AND ((sent_original REGEXP '[0-9]' AND sent_confirm = 0) OR (sent_converted REGEXP '[0-9]' AND sent_confirm = 1))"
        # 모두
        else:
            regex_req = ""

        sql = "SELECT COUNT(*) as total_count FROM SentenceTable"
        sql += " WHERE ArticleTable_article_id = %s" % id
        sql += " AND ((sent_original LIKE '%%%s%%' AND sent_confirm = 0) OR (sent_original LIKE '%%%s%%' AND sent_confirm = 1))" % (text, text)
        sql += regex_req

        c.execute(sql)

        total_count = c.fetchone()['total_count']
        c.close()
        return total_count



    def total_count_every_sentences(self, inc_num):
        c = self.conn.cursor()

        # 숫자 미포함
        if inc_num == '0':
            regex_req = " WHERE ((sent_original NOT REGEXP '[0-9]' AND sent_confirm = 0) OR (sent_converted NOT REGEXP '[0-9]' AND sent_confirm = 1))"
        # 숫자 포함
        elif inc_num == '1':
            regex_req = " WHERE ((sent_original REGEXP '[0-9]' AND sent_confirm = 0) OR (sent_converted REGEXP '[0-9]' AND sent_confirm = 1))"
        # 모두
        else:
            regex_req = ""


        sql = "SELECT count(*) as total_count FROM SentenceTable"
        sql += regex_req

        c.execute(sql)

        total_count = c.fetchone()['total_count']
        c.close()
        return total_count



    def total_count_article_search(self, text):
        c = self.conn.cursor()

        sql = "SELECT count(*) as total_count FROM ArticleTable WHERE article_title LIKE '%%%s%%'" % text


        c.execute(sql)


        total_count = c.fetchone()['total_count']
        c.close()
        return total_count


    def total_count_article_category(self, sid1, sid2):
        c = self.conn.cursor()

        sql = "SELECT count(*) as total_count FROM ArticleTable WHERE article_sid1 = '%s' and article_sid2 = '%s'" % (sid1, sid2)

        c.execute(sql)

        total_count = c.fetchone()['total_count']
        c.close()
        return total_count



    def total_count_every_articles(self):
        c = self.conn.cursor()

        sql = "SELECT count(*) as total_count FROM ArticleTable"

        c.execute(sql)

        total_count = c.fetchone()['total_count']
        c.close()
        return total_count




    def select_every_rows_from_table(self, table_name):
        c = self.conn.cursor()

        sql = "SELECT * FROM %s" % table_name


        c.execute(sql)

        rows = c.fetchall()

        c.close()
        return rows



    def select_before_row_from_sentence(self, sent_id, article_id):
        c = self.conn.cursor()

        if article_id != None:
            sql = "SELECT * FROM SentenceTable WHERE sent_id < %s AND ArticleTable_article_id = %s ORDER BY sent_id DESC LIMIT 1" % (sent_id, article_id)
        elif article_id == None:
            sql = "SELECT * FROM SentenceTable WHERE sent_id < %s ORDER BY sent_id DESC LIMIT 1" % sent_id

        c.execute(sql)

        row = c.fetchone()

        c.close()
        return row


    def select_after_row_from_sentence(self, sent_id, article_id):
        c = self.conn.cursor()

        if article_id != None:
            sql = "SELECT * FROM SentenceTable WHERE sent_id > %s AND ArticleTable_article_id = %s ORDER BY sent_id ASC LIMIT 1" % (sent_id, article_id)
        elif article_id == None:
            sql = "SELECT * FROM SentenceTable WHERE sent_id > %s ORDER BY sent_id ASC LIMIT 1" % sent_id

        c.execute(sql)

        row = c.fetchone()

        c.close()
        return row



    def select_every_rows_from_sentence_by_id(self, article_id):
        c = self.conn.cursor()

        sql = "SELECT * FROM SentenceTable WHERE ArticleTable_article_id= %s" % article_id

        c.execute(sql)

        rows = c.fetchall()
        c.close()
        return rows


    def select_row_from_sentence_by_conds(self, sent_id, article_id):
        c = self.conn.cursor()

        sql = "SELECT * FROM SentenceTable WHERE sent_id = %s AND ArticleTable_article_id = %s" % (sent_id, article_id)

        c.execute(sql)

        rows = c.fetchall()
        c.close()
        return rows




    def select_data_from_table_by_id(self, column_name, table_name, id):
        c = self.conn.cursor()

        if table_name == 'ArticleTable':
            sql = "SELECT %s as data FROM %s WHERE article_id = %s" % (column_name, table_name, id)
        elif table_name == 'SentenceTable':
            sql = "SELECT %s as data FROM %s WHERE sent_id = %s" % (column_name, table_name, id)


        c.execute(sql)


        row = c.fetchone()['data']
        c.close()
        return row



    def select_largest_sent_id(self):
        c = self.conn.cursor()

        sql = "SELECT sent_id as id FROM SentenceTable ORDER BY sent_id DESC LIMIT 1"

        c.execute(sql)


        row = c.fetchone()['id']
        c.close()
        return row


    def select_every_rows_including_text_from_table(self, table_name, text):
        c = self.conn.cursor()


        sql = "SELECT * FROM %s WHERE (sent_original LIKE '%%%s%%' AND sent_confirm = 0) OR " \
                                        "(sent_converted LIKE '%%%s%%' AND sent_confirm = 1)" % (table_name, text, text)

        c.execute(sql)


        rows = c.fetchall()
        c.close()
        return rows




    def select_one_column(self, column_name, table_name):
        c = self.conn.cursor()

        sql = "SELECT %s FROM %s" % (column_name, table_name)


        c.execute(sql)

        rows = c.fetchall()
        c.close()
        return rows


    def select_column_with_cond(self, column1, column2, table_name, sid1, sid2):
        c = self.conn.cursor()

        sql = "SELECT %s, %s FROM %s WHERE article_sid1 = '%s' and article_sid2 = '%s'" % (column1, column2, table_name, sid1, sid2)

        c.execute(sql)


        rows = c.fetchall()
        c.close()
        return rows



    def select_article_with_sid1_sid2(self, sid1, sid2):
        c = self.conn.cursor()

        sql = "SELECT article_id, article_aid, article_url, article_title, article_uploaded_date, article_collected_date, article_sid1, article_sid2 FROM ArticleTable" \
              " WHERE article_sid1 = '%s' AND article_sid2 = '%s'" % (sid1, sid2)

        c.execute(sql)

        rows = c.fetchall()
        c.close()
        return rows

    def select_article_with_sid1(self, sid1):
        c = self.conn.cursor()

        sql = "SELECT article_id, article_aid, article_url, article_title, article_uploaded_date, article_collected_date, article_sid1, article_sid2 FROM ArticleTable" \
              " WHERE article_sid1 = '%s'" % sid1

        c.execute(sql)

        rows = c.fetchall()
        c.close()
        return rows

    def select_article_with_no_cond(self):
        c = self.conn.cursor()

        sql = "SELECT article_id, article_aid, article_url, article_title, article_uploaded_date, article_collected_date, article_sid1, article_sid2 FROM ArticleTable"

        c.execute(sql)

        rows = c.fetchall()
        c.close()
        return rows


    def select_article_with_date_sid1_sid2(self, sid1, sid2,fromdate, todate):
        c = self.conn.cursor()

        sql = "SELECT article_id, article_aid, article_url, article_title, article_uploaded_date, article_collected_date, article_sid1, article_sid2 FROM ArticleTable" \
              " WHERE (article_sid1 = '%s' AND article_sid2 = '%s') AND (article_uploaded_date >= '%s' AND article_uploaded_date <= '%s')" % (sid1, sid2, fromdate, todate)

        c.execute(sql)

        rows = c.fetchall()
        c.close()
        return rows

    def select_article_with_date_sid1(self, sid1,fromdate, todate):
        c = self.conn.cursor()

        sql = "SELECT article_id, article_aid, article_url, article_title, article_uploaded_date, article_collected_date, article_sid1, article_sid2 FROM ArticleTable" \
              " WHERE article_sid1 = '%s' AND (article_uploaded_date >= '%s' AND article_uploaded_date <= '%s')" % (sid1, fromdate, todate)

        c.execute(sql)

        rows = c.fetchall()
        c.close()
        return rows


    def select_article_with_date(self, fromdate, todate):
        c = self.conn.cursor()

        sql = "SELECT article_id, article_aid, article_url, article_title, article_uploaded_date, article_collected_date, article_sid1, article_sid2 FROM ArticleTable" \
              " WHERE (article_uploaded_date >= '%s' AND article_uploaded_date <= '%s')" % (fromdate, todate)

        c.execute(sql)

        rows = c.fetchall()
        c.close()
        return rows

    # ===============================================================================================

    def update_sent_converted(self, text, id):
        c = self.conn.cursor()

        sql = "UPDATE SentenceTable SET sent_converted = '%s' WHERE sent_id = %s" % (text, id)

        self.print_sql(sql)

        c.execute(sql)
        self.conn.commit()

        print("Number of rows updated: %d" % c.rowcount)
        c.close()


    def update_sent_modified_date(self, id):
        c = self.conn.cursor()

        current = self.now()
        sql = "UPDATE SentenceTable SET sent_modified_date = '%s' WHERE sent_id = %s" % (current, id)

        self.print_sql(sql)

        c.execute(sql)
        self.conn.commit()


        print("Number of rows updated: %d" % c.rowcount)
        c.close()



    def update_sent_confirm(self, id):
        c = self.conn.cursor()

        sql = "UPDATE SentenceTable SET sent_confirm = 1 WHERE sent_id = %s" % id

        self.print_sql(sql)

        c.execute(sql)
        self.conn.commit()


        print("Number of rows updated: %d" % c.rowcount)
        c.close()



    def update_sent_ambiguity(self, value, id):
        c = self.conn.cursor()

        sql = "UPDATE SentenceTable SET sent_ambiguity = %s WHERE sent_id = %s" % (value, id)

        self.print_sql(sql)

        c.execute(sql)
        self.conn.commit()


        print("Number of rows updated: %d" % c.rowcount)
        c.close()



    def update_sent_converted_count(self, converted_count, id):
        c = self.conn.cursor()

        sql = "UPDATE SentenceTable SET sent_converted_count = %s WHERE sent_id = %s" % (converted_count, id)

        self.print_sql(sql)

        c.execute(sql)
        self.conn.commit()


        print("Number of rows updated: %d" % c.rowcount)
        c.close()



    def update_article_sent_count(self, plus_or_minus, id):
        c = self.conn.cursor()

        sql = "UPDATE ArticleTable SET article_sent_count = article_sent_count + %s WHERE article_id = %s" % (plus_or_minus, id)

        self.print_sql(sql)

        c.execute(sql)
        self.conn.commit()

        print("Number of rows updated: %d" % c.rowcount)
        c.close()



    # ===============================================================================================

    '''
    def delete_by_id(self, table_name, id):
        c = self.conn.cursor()

        if table_name == 'ArticleTable':
            sql = "DELETE FROM ArticleTable WHERE article_id = %s" % id
        elif table_name == 'SentenceTable':
            sql = "DELETE FROM SentenceTable WHERE sent_id = %s" % id


        c.execute(sql)
        self.conn.commit()


        print("Number of rows deleted: %d" % c.rowcount)
        c.close()
    '''


    # ===============================================================================================


    def call_every_article(self, page, per_page, asc1_desc0, col_name):
        c = self.conn.cursor()

        # 1페이지는 0부터 시작, 2페이지는 10부터 시작...
        limit_start = per_page * (page - 1)


        if asc1_desc0 == '1':
            sql = "SELECT * FROM ArticleTable"
            sql += " ORDER BY %s %s" % (col_name, 'ASC')
            sql += " LIMIT %s,%s" % (limit_start, per_page)

        elif asc1_desc0 == '0':
            sql = "SELECT * FROM ArticleTable"
            sql += " ORDER BY %s %s" % (col_name, 'DESC')
            sql += " LIMIT %s,%s" % (limit_start, per_page)

        elif asc1_desc0 == None:
            sql = "SELECT * FROM ArticleTable"
            sql += " LIMIT %s,%s" % (limit_start, per_page)


        c.execute(sql)


        rows = c.fetchall()
        c.close()
        return rows




    def call_every_sentence(self, page, per_page, asc1_desc0, col_name, inc_num):

        c = self.conn.cursor()


        # 1페이지는 0부터 시작, 2페이지는 10부터 시작...
        limit_start = per_page * (page - 1)

        # 숫자 미포함
        if inc_num == '0':
            regex_req = " WHERE ((sent_original NOT REGEXP '[0-9]' AND sent_confirm = 0) OR (sent_converted NOT REGEXP '[0-9]' AND sent_confirm = 1))"
        # 숫자 포함
        elif inc_num == '1':
            regex_req = " WHERE ((sent_original REGEXP '[0-9]' AND sent_confirm = 0) OR (sent_converted REGEXP '[0-9]' AND sent_confirm = 1))"
        # 모두
        else:
            regex_req = ""




        if asc1_desc0 == '1':
            sql = "SELECT ST.*, AT.article_id, AT.article_collected_date FROM SentenceTable as ST left join ArticleTable as AT on ST.ArticleTable_article_id = AT.article_id"
            sql += regex_req
            sql += " ORDER BY %s %s" % (col_name, 'ASC')
            sql += " LIMIT %s,%s" % (limit_start, per_page)

        elif asc1_desc0 == '0':
            sql = "SELECT ST.*, AT.article_id, AT.article_collected_date FROM SentenceTable as ST left join ArticleTable as AT on ST.ArticleTable_article_id = AT.article_id"
            sql += regex_req
            sql += " ORDER BY %s %s" % (col_name, 'DESC')
            sql += " LIMIT %s,%s" % (limit_start, per_page)

        elif asc1_desc0 == None:
            sql = "SELECT ST.*, AT.article_id, AT.article_collected_date FROM SentenceTable as ST left join ArticleTable as AT on ST.ArticleTable_article_id = AT.article_id"
            sql += regex_req
            sql += " LIMIT %s,%s" % (limit_start, per_page)



        c.execute(sql)


        rows = c.fetchall()
        c.close()
        return rows



    def call_search_sentence(self, page, per_page, search_msg, asc1_desc0, col_name, inc_num):

        c = self.conn.cursor()

        # 1페이지는 0부터 시작, 2페이지는 10부터 시작...
        limit_start = per_page * (page - 1)


        # 숫자 미포함
        if inc_num == '0':
            regex_req = " AND ((sent_original NOT REGEXP '[0-9]' AND sent_confirm = 0) OR (sent_converted NOT REGEXP '[0-9]' AND sent_confirm = 1))"
        # 숫자 포함
        elif inc_num == '1':
            regex_req = " AND ((sent_original REGEXP '[0-9]' AND sent_confirm = 0) OR (sent_converted REGEXP '[0-9]' AND sent_confirm = 1))"
        # 모두
        else:
            regex_req = ""


        if asc1_desc0 == '1':
            sql = "SELECT ST.*, AT.article_id, AT.article_collected_date FROM SentenceTable as ST left join ArticleTable as AT on ST.ArticleTable_article_id = AT.article_id"
            sql += " WHERE ((sent_original LIKE '%%%s%%' AND sent_confirm = 0) OR (sent_converted LIKE '%%%s%%' AND sent_confirm = 1))" % (search_msg, search_msg)
            sql += regex_req
            sql += " ORDER BY %s %s" % (col_name, 'ASC')
            sql += " LIMIT %s,%s" % (limit_start, per_page)
        elif asc1_desc0 == '0':
            sql = "SELECT ST.*, AT.article_id, AT.article_collected_date FROM SentenceTable as ST left join ArticleTable as AT on ST.ArticleTable_article_id = AT.article_id"
            sql += " WHERE ((sent_original LIKE '%%%s%%' AND sent_confirm = 0) OR (sent_converted LIKE '%%%s%%' AND sent_confirm = 1))" % (search_msg, search_msg)
            sql += regex_req
            sql += " ORDER BY %s %s" % (col_name, 'DESC')
            sql += " LIMIT %s,%s" % (limit_start, per_page)
        elif asc1_desc0 == None:
            sql = "SELECT ST.*, AT.article_id, AT.article_collected_date FROM SentenceTable as ST left join ArticleTable as AT on ST.ArticleTable_article_id = AT.article_id"
            sql += " WHERE ((sent_original LIKE '%%%s%%' AND sent_confirm = 0) OR (sent_converted LIKE '%%%s%%' AND sent_confirm = 1))" % (search_msg, search_msg)
            sql += regex_req
            sql += " LIMIT %s,%s" % (limit_start, per_page)



        c.execute(sql)


        rows = c.fetchall()
        c.close()
        return rows


    def call_search_article(self, page, per_page, search_msg, asc1_desc0, col_name):
        c = self.conn.cursor()

        # 1페이지는 0부터 시작, 2페이지는 10부터 시작...
        limit_start = per_page * (page - 1)

        if asc1_desc0 == '1':
            sql = "SELECT * FROM ArticleTable"
            sql += " WHERE article_title LIKE \'%%%s%%\'" % search_msg
            sql += " ORDER BY %s %s" % (col_name, 'ASC')
            sql += " LIMIT %s,%s" % (limit_start, per_page)
        elif asc1_desc0 == '0':
            sql = "SELECT * FROM ArticleTable"
            sql += " WHERE article_title LIKE \'%%%s%%\'" % search_msg
            sql += " ORDER BY %s %s" % (col_name, 'DESC')
            sql += " LIMIT %s,%s" % (limit_start, per_page)
        elif asc1_desc0 == None:
            sql = "SELECT * FROM ArticleTable"
            sql += " WHERE article_title LIKE \'%%%s%%\'" % search_msg
            sql += " LIMIT %s,%s" % (limit_start, per_page)


        c.execute(sql)


        rows = c.fetchall()
        c.close()
        return rows


    def call_sentence_by_article_id(self, page, per_page, article_id, asc1_desc0, col_name, inc_num):
        c = self.conn.cursor()

        # 1페이지는 0부터 시작, 2페이지는 10부터 시작...
        limit_start = per_page * (page - 1)


        # 숫자 미포함
        if inc_num == '0':
            regex_req = " AND ((sent_original NOT REGEXP '[0-9]' AND sent_confirm = 0) OR (sent_converted NOT REGEXP '[0-9]' AND sent_confirm = 1))"
        # 숫자 포함
        elif inc_num == '1':
            regex_req = " AND ((sent_original REGEXP '[0-9]' AND sent_confirm = 0) OR (sent_converted REGEXP '[0-9]' AND sent_confirm = 1))"
        # 모두
        else:
            regex_req = ""



        if asc1_desc0 == '1':
            sql = "SELECT ST.*, AT.article_id, AT.article_collected_date FROM SentenceTable as ST INNER join ArticleTable as AT on ST.ArticleTable_article_id = AT.article_id"
            sql += " WHERE ST.ArticleTable_article_id = %s" % article_id
            sql += regex_req
            sql += " ORDER BY %s %s" % (col_name, 'ASC')
            sql += " LIMIT %s, %s" % (limit_start, per_page)
        elif asc1_desc0 == '0':
            sql = "SELECT ST.*, AT.article_id, AT.article_collected_date FROM SentenceTable as ST INNER join ArticleTable as AT on ST.ArticleTable_article_id = AT.article_id"
            sql += " WHERE ST.ArticleTable_article_id = %s" % article_id
            sql += regex_req
            sql += " ORDER BY %s %s" % (col_name, 'DESC')
            sql += " LIMIT %s, %s" % (limit_start, per_page)
        elif asc1_desc0 == None:
            sql = "SELECT ST.*, AT.article_id, AT.article_collected_date FROM SentenceTable as ST INNER join ArticleTable as AT on ST.ArticleTable_article_id = AT.article_id"
            sql += " WHERE ST.ArticleTable_article_id = %s" % article_id
            sql += regex_req
            sql += " LIMIT %s, %s" % (limit_start, per_page)



        c.execute(sql)


        rows = c.fetchall()
        c.close()
        return rows



    def call_clicked_search(self, page, per_page, article_id, search_msg, asc1_desc0, col_name, inc_num):
        c = self.conn.cursor()

        # 1페이지는 0부터 시작, 2페이지는 10부터 시작...
        limit_start = per_page * (page - 1)

        # 숫자 미포함
        if inc_num == '0':
            regex_req = " AND ((sent_original NOT REGEXP '[0-9]' AND sent_confirm = 0) OR (sent_converted NOT REGEXP '[0-9]' AND sent_confirm = 1))"
        # 숫자 포함
        elif inc_num == '1':
            regex_req = " AND ((sent_original REGEXP '[0-9]' AND sent_confirm = 0) OR (sent_converted REGEXP '[0-9]' AND sent_confirm = 1))"
        # 모두
        else:
            regex_req = ""


        if asc1_desc0 == '1':
            sql = "SELECT ST.*, AT.article_id, AT.article_collected_date FROM SentenceTable as ST INNER join ArticleTable as AT on ST.ArticleTable_article_id = AT.article_id"
            sql += " WHERE ST.ArticleTable_article_id = %s" % article_id
            sql += " AND ((sent_original LIKE '%%%s%%' AND sent_confirm = 0) OR (sent_converted LIKE '%%%s%%' AND sent_confirm = 1))" % (search_msg, search_msg)
            sql += regex_req
            sql += " ORDER BY %s %s" % (col_name, 'ASC')
            sql += " LIMIT %s, %s" % (limit_start, per_page)
        elif asc1_desc0 == '0':
            sql = "SELECT ST.*, AT.article_id, AT.article_collected_date FROM SentenceTable as ST INNER join ArticleTable as AT on ST.ArticleTable_article_id = AT.article_id"
            sql += " WHERE ST.ArticleTable_article_id = %s" % article_id
            sql += " AND ((sent_original LIKE '%%%s%%' AND sent_confirm = 0) OR (sent_converted LIKE '%%%s%%' AND sent_confirm = 1))" % (search_msg, search_msg)
            sql += regex_req
            sql += " ORDER BY %s %s" % (col_name, 'DESC')
            sql += " LIMIT %s, %s" % (limit_start, per_page)
        elif asc1_desc0 == None:
            sql = "SELECT ST.*, AT.article_id, AT.article_collected_date FROM SentenceTable as ST INNER join ArticleTable as AT on ST.ArticleTable_article_id = AT.article_id"
            sql += " WHERE ST.ArticleTable_article_id = %s" % article_id
            sql += " AND ((sent_original LIKE '%%%s%%' AND sent_confirm = 0) OR (sent_converted LIKE '%%%s%%' AND sent_confirm = 1))" % (search_msg, search_msg)
            sql += regex_req
            sql += " LIMIT %s, %s" % (limit_start, per_page)


        c.execute(sql)

        rows = c.fetchall()
        c.close()
        return rows






    def call_article_by_category(self, page, per_page, asc1_desc0, col_name, sid1, sid2):
        c = self.conn.cursor()

        # 1페이지는 0부터 시작, 2페이지는 10부터 시작...
        limit_start = per_page * (page - 1)

        if asc1_desc0 == '1':
            sql = "SELECT * FROM ArticleTable"
            sql += " WHERE article_sid1 = '%s' and article_sid2 = '%s'" % (sid1, sid2)
            sql += " ORDER BY %s %s" % (col_name, 'ASC')
            sql += " LIMIT %s, %s" % (limit_start, per_page)
        elif asc1_desc0 == '0':
            sql = "SELECT * FROM ArticleTable"
            sql += " WHERE article_sid1 = '%s' and article_sid2 = '%s'" % (sid1, sid2)
            sql += " ORDER BY %s %s" % (col_name, 'DESC')
            sql += " LIMIT %s, %s" % (limit_start, per_page)
        elif asc1_desc0 == None:
            sql = "SELECT * FROM ArticleTable"
            sql += " WHERE article_sid1 = '%s' and article_sid2 = '%s'" % (sid1, sid2)
            sql += " LIMIT %s, %s" % (limit_start, per_page)


        c.execute(sql)


        rows = c.fetchall()
        c.close()
        return rows



    def select_sent_original_inc_num_sent(self):
        c = self.conn.cursor()

        sql = "SELECT sent_original FROM SentenceTable WHERE sent_original REGEXP '[0-9]' AND sent_original NOT REGEXP '[a-zA-Z]'"

        c.execute(sql)

        rows = c.fetchall()
        c.close()
        return rows



    # ===============================================================================================
    # ===============================================================================================
    # ===============================================================================================
    # ===============================================================================================
    # ===============================================================================================
    # ===============================================================================================

    def insert_new_category(self, category):
        c = self.conn.cursor()

        sql = "INSERT INTO category (category, domain_id) VALUES ('%s', 1)" % category

        c.execute(sql)
        self.conn.commit()
        c.close()


    def insert_new_topic(self, topic, category_id):
        c = self.conn.cursor()

        sql = "INSERT INTO topic (topic, category_id) VALUES ('%s', %s)" % (topic, category_id)

        c.execute(sql)
        self.conn.commit()
        c.close()


    def insert_new_act(self, act, topic_id, category_id):
        c = self.conn.cursor()

        sql = "INSERT INTO act (act, topic_id, category_id) VALUES ('%s', %s, %s)" % (act, topic_id, category_id)

        c.execute(sql)
        self.conn.commit()
        c.close()

    def insert_new_slot_value(self, speech_id, slot_id, value_id):
        c = self.conn.cursor()

        sql = "INSERT INTO slot_value (speech_id, slot_id, value_id) VALUES (%s, %s, %s)" % (speech_id, slot_id, value_id)

        c.execute(sql)
        self.conn.commit()
        c.close()

    def insert_new_slot(self, slot):
        c = self.conn.cursor()

        sql = "INSERT INTO slot (slot) VALUES ('%s')" % slot

        c.execute(sql)
        self.conn.commit()
        c.close()

    def insert_new_value(self, value, slot_id):
        c = self.conn.cursor()

        sql = "INSERT INTO value (value, slot_id) VALUES ('%s', %s)" % (value, slot_id)

        c.execute(sql)
        self.conn.commit()
        c.close()


    def insert_new_speech(self, speech, act_id):
        c = self.conn.cursor()

        sql = "INSERT INTO speech (speech, act_id) VALUES ('%s', %s)" % (speech, act_id)

        c.execute(sql)
        self.conn.commit()
        c.close()



    def select_table(self, table_name):
        c = self.conn.cursor()

        sql = "SELECT * FROM %s" % table_name

        c.execute(sql)

        rows = c.fetchall()
        c.close()
        return rows



    def select_row_by_id(self, table_name, id):
        c = self.conn.cursor()

        sql = "SELECT * FROM %s WHERE id = %s" % (table_name, id)

        c.execute(sql)

        row = c.fetchone()
        c.close()
        return row


    def select_rows_by_condition(self, column_name, table_name, condition):
        c = self.conn.cursor()

        sql = "SELECT * FROM %s WHERE %s = '%s'" % (table_name, column_name, condition)

        c.execute(sql)

        rows = c.fetchall()
        c.close()
        return rows


    def select_latest_row(self, table_name):
        c = self.conn.cursor()

        sql = "SELECT * FROM %s ORDER BY id DESC LIMIT 1" % table_name

        c.execute(sql)

        row = c.fetchone()
        c.close()
        return row


    def update_act_count(self, act_id, desc0_inc1):
        c = self.conn.cursor()

        if desc0_inc1 == 0:
            sql = "UPDATE act SET act_count = act_count - 1 WHERE id = %s" % act_id
        elif desc0_inc1 == 1:
            sql = "UPDATE act SET act_count = act_count + 1 WHERE id = %s" % act_id
        else:
            print("???????????")


        c.execute(sql)
        self.conn.commit()

        c.close()


    def update_content_by_id(self, table_name, column_name, content, id):
        c = self.conn.cursor()

        sql = "UPDATE %s SET %s = '%s' WHERE id = %s" % (table_name, column_name, content, id)

        c.execute(sql)
        self.conn.commit()

        c.close()



    def delete_row_by_id(self, table_name, id):
        c = self.conn.cursor()

        sql = "DELETE FROM %s WHERE id = %s" % (table_name, id)

        c.execute(sql)
        self.conn.commit()

        print("Number of rows deleted: %d" % c.rowcount)
        c.close()



    def delete_rows_by_contidion(self, table_name, column_name, condition):
        c = self.conn.cursor()

        sql = "DELETE FROM %s WHERE %s = '%s'" % (table_name, column_name, condition)

        c.execute(sql)
        self.conn.commit()

        print("Number of rows deleted: %d" % c.rowcount)
        c.close()





    #################################################################################################


    def select_by_token(self, accessToken):
        c = self.conn.curosr()

        sql = "SELECT * FROM user_info WHERE accessToken = '%s'" % accessToken

        c.execute(sql)

        row = c.fetchone()
        c.close()
        return row


    def select_by_email(self, user_email):
        c = self.conn.curosr()

        sql = "SELECT * FROM user_info WHERE user_email = '%s'" % user_email

        c.execute(sql)

        row = c.fetchone()
        c.close()
        return row


    def update_user_info_table(self, col_upd, val_upd, col_cond, val_cond ):
        c = self.conn.cursor()

        sql = "UPDATE user_info SET %s = '%s' WHERE %s = '%s'" % (col_upd, val_upd, col_cond, val_cond)

        c.execute(sql)
        self.conn.commit()

        #print("Number of rows updated: %d" % c.rowcount)
        c.close()


    def insert_new_user(self, accessToken, user_email, need_oauth_reconnect):
        c = self.conn.cursor()

        sql = "INSERT INTO user_info (accessToken, user_email, need_oauth_reconnect, run_count, skip_mode) VALUES ('%s', '%s', %s, 0, 0)" % (accessToken, user_email, need_oauth_reconnect)

        c.execute(sql)
        self.conn.commit()

        #print("Number of rows inserted: %d" % c.rowcount)
        c.close()