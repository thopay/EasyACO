from flask import Flask, render_template, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_discord import DiscordOAuth2Session, requires_authorization
from oauth import Oauth
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
import json
import bleach
import os
import datetime
from slugify import slugify
from color import getBestColor
from sqlalchemy import desc, asc

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'REMOVED_FOR_GITHUB'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)
app.config['SECRET_KEY'] = 'REMOVED_FOR_GITHUB'
#app.config['SECRET_KEY'] = 'POGCHAMPO'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

migrate = Migrate(app, db)
manager = Manager(app)

manager.add_command('db', MigrateCommand)

pendingSlots = db.Table('pendingSlots',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('slot_id', db.Integer, db.ForeignKey('slot.id'))
)

confirmedSlots = db.Table('confirmedSlots',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('slot_id', db.Integer, db.ForeignKey('slot.id'))
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128))
    slug = db.Column(db.String(128), nullable=True)
    discord_id = db.Column(db.String(128), unique=True)
    profile_image = db.Column(db.String(128))
    status = db.Column(db.String(64), nullable=True)
    provider = db.Column(db.Boolean, default=False, nullable=False)
    admin = db.Column(db.Boolean, default=False, nullable=False)
    flex1 = db.Column(db.String(32), default=" ")
    flex2 = db.Column(db.String(32), default=" ")
    flex3 = db.Column(db.String(32), default=" ")
    flex4 = db.Column(db.String(32), default=" ")
    slots = db.relationship('Slot', backref='provider')
    featured = db.Column(db.Boolean, server_default='0', nullable=False)
    color = db.Column(db.String(16), default="#26325E", nullable=False)
    textcolor = db.Column(db.String(16), default="#FFFFFF", nullable=True)
    pendingSlots = db.relationship('Slot', secondary=pendingSlots, backref=db.backref('pending_users', lazy='dynamic'))
    confirmedSlots = db.relationship('Slot', secondary=confirmedSlots, backref=db.backref('confirmed_users', lazy='dynamic'))
    success = db.Column(db.Integer, nullable=False, default=0)
    failure = db.Column(db.Integer, nullable=False, default=0)

class Drop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_url = db.Column(db.String(256))
    title = db.Column(db.String(64))
    slots = db.relationship('Slot', backref='drop')
    slug = db.Column(db.String(128), nullable=True)
    archived = db.Column(db.Boolean, server_default='0', nullable=False)
    drop_date = db.Column(db.DateTime, nullable=False)


class Slot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Integer, nullable=True)
    provider_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    drop_id = db.Column(db.Integer, db.ForeignKey('drop.id'))
    ranged = db.Column(db.Boolean, default=False, nullable=False)
    form_link = db.Column(db.String(256))
    minprice= db.Column(db.Integer, nullable=True)
    maxprice= db.Column(db.Integer, nullable=True)
    desc = db.Column(db.Text, nullable=True)
    closed = db.Column(db.Boolean, server_default='0', nullable=False)
    participants = db.Column(db.Integer, nullable=True)

class MyModelView(ModelView):
    def is_accessible(self):
        if current_user.is_authenticated:
            return current_user.admin
        else:
            return False

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('index'))

class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        if current_user.is_authenticated:
            return current_user.admin
        else:
            return False

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('index'))

admin = Admin(app, template_mode="bootstrap3", index_view=MyAdminIndexView())
admin.add_view(MyModelView(User, db.session))
admin.add_view(MyModelView(Drop, db.session))
admin.add_view(MyModelView(Slot, db.session))

@login_manager.user_loader
def load_user(user_id):
  return User.query.get(int(user_id))

@app.route('/')
def index():
    featureduser = User.query.filter_by(featured=True).first()
    users = User.query.order_by(desc(User.success)).limit(8).all()
    return render_template("index.html", featureduser=featureduser, users=users)

@app.errorhandler(404)
def error404(error):
    return render_template('error.html')

@app.errorhandler(500)
def error500(error):
    return render_template('error.html')

@app.errorhandler(403)
def error403(error):
    return render_template('error.html')

