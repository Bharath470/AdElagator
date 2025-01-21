from app import app
from flask import Flask, render_template, request, redirect, session, url_for, flash
from models import Ratings, Review, db, User,Infl_platform,Spon_industry,Campaign,Ads,Request,Influencer,Negotiate,Sponsor
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
from sqlalchemy import desc, select,func
from werkzeug.utils import secure_filename

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            flash("You need to login first")
            return redirect(url_for('login'))
        user = User.query.filter_by(username=session['username']).first()
        if not user:
            session.pop('username')
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return wrapper
def blocked_user_check(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = User.query.filter_by(username=session['username']).first()
        if user.is_flag:
            flash("You are blocked by admin")
            return redirect(url_for(session['role']+'_dashboard'))
        return func(*args, **kwargs)
    return wrapper

@app.route('/sponsor_register',methods=['GET','POST'])
def sponsor_register():    
    if request.method == "GET":
        industries = Spon_industry.query.all()
        return render_template("sponsor/sponsor_register.html", industries=industries,user=None)
    if request.method == 'POST':
        username=request.form['username']
        name=request.form['name']
        pw=request.form['password']
        cpw=request.form['confirmpassword']
        email=request.form['email']
        industry = request.form['industry']
        gender = request.form['gender']
        if not username or not pw or not cpw:
            flash("Please fill all the mandatory fields")
            return redirect(url_for('sponsor_register'))
        if not pw == cpw:
            flash("Confirm and Password are not same")
            return redirect(url_for('sponsor_register'))
        user = User.query.filter_by(username=username).first()
        if user:
            flash("Please choose another username, selected username is taken")
            return redirect(url_for('sponsor_register'))
        user = User(username=username, password=generate_password_hash(pw),email=email,name=name,role="sponsor",gender=gender)
        db.session.add(user)
        db.session.commit()
        industry = Spon_industry(industry=industry,user_id=user.id)
        db.session.add(industry)
        db.session.commit()
        sponsor =Sponsor(user_id =user.id,industry=industry.industry)
        db.session.add(sponsor)
        db.session.commit()
        flash(f'thanks for registration {name}',category="success")
        return redirect(url_for('login'))


@app.route('/',methods=['GET','POST'])
def login():
    if request.method == 'GET':
            return render_template('login.html',user=None)
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password, password):
            flash("Username or password is incorrect")
            print(user,'1')
            return redirect(url_for('login'))

        session['username'] = username
        session['id'] = user.id
        session['role'] = user.role
        if user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        if user.role =='sponsor':
            return redirect(url_for('sponsor_dashboard'))
        if user.role == 'influencer':
            return redirect(url_for('influencer_dashboard'))
        if user.role not in ['admin','influencer','sponsor']:
            flash("You are not authorized to access this page")
            return redirect(url_for('login'))
        # return redirect(url_for('_profile'))



@app.route('/sponsor_dashboard',methods=['GET','POST']) 
@login_required
def sponsor_dashboard():
       if 'username' not in session:
           flash("Please login to access this page")
           return redirect(url_for('login'))
       if request.method == 'GET':
            username=session['username']
            user = User.query.filter_by(username=username).first()
            return render_template('sponsor/sponsor_dashboard.html',user=user,active_campaigns=get_active_campaigns(),active_requests=get_campaign_requests(),active_negotiations=get_active_negotiations())
       if request.method == 'POST':
         pass
@app.route('/campaign_create', methods=['GET', 'POST'])
@blocked_user_check
@login_required
def create_campaign():
    if request.method == 'GET':
        return render_template('campaign/create.html')
    if request.method == 'POST':
        # organisation name
        org_name = request.form.get('org_name')
        campaign_name = request.form.get('campaign_name')
        campaign_description = request.form.get('description')
        #industry name
        industry_name = request.form.get('industry')
        # start date
        start_date = datetime.strptime(request.form.get('start_date'), "%Y-%m-%d").date()
        # end date
        end_date = datetime.strptime(request.form.get('end_date'), "%Y-%m-%d").date()
        # campaign_category
        category = request.form.get('category')
        # budget
        budget = request.form.get('budget')
        #niche
        niche = request.form.get('niche')
        # campaign_type
        campaign_type = request.form.get('private')
        if campaign_type == 'private':
            campaign_type = True
        else:
            campaign_type = False
        # campaign object creation
        username=session['username']
        if end_date <  start_date or end_date<datetime.now().date():
            flash("Start date should be greater than current date and end date should be greater than start date")
            return redirect(url_for('create_campaign'))
        user = User.query.filter_by(username=username).first()
        
        campaign = Campaign(org_name=org_name, campaign_name=campaign_name,status = "active" if datetime.now().date() <= start_date else "inactive",description=campaign_description,industry_name=industry_name, start_date=start_date, end_date=end_date, category = category ,niche=niche, budget=budget,private=campaign_type)
        campaign.user_id=user.id
        db.session.add(campaign)
        db.session.commit()
        flash("Campaign created successfully",category="success")
        return redirect('/campaign_view')       
