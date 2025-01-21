
from sqlalchemy import desc, func, select
from app import app
from flask import Flask, render_template, request, redirect, session, url_for, flash
from models import db, User,Infl_platform,Spon_industry,Campaign,Ads,Request,Influencer,Negotiate,Ratings,Review
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
# from flask_wtf import FlaskForm
from werkzeug.utils import secure_filename

from routes import blocked_user_check, login_required


@app.route('/infl_register',methods=['GET','POST'])
def infl_register():    
    if request.method == "GET":
        return render_template("influencer/infl_register.html",user=None)
    if request.method == 'POST':
        username=request.form['username']
        name = request.form['name']
        pw=request.form['password']
        cpw=request.form['confirmpassword']
        email=request.form['email']
        niche=request.form['niche']
        gender=request.form['gender']
        twitter=bool(request.form.get('twitter',False))
        insta = bool(request.form.get('insta',False))
        youtube=bool(request.form.get('youtube',False))
        
        if not username or not pw or not cpw:
            flash("Please fill all the mandatory fields")
           
            return redirect(url_for('infl_register'))

        # confirm and password should be same
        if not pw == cpw:
            flash("Confirm and Password are not same")
            return redirect(url_for('infl_register'))
        if User.query.filter_by(username=username).first():
            flash("Please choose another username, selected username is taken")
            return redirect(url_for('infl_register'))
        platform = Infl_platform.query.filter_by(youtube=youtube).filter_by(twitter=twitter).filter_by(instagram=insta).first()
        if not platform:
            platform = Infl_platform(youtube=youtube, twitter=twitter, instagram=insta)
            db.session.add(platform)
        user = User(username=username, password=generate_password_hash(pw),email=email,name=name,role="influencer",gender=gender)
        db.session.add(user)
        db.session.commit()
        influencer = Influencer(user_id=user.id, platform=platform.id,niche=niche)
        db.session.add(influencer)
        db.session.commit()
        flash(f'thanks for registration {name}',category="success")
        return redirect(url_for('login'))
    

@app.route('/infl_dashboard',methods=['GET'])
@login_required
def influencer_dashboard():
    if request.method == "GET":
        username=session.get('username')
        user = User.query.filter_by(username=username).first()
        influencer = Influencer.query.filter_by(user_id=user.id).first()
        return render_template("influencer/infl_dashboard.html",user=user,influencer=influencer,active_campaigns = get_active_influencer_campaign(user),active_requests=get_active_ad_requests(),active_negotiations=get_active_negotiations())


@app.route('/influencer_profile/<int:req_id>',methods=['GET'])
@login_required
def influencer_profile(req_id):
    if request.method == "GET":
        id = session['id'] if req_id==session['id'] else req_id
        user = User.query.filter_by(id=id).first()
        influencer = Influencer.query.filter_by(user_id=user.id).first()
        req_type = 'self' if req_id==session['id'] else 'others'
        platform= Infl_platform.query.filter_by(id=influencer.platform).first()
        ad_requests = Request.query.filter_by(influencer_id = influencer.id,status='completed').all()
        recent_work = []
        campaigns = set()
        ratings = Ratings.query.filter_by(user_id=user.id).first()
        for ad_request in ad_requests:
            ad = Ads.query.filter_by(id = ad_request.ads_id).first()
            campaign = Campaign.query.filter_by(id=ad.campaign_id).first()
            if campaign in campaigns:
                continue
            review = Review.query.filter_by(user_id=id,campaign_id=campaign.id).first()
            if not review:
                is_reviewed = False
            else:
                is_reviewed = True
            if ad:
                recent_work.append((ad,campaign.user_id,is_reviewed,campaign.campaign_name))
                campaigns.add(campaign)
        return render_template("influencer/infl_profile.html",user=user,influencer=influencer,platform=platform,recent_work=recent_work,req_type=req_type,ratings=ratings)

