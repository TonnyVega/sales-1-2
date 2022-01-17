from itertools import product
from flask import Flask, redirect, render_template, request, url_for, session,flash
import psycopg2
from werkzeug.utils import redirect
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy




app= Flask(__name__)
app.secret_key="tonny"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite3'
# users here refers to the table we reffer to.
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]= False
# ensure we are not tracking all modifications to the database.
app.permanent_session_lifetime=timedelta(minutes=5)
# this is to determine how long a session data is kept.
conn = psycopg2.connect("dbname='my_market' user='postgres' password='tony' host='localhost' port='5433'")




db = SQLAlchemy(app)
@app.before_first_request
def create_tables():
    db.create_all()

class users(db.Model):
    _id =db.Column("id",db.Integer, primary_key=True)
    # this is each model will have an id which is an int, unique (primary_key=true) means we will be refferencing each model with this key.
    # Every row needs to have an Id.
    name= db.Column(db.String(100))
    email = db.Column(db.String(100))

    def __init__(self,name,email):   #for values with no values, like gender, or status.
        self.name= name
        self.email= email







@app.route('/')
def index():
    user_name="Vega Tech"
    return render_template('index.html',user_name=user_name)
    


@app.route("/login", methods=["POST","GET"])
def login():
    if request.method=="POST":
        session.permanent=True
        # to ensure the session lasts for determined time. meaning once logged in the data will remain for the time in timedelta.
        user= request.form["nm"]
        session["user"]=user

# below we filter all logged in users by name incase they are already logged in.
        found_user=users.query.filter_by(name=user).first()
        if found_user:
            session["email"]= found_user.email
        
        else:
            usr= users(user, "")
            db.session.add(usr)
            db.session.commit()


        flash("Login successful!")
        return redirect(url_for("user"))
        # essentially this returns us to the user page
    else:
        if "user" in session:
            flash("Already Logged In!")
            return redirect(url_for("user"))
            # this keeps user logged in.
            # if user logs out, they have to login again.
        return render_template("login.html")
    


@app.route("/user", methods=["POST","GET"])   
def user():
    email= None
    if "user" in session:
        user=session["user"]

        if request.method =="POST":
            email = request.form["email"]
            session["email"]= email
# to save the email into the database. 
            found_user = users.query.filter_by(name=user).first()
            found_user.email=email
            db.session.commit()
            flash("Email was saved!")
        else:
            if "email" in session:
                email=session["email"]
        return render_template("user.html",email=email)
    else:
        flash("You Are Not Logged In! Please Login to Continue.")
        return redirect(url_for("login"))



@app.route("/logout")
def logout():
    flash("you have been logged out!", "info")
    session.pop("user", None)
    session.pop("email",None)
    # this removes user data from sessions.
    return redirect(url_for("login"))
  







@app.route('/products', methods=["POST","GET"])
def products():
    if request.method=="POST":
        cur=conn.cursor()
        name=request.form["product_name"]
        price=request.form["price"]
        quantity=request.form["quantity"]

        cur.execute(""" INSERT INTO products(product_name,quantity,price) VALUES (%(name)s,%(price)s,%(quantity)s)""",{"name":name,"price":price,"quantity":quantity})
        conn.commit()
        return redirect("/products")

    else:
        cur=conn.cursor()
        cur.execute("""SELECT product_id, product_name, price, quantity FROM products""")
        rows=cur.fetchall()
    return render_template('products.html',rows=rows)






@app.route('/sales', methods=['POST','GET'])
def sales():
    cur=conn.cursor()
    cur.execute("""SELECT * FROM sales""")
    x=cur.fetchall()
    print(x)
   
    

    if request.method== 'POST':
        cur=conn.cursor()
        r=request.form['product_id']
        t=request.form['product_name']
        q=request.form["quantity"]
        # e=request.form["sales_id"]
        cur.execute("""SELECT quantity FROM products WHERE product_id=%(r)s AND product_name=%(t)s""",{"r":r,"t":t})
        y=cur.fetchone()
        q=int(q)
        b=y[0]-q


        if b>=0:
            cur.execute(""" UPDATE products SET quantity=%(b)s WHERE product_id=%(r)s AND product_name=%(t)s""",{"b":b,"r":r,"t":t})
            cur.execute("""INSERT INTO sales(product_id,product_name,quantity) VALUES(%(r)s,%(t)s,%(q)s)""",{"r":r,"t":t,"q":q})
            conn.commit()
            return redirect(url_for('sales'))

    return render_template("sales.html",rows=x)


@app.route('/sales/<int:x>')
def view_sales(x):
    cur=conn.cursor()
    cur.execute("""SELECT sales_id,product_id,product_name,quantity,created_at FROM sales WHERE product_id= %(product_id)s""", {"product_id":x})
    x=cur.fetchall()
    return render_template('sales.html', rows=x)
    




@app.route('/product',methods=['GET','POST'])
def edit_products():
   if request.method== 'POST': 
    cur = conn.cursor()
    v=request.form["product_id"]
    n=request.form['product_name']
    y=request.form["price"]
    q=request.form['quantity']
    cur.execute("""UPDATE products SET product_name=%(n)s, price =%(y)s , quantity = %(q)s WHERE product_id=%(v)s;""",{"v":v,"n":n,"y":y,"q":q})
    conn.commit()
    
   


    return redirect(url_for('products'))
     
       
@app.route('/phones') 
def phones():
    return render_template('phones.html')
          

    
    
    
    
    




@app.route('/insights')
def insights():
    cur= conn.cursor()
    cur.execute("""SELECT quantity, product_name FROM sales""")
    data=cur.fetchall()
    # print(data)
    # values=[data[0][0]]
    # labels=[data[0][1]]
    values=[row[0] for row in data]
    labels=[row[1] for row in data]
    print("this is values",values)
    print("this is labels",labels)

    
    
   
    # data is a list of tuples from sales.
    # labels= quantity sold
    # values=name of products


    return render_template("insights.html",labels=labels,values=values)

    

if __name__ == '__main__':
    # if not os.path.exists('db.sqlite'):
        db.create_all()
#    creates this database if it doesn't exist.
        app.run(debug=True)