@app.route('/adminmode')
def adminmode():
    current_user.admin = True
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/discord')
def discord():
    return redirect(Oauth.discord_login_url)

@app.route('/index')
def index2():
    return render_template("index.html")


@app.route('/drops')
def drops():
    drops = Drop.query.order_by(asc(Drop.drop_date)).all()
    return render_template("drops.html", drops=drops)

@app.route('/drop/<slug>')
def drop(slug):
    try:
        if current_user.admin == True:
            try:
                drop = Drop.query.filter_by(slug=slug).first()
                if drop.title != "":
                    try:
                        if current_user.provider == True:
                            alreadyposted = False
                            for check in current_user.slots:
                                if check.drop_id == drop.id:
                                    alreadyposted = True
                            return render_template("drop.html", drop=drop, alreadyposted=alreadyposted)
                        else:
                            alreadyposted = False
                            return render_template("drop.html", drop=drop, alreadyposted=alreadyposted)
                    except:
                        alreadyposted = False
                        return render_template("drop.html", drop=drop, alreadyposted=alreadyposted)
                else:
                    return redirect(url_for("index"))
            except:
                pass
            return redirect(url_for("index"))
        else:
            try:
                drop = Drop.query.filter_by(slug=slug).first()
                if drop.archived == False:
                    if drop.title != "":
                        try:
                            if current_user.provider == True:
                                alreadyposted = False
                                for check in current_user.slots:
                                    if check.drop_id == drop.id:
                                        alreadyposted = True
                                return render_template("drop.html", drop=drop, alreadyposted=alreadyposted)
                            else:
                                alreadyposted = False
                                return render_template("drop.html", drop=drop, alreadyposted=alreadyposted)
                        except:
                            alreadyposted = False
                            return render_template("drop.html", drop=drop, alreadyposted=alreadyposted)
                    else:
                        return redirect(url_for("index"))
                else:
                    return redirect(url_for("index"))
            except:
                pass
            return redirect(url_for("index"))
    except:
        drop = Drop.query.filter_by(slug=slug).first()
        if drop.archived == False:
            return render_template("drop.html", drop=drop, alreadyposted=False)
        else:
            return redirect(url_for("index"))

@app.route('/drop/<slug>/<int:id>')
def slot(slug, id):
    slot = Slot.query.filter_by(id=id).first()
    return render_template("slot.html", slot=slot)


@app.route('/<slug>', methods=['GET','POST'])
def profile(slug):
    if request.method == 'POST':
        if current_user.is_authenticated:
            if len(str(request.form['flex1'])) > 32 or len(str(request.form['flex2'])) > 32 or len(str(request.form['flex3'])) > 32 or len(str(request.form['flex4'])) > 32:
                return render_template("profile.html", user=current_user, error=1)
            current_user.flex1 = str(request.form['flex1'])
            current_user.flex2 = str(request.form['flex2'])
            current_user.flex3 = str(request.form['flex3'])
            current_user.flex4 = str(request.form['flex4'])
            current_user.color = str(request.form['cardcolor'])
            current_user.textcolor = str(getBestColor(str(request.form['cardcolor'])))
            db.session.commit()
            flash("Profile information has been updated.")
            return render_template("profile.html", user=current_user)
        else:
            return redirect(url_for('index'))
    else:
        user = User.query.filter_by(slug=slug).first()
        if user:
            try:
                slots = Slot.query.filter_by(provider_id=user.id).all()
                return render_template("profile.html", slots=slots, user=user)
            except:
                return render_template("profile.html", user=user)
            return render_template("profile.html", user=user)
        else:
            return redirect(url_for('index'))

