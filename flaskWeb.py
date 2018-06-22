from flask import Flask,request,render_template,session,redirect,url_for,flash
from werkzeug.utils import secure_filename
import sqlite3
from datetime import datetime
import os
import config
from socket import *

app=Flask(__name__)
app.config.from_object(config)


@app.route('/',methods=['get'])
def home():
    if not session.get('logged_in'):
        return render_template('home.html')
    else:
        username=session.get('user')
        return render_template('welcome.html', username=username,results=getpage(1),pageno=total_page_no())


@app.route('/page=<i>',methods=['get'])
def page(i):
    if not session.get('logged_in'):
        return render_template('home.html')
    else:
        username=session.get('user')
        return render_template('welcome.html', username=username,results=getpage(int(i)),pageno=total_page_no())


@app.route('/', methods=['POST'])
def signin():
    username = request.form['username']
    password = request.form['password']
    con=sqlite3.connect('userdata.db')
    cur=con.cursor()
    cur.execute('select * from user where name=\'%s\' AND password=\'%s\''%(username,password))
    s=cur.fetchall()
    cur.close()
    con.close()
    if s:
        results=getboard()
        session['logged_in']=True
        session['user']=username
        return redirect(url_for('home'))
    else:
        return render_template('home.html', message='账户名或密码错误', username=username)

@app.route('/newuser',methods=['GET'])
def newuser():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register():
    username=request.form['username']
    password=request.form['password']
    con=sqlite3.connect('userdata.db')
    cur=con.cursor()
    cur.execute('select * from user where name=\'%s\''%username)
    s=cur.fetchall()
    if s:
        cur.close()
        con.close()
        return render_template('register.html',message='该用户已经存在，请重新注册',username=username)

    else:
        cur.execute('insert into user values(\'%s\',\'%s\')'%(username,password))
        con.commit()
        cur.close()
        con.close()
        return render_template('home.html',message='你已注册成功，请登录',username=username)


@app.route('/message', methods=['POST'])
def message():
    time=str(datetime.now())[:16]
    ip=request.remote_addr
    content=request.form['content']
    if content!='':
        con=sqlite3.connect('userdata.db')
        cur=con.cursor()
        try:
            cur.execute('insert into message values(\'%s\',\'%s\',\'%s\',\'%s\')'%(session['user'],content,time,ip))
            con.commit()
            sendmessages(session['user'])
            flash('留言成功','success')
        except:
            flash('留言失败','warning')
        cur.close()
        con.close()
        return  redirect(url_for('home'))
    else:
        return redirect(url_for('home'))

@app.route('/log_out', methods=['GET'])
def logout():
    session.pop('logged_in',None)
    return redirect(url_for('home'))

@app.route('/admin', methods=['GET'])
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    else:
        name=session['user']
        return render_template('admin.html',content=getboard(name))
    
@app.route('/delete/<i>', methods=['GET'])
def delete(i):
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    else:
        name=session['user']
        con=sqlite3.connect('userdata.db')
        cur=con.cursor()
        cur.execute('delete from message where rowid=%d and name=\'%s\''%(int(i),name))
        con.commit()
        cur.close()
        con.close()
        flash('删除成功','success')
        return redirect(url_for('home'))
            
        
def getboard(username=None):
    con=sqlite3.connect('userdata.db')
    cur=con.cursor()
    if username==None:
        cur.execute('select rowid,* from message order by rowid desc')
    else:
        cur.execute('select rowid,* from message where name=\'%s\' order by rowid desc'%username)
    while True:
        res=cur.fetchmany(10)
        if res:
            li=[]
            for re in res:
                result_dic={}
                result_dic['ID']=re[0]
                result_dic['name']=re[1]
                result_dic['content']=re[2]
                result_dic['time']=re[3]
                result_dic['ip']=re[4]
                li.append(result_dic)
            yield li
        else:
            break
    cur.close()
    con.close()
    
def getpage(pageno):
    g=getboard()
    i=0
    while i<pageno:
        l=next(g)
        i=i+1
    return l

def get_user_ip():
    con=sqlite3.connect('userdata.db')
    cur=con.cursor()
    cur.execute('select rowid,* from message order by rowid desc')
    while True:
        res=cur.fetchone()
        if res:
            yield res[4]
        else:
            break
    cur.close()
    con.close()


def total_page_no():
    con=sqlite3.connect('userdata.db')
    cur=con.cursor()
    cur.execute('select count(*) from message')
    result=cur.fetchone()
    cur.close()
    con.close()
    return range(1,int(result[0]/10)+2)



@app.route('/upload/file',methods=['POST','GET'])
def uploadfile():
    if request.method=='POST':
        f=request.files['file']
        suffix_name=(f.filename).rsplit('.',1)[1]
        upload_path='E:/flaskweb/static/images/upload/'+str(datetime.now())[:10]\
                     +'-'+'.'+suffix_name
        x=0
        while True:
            if os.path.exists(upload_path):
                x=x+1           
                upload_path='E:/flaskweb/static/images/upload/'+str(datetime.now())[:10]\
                              +'-'+str(x)+'.'+suffix_name
            else:
                break
        f.save(upload_path)
        message='上传成功 url:  ..'+upload_path[11:]
        flash(message,'success')
        return redirect(url_for('home'))


