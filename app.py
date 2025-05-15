from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify,
)
from openai import OpenAI
from dotenv import load_dotenv
import sqlite3, os, hashlib

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
# 建立一個 OpenAI 客戶端實例
client = OpenAI(api_key=api_key)
app = Flask(__name__)
app.secret_key = "your_secret_key_here"

DB_NAME = "users.db"


@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")
    try:
        msgs = [
            {
                "role": "system",
                "content": (
                    "你是一位有耐心、善於引導的中文老師。"
                    "當學生提出問題時，你要用繁體中文回答，"
                    "語氣像在課堂上啟發學生思考，"
                    "並幫助他們一步步理解概念。"
                ),
            },
            {"role": "user", "content": user_message},
        ]
        # 使用新的 chat.completions.create 方法
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=msgs,
        )
        # 读取回复内容
        reply = resp.choices[0].message.content
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def init_db():
    if not os.path.exists(DB_NAME):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute(
            """CREATE TABLE users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL)"""
        )
        conn.commit()
        conn.close()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = hash_password(request.form["password"])
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password),
            )
            conn.commit()
            conn.close()
            flash("註冊成功，請登入！")
            return render_template("home.html")
        except sqlite3.IntegrityError:
            flash("使用者名稱已存在")
    return render_template("home.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = hash_password(request.form["password"])

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, password),
        )
        user = c.fetchone()
        conn.close()

        if user:
            session["username"] = username
            return redirect(url_for("dashboard"))
        else:
            flash("帳號或密碼錯誤")
            return redirect(url_for("home"))  # 導回首頁，再顯示錯誤訊息

    return redirect(url_for("home"))


@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return render_template("home.html")
    return render_template("index.html", username=session["username"])


@app.route("/logout")
def logout():
    session.pop("username", None)
    flash("已登出")
    return render_template("home.html")


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