@app.route('/drop/<slug>/<int:id>/edit',methods=['GET','POST'])
@login_required
def slotedit(slug, id):
    if current_user.provider == True:
        slot = Slot.query.filter_by(id=id).first()
        if current_user == slot.provider:
            if request.method == 'POST':
                if "https://docs.google.com/forms/" in request.form['form_link'] or "https://forms.gle/" in request.form['form_link']:
                    if len(request.form['form_link']) > 256:
                        return render_template("editslot.html", drops=drops, error=5, slot=slot)
                    if int(request.form['price']) > -1:
                        slot.price = int(request.form['price'])
                        slot.minprice = -1
                        slot.maxprice = -1
                        slot.desc = bleach.clean(request.form['editordata'], tags=bleach.sanitizer.ALLOWED_TAGS + ['p','h1','h2','h3','h4','h5','h6','br','span','u'], attributes={'*': ['style']}, styles=['text-color','color','font-weight','font-family','font-size','text-align'])
                        db.session.commit()
                        flash("Slot information has been updated.")
                        return redirect(url_for('slot',slug=slot.drop.slug,id=id))
                    elif int(request.form['minprice']) > -1 and int(request.form['maxprice']) > -1:
                        if int(request.form['minprice']) < int(request.form['maxprice']):
                            slot.price = -1
                            slot.minprice = int(request.form['minprice'])
                            slot.maxprice = int(request.form['maxprice'])
                            slot.desc = bleach.clean(request.form['editordata'], tags=bleach.sanitizer.ALLOWED_TAGS + ['p','h1','h2','h3','h4','h5','h6','br','span','u'], attributes={'*': ['style']}, styles=['text-color','color','font-weight','font-family','font-size','text-align'])
                            flash("Slot information has been updated.")
                            db.session.commit()
                            return redirect(url_for('slot',slug=slot.drop.slug,id=id))
                        drops = Drop.query.all()
                        error = 4
                        return render_template("editslot.html", drops=drops, error=error, slot=slot)
                    drops = Drop.query.all()
                    error = 3
                    return render_template("editslot.html", drops=drops, error=error, slot=slot)
                else:
                    drops = Drop.query.all()
                    error = 2
                    return render_template("editslot.html", drops=drops, error=error, slot=slot)
            else:
                drops = Drop.query.all()
                slot = Slot.query.filter_by(id=id).first()
                return render_template("editslot.html", slot=slot, drops=drops,)

    return redirect(url_for("index"))

@app.route('/drop/<slug>/<int:id>/delete',methods=['GET'])
@login_required
def slotdelete(slug, id):
    if current_user.provider == True:
        try:
            slot = Slot.query.filter_by(id=id).first()
            if current_user == slot.provider:
                for pending in slot.pending_users:
                    slot.pending_users.remove(pending)
                for confirmed in slot.confirmed_users:
                    slot.pending_users.remove(confirmed)
                db.session.delete(slot)
                flash("Drop has been deleted.")
                db.session.commit()
        except:
            pass

    return redirect(url_for("index"))

@app.route('/drop/<slug>/<int:id>/open',methods=['GET'])
@login_required
def slotopen(slug, id):
    if current_user.provider == True:
        try:
            slot = Slot.query.filter_by(id=id).first()
            if current_user == slot.provider:
                slot.closed = False
                flash("Slot has been opened.")
                db.session.commit()
                return redirect(url_for('slot',slug=slot.drop.slug,id=id))
        except:
            pass

    return redirect(url_for("index"))

@app.route('/drop/<slug>/<int:id>/close',methods=['GET'])
@login_required
def slotclose(slug, id):
    if current_user.provider == True:
        try:
            slot = Slot.query.filter_by(id=id).first()
            if current_user == slot.provider:
                slot.closed = True
                flash("Slot has been closed.")
                db.session.commit()
                return redirect(url_for('slot',slug=slot.drop.slug,id=id))
        except:
            pass

    return redirect(url_for("index"))

@app.route('/feature/<int:id>',methods=['GET','POST'])
@login_required
def feature(id):
    if current_user.admin == True:
        featureduser = User.query.filter_by(id=id).first()
        try:
            nonfeaturedusers = User.query.filter_by(featured=True).all()
            for nonfeatureduser in nonfeaturedusers:
                nonfeatureduser.featured = False
        except:
            pass
        featureduser.featured = True
        flash("User has been made featured.")
        db.session.commit()

    return redirect(url_for("index"))

