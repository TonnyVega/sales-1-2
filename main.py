from itertools import product
from unicodedata import category
from flask import Flask, jsonify, redirect, render_template, request, url_for, session,flash
import psycopg2
from werkzeug.utils import redirect
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user,login_required,logout_user,current_user
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash #for storing a password in a secure way. hash func has no inverse.
import json




app= Flask(__name__)


app.config['SECRET_KEY']='tony_vega'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite3'






# users here refers to the table we reffer to.
# app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]= False
# ensure we are not tracking all modifications to the database.

conn = psycopg2.connect(user='ldbwnrvvijnoop',
                        password='87bc8a1093591d5219158ed15a6d3225b1f1ef27dd0395d2a496f560d24c5d83',
                        host='ec2-54-74-60-70.eu-west-1.compute.amazonaws.com',
                        port='5432',
                        database='d33chu23k06set')

cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS products(product_id SERIAL PRIMARY KEY, product_name VARCHAR(255),selling_price INT NOT NULL,buying_price INT NOT NULL,quantity INT NOT NULL)")
cur.execute("CREATE TABLE IF NOT EXISTS sales(sales_id SERIAL PRIMARY KEY ,product_id INT,product_name VARCHAR(100),quantity_sold INT,created_at DATE NOT NULL DEFAULT NOW())")


db = SQLAlchemy(app)
@app.before_first_request
def create_tables():
    db.create_all()
    create_database(app)
    db.init_app(app)




login_manager= LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    notes = db.relationship('Note') #user.id is the primary key you're reffering to from the parent table.
def create_database(app):
    db.create_all(app=app)
    print('created db')






    
   
   






@app.route('/')
def index():
    return render_template('index.html')
    


@app.route("/login", methods=['GET','POST'])
def login():
    if request.method=='POST':
        email= request.form.get('email')
        password=request.form.get('password')

        user=User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password,password):
                flash("Logged in successfully!", category='success')
                login_user(user, remember=True)
                return redirect(url_for('dashboard'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('email does not exist', category='error')
    return render_template('login.html', user=current_user)  

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))



@app.route("/sign_up", methods=["GET","POST"])
def sign_up():

    if request.method== 'POST':
        email= request.form.get('email')
        first_name= request.form.get('firstName')
        password1= request.form.get('password1')
        password2= request.form.get('password2')

        user=User.query.filter_by(email=email).first()
        if user:
            flash('email already exists')

        elif len(email)< 4:
            flash("EMAIL must have more than 4 characters!", category='error!')
        elif len(first_name)< 2:
             flash("name must have more than 2 characters!", category='error!')
        elif password1 != password2:
             flash("password does not match", category='error!')
        elif len (password1) < 7:
             flash("password is too short, it must be 8 characters or above", category='error!')
        else:
            new_user= User(email=email, first_name=first_name,password=generate_password_hash(password1, method='sha256'))
            db.session.add(new_user)
            db.session.commit()
            login_user(user=new_user, remember=True)
            flash('Account created. WELCOME TO VEGA TECH!', category='success')
            return redirect(url_for('dashboard'))

    return render_template("sign_up.html", user=current_user)

@app.route('/dashboard', methods=['GET','POST'])
def dashboard():
    if request.method == 'POST':
        note = request.form.get('note')

        if len(note) < 1:
            flash('Note is too short!', category='error')
        else:
            new_note = Note(data=note, user_id=current_user.id)
            db.session.add(new_note)
            db.session.commit()
            flash('Note added!', category='success')

    return render_template("dashboard.html", user=current_user)
    
   


@app.route('/delete-note', methods=['POST'])
def delete_note():
    note=json.loads(request.data)
    noteId=note['noteId']
    note=Note.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()
           
           
    return jsonify({})











@app.route('/products', methods=["POST","GET"])
@login_required
def products():
    if request.method=="POST":
        cur=conn.cursor()
        name=request.form["product_name"]
        selling_price=request.form["selling_price"]
        buying_price=request.form["buying_price"]
        quantity=request.form["quantity"]

        cur.execute(""" INSERT INTO products(product_name,buying_price,selling_price,quantity) VALUES (%(name)s,%(selling_price)s,%(buying_price)s,%(quantity)s)""",{"name":name,"selling_price":selling_price,"buying_price":buying_price,"quantity":quantity})
        conn.commit()
        return redirect("/products")

    else:
        cur=conn.cursor()
        cur.execute("""SELECT product_id, product_name, selling_price,buying_price, quantity FROM products""")
        rows=cur.fetchall()
    return render_template('products.html',rows=rows)






