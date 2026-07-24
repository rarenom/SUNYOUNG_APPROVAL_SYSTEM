from flask import Flask, render_template, request, redirect, session, send_file, jsonify
import psycopg2
from datetime import datetime, timezone, timedelta
import pandas as pd
import os


app = Flask(__name__)
app.secret_key = "SUNYOUNG_SECRET_KEY"

# ==========================
# Firebase Push 설정
# ==========================

import firebase_admin
from firebase_admin import credentials, messaging


cred = credentials.Certificate(
    "/etc/secrets/firebase_key.json"
)

firebase_admin.initialize_app(cred)

KST = timezone(timedelta(hours=9))


def now_korea():

    return datetime.now(KST)
    
# ==========================
# 푸시 알림 함수
# ==========================
def send_push(role, message):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT push_token
    FROM users
    WHERE role=%s
    AND push_token IS NOT NULL
    """, (role,))

    users = cur.fetchall()
    conn.close()

    for user in users:

        token = user[0]

        try:

            msg = messaging.Message(

                notification=messaging.Notification(
                    title="선영알림",
                    body=message
                ),

                data={
                    "title":"선영알림",
                    "body":message
                },

                android=messaging.AndroidConfig(
                    priority="high"
                ),

                webpush=messaging.WebpushConfig(
                    notification=messaging.WebpushNotification(
                        title="선영알림",
                        body=message
                    ),
                    headers={
                        "Urgency":"high"
                    }
                ),

                token=token
            )

            response = messaging.send(msg)

            print("푸시 성공:", response)

        except Exception as e:

            print("푸시 오류:", e)


# ==========================
# 개인 푸시
# ==========================
def send_push_user(name, message):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    SELECT push_token
    FROM users
    WHERE name=%s
    """, (name,))

    user = cur.fetchone()
    conn.close()

    if user and user[0]:

        try:

            msg = messaging.Message(

                notification=messaging.Notification(
                    title="SUNYOUNG ERP",
                    body=message
                ),

                data={
                    "title":"SUNYOUNG ERP",
                    "body":message
                },

                android=messaging.AndroidConfig(
                    priority="high"
                ),

                webpush=messaging.WebpushConfig(
                    notification=messaging.WebpushNotification(
                        title="SUNYOUNG ERP",
                        body=message
                    ),
                    headers={
                        "Urgency":"high"
                    }
                ),

                token=user[0]
            )           

            response = messaging.send(msg)

            print("개인 푸시 성공:", response)

        except Exception as e:

            print("개인 푸시 오류:", e)

# ==========================
# DB 연결 (Supabase PostgreSQL)
# ==========================

def get_db():

    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        raise Exception("DATABASE_URL 환경변수가 없습니다.")

    conn = psycopg2.connect(
        database_url,
        sslmode="require"
    )

    return conn
# ==========================
# Firebase Push Token 저장
# ==========================

@app.route("/save_push_token", methods=["POST"])
def save_push_token():

    if "id" not in session:
        return jsonify({
            "result":"login required"
        })


    data = request.get_json()

    token = data.get("token")


    conn = get_db()

    cur = conn.cursor()


    cur.execute("""
    UPDATE users

    SET push_token=%s

    WHERE id=%s

    """,
    (
        token,
        session["id"]
    ))


    conn.commit()

    conn.close()


    return jsonify({
        "result":"saved"
    })
# ==========================
# DB 생성
# ==========================