#view
@app.route('/campaign_view', methods=['GET'])
@login_required
def campaign_view():
    if request.method == 'GET':
        username=session['username']
        user = User.query.filter_by(username=username).first()
        if (user.role=="admin"):
            campaigns = Campaign.query.all()
        else:
            campaigns = Campaign.query.filter_by(user_id=user.id).filter(Campaign.status != "deleted").all()
        final_campaigns = []
        for campaign in campaigns:
            if campaign.status == "active":
                if campaign.start_date > datetime.now().date() or campaign.end_date < datetime.now().date():
                    campaign.status = "inactive"
            elif campaign.status == "inactive":
                if campaign.start_date <= datetime.now().date() and campaign.end_date > datetime.now().date():
                    campaign.status = "active"
            final_campaigns.append(campaign)
            db.session.commit()
        return render_template('campaign/view.html', campaigns=final_campaigns,user = user,datetime=datetime )

@app.route('/campaign_edit/<int:id>', methods=['GET', 'POST'])
@blocked_user_check
@login_required
def edit_campaign(id):
    campaign = Campaign.query.filter_by(id=id).first()
    response = validate_before_processing(campaign,True)
    if campaign.is_flagged:
        flash("Campaign is flagged")
        return redirect(url_for('campaign_view'))
    if response:
        return redirect(response)
    if request.method == 'GET':
        return render_template('campaign/edit.html', campaign=campaign)
    if request.method == 'POST':
        # organisation name
        org_name = request.form.get('org_name')
        campaign_name = request.form.get('campaign_name')
        campaign_description = request.form.get('campaign_description')
        # start date
        start_date = datetime.strptime(request.form.get('start_date'), "%Y-%m-%d").date()
        # end date
        end_date = datetime.strptime(request.form.get('end_date'), "%Y-%m-%d").date()
        # campaign_category
        campaign_category = request.form.get('campaign_category')
        #niche
        niche = request.form.get('niche')
        # budget
        budget = request.form.get('budget')
        privacy = request.form.get('privacy')
        category = request.form.get('category')
        industry = request.form.get('industry')
        if end_date <  start_date or end_date < datetime.now().date():
            flash("Start date should be greater than current date and end date should be greater than start date")
            return redirect(url_for('edit_campaign'))
        campaign.org_name = org_name
        campaign.campaign_name = campaign_name
        campaign.description = campaign_description
        campaign.start_date = start_date
        campaign.end_date = end_date
        campaign.category = campaign_category
        campaign.niche = niche
        campaign.budget = budget
        campaign.private = privacy=='private'
        campaign.industry_name =industry
        campaign.category=category
        db.session.commit()
        flash("Campaign updated successfully",category='success')
        return redirect('/campaign_view')
#delete campaign
@app.route('/campaign_delete/<int:id>', methods=['GET'])
@blocked_user_check
@login_required
def delete_campaign(id):
    campaign = Campaign.query.filter_by(id=id).first()
    response = validate_before_processing(campaign,False)
    if response:
        return redirect(response)
    if campaign.status == "active":
        flash("Can't delete campaign with status 'Active'! Please contact admin for more information!")
        return redirect('/campaign_view')
    campaign.status = 'deleted'
    db.session.commit()
    flash("Campaign deleted successfully")
    return redirect('/campaign_view')
    
#get active campaign name linked to user
def get_active_campaigns():

    campaigns = Campaign.query.filter_by(user_id=session.get('id')).filter_by(status="active").all()
    
    active_campaigns=[]
    for i in campaigns:
        today=datetime.now().date()
        if i.end_date >= today and i.start_date <= today:
            n=today-i.start_date
            t=i.end_date-i.start_date
            percentage=round((n.days/t.days)*100,2)
            active_campaigns.append((i,percentage))
        elif i.start_date>today:
            pass
        else:
            i.status="completed"
            db.session.commit()
    
    return active_campaigns
    