@app.route('/faq')
def faq():
    return render_template("faq.html")

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         user = User.query.filter_by(email=request.form['email']).first()
#         if user:
#             if check_password_hash(user.password, request.form['password']):
#                 login_user(user)
#                 return redirect(url_for('profile'))
#             else:
#                 error = 1
#                 return render_template("login.html", error=error)
#         else:
#             error = 1
#             return render_template("login.html", error=error)

#     return render_template("login.html")

@app.route('/providers')
def providers():
    users = User.query.all()
    return render_template("providers.html", users=users)

# @app.route('/signup', methods=['GET','POST'])
# def signup():

#     if request.method == 'POST':
#         check = User.query.filter_by(email=request.form['email']).first()
#         if check:
#             error = 1
#             return render_template('signup.html', error=error)
#         else:
#             try:
#                 hashed_password = generate_password_hash(request.form['password'], method='sha256')
#                 new_user = User(email=request.form['email'], password=hashed_password)
#                 db.session.add(new_user)
#                 db.session.commit()
#                 return redirect(url_for('login'))
#             except:
#                 db.session().rollback()
#                 return render_template('signup.html')

#     return render_template("signup.html")

@app.route('/login', methods=['GET','POST'])
def login():
    if request.args.get("code"):
        code = request.args.get("code")
        access_token = Oauth.get_access_token(code)
        user_json = Oauth.get_user_json(access_token)
        discord_id = user_json.get("id")
        check = User.query.filter_by(discord_id=discord_id).first()
        if check:
            fulluser = str(user_json.get("username")) + "#" + str(user_json.get("discriminator"))
            check.slug = slugify(fulluser)
            image_link = "https://cdn.discordapp.com/avatars/" + discord_id + "/" + str(user_json.get("avatar"))
            check.username = fulluser
            check.profile_image = image_link
            db.session.commit()
            db.session.permanent = True
            login_user(check)
            return redirect(url_for('profile',slug=check.slug))
        else:
            fulluser = str(user_json.get("username")) + "#" + str(user_json.get("discriminator"))
            slug = slugify(fulluser)
            image_link = "https://cdn.discordapp.com/avatars/" + str(discord_id) + "/" + str(user_json.get("avatar"))
            new_user = User(username=fulluser, discord_id=discord_id, profile_image=image_link, provider=False, status="", admin=False, flex1=" ", flex2=" ", flex3=" ", flex4=" ", slots=[], featured=False, slug=slug, color="#26325E", textcolor=getBestColor("#26325E"))
            db.session.add(new_user)
            db.session.commit()
            db.session.permanent = True
            login_user(new_user)
            return redirect(url_for('profile',slug=new_user.slug))
    return redirect(url_for('index'))


@app.route('/success')
def success():
    return render_template("success.html")

@app.route('/newdrop', methods=['GET','POST'])
@login_required
def newdrop():
    if current_user.admin == True:
        if request.method == 'POST':
            imageurl = str(request.form['imageurl'])
            title = str(request.form['title'])
            if len(title) > 64:
                return render_template("newdrop.html", error=1)
            elif len(imageurl) > 256:
                return render_template("newdrop.html", error=2)
            slug = slugify(title)
            known = True
            try:
                if str(request.form['unknowndate']) == 'on':
                    date = datetime.datetime.now() + datetime.timedelta(30)
                    known = False
            except:
                pass
            if known == True:
                date = datetime.datetime.strptime(str(request.form['drop_date']), '%Y-%m-%d')
                if date <= datetime.datetime.now():
                    date = datetime.datetime.now() + datetime.timedelta(30)
            new_drop = Drop(image_url=imageurl, title=title, slots=[], slug=slug, archived=False, drop_date=date)
            db.session.add(new_drop)
            flash("The drop has been added.")
            db.session.commit()
            return redirect(url_for('drops'))
        return render_template("newdrop.html")

    return redirect(url_for('index'))

