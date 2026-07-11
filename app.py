from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3
from datetime import datetime
import pandas as pd


app = Flask(__name__)

app.secret_key = "SUNYOUNG_SECRET_KEY"



# ==========================
# DB 연결
# ==========================

def get_db():

    return sqlite3.connect("database.db")




# ==========================
# DB 생성
# ==========================

def init_db():

    conn = get_db()

    cur = conn.cursor()



    # 사용자

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id TEXT UNIQUE,

        password TEXT,

        name TEXT,

        role TEXT

    )
    """)



    # 연차 신청

    cur.execute("""
    CREATE TABLE IF NOT EXISTS leave_request(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        applicant TEXT,

        leave_type TEXT,

        leave_date TEXT,

        half_type TEXT,

        reason TEXT,

        status TEXT,

        reg_date TEXT

    )
    """)



    # 구매 신청

    cur.execute("""
    CREATE TABLE IF NOT EXISTS purchase_request(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        applicant TEXT,

        item TEXT,

        quantity TEXT,

        reason TEXT,

        status TEXT,

        reg_date TEXT

    )
    """)



    # 기본 사용자

    default_users = [

        (
        "employee01",
        "1234",
        "홍길동",
        "직원"
        ),

        (
        "factory01",
        "1234",
        "김공장",
        "공장장"
        ),

        (
        "manager01",
        "1234",
        "이담당",
        "담당자"
        ),

        (
        "ceo01",
        "1234",
        "대표",
        "대표"
        )

    ]



    for user in default_users:

        try:

            cur.execute("""
            INSERT INTO users
            (
            user_id,
            password,
            name,
            role
            )

            VALUES(?,?,?,?)
            """,
            user)


        except:

            pass



    conn.commit()

    conn.close()





# ==========================
# 시작
# ==========================

@app.route("/")
def index():

    return redirect("/login")





# ==========================
# 로그인
# ==========================

@app.route("/login", methods=["GET","POST"])
def login():


    if request.method == "POST":


        user_id = request.form["user_id"]

        password = request.form["password"]



        conn = get_db()

        cur = conn.cursor()



        cur.execute("""
        SELECT *

        FROM users

        WHERE user_id=?

        AND password=?

        """,
        (
            user_id,
            password
        ))



        user = cur.fetchone()



        conn.close()



        if user:


            session["id"] = user[1]

            session["name"] = user[3]

            session["role"] = user[4]


            return redirect("/main")



    return render_template(
        "login.html"
    )
# ==========================
# 메인 화면
# ==========================

@app.route("/main")
def main():

    if "id" not in session:

        return redirect("/login")


    return render_template(

        "main.html",

        name=session["name"],

        role=session["role"]

    )





# ==========================
# 연차 신청
# ==========================

@app.route("/leave", methods=["GET","POST"])
def leave():


    if "id" not in session:

        return redirect("/login")



    if request.method == "POST":


        conn = get_db()

        cur = conn.cursor()



        cur.execute("""
        INSERT INTO leave_request
        (
        applicant,
        leave_type,
        leave_date,
        half_type,
        reason,
        status,
        reg_date
        )

        VALUES(?,?,?,?,?,?,?)

        """,
        (

        session["name"],

        request.form["leave_type"],

        request.form["leave_date"],

        request.form.get("half_type",""),

        request.form["reason"],

        "공장장 승인 대기",

        datetime.now().strftime("%Y-%m-%d")

        ))



        conn.commit()

        conn.close()



        return redirect("/my_request")



    return render_template(

        "leave.html",

        name=session["name"],

        role=session["role"]

    )






# ==========================
# 구매 요청
# ==========================

@app.route("/purchase", methods=["GET","POST"])
def purchase():


    if "id" not in session:

        return redirect("/login")



    if request.method=="POST":


        conn=get_db()

        cur=conn.cursor()



        cur.execute("""
        INSERT INTO purchase_request

        (
        applicant,
        item,
        quantity,
        reason,
        status,
        reg_date
        )

        VALUES(?,?,?,?,?,?)

        """,

        (

        session["name"],

        request.form["item"],

        request.form["quantity"],

        request.form["reason"],

        "공장장 승인 대기",

        datetime.now().strftime("%Y-%m-%d")

        ))



        conn.commit()

        conn.close()



        return redirect("/my_request")



    return render_template(

        "purchase.html",

        name=session["name"],

        role=session["role"]

    )







# ==========================
# 내 신청 현황
# ==========================

@app.route("/my_request")
def my_request():


    if "id" not in session:

        return redirect("/login")



    conn=get_db()

    cur=conn.cursor()



    name=session["name"]



    cur.execute("""
    SELECT *

    FROM leave_request

    WHERE applicant=?

    ORDER BY id DESC

    """,
    (name,))


    leave_data=cur.fetchall()



    cur.execute("""
    SELECT *

    FROM purchase_request

    WHERE applicant=?

    ORDER BY id DESC

    """,
    (name,))


    purchase_data=cur.fetchall()



    conn.close()



    return render_template(

        "my_request.html",

        leave_data=leave_data,

        purchase_data=purchase_data

    )
# ==========================
# 결재 대기함
# ==========================

@app.route("/approval")
def approval():

    if "id" not in session:

        return redirect("/login")



    role = session["role"]



    # 결재 순서

    if role == "공장장":

        status = "공장장 승인 대기"


    elif role == "담당자":

        status = "담당자 승인 대기"


    elif role == "대표":

        status = "대표 승인 대기"


    else:

        return "권한 없음"



    conn=get_db()

    cur=conn.cursor()



    cur.execute("""
    SELECT *

    FROM leave_request

    WHERE status=?

    """,
    (status,))


    leave_data=cur.fetchall()



    cur.execute("""
    SELECT *

    FROM purchase_request

    WHERE status=?

    """,
    (status,))


    purchase_data=cur.fetchall()



    conn.close()



    return render_template(

        "approval.html",

        leave_data=leave_data,

        purchase_data=purchase_data

    )







# ==========================
# 승인 처리
# ==========================

@app.route("/approve/<int:id>/<kind>")
def approve(id,kind):


    if "id" not in session:

        return redirect("/login")



    role=session["role"]



    if role=="공장장":

        status="담당자 승인 대기"


    elif role=="담당자":

        status="대표 승인 대기"


    elif role=="대표":

        status="최종 승인 완료"


    else:

        return "권한 없음"




    conn=get_db()

    cur=conn.cursor()



    if kind=="leave":


        cur.execute("""
        UPDATE leave_request

        SET status=?

        WHERE id=?

        """,
        (
        status,
        id
        ))


    else:


        cur.execute("""
        UPDATE purchase_request

        SET status=?

        WHERE id=?

        """,
        (
        status,
        id
        ))



    conn.commit()

    conn.close()



    return redirect("/approval")



# ==========================
# 반려 처리
# ==========================

@app.route("/reject/<int:id>/<kind>", methods=["GET","POST"])
def reject(id,kind):


    if "id" not in session:

        return redirect("/login")



    if request.method=="POST":


        reason=request.form["reason"]



        status="반려 : "+reason



        conn=get_db()

        cur=conn.cursor()



        if kind=="leave":


            cur.execute("""
            UPDATE leave_request

            SET status=?

            WHERE id=?

            """,
            (
            status,
            id
            ))


        else:


            cur.execute("""
            UPDATE purchase_request

            SET status=?

            WHERE id=?

            """,
            (
            status,
            id
            ))



        conn.commit()

        conn.close()



        return redirect("/approval")




    return """

    <h2 style='text-align:center'>

    반려 사유 입력

    </h2>


    <form method='post'

    style='text-align:center'>


    <textarea name='reason'

    style='width:300px;height:100px'>

    </textarea>


    <br><br>


    <button>

    반려 처리

    </button>


    </form>

    """

# ==========================
# 직원 관리
# ==========================
@app.route("/user_manage", methods=["GET", "POST"])
def user_manage():

    print("REQUEST METHOD :", request.method)

    if "id" not in session:
        return redirect("/login")

    if session["role"] != "담당자":
        return "권한 없음"

    conn = get_db()
    cur = conn.cursor()

    # 직원 등록
    if request.method == "POST":

        cur.execute("""
        INSERT INTO users
        (
            user_id,
            password,
            name,
            role
        )
        VALUES (?,?,?,?)
        """,
        (
            request.form["user_id"],
            request.form["password"],
            request.form["name"],
            request.form["role"]
        ))

        conn.commit()

    cur.execute("""
    SELECT *
    FROM users
    ORDER BY id DESC
    """)

    users = cur.fetchall()

    conn.close()

    return render_template(
        "user_manage.html",
        users=users
    )


# ==========================
# 직원 수정
# ==========================
@app.route("/user_edit/<int:id>", methods=["GET","POST"])
def user_edit(id):

    if "id" not in session:
        return redirect("/login")

    if session["role"] != "담당자":
        return "권한 없음"

    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":

        cur.execute("""
        UPDATE users
        SET
            password=?,
            name=?,
            role=?
        WHERE id=?
        """,
        (
            request.form["password"],
            request.form["name"],
            request.form["role"],
            id
        ))

        conn.commit()
        conn.close()

        return redirect("/user_manage")

    cur.execute("""
    SELECT *
    FROM users
    WHERE id=?
    """, (id,))

    user = cur.fetchone()

    conn.close()

    return render_template(
        "user_edit.html",
        user=user
    )

# ==========================
# 연차 엑셀 다운로드
# ==========================

@app.route("/export_leave")
def export_leave():


    # 로그인 확인

    if "id" not in session:

        return redirect("/login")



    # 담당자만 가능

    if session["role"] != "담당자":

        return "권한 없음"



    conn = get_db()



    df = pd.read_sql_query(

        """
        SELECT *
        FROM leave_request
        ORDER BY id DESC
        """,

        conn

    )


    conn.close()



    filename = "연차신청현황.xlsx"



    df.to_excel(

        filename,

        index=False

    )



    return send_file(

        filename,

        as_attachment=True

    )



# ==========================
# 로그아웃
# ==========================

@app.route("/logout")
def logout():


    session.clear()


    return redirect("/login")


# ==========================
# 실행
# ==========================

if __name__=="__main__":

    init_db()

    app.run(
        host="0.0.0.0",
        port=5000
    )