@app.route('/<int:id>/ads_create',methods=['GET','POST'])
@blocked_user_check
@login_required
def ads_create(id):
    campaign = Campaign.query.filter_by(id=id,status="active").first()
    if campaign.is_flagged:
        flash(f'{campaign.campaign_name} campaign is spammed by admin')
        return redirect('/campaign_view')
    response = validate_before_processing(campaign,True)
    if response:
        return redirect(response)
    if request.method == 'GET':
        return render_template('campaign/ads/create.html',campaign_name=campaign.campaign_name)
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        payment = request.form.get('payment')
        terms = request.form.get('terms')
        campaign_id = id
        ads=Ads(title=title, description=description, category=category, payment=payment, terms=terms,campaign_id=campaign_id)

        db.session.add(ads)
        db.session.commit()
        flash("Ads created successfully",category="success")
        return redirect('/'.join(['ads_view']))
#view ads
@app.route('/<int:id>/ads_view',methods=['GET'])
@login_required
def ads_view(id):
    ads=Ads.query.filter_by(campaign_id=id).all()
    if session['role'] == 'admin':
        campaign = Campaign.query.filter_by(id=id).first()
    else:
        campaign = Campaign.query.filter_by(id=id,status="active").first()
    if not campaign:
        flash("Campaign inactive/deleted Please contact admin!")
        return redirect(url_for(session['role']+"_dashboard"))
    prefix = "Remaining days " if (datetime.now().date() >= campaign.start_date) else "Starts in "
    remaining = abs((datetime.now().date() - (campaign.start_date if (datetime.now().date() < campaign.start_date) else campaign.end_date)).days)
    remaining = prefix + str(remaining) + (" days" if remaining>1 else " day")
    if request.method == 'GET':
        final_list = []
        for ad in ads:
            influencer = Influencer.query.filter_by(id=ad.influencer_id).first()
            ad_request = None
            infl_req_username=''
            if influencer:
                username= User.query.filter_by(id=influencer.user_id).first().username
            else:
                username = "No Influencer Assigned"
            neg_status = "No Negotiate"
            neg_amount = 0
            requests = Request.query.filter_by(ads_id=ad.id).filter(Request.status != "rejected").order_by(Request.date).all()
            if len(requests)>0:
                ad_request = requests[-1]
                influencer = Influencer.query.filter_by(id=ad_request.influencer_id).first()
                infl_req_username = User.query.filter_by(id=influencer.user_id).first().username
                statement = select(Negotiate.status,func.count(Negotiate.status).label('count'),Negotiate.date,Negotiate.new_amount).group_by(Negotiate.status,Negotiate.date).having(Negotiate.request_id==ad_request.id).order_by(desc(Negotiate.date))
                result = db.session.execute(statement).first()
                if result:
                    neg_status ="Negotitate "+result.status
                    neg_amount = result.new_amount
                if result:
                    neg_status ="Negotitate "+result.status
            final_list.append((ad,username,{"assigned_infl":infl_req_username,"status":ad_request.status if ad_request else 'no reqeusts',"id":ad_request.id if ad_request else "no id"},{"status":neg_status,"new_amount":neg_amount},{"flagged":campaign.is_flagged or ad.is_flagged}))
        return render_template('campaign/ads/view.html',ads=final_list,campaign_id=id,owner=campaign.user_id,campaign_name = campaign.campaign_name,remaining = remaining)
#edit ads
@app.route('/<int:id>/ads_edit',methods=['GET','POST'])
@login_required
@blocked_user_check
def ads_edit(id):
    ads=Ads.query.filter_by(id=id).first()
    campaign = Campaign.query.filter_by(id=ads.campaign_id,status="active").first()
    response = validate_before_processing(campaign,True)
    if campaign.is_flagged or ads.is_flagged:
        flash("Campaign or ad is spamed by admin")
        return redirect('/'+str(campaign.id)+'/ads_view')
    if response:
        return redirect(response)
    if request.method == 'GET':
        ad_request = Request.query.filter_by(ads_id=ads.id,status="pending").first()
        username = ''
        accepted_requests = Request.query.filter_by(ads_id=ads.id).all()
        accepted_requests = list(filter(lambda x: x.status in ["accepted","completed","verified"],accepted_requests))
        accepted_request = accepted_requests[-1] if len(accepted_requests)>0 else None
        if not ad_request and  not accepted_requests:
            return render_template('campaign/ads/edit.html',ads=ads,influencer_name=username,campaign_name=campaign.campaign_name,
                                   pending=False)
        influencer = Influencer.query.filter_by(id=ad_request.influencer_id if ad_request else accepted_request.influencer_id).first()
        influencer = influencer if influencer else accepted_request[-1]
        if influencer != None:
            user = User.query.filter_by(id=influencer.user_id).first()
            username = user.username
        return render_template('campaign/ads/edit.html',ads=ads,influencer_name=username,
                               campaign_name=campaign.campaign_name,
                               pending=not accepted_request)
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        payment = request.form.get('payment')
        terms = request.form.get('terms')
        username = request.form.get('influencer')
        search_result = User.query.filter_by(is_flag=False,role='influencer').filter(User.username.ilike(f'%{username}%')).all()
        if len(search_result)==1 :
            influencer = Influencer.query.filter_by(user_id=search_result[0].id).first()
        elif username!=None and len(search_result)!=1:
            flash("found 0 or greater than 1 influencers with given "+username)
            return redirect('/'+ str(id)+'/ads_edit')
        ads.title=title
        ads.description=description
        ads.category=category
        ads.payment=payment
        ads.terms=terms
        ad_request = Request(ads_id=ads.id,influencer_id = influencer.id,request_id = session.get('id'),status="pending",date=datetime.now())
        db.session.add(ad_request)
        db.session.commit()
        flash("Ads updated successfully",category="success")
        return redirect('/'+ str(ads.campaign_id)+'/ads_view')