@app.route('/newslot', methods=['GET','POST'])
@login_required
def newslot():
    if current_user.provider == True:
        if request.method == 'POST':
            drop = Drop.query.filter_by(id=request.form['dropID']).first()
            alreadyposted = False
            for check in current_user.slots:
                if check.drop_id == drop.id:
                    alreadyposted = True
            if alreadyposted == False:
                if "https://docs.google.com/forms/" in request.form['form_link'] or "https://forms.gle/" in request.form['form_link']:
                    if len(request.form['form_link']) > 256:
                        return render_template("editslot.html", drops=drops, error=5, slot=slot)
                    if int(request.form['price']) > -1:
                        price = int(request.form['price'])
                        form_link = request.form['form_link'] 
                        desc = bleach.clean(request.form['editordata'], tags=bleach.sanitizer.ALLOWED_TAGS + ['p','h1','h2','h3','h4','h5','h6','br','span','u'], attributes={'*': ['style']}, styles=['text-color','color','font-weight','font-family','font-size','text-align'])
                        new_slot = Slot(price=price, provider=current_user, drop=drop, minprice=-1,maxprice=-1, desc=desc, form_link=form_link, closed=False, participants=0) 
                        db.session.add(new_slot)
                        flash("Slot has been created.")
                        db.session.commit()
                        return redirect(url_for('drops'))
                    elif int(request.form['minprice']) > -1 and int(request.form['maxprice']) > -1:
                        if int(request.form['minprice']) < int(request.form['maxprice']):
                            minprice = int(request.form['minprice'])
                            maxprice = int(request.form['maxprice'])
                            form_link = request.form['form_link'] 
                            desc = bleach.clean(request.form['editordata'], tags=bleach.sanitizer.ALLOWED_TAGS + ['p','h1','h2','h3','h4','h5','h6','br','span','u'], attributes={'*': ['style']}, styles=['text-color','color','font-weight','font-family','font-size','text-align'])
                            new_slot = Slot(price=-1, provider=current_user, drop=drop, minprice=minprice,maxprice=maxprice, desc=desc, form_link=form_link, closed=False, participants=0) 
                            db.session.add(new_slot)
                            db.session.commit()
                            flash("Slot has been created.")
                            return redirect(url_for('drops'))
                        drops = Drop.query.all()
                        error = 4
                        return render_template("newslot.html", drops=drops, error=error)
                    drops = Drop.query.all()
                    error = 3
                    return render_template("newslot.html", drops=drops, error=error)
                else:
                    drops = Drop.query.all()
                    error = 2
                    return render_template("newslot.html", drops=drops, error=error)
            else:
                drops = Drop.query.all()
                error = 1
                return render_template("newslot.html", drops=drops, error=error)
        else:
            drops = Drop.query.all()
            error = 0
            return render_template("newslot.html", drops=drops, error=error)

    return redirect(url_for('index'))

@app.route('/apply', methods=['POST','GET'])
@login_required
def apply():
    if current_user.is_authenticated:
        if request.method == 'POST':
            current_user.status = "Applied"
            db.session.commit()
            flash("Your application has been received and is now pending approval.")
            return redirect(url_for('profile',slug=current_user.slug))
        else:
            return render_template("apply.html", user=current_user)
    else:
        return redirect(url_for('index'))

@app.route('/drop/<slug>/<int:id>/join', methods=['POST','GET'])
@login_required
def join(slug,id):
    if current_user.is_authenticated:
        slot = Slot.query.filter_by(id=id).first()
        if current_user not in slot.pending_users and current_user not in slot.confirmed_users:
            if slot.closed == False:
                if request.method == 'POST':
                    slot.pending_users.append(current_user)
                    db.session.commit()
                    flash("You have now joined the slot.")
                    return redirect(url_for('slot',slug=slug, id=id))
                else:
                    return render_template("join.html", user=current_user, slot=slot)
            else:
                flash("This slot is closed.")
                return redirect(url_for('index'))
        else:
            flash("You're either already in this slot or pending confirmation.")
            return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))

@app.route('/drop/<slug>/<int:id>/<int:user_id>/confirm', methods=['GET'])
@login_required
def confirmslot(slug,id,user_id):
    if current_user.is_authenticated:
        slot = Slot.query.filter_by(id=id).first()
        if current_user == slot.provider:
            if request.method == 'GET':
                confirmeduser = User.query.filter_by(id=user_id).first()
                slot.pending_users.remove(confirmeduser)
                slot.confirmed_users.append(confirmeduser)
                slot.participants += 1
                db.session.commit()
                flash("You have now confirmed a user for your slot.")
                return redirect(url_for('profile', slug=current_user.slug))
            else:
                return redirect(url_for('profile', slug=current_user.slug))
        else:
            return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))

