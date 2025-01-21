from functools import wraps
from app import app
from flask import Flask, render_template, request, redirect, session, url_for, flash
from models import db, User,Infl_platform,Spon_industry,Campaign,Ads,Request,Influencer
from sqlalchemy import select
from datetime import datetime
from routes import login_required

def validate_admin(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            flash("You need to login first")
            return redirect(url_for('login'))
        user = User.query.filter_by(username=session['username']).first()
        if user.role != 'admin':
            flash("You are not authorized to access this page")
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return wrapper


@app.route('/admin_dashboard',methods=["GET",'POST'])
@login_required
@validate_admin
def admin_dashboard():
    if request.method == "GET":
        campaigns = Campaign.query.filter(Campaign.status != "delete").all()
        active_campaigns,inactive_campaigns,upcoming_campaigns,spam_campaigns= [],[],[],[]
        for campaign in campaigns:
            if campaign.is_flagged:
                spam_campaigns.append({"data":campaign,"progress":progress(campaign),"type":'spam'})
                continue
            if campaign.start_date > datetime.now().date():
                upcoming_campaigns.append({"data":campaign,"progress":progress(campaign),"type":"view"})
            if campaign.status == "active":
                if campaign.start_date > datetime.now().date() or campaign.end_date < datetime.now().date():
                    campaign.status = "inactive"
                    inactive_campaigns.append({"data":campaign,"progress":progress(campaign),"type":"view"})
                else:
                    active_campaigns.append({"data":campaign,"progress":progress(campaign),"type":"view"})
            elif campaign.status == "inactive":
                if campaign.start_date <= datetime.now().date() and campaign.end_date > datetime.now().date():
                    campaign.status = "active"
                    active_campaigns.append({"data":campaign,"progress":progress(campaign),"type":"view"})
                else:
                    inactive_campaigns.append({"data":campaign,"progress":progress(campaign),"type":"view"})
        spammed_influencers = User.query.filter_by(is_flag=True).all()
        db.session.commit()
        return render_template("/admin_dashboard.html",campaigns = {"active":active_campaigns,"inactive":inactive_campaigns,"upcoming":upcoming_campaigns,"spam":spam_campaigns,'spammed_influencers':spammed_influencers},user_details = {"id":session['id'],"username":session["username"]})
    if request.method == "POST":
        return "success"
    

@app.route('/spam/<obj_type>/<int:int_id>',methods=['POST'])
@login_required
@validate_admin
def spam(obj_type, int_id):
    if obj_type == "campaign":
        campaign = Campaign.query.filter_by(id=int_id).first()
        campaign.is_flagged = True
        db.session.commit()
        return redirect("/campaign_view")
    elif obj_type == "ads":
        ad = Ads.query.filter_by(id=int_id).first()
        campaign = Campaign.query.filter_by(id=ad.campaign_id).first()
        if campaign.is_flagged:
            flash(f"Campaign is spammed can't unspam {campaign.campaign_name}!")
            return redirect("/campaign_view")
        ad.is_flagged = True
        db.session.commit()
        return redirect("/"+str(campaign.id)+"/ads_view")
    elif obj_type == "user":
        user = User.query.filter_by(id=int_id).first()
        user.is_flag = True
        db.session.commit()
        return redirect("/admin_dashboard")

@app.route('/unspam/<obj_type>/<int:int_id>',methods=['POST'])
@login_required
@validate_admin
def unspam(obj_type, int_id):
    if obj_type == "campaign":
        campaign = Campaign.query.filter_by(id=int_id).first()
        campaign.is_flagged = False
        db.session.commit()
        return redirect("/campaign_view")
    elif obj_type == "ads":
        ad = Ads.query.filter_by(id=int_id).first()
        campaign = Campaign.query.filter_by(id=ad.campaign_id).first()
        if campaign.is_flagged:
            flash(f"Campaign is spammed can't unspam {campaign.campaign_name}!")
            return redirect("/campaign_view")
        ad.is_flagged = False
        db.session.commit()
        return redirect("/admin_dashboard")
    elif obj_type == "user":
        user = User.query.filter_by(id=int_id).first()
        user.is_flag = False
        db.session.commit()
        return redirect("/admin_dashboard")



def progress(campaign):
    today=datetime.now().date()
    if campaign.end_date >= today and campaign.start_date <= today:
        n=today-campaign.start_date
        t=campaign.end_date-campaign.start_date
        percentage=round((n.days/t.days)*100,2)
    elif campaign.end_date < today:
        percentage = 100
    else:
        percentage = 0
    return percentage