#delete ads
@app.route('/<int:id>/ads_delete',methods=['GET'])
@login_required
@blocked_user_check
def ads_delete(id):
    ads=Ads.query.filter_by(id=id).first()
    campaign = Campaign.query.filter_by(id=ads.campaign_id).first()
    response = validate_before_processing(campaign,True)
    if ads and ads.influencer_id and campaign.status=='active':
        flash("Can't Delete active Ad as influencer is assigned! Please contact admin")
        return redirect('/'+ str(ads.campaign_id)+'/ads_view')
    if response:
        return redirect(response)
    if request.method == 'GET':
        db.session.delete(ads)
        db.session.commit()
        flash("Ads deleted successfully",category="success")
        return redirect('/'+ str(ads.campaign_id)+'/ads_view')


def get_campaign_requests():
    user_id = session.get("id")
    campaigns = Campaign.query.filter_by(user_id=user_id,status="active").all()
    final_requests = []
    for campaign in campaigns:
        ads = Ads.query.filter_by(campaign_id = campaign.id).all()
        for ad in ads:
            requests = Request.query.filter_by(ads_id = ad.id).all()
            for ad_request in requests:
                if ad_request.request_id != user_id and ad_request.status=="pending":
                    influencer = Influencer.query.filter_by(id = ad_request.influencer_id).first()
                    influencer_name = User.query.filter_by(id=influencer.user_id).first().username
                    final_requests.append((ad.title,campaign.campaign_name,influencer_name,influencer.niche,ad_request,None))
    return final_requests

def get_active_negotiations():
    user_id = session.get("id")
    campaigns = Campaign.query.filter_by(user_id=user_id,status="active").all()
    final_requests = []
    for campaign in campaigns:
        ads = Ads.query.filter_by(campaign_id = campaign.id).all()
        for ad in ads:
            ad_request = Request.query.filter_by(ads_id = ad.id,status="pending").first()
            if ad_request:
                influencer = Influencer.query.filter_by(id = ad_request.influencer_id).first()
                influencer_name = User.query.filter_by(id=influencer.user_id).first()
                nego_requests = Negotiate.query.filter_by(request_id = ad_request.id,status='requested').filter(Negotiate.requested_by!= session['id']).all()
                for negotiation_request in nego_requests:
                    final_requests.append((ad,campaign,influencer,ad_request.id,negotiation_request,influencer_name.username))
    return final_requests

@app.route('/accept_request/<request_type>/<int:id>')
@blocked_user_check
@login_required
def ad_accept(request_type,id):
    role = session['role']
    ad_request = Request.query.filter_by(id=id).first()
    ad = Ads.query.filter_by(id=ad_request.ads_id).first()
    if request_type == "ad_request":
        ad_request.status = "accepted"
        ad.influencer_id = ad_request.influencer_id
    elif request_type == "negotiation_request":
        negotiation_request = Negotiate.query.filter_by(request_id=ad_request.id,status="requested").first()
        negotiation_request.status = "accepted"
        ad.payment = negotiation_request.new_amount
        ad_request.status = "pending"
    db.session.commit()
    flash("Request accepted successfully",category="success")
    return redirect(url_for(role+'_dashboard'))

@app.route('/reject_request/<request_type>/<int:id>')
@blocked_user_check
@login_required
def reject_request(request_type,id):
    role = session['role']
    ad_request = Request.query.filter_by(id=id).first()
    ad = Ads.query.filter_by(id=ad_request.ads_id).first()
    if request_type == "ad_request":
        ad_request.status = "rejected"
    elif request_type == "negotiation_request":
        negotiation_request = Negotiate.query.filter_by(request_id=ad_request.id,status="requested").first()
        negotiation_request.status = "rejected"
        ad.payment = negotiation_request.new_amount
        ad_request.status = "pending"
    db.session.commit()
    flash("Request rejected successfully",category="success")
    return redirect(url_for(role+'_dashboard'))