@app.route('/infl_edit_dashboard',methods=['GET', 'POST'])
@login_required
@blocked_user_check
def influencer_edit_dashboard():
 
    if request.method == "GET":
        username=session.get('username')
        user = User.query.filter_by(username=username).first()
        influencer = Influencer.query.filter_by(user_id=user.id).first()
        platform= Infl_platform.query.filter_by(id=influencer.platform).first()
        return render_template("influencer/infl_edit.html",user=user,influencer=influencer,platform=platform,active_campaigns = get_active_influencer_campaign(user),active_requests=get_active_ad_requests(),active_negotiations=get_active_negotiations())
    if request.method == "POST":
        id = session['id']
        name = request.form.get('name')
        pw=request.form.get('password')
        gn=request.form.get('gender')
        cpw=request.form.get('confirmpassword')
        email=request.form.get('email')
        niche=request.form.get('niche')
        twitter=bool(request.form.get('twitter',False))
        insta = bool(request.form.get('insta',False))
        youtube=bool(request.form.get('youtube',False))
        user = User.query.filter_by(id = id).first()
        infl = Influencer.query.filter_by(user_id = id).first()

        if 'file' in request.files and validate_filename(request.files['file'].filename) :
            file=request.files['file']
            image_path=app.config.get('UPLOAD_FOLDER')+secure_filename(session['username']+str(session['id'])+"."+file.filename.split('.')[-1])
            file.save(image_path)
            infl.image_path=secure_filename(session['username']+str(session['id'])+"."+file.filename.split('.')[-1])
            db.session.commit()
        elif 'file' in request.files :
            error = 'Invalid file or file extension accepts png/jpg/jpeg'
        if not gn or not name:
            flash("Please fill all the mandatory fields")
           
            return redirect(url_for('infl_profile'))
        if pw and not pw == cpw:
            flash("Confirm and Password are not same")
            return redirect(url_for('influencer_edit_dashboard'))
        elif pw:
            user.password = generate_password_hash(pw)            
        platform = Infl_platform.query.filter_by(youtube=youtube).filter_by(twitter=twitter).filter_by(instagram=insta).first()
        if not platform:
            platform = Infl_platform(youtube=youtube, twitter=twitter, instagram=insta)
            db.session.add(platform)
            db.session.commit()
        platform = Infl_platform.query.filter_by(youtube=youtube).filter_by(twitter=twitter).filter_by(instagram=insta).first()
        user.name = name
        user.gender = gn
        user.email = email
        infl.platform = platform.id
        infl.niche = niche
        db.session.commit()
        flash(f'Successfully Updated {name}',category="success")
        return redirect('influencer_profile/'+str(id))

def validate_filename(filename):
    filename_list = filename.split('.')
    allowed_ext = ['png','jpg','jpeg']
    return len(filename_list) > 1 and filename_list[-1] in allowed_ext

def get_active_influencer_campaign(user):
    influencer = Influencer.query.filter_by(user_id=user.id).first()
    ads = Ads.query.filter_by(influencer_id=influencer.id).all()
    today=datetime.now().date()
    campaign_list = []
    active_campaigns = []
    for ad in ads:
        campaign = Campaign.query.filter_by(id=ad.campaign_id,status="active").first()
        if not campaign:
            continue
        if campaign in campaign_list:
            continue
        campaign_list.append(campaign)
        if campaign.end_date >= today and campaign.start_date <= today:
            n=today-campaign.start_date
            t=campaign.end_date-campaign.start_date
            percentage=round((n.days/t.days)*100,2)
            active_campaigns.append((campaign,percentage))

        elif campaign.start_date>today:
            pass
        else:
            campaign.status="completed"
            db.session.commit()
    return active_campaigns
def get_active_ad_requests():
    id = session.get('id')
    influencer = Influencer.query.filter_by(user_id=id).first()
    ad_requests = Request.query.filter(Request.request_id != id).filter_by(influencer_id=influencer.id,status="pending").all()
    final_requests = []
    for ad_request in ad_requests:
        neg_status = "No Negotiations"
        neg_amount = 0
        ad = Ads.query.filter_by(id=ad_request.ads_id).first()
        campaign = Campaign.query.filter_by(id=ad.campaign_id,status="active").first()
        if not campaign:
            continue
        sponsor = User.query.filter_by(id=campaign.user_id).first()
        statement = select(Negotiate.status,func.count(Negotiate.status).label('count'),Negotiate.date,Negotiate.new_amount).group_by(Negotiate.status,Negotiate.date).having(Negotiate.request_id==ad_request.id).order_by(desc(Negotiate.date))
        result = db.session.execute(statement).first()
        if result:
            neg_status ="Negotitate "+result.status
            neg_amount = result.new_amount
        final_requests.append((ad,campaign,sponsor.username,ad_request.id,None,{"status":neg_status,"new_amount":neg_amount}))
    
    return final_requests
def get_active_negotiations():
    id = session.get('id')
    influencer = Influencer.query.filter_by(user_id=id).first()
    ad_requests = Request.query.filter_by(influencer_id=influencer.id,status="pending").all()
    
    final_requests = []
    for ad_request in ad_requests:
        nego_requests = Negotiate.query.filter_by(request_id=ad_request.id,status="requested").filter(Negotiate.requested_by != session['id']).all()
        ad = Ads.query.filter_by(id=ad_request.ads_id).first()
        campaign = Campaign.query.filter_by(id=ad.campaign_id,status="active").first()
        if not campaign:
            continue
        sponsor = User.query.filter_by(id=campaign.user_id).first()
        for negotiation_request in nego_requests:
            final_requests.append((ad,campaign,sponsor,ad_request.id,negotiation_request))
    return final_requests