@app.route('/sales', methods=['POST','GET'])
@login_required
def sales():
    cur=conn.cursor()
    cur.execute("""SELECT sales_id, product_id,product_name,quantity_sold, created_at FROM sales""")
    x=cur.fetchall()
    print(x)
   
    

    if request.method== 'POST':
        cur=conn.cursor()
        r=request.form['product_id']
        t=request.form['product_name']
        q=request.form["quantity"]
        
        cur.execute("""SELECT quantity FROM products WHERE product_id=%(r)s AND product_name=%(t)s""",{"r":r,"t":t})
        y=cur.fetchone()
        q=int(q)
        b=y[0]-q


        if b>=0:
            cur.execute(""" UPDATE products SET quantity=%(b)s WHERE product_id=%(r)s AND product_name=%(t)s""",{"b":b,"r":r,"t":t})
            cur.execute("""INSERT INTO sales(product_id,product_name,quantity_sold) VALUES(%(r)s,%(t)s,%(q)s)""",{"r":r,"t":t,"q":q})
            conn.commit()
            return redirect(url_for('sales'))

    return render_template("sales.html",rows=x)


@app.route('/sales/<int:x>')
def view_sales(x):
    cur=conn.cursor()
    cur.execute("""SELECT sales_id,product_id,product_name,quantity_sold,created_at FROM sales WHERE product_id= %(product_id)s""", {"product_id":x})
    x=cur.fetchall()
    return render_template('sales.html', rows=x)
    




@app.route('/product',methods=['GET','POST'])
@login_required
def edit_products():
   if request.method== 'POST': 
    cur = conn.cursor()
    v=request.form["product_id"]
    n=request.form['product_name']
    y=request.form["selling_price"]
    bp=request.form["buying_price"]
    q=request.form['quantity']
    cur.execute("""UPDATE products SET product_name=%(n)s, selling_price =%(y)s, buying_price=%(bp)s , quantity = %(q)s WHERE product_id=%(v)s;""",{"v":v,"n":n,"y":y,"q":q,"bp":bp})
    conn.commit()
    
   


    return redirect(url_for('products'))
     

@app.route('/stock',methods=['POST','GET'])
@login_required
def stock():
    cur=conn.cursor()
    cur.execute("""SELECT product_id,product_name,quantity,quantity_sold,buying_price,selling_price FROM stocks""")
    conn.commit()
    rows=cur.fetchall()
    print(rows)
    return render_template('stock.html',rows=rows)

@app.route('/stock/<int:x>')
@login_required
def profit():
    if request.method=='post':
        cur=conn.cursor()
        p_id=request.form['product_id']
        name=request.form['product_name']
        quantity=request.form['quantity']
        sold=request.form['quantity_sold']
        bp=request.form['buying_price']
        sp=request.form['selling_price']
        cur.execute()
        cur.fetchall()
        prof= int(sp-bp)
        print(prof)
    

        if sp>bp:
            prof=sp-bp
            print("you have a profit of",prof)

        elif bp<sp:
            loss= bp-sp
            print("you have a loss of",loss)
        else:
            print("you have made neither a profit or a loss")

        return render_template('stock.html')



    
    
    
    
    




@app.route('/insights')
@login_required
def insights():
    cur= conn.cursor()
    cur.execute("""SELECT quantity_sold, product_name FROM sales""")
    data=cur.fetchall()
    # print(data)
    # values=[data[0][0]]
    # labels=[data[0][1]]
    values=[row[0] for row in data]
    labels=[row[1] for row in data]
  

    
    
   
    # data is a list of tuples from sales.
    # labels= quantity sold
    # values=name of products


    return render_template("insights.html",labels=labels,values=values)





    

if __name__ == '__main__':
    # if not os.path.exists('db.sqlite'):
    db.create_all()
    app.run(debug=True)