@app.route('/sponsor_profile/<int:req_id>',methods=['GET'])
@login_required
def sponsor_profile(req_id):
    id = session['id']  if req_id==session['id'] else req_id
    user = User.query.filter_by(id=id).first()
    req_type = 'self' if req_id==session['id'] else 'others'
    campaigns = Campaign.query.filter_by(user_id=user.id).all()
    sponsor = Sponsor.query.filter_by(user_id=user.id).first()
    ads = []
    recent_work = []
    for campaign in campaigns:
        ads = Ads.query.filter_by(campaign_id=campaign.id).filter(Ads.influencer_id != None).all()
        influencers = set()
        for ad in ads:
            request = Request.query.filter_by(ads_id = ad.id,status='completed').first()
            influencer = Influencer.query.filter_by(id=ad.influencer_id).first()
            influencer_name = User.query.filter_by(id=influencer.user_id).first()
            if ad and influencer and not influencer in influencers and request:
                review = Review.query.filter_by(user_id=id,campaign_id=campaign.id).first()
                if not review:
                    is_reviewed = False
                else:
                    is_reviewed = True
                recent_work.append((ad,influencer_name.username,is_reviewed,influencer_name.id,campaign.campaign_name))
                influencers.add(influencer)
    ratings = Ratings.query.filter_by(user_id=id).first()
    print(req_type)
    return render_template('sponsor/sponsor_profile.html',sponsor=sponsor,user=user,ads=ads,recent_work=recent_work,ratings=ratings,req_type=req_type)

@app.route('/sponsor_edit_dashboard',methods=['GET', 'POST'])
@blocked_user_check
@login_required
def sponsor_edit_dashboard():
    if request.method == "GET":
        username=session.get('username')
        user = User.query.filter_by(username=username).first()
        campaign = Campaign.query.filter_by(user_id=user.id).first()
        sponsor = Sponsor.query.filter_by(user_id=user.id).first()
        return render_template("sponsor/sponsor_ edit.html",user=user,campaign=campaign,sponsor=sponsor,active_campaigns =  get_active_campaigns(),active_requests=get_campaign_requests(),active_negotiations=get_active_negotiations())
    if request.method == "POST":
        id = session['id']
        name = request.form.get('name')
        pw=request.form.get('password')
        gn=request.form.get('gender')
        cpw=request.form.get('confirmpassword')
        email=request.form.get('email')
        user = User.query.filter_by(id = id).first()
        sponsor = Sponsor.query.filter_by(user_id = user.id).first()

        if 'file' in request.files and validate_filename(request.files['file'].filename) :
            file=request.files['file']
            image_path=app.config.get('UPLOAD_FOLDER')+secure_filename(session['username']+str(session['id'])+"."+file.filename.split('.')[-1])
            file.save(image_path)
            sponsor.image_path=secure_filename(session['username']+str(session['id'])+"."+file.filename.split('.')[-1])
            db.session.commit()
        elif 'file' in request.files :
            error = 'Invalid file or file extension accepts png/jpg/jpeg'
        if not gn or not name:
            flash("Please fill all the mandatory fields")
           
            return redirect(url_for('sponsor_profile'))
        if pw and not pw == cpw:
            flash("Confirm and Password are not same")
            return redirect(url_for('sponsor_edit_dashboard'))
        elif pw:
            user.password = generate_password_hash(pw) 

        user.name = name
        user.gender = gn
        user.email = email
        db.session.commit()
        flash(f'Successfully Updated {name}',category="success")
        return redirect('/'+session['role']+'_profile/'+str(id))
    
def validate_filename(filename):
    filename_list = filename.split('.')
    allowed_ext = ['png','jpg','jpeg']
    return len(filename_list) > 1 and filename_list[-1] in allowed_ext







@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

def validate_before_processing(campaign,inactive_check):
    if not campaign:
        flash("Campaign not found Please contact admin!")
        return url_for(session['role']+"_dashboard")
    if not session['id'] == campaign.user_id:
        flash("you are not authorized to edit this campaign! Please contact admin for more information")
        return url_for(session['role']+"_dashboard")
    if inactive_check and campaign.status in ['in-active','deleted']:
        flash("Can't process a in-active/delete campagin related requests! Please contact admin for more info!")
        return url_for(session['role']+"_dashboard")
    return None
if __name__ == '__main__':
    app.debug=True
    app.run()