def init_db():

    conn = get_db()

    conn.autocommit = True

    cur = conn.cursor()


    # 사용자

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(

        id SERIAL PRIMARY KEY,

        user_id TEXT UNIQUE,

        password TEXT,

        name TEXT,

        role TEXT,

        factory_approval INTEGER DEFAULT 1,

        manager_approval INTEGER DEFAULT 1

    )
    """)



    # 연차 신청

    cur.execute("""
    CREATE TABLE IF NOT EXISTS leave_request(

        id SERIAL PRIMARY KEY,

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

        id SERIAL PRIMARY KEY,

        applicant TEXT,

        item TEXT,

        quantity TEXT,

        reason TEXT,

        status TEXT,

        reg_date TEXT

    )
    """)

    # 승인 이력 컬럼 추가

    try:

        cur.execute("""
        ALTER TABLE leave_request
        ADD COLUMN IF NOT EXISTS approval_history TEXT
        """)

    except:

        pass

    try:

        cur.execute("""
        ALTER TABLE purchase_request
        ADD COLUMN IF NOT EXISTS approval_history TEXT
        """)

    except:

        pass    

    # 반려 이력 컬럼 추가

    try:
        cur.execute("""
        ALTER TABLE leave_request
        ADD COLUMN IF NOT EXISTS reject_history TEXT
        """)
    except:
        pass


    try:
        cur.execute("""
        ALTER TABLE purchase_request
        ADD COLUMN reject_history TEXT
        """)
    except:
        pass
        

    # 기존 DB 컬럼 추가

    try:
        cur.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS factory_approval INTEGER DEFAULT 1
        """)
    except:
        pass


    try:
        cur.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS manager_approval INTEGER DEFAULT 1
        """)
    except:
        pass

    try:
        cur.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS push_token TEXT
        """)
    except:
        pass

    # 기본 사용자

    default_users = [

        (
            "jwlee01",
            "4715",
            "이재우",
            "직원",
            0,
            1
        ),

        (
            "hrkim01",
            "3234",
            "김홍래",
            "공장장",
            1,
            1
        ),

        (
            "rarenom",
            "2266",
            "박용현",
            "담당자",
            0,
            0
        ),

        (
            "ceo01",
            "5102",
            "남영진",
            "대표",
            0,
            0
        )

    ]

    for user in default_users:
        cur.execute("""
        INSERT INTO users
        (
            user_id,
            password,
            name,
            role,
            factory_approval,
            manager_approval
        )
        VALUES (%s,%s,%s,%s,%s,%s)
        ON CONFLICT (user_id)
        DO NOTHING
        """, user)

    # ==========================
    # 공지사항 테이블 추가
    # ==========================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS notice(

        id SERIAL PRIMARY KEY,

        title TEXT NOT NULL,

        content TEXT NOT NULL,

        writer TEXT,

        important INTEGER DEFAULT 0,

        reg_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )
    """)

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

        user_id = request.form["user_id"].strip()
        password = request.form["password"].strip()


        conn = get_db()
        cur = conn.cursor()

        
        cur.execute("""
        SELECT *
        FROM users
        WHERE user_id=%s
        AND password=%s
        """, (
            user_id,
            password
        ))


        user = cur.fetchone()

        conn.close()



        if user:


            session["id"] = user[0]

            session["name"] = user[3]

            session["role"] = user[4]


            print("로그인 성공")
            print("이름 :", session["name"])
            print("권한 :", session["role"])


            return redirect("/main")



        else:

            print("로그인 실패")

            return render_template(
                "login.html",
                error="아이디 또는 비밀번호가 맞지 않습니다.\n잘 기억해 보세요! 그래도 모르면 담당자에게 문의 바랍니다."
            )



    return render_template(
        "login.html",
        error=""
    )


# ==========================
# 메인
# ==========================

@app.route("/main")
def main():

    if "id" not in session:

        return redirect("/login")


    conn = get_db()

    cur = conn.cursor()


    cur.execute("""
    SELECT *
    FROM notice
    ORDER BY important DESC, id DESC
    """)


    notices = cur.fetchall()


    conn.close()


    return render_template(

        "main.html",

        name=session["name"],

        role=session["role"],

        notices=notices

    )

# ==========================
# 현재 상태 기준 다음 승인자 찾기
# ==========================
def get_next_approver(status):

    if status=="공장장 승인 대기":
        return "공장장"

    elif status=="담당자 확인 대기":
        return "담당자"

    elif status=="대표 승인 대기":
        return "대표"

    return None

# ==========================
# 승인 단계 확인 함수
# ==========================

def get_first_status(name):

    conn=get_db()

    cur=conn.cursor()


    cur.execute("""
    SELECT factory_approval,
           manager_approval

    FROM users

    WHERE name=%s

    """,
    (name,))


    data=cur.fetchone()


    conn.close()



    if not data:

        return "공장장 승인 대기"



    factory=data[0]

    manager=data[1]



    if factory==1:

        return "공장장 승인 대기"



    elif manager==1:

        return "담당자 확인 대기"



    else:

        return "대표 승인 대기"





# ==========================
# 연차 신청
# ==========================

@app.route("/leave", methods=["GET","POST"])
def leave():


    if "id" not in session:

        return redirect("/login")



    if request.method=="POST":


        conn=get_db()

        cur=conn.cursor()



        status=get_first_status(
            session["name"]
        )



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

        VALUES(%s,%s,%s,%s,%s,%s,%s)

        """,
        (

        session["name"],

        request.form["leave_type"],

        request.form["leave_date"],

        request.form.get("half_type",""),

        request.form["reason"],

        status,


        now_korea().strftime("%Y-%m-%d")

        ))



        conn.commit()   


        # 첫 승인자 푸시

        approver = get_next_approver(status)


        if approver:

            send_push(
                approver,
                "새로운 연차 신청이 있습니다."
            )


        conn.close()



        return redirect("/my_request")



    return render_template(

        "leave.html",

        name=session["name"],

        role=session["role"]

    )