def sendmessages(user):
    s=socket(AF_INET,SOCK_DGRAM)
    ip_list=[]
    for x in get_user_ip():
        if x not in ip_list:
            ip_list.append(x)
            
    for address in ip_list:
        add = (address,2425)
        message='1_lbt4_10#32899#002481627512#0#0#0:123456789:莫莠君_324:HG-A-MYOUJ:288:%s 在留言板发布了新的留言'%user
        s.sendto(message.encode('gbk'),add)      
    s.close()



@app.route('/myquestion',methods=['GET','POST'])
def myquestion():
    if request.method=='GET':
        return render_template('question.html')
    if request.method=='POST':
        question = request.form['question']
        choice=[]
        for x in ['A','B','C','D','E','F','G','H','I','J','K','L']:
            try:
                c = request.form['choice '+x]
                if c is not None or c!='':
                    choice.append(c)
            except:
                pass
        question_id = questionnaire_db().add_question(question,choice)
        return render_template('questionnaire.html',question_id=question_id,question=question,choice=choice)
        
@app.route('/myquestion/post/<question_id>/pub',methods=['GET','POST'])
def myquestionnaire(question_id):    
    if request.method=='GET':
        res=questionnaire_db().show_question_and_choice(question_id)
        question=res[0][1]
        choice=(x[1] for x in res[1:])
        return render_template('questionnaire.html',question_id=question_id,question=question,choice=choice)   
    
    if request.method=='POST':
        if not session.get('logged_in'):
            return redirect(url_for('home'))
        else:
            name=session['user']
            choice=request.form['choice']
            db=questionnaire_db()
            db.add_answer(question_id,name,choice)
            res=questionnaire_db().show_question_and_choice(question_id)
            question=res[0][1]
            choice=(x[1] for x in res[1:])
            answer=questionnaire_db().show_result(question_id)
        return render_template('questionnaire_result.html',question_id=question_id,answer=answer,question=question,choice=choice)

@app.route('/myquestion/post/<question_id>/show_result',methods=['GET'])
def show_questionnaire_result(question_id):
    answer=questionnaire_db().show_result(question_id)
    res=questionnaire_db().show_question_and_choice(question_id)
    question=res[0][1]
    choice=(x[1] for x in res[1:])
    return render_template('questionnaire_result.html',answer=answer,question=question,choice=choice)

@app.route('/myquestion/post',methods=['GET'])
def show_all_questionnaire():
    question_list=questionnaire_db().show_all_questionnaire()
    return render_template('all_questionnaire.html',question_list=question_list)

class questionnaire_db:

    def __init__(self):
        self.con = sqlite3.connect('userquestionnaire.db')
        self.cur = self.con.cursor()
    
    def close(self):
        self.con.commit()
        self.cur.close()
        self.con.close() 
    
    def add_question(self,question,choice):
        i=1
        while True:
            question_id=str(int(datetime.now().timestamp()))+'%d'%i
            self.cur.execute('select * from question where question=\'%s\''%question_id)   
            if self.cur.fetchone():
                i=i+1
            else:
                break
        self.cur.execute('insert into question values(\'%s\',\'%s\')'%(question_id,question))
        self.con.commit()
        for x in choice: 
            self.cur.execute('insert into question values(\'%s\',\'%s\')'%(question_id,x))

        self.close()
        return question_id

    def add_answer(self,question_id,name,answer):
        self.cur.execute('select * from answer where question=\'%s\' and name=\'%s\''%(question_id,name))
        if self.cur.fetchone():
            self.cur.execute('delete from answer where question=\'%s\' and name=\'%s\''%(question_id,name))
            self.con.commit()
        self.cur.execute('insert into answer values(\'%s\',\'%s\',\'%s\')'%(question_id,name,answer))
        self.close()

    def show_question_and_choice(self,question_id):
        self.cur.execute('select * from question where question=\'%s\''%question_id)
        res=self.cur.fetchall()
        self.close()
        return res
    
    def show_all_questionnaire(self):
        self.cur.execute('select * from question')
        id_list=[]
        question_list=[]
        while True:
            res=self.cur.fetchone()
            if res:
                if res[0] not in id_list:
                    id_list.append(res[0])
                    question_list.append(('/myquestion/post/%s/pub'%res[0],res[1]))
            else:
                break
        return question_list

    def show_result(self,question_id):
        self.cur.execute('select * from answer where question=\'%s\''%question_id) 
        result=self.cur.fetchall()
        res=self.show_question_and_choice(question_id)
        choice=[x[1] for x in res[1:]]
        for each in result:
            cho=['A','B','C','D','E','F','G','H','I','J','K','L'][choice.index(each[2])]
            yield each[1],each[2],cho

if __name__=='__main__':
    app.run(host='0.0.0.0',port=80)
    