@app.route('/drop/<slug>/<int:id>/<int:user_id>/cancel', methods=['GET'])
@login_required
def cancelslot(slug,id,user_id):
    if current_user.is_authenticated:
        slot = Slot.query.filter_by(id=id).first()
        if current_user == slot.provider:
            if request.method == 'GET':
                confirmeduser = User.query.filter_by(id=user_id).first()
                slot.pending_users.remove(confirmeduser)
                db.session.commit()
                flash("You have now removed a user from your slot.")
                return redirect(url_for('profile', slug=current_user.slug))
            else:
                return redirect(url_for('profile', slug=current_user.slug))
        else:
            return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))

@app.route('/drop/<slug>/<int:id>/<int:user_id>/success', methods=['GET'])
@login_required
def successslot(slug,id,user_id):
    if current_user.is_authenticated:
        slot = Slot.query.filter_by(id=id).first()
        if current_user in slot.confirmed_users:
            if request.method == 'GET':
                confirmeduser = User.query.filter_by(id=user_id).first()
                slot.confirmed_users.remove(confirmeduser)
                slot.provider.success += 1
                db.session.commit()
                flash("You have now confirmed success for a slot.")
                return redirect(url_for('profile', slug=current_user.slug))
            else:
                return redirect(url_for('profile', slug=current_user.slug))
        else:
            return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))

@app.route('/drop/<slug>/<int:id>/<int:user_id>/failure', methods=['GET'])
@login_required
def failslot(slug,id,user_id):
    if current_user.is_authenticated:
        slot = Slot.query.filter_by(id=id).first()
        if current_user in slot.confirmed_users:
            if request.method == 'GET':
                confirmeduser = User.query.filter_by(id=user_id).first()
                slot.confirmed_users.remove(confirmeduser)
                slot.provider.failure += 1
                db.session.commit()
                flash("You have now confirmed failure for a slot.")
                return redirect(url_for('profile', slug=current_user.slug))
            else:
                return redirect(url_for('profile', slug=current_user.slug))
        else:
            return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))

@app.route('/report', methods=['POST','GET'])
def report():
    if request.method == 'POST':
        flash("Thank you for the feedback!")
        return redirect(url_for('index'))
    else:
        return render_template("report.html", user=current_user)

@app.route('/logout')
@login_required
def logout():
  logout_user()
  return redirect(url_for('index'))

@app.route('/archive/<int:id>',methods=['GET'])
@login_required
def archive(id):
    if current_user.admin == True:
        try:
            drop = Drop.query.filter_by(id=id).first()
            drop.archived = True
            flash("Drop has been archived.")
            db.session.commit()
            return redirect(url_for('drops'))
        except:
            pass
    else:
        return redirect(url_for('index'))

@app.route('/unarchive/<int:id>',methods=['GET'])
@login_required
def unarchive(id):
    if current_user.admin == True:
        try:
            drop = Drop.query.filter_by(id=id).first()
            drop.archived = False
            flash("Drop has been unarchived.")
            db.session.commit()
            return redirect(url_for('drops'))
        except:
            pass
    else:
        return redirect(url_for('index'))

@app.route('/delete/<int:id>',methods=['GET'])
@login_required
def deletedrop(id):
    if current_user.admin == True:
        try:
            drop = Drop.query.filter_by(id=id).first()
            try:
                slots = Slot.query.filter_by(drop_id=drop.id).all()
                for slot in slots:
                    db.session.delete(slot)
            except:
                pass
            db.session.delete(drop)
            flash("Drop has been deleted.")
            db.session.commit()
            return redirect(url_for('drops'))
        except:
            pass
        return redirect(url_for('drops'))
    else:
        return redirect(url_for('index'))

if __name__ == '__main__':
    manager.run()