@app.route("/request/<int:id>",methods=["POST"])
@login_required
@blocked_user_check
def influencer_ad_request(id):
    ad = Ads.query.filter_by(id=id).first()
    user = User.query.filter_by(username=session['username']).first()
    influencer = Influencer.query.filter_by(user_id=user.id).first()
    request = Request(ads_id=id,influencer_id=influencer.id,request_id=user.id,status="pending",date=datetime.now())
    db.session.add(request)
    db.session.commit()
    return redirect('/'+str(ad.campaign_id)+"/ads_view")

@app.route("/negotiate/<req_type>/<int:ad_id>",methods=["POST"])
@login_required
@blocked_user_check
def negotiate(ad_id,req_type):
    id = session['id']
    new_amount = request.form.get("negotiate")
    ad_request = Request.query.filter_by(ads_id=ad_id,status="pending").first()
    ad = Ads.query.filter_by(id=ad_request.ads_id).first()
    ad.status = "negotiating"
    negotiate = Negotiate.query.filter_by(request_id= ad_request.id,status="requested").first()
    if not negotiate:
        negotiate = Negotiate(requested_by=id,status="requested",date=datetime.now(),modified_by=id,request_id=ad_request.id,old_amount=ad.payment,new_amount=new_amount)
        db.session.add(negotiate)
    if negotiate.requested_by == id:
        flash("Negotiation request sent!",category='success')
        negotiate.new_amount = new_amount
    else :
        new_negotiate = Negotiate(requested_by=id,status="requested",date=datetime.now(),modified_by=id,request_id=ad_request.id,old_amount=negotiate.new_amount,new_amount=new_amount)
        negotiate.status = "rejected"
        db.session.add(new_negotiate)
    db.session.commit()
    return redirect(url_for(session['role']+'_dashboard'))


@app.route("/remove_request/<int:id>",methods=["POST"])
@login_required
@blocked_user_check
def remove_influencer_request(id):
    ad_request = Request.query.filter_by(ads_id=id,status="pending").first()
    ad_request.status = "rejected"
    db.session.commit()
    flash("Successfully revoked the request",category="success")
    return redirect('/'+str(ad_request.ads_id)+"/ads_edit")

@app.route("/complete/<int:ad_id>",methods=["POST"])
@login_required
@blocked_user_check
def complete(ad_id):
    id = session['id']
    url = request.form.get("evidance_url")
    if not url:
        flash("Please provide evidance url")
        return redirect('/'+str(ad_id)+"/ads_view")
    influencer = Influencer.query.filter_by(user_id = id).first()
    ad_req = Request.query.filter_by(ads_id=ad_id,status="accepted").first()
    ad = Ads.query.filter_by(id=ad_id).first()
    if ad.influencer_id != influencer.id or not ad_req or not ad:
        flash("You are not the influencer of this ad. Please contact admin for more information")
        return redirect(url_for(session["role"]+"_profile"))
    ad_req.status = "completed"
    ad.is_complete = True
    influencer.earnings += ad.payment
    ad.evidence_url = url
    db.session.commit()
    flash(f"Successfully completed the ad {ad.title}")
    # return redirect(url_for(session['role']+'_profile'))
    return redirect(url_for(session['role']+'_dashboard'))


@app.route('/rating/<int:reviewee_id>', methods=['GET', 'POST'])
@login_required
@blocked_user_check
def rating(reviewee_id):
    id = session.get('id')
    if request.method == 'POST':
        campaign_id = request.args['campaign_id']
        rating_value = request.form['rating']
        description = request.form['description']
        user=User.query.filter_by(id=id).first()
        reviewee = User.query.filter_by(id=reviewee_id).first()
        rating = Ratings.query.filter_by(user_id=reviewee.id).first()
        campaign = Campaign.query.filter_by(id=campaign_id).first()
        if not campaign:
            flash("Campaign not found")
            return redirect('/'+session['role']+'_profile/'+str(id))
        if not rating:
            rating = Ratings(rating=0,user_id=reviewee.id)
            db.session.add(rating)
            db.session.commit()
        review = Review(rating_id = rating.id,user_id = user.id,description = description,date=datetime.now(),rating=rating_value,campaign_id=campaign.id)
        db.session.add(review)
        db.session.commit()
        rating.count += 1
        avg_rating = round((rating.rating + int(rating_value))/rating.count,2)
        rating.rating = avg_rating
        
        db.session.commit()
        flash ('Rating submitted successfully!',category='success')
        return redirect('/'+session['role']+'_profile/'+str(id))
    return render_template("rating.html")
     