# ==========================
# 구매 신청
# ==========================

@app.route("/purchase", methods=["GET","POST"])
def purchase():


    if "id" not in session:

        return redirect("/login")



    if request.method=="POST":


        conn=get_db()

        cur=conn.cursor()



        status=get_first_status(
            session["name"]
        )



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

        VALUES(%s,%s,%s,%s,%s,%s)

        """,
        (

        session["name"],

        request.form["item"],

        request.form["quantity"],

        request.form["reason"],

        status,

        now_korea().strftime("%Y-%m-%d")
        ))


        conn.commit()

        # 첫 승인자 푸시

        approver = get_next_approver(status)


        if approver:

            send_push(
                approver,
                "새로운 구매 요청이 있습니다."
            )

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



    cur.execute("""
    SELECT *

    FROM leave_request

    WHERE applicant=%s

    ORDER BY id DESC

    """,
    (
    session["name"],
    ))


    leave_data=cur.fetchall()



    cur.execute("""
    SELECT *

    FROM purchase_request

    WHERE applicant=%s

    ORDER BY id DESC

    """,
    (
    session["name"],
    ))


    purchase_data=cur.fetchall()



    conn.close()



    return render_template(

        "my_request.html",

        leave_data=leave_data,

        purchase_data=purchase_data,

        role=session["role"]

    )   

# ==========================
# 결재 대기함
# ==========================

@app.route("/approval")
def approval():

    if "id" not in session:
        return redirect("/login")


    role = session["role"]


    # 현재 로그인자의 승인 차례
    if role == "공장장":

        status = "공장장 승인 대기"


    elif role == "담당자":

        status = "담당자 확인 대기"


    elif role == "대표":

        status = "대표 승인 대기"


    else:

        return "권한 없음"



    conn = get_db()

    cur = conn.cursor()



    # ==========================
    # 연차 결재 대기
    # ==========================

    cur.execute("""
    SELECT *

    FROM leave_request

    WHERE status=%s

    ORDER BY id DESC

    """,
    (
        status,
    ))


    leave_data = cur.fetchall()



    # ==========================
    # 구매 결재 대기
    # ==========================

    cur.execute("""
    SELECT *

    FROM purchase_request

    WHERE status=%s

    ORDER BY id DESC

    """,
    (
        status,
    ))


    purchase_data = cur.fetchall()



    conn.close()



    return render_template(

        "approval.html",

        leave_data=leave_data,

        purchase_data=purchase_data

    )




# ==========================
# 전체 결재 진행 현황
# ==========================

@app.route("/approval_status")
def approval_status():


    if "id" not in session:

        return redirect("/login")



    if session["role"] not in ["담당자","대표"]:

        return "권한 없음"



    conn=get_db()

    cur=conn.cursor()



    cur.execute("""
    SELECT *
    FROM leave_request

    WHERE status IN
    (
    '공장장 승인 대기',
    '담당자 확인 대기',
    '대표 승인 대기',
    '최종 승인 완료'
    )

    OR status LIKE '반려%'

    ORDER BY id DESC

    """)


    leave_data=cur.fetchall()



    cur.execute("""
    SELECT *
    FROM purchase_request

    WHERE status IN
    (
    '공장장 승인 대기',
    '담당자 확인 대기',
    '대표 승인 대기',
    '최종 승인 완료'
    )

    OR status LIKE '반려%'

    ORDER BY id DESC

    """)


    purchase_data=cur.fetchall()



    conn.close()



    return render_template(

        "approval_status.html",

        leave_data=leave_data,

        purchase_data=purchase_data

    )
    
# ==========================
# 신청자 기준 다음 승인 단계 계산
# ==========================

def get_next_status(applicant, current_role):


    conn = get_db()

    cur = conn.cursor()


    cur.execute("""
    SELECT factory_approval,
           manager_approval

    FROM users

    WHERE name=%s
    """,
    (applicant,))


    user = cur.fetchone()


    conn.close()


    if not user:

        return "대표 승인 대기"



    factory = user[0]

    manager = user[1]



    if current_role == "공장장":


        if manager == 1:

            return "담당자 확인 대기"

        else:

            return "대표 승인 대기"



    elif current_role == "담당자":


        return "대표 승인 대기"



    elif current_role == "대표":


        return "최종 승인 완료"



    return "대표 승인 대기"




# ==========================
# 승인 처리
# ==========================

@app.route("/approve/<int:id>/<kind>")
def approve(id,kind):


    if "id" not in session:

        return redirect("/login")



    role=session["role"]



    conn=get_db()

    cur=conn.cursor()



    # ==========================
    # 현재 결재 상태 확인
    # ==========================


    if kind=="leave":

        cur.execute("""
        SELECT status
        FROM leave_request
        WHERE id=%s
        """,
        (id,))


    else:

        cur.execute("""
        SELECT status
        FROM purchase_request
        WHERE id=%s
        """,
        (id,))


    status_row = cur.fetchone()


    if not status_row:

        conn.close()

        return "자료 없음"


    current_status=status_row[0]



    # ==========================
    # 승인 순서 체크
    # ==========================


    if role=="공장장" and current_status!="공장장 승인 대기":

        conn.close()

        return """
        <script>
        alert('현재 공장장 승인 차례가 아닙니다.');
        history.back();
        </script>
        """



    if role=="담당자" and current_status!="담당자 확인 대기":

        conn.close()

        return """
        <script>
        alert('현재 담당자 확인 차례가 아닙니다.');
        history.back();
        </script>
        """



    if role=="대표" and current_status!="대표 승인 대기":

        conn.close()

        return """
        <script>
        alert('현재 대표 승인 차례가 아닙니다.');
        history.back();
        </script>
        """



    # ==========================
    # 신청자 확인
    # ==========================


    if kind=="leave":


        cur.execute("""
        SELECT applicant
        FROM leave_request
        WHERE id=%s
        """,
        (id,))


    else:


        cur.execute("""
        SELECT applicant
        FROM purchase_request
        WHERE id=%s
        """,
        (id,))



    row=cur.fetchone()



    if not row:

        conn.close()

        return "자료 없음"



    applicant=row[0]



    next_status=get_next_status(
        applicant,
        role
    )


    now = now_korea().strftime("%Y-%m-%d %H:%M:%S")



    history_text=(

        session["role"]
        + " "
        + session["name"]
        + " 승인 "
        + now

    )



    # ==========================
    # 연차 승인
    # ==========================


    if kind=="leave":


        cur.execute("""
        SELECT approval_history
        FROM leave_request
        WHERE id=%s
        """,
        (id,))


        old=cur.fetchone()[0]



        if old:

            history=old+"\n"+history_text

        else:

            history=history_text



        cur.execute("""
        UPDATE leave_request

        SET

        status=%s,

        approval_history=%s

        WHERE id=%s

        """,
        (
        next_status,
        history,
        id
        ))



    # ==========================
    # 구매 승인
    # ==========================


    else:


        cur.execute("""
        SELECT approval_history
        FROM purchase_request
        WHERE id=%s
        """,
        (id,))



        old=cur.fetchone()[0]



        if old:

            history=old+"\n"+history_text

        else:

            history=history_text



        cur.execute("""
        UPDATE purchase_request

        SET

        status=%s,

        approval_history=%s

        WHERE id=%s

        """,
        (
        next_status,
        history,
        id
        ))



    conn.commit()


    # 다음 결재자 푸시

    approver = get_next_approver(next_status)


    if approver:


        send_push(
            approver,
            "승인 확인 요청이 있습니다."
        )


    else:


        # 최종 승인 완료
        send_push_user(
            applicant,
            "신청이 최종 승인되었습니다."
        )


    conn.close()


    return redirect("/approval")

# ==========================
# 반려 처리
# ==========================

@app.route("/reject/<int:id>/<kind>", methods=["GET","POST"])
def reject(id,kind):

    if "id" not in session:
        return redirect("/login")


    if request.method=="GET":

        return render_template(
            "reject.html",
            id=id,
            kind=kind
        )


    reason=request.form["reason"]


    now = now_korea().strftime("%Y-%m-%d %H:%M:%S")

    reject_text = (
        session["role"]
        + " "
        + session["name"]
        + " 반려 : "
        + reason
        + " "
        + now
    )


    status="반려 : " + reason


    conn=get_db()
    cur=conn.cursor()


    # ==========================
    # 신청자 확인
    # ==========================

    if kind=="leave":

        cur.execute("""
        SELECT applicant
        FROM leave_request
        WHERE id=%s
        """,
        (id,))

    else:

        cur.execute("""
        SELECT applicant
        FROM purchase_request
        WHERE id=%s
        """,
        (id,))


    applicant_row = cur.fetchone()


    if not applicant_row:

        conn.close()

        return "신청자 없음"


    applicant = applicant_row[0]


    if kind=="leave":


        cur.execute("""
        SELECT reject_history
        FROM leave_request
        WHERE id=%s
        """,
        (id,))


        row=cur.fetchone()


        history = row[0] + "\n" + reject_text if row[0] else reject_text


        cur.execute("""
        UPDATE leave_request

        SET
        status=%s,
        reject_history=%s

        WHERE id=%s
        """,
        (
        status,
        history,
        id
        ))



    else:


        cur.execute("""
        SELECT reject_history
        FROM purchase_request
        WHERE id=%s
        """,
        (id,))


        row=cur.fetchone()


        history = row[0] + "\n" + reject_text if row[0] else reject_text


        cur.execute("""
        UPDATE purchase_request

        SET
        status=%s,
        reject_history=%s

        WHERE id=%s
        """,
        (
        status,
        history,
        id
        ))


    conn.commit()


    send_push_user(
        applicant,
        "신청이 반려되었습니다."
    )


    conn.close()

    return redirect("/approval")


# ==========================
# 공지사항 관리
# ==========================

@app.route("/notice_manage", methods=["GET","POST"])
def notice_manage():

    if "id" not in session:
        return redirect("/login")


    if session["role"] not in ["담당자","대표"]:
        return "권한 없음"



    conn = get_db()

    cur = conn.cursor()



    # ==========================
    # 공지 등록
    # ==========================

    if request.method == "POST":


        cur.execute("""
        INSERT INTO notice
        (
            title,
            content,
            writer,
            important
        )

        VALUES(%s,%s,%s,%s)

        """,
        (
            request.form["title"],
            request.form["content"],
            session["name"],
            request.form.get("important","0")
        ))


        conn.commit()



        # ==========================
        # 전체 사용자 공지 푸시
        # ==========================

        send_notice_push(
            "새로운 공지사항이 등록되었습니다.\n\n"
            + request.form["title"]
        )



    # ==========================
    # 공지 목록 조회
    # ==========================

    cur.execute("""
    SELECT *
    FROM notice
    ORDER BY important DESC,id DESC
    """)


    notices = cur.fetchall()


    conn.close()



    return render_template(
        "notice_manage.html",
        notices=notices
    )




# ==========================
# 전체 사용자 공지 푸시
# ==========================

def send_notice_push(message):


    conn = get_db()

    cur = conn.cursor()



    cur.execute("""
    SELECT push_token
    FROM users
    WHERE push_token IS NOT NULL
    """)



    users = cur.fetchall()



    conn.close()



    for user in users:


        token = user[0]


        try:


            msg = messaging.Message(

                notification=messaging.Notification(
                    title="선영알림",
                    body=message
                ),

                data={
                    "title":"선영알림",
                    "body":message
                },

                android=messaging.AndroidConfig(
                    priority="high"
                ),

                webpush=messaging.WebpushConfig(
                    notification=messaging.WebpushNotification(
                        title="선영알림",
                        body=message
                    ),
                    headers={
                        "Urgency":"high"
                    }
                ),

                token=token
            ) 



            response = messaging.send(msg)



            print(
                "공지 푸시 성공:",
                response
            )



        except Exception as e:


            print(
                "공지 푸시 오류:",
                e
            )       

# ==========================
# 공지 수정
# ==========================

@app.route("/notice_edit/<int:id>", methods=["GET","POST"])
def notice_edit(id):


    if "id" not in session:
        return redirect("/login")


    if session["role"] not in ["담당자","대표"]:
        return "권한 없음"



    conn=get_db()

    cur=conn.cursor()



    if request.method=="POST":


        cur.execute("""
        UPDATE notice

        SET

        title=%s,

        content=%s,

        important=%s

        WHERE id=%s

        """,
        (
            request.form["title"],
            request.form["content"],
            request.form.get("important","0"),
            id
        ))


        conn.commit()


        conn.close()


        return redirect("/notice_manage")



    cur.execute("""
    SELECT *
    FROM notice
    WHERE id=%s
    """,
    (id,))


    notice=cur.fetchone()


    conn.close()



    return render_template(
        "notice_edit.html",
        notice=notice
    )



# ==========================
# 공지 삭제
# ==========================

@app.route("/notice_delete/<int:id>")
def notice_delete(id):


    if "id" not in session:
        return redirect("/login")


    if session["role"] not in ["담당자","대표"]:
        return "권한 없음"



    conn=get_db()

    cur=conn.cursor()



    cur.execute("""
    DELETE FROM notice
    WHERE id=%s
    """,
    (id,))


    conn.commit()

    conn.close()


    return redirect("/notice_manage")

# ==========================
# 직원 관리
# ==========================

@app.route("/user_manage", methods=["GET","POST"])
def user_manage():


    if "id" not in session:

        return redirect("/login")


    if session["role"] not in ["담당자","대표"]:

        return "권한 없음"



    conn=get_db()

    cur=conn.cursor()



    if request.method=="POST":


        cur.execute("""
        INSERT INTO users
        (
        user_id,
        password,
        name,
        role,
        factory_approval,
        manager_approval
        )

        VALUES(%s,%s,%s,%s,%s,%s)

        """,
        (

        request.form["user_id"],

        request.form["password"],

        request.form["name"],

        request.form["role"],

        request.form.get(
            "factory_approval",
            "1"
        ),

        request.form.get(
            "manager_approval",
            "1"
        )

        ))



        conn.commit()



    cur.execute("""
    SELECT *

    FROM users

    ORDER BY id DESC

    """)



    users=cur.fetchall()



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



    if session["role"] not in ["담당자","대표"]:

        return "권한 없음"



    conn=get_db()

    cur=conn.cursor()



    if request.method=="POST":


        user_id=request.form["user_id"].strip()

        password=request.form["password"].strip()

        name=request.form["name"].strip()

        role=request.form["role"].strip()

        factory_approval=request.form["factory_approval"]

        manager_approval=request.form["manager_approval"]



        cur.execute("""
        SELECT id

        FROM users

        WHERE user_id=%s
        
        AND id!=%s

        """,
        (
        user_id,
        id
        ))



        exist=cur.fetchone()



        if exist:


            conn.close()


            return """
            <script>
            alert('이미 존재하는 아이디입니다.');
            history.back();
            </script>
            """



        cur.execute("""
        UPDATE users

        SET

        user_id=%s,

        password=%s,

        name=%s,

        role=%s,

        factory_approval=%s,

        manager_approval=%s

        WHERE id=%s

        """,
        (

        user_id,

        password,

        name,

        role,

        factory_approval,

        manager_approval,

        id

        ))



        conn.commit()

        conn.close()



        return redirect("/user_manage")





    cur.execute("""
    SELECT *

    FROM users

    WHERE id=%s

    """,
    (id,))



    user=cur.fetchone()



    conn.close()



    return render_template(

        "user_edit.html",

        user=user

    )

# ==========================
# 직원 삭제
# ==========================

@app.route("/user_delete/<int:id>")
def user_delete(id):

    if "id" not in session:
        return redirect("/login")

    if session["role"] not in ["담당자","대표"]:
        return "권한 없음"

    conn=get_db()
    cur=conn.cursor()

    cur.execute("""
    SELECT user_id
    FROM users
    WHERE id=%s
    """,(id,))

    row=cur.fetchone()

    if not row:
        conn.close()
        return redirect("/user_manage")

    # 기본계정 삭제금지
    if row[0] in [
        "jwlee01",
        "hrkim01",
        "rarenom",
        "ceo01"
    ]:

        conn.close()

        return """
        <script>
        alert('기본 계정은 삭제할 수 없습니다.');
        location.href='/user_manage';
        </script>
        """

    cur.execute("""
    DELETE FROM users
    WHERE id=%s
    """,(id,))

    conn.commit()
    conn.close()

    return redirect("/user_manage")



# ==========================
# 연차 엑셀 다운로드
# ==========================

@app.route("/export_leave")
def export_leave():


    if "id" not in session:

        return redirect("/login")



    if session["role"] not in ["담당자","대표"]:

        return "권한 없음"


    conn=get_db()



    df=pd.read_sql_query(
        """
        SELECT *

        FROM leave_request

        ORDER BY id DESC

        """,
        conn
    )



    conn.close()



    filename = (
        "연차신청현황_"
        +
        now_korea().strftime("%Y%m%d_%H%M%S")
        +
        ".xlsx"
    )



    df.to_excel(

        filename,

        index=False

    )



    return send_file(

        filename,

        as_attachment=True

    )

# ==========================
# 구매 요청 엑셀 다운로드
# ==========================

@app.route("/export_purchase")
def export_purchase():

    if "id" not in session:

        return redirect("/login")


    if session["role"] not in ["담당자","대표"]:

        return "권한 없음"



    conn = get_db()


    df = pd.read_sql_query(
        """
        SELECT *

        FROM purchase_request

        ORDER BY id DESC

        """,

        conn
    )


    conn.close()



    filename = (
        "구매요청현황_"
        +
        now_korea().strftime("%Y%m%d_%H%M%S")
        +
        ".xlsx"
    )



    df.to_excel(

        filename,

        index=False

    )



    return send_file(

        filename,

        as_attachment=True

    )

# ==========================
# DB 전체 Excel 백업 다운로드
# ==========================

@app.route("/backup_database")
def backup_database():

    if "id" not in session:
        return redirect("/login")


    if session["role"] not in ["담당자","대표"]:
        return "권한 없음"


    conn = get_db()


    filename = (
        "SUNYOUNG_DB_BACKUP_"
        +
        now_korea().strftime("%Y%m%d_%H%M%S")
        +
        ".xlsx"
    )


    with pd.ExcelWriter(filename) as writer:


        tables = [
            "users",
            "leave_request",
            "purchase_request"
        ]


        for table in tables:


            df = pd.read_sql_query(
                f"SELECT * FROM {table}",
                conn
            )


            df.to_excel(
                writer,
                sheet_name=table,
                index=False
            )


    conn.close()


    return send_file(
        filename,
        as_attachment=True
    )
    
# ==========================
# DB Excel 복원
# ==========================

@app.route("/restore_database", methods=["GET","POST"])
def restore_database():


    if "id" not in session:
        return redirect("/login")


    if session["role"] not in ["담당자","대표"]:
        return "권한 없음"



    if request.method == "POST":


        file = request.files["file"]


        if not file:

            return """
            <script>
            alert('파일을 선택하세요.');
            history.back();
            </script>
            """



        conn = get_db()

        cur = conn.cursor()



        tables = [

            "users",

            "leave_request",

            "purchase_request"

        ]



        try:


            # 기존 데이터 삭제

            for table in tables:

                cur.execute(
                    f"DELETE FROM {table}"
                )



            # 엑셀 데이터 읽기

            excel = pd.ExcelFile(file)



            for table in tables:


                if table in excel.sheet_names:


                    df = pd.read_excel(
                        file,
                        sheet_name=table
                    )


                    columns = list(df.columns)



                    column_text = ",".join(columns)



                    value_text = ",".join(
                        ["%s"] * len(columns)
                    )



                    for _, row in df.iterrows():


                        values = []


                        for v in row:

                            if pd.isna(v):

                                values.append(None)

                            else:

                                values.append(v)



                        cur.execute(
                            f"""
                            INSERT INTO {table}
                            ({column_text})
                            VALUES
                            ({value_text})
                            """,
                            values
                        )



            conn.commit()


            conn.close()



            return """
            <script>
            alert('DB 복원이 완료되었습니다.');
            location.href='/main';
            </script>
            """



        except Exception as e:


            conn.rollback()

            conn.close()


            return f"""
            <script>
            alert('복원 오류 : {e}');
            history.back();
            </script>
            """




    return """
    <h2>DB 복원</h2>

    <form method="post" enctype="multipart/form-data">

        <input type="file" name="file">

        <button type="submit">
        복원 실행
        </button>

    </form>
    """

@app.route("/test_push")
def test_push():

    if "id" not in session:
        return redirect("/login")


    send_push_user(
        session["name"],
        "테스트 푸시 알림입니다."
    )


    return "푸시 전송 완료"
    
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

init_db()

if __name__=="__main__":

    app.run(
        host="0.0.0.0",
        port=5000
    )