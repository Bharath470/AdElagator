from admin import progress
from app import app
from flask import Flask, render_template, request, redirect, session, url_for, flash
from models import db, User,Infl_platform,Spon_industry,Campaign,Ads,Request,Influencer
from sqlalchemy import select

filter_dict = {Campaign: ["niche","campaign_name","organization"],User:["username"],Influencer:["user_niche"]}
column_dict = {"niche":Campaign.niche,"campaign_name":Campaign.campaign_name,"organization":Campaign.org_name,"username":User.username,"user_niche":Influencer.niche}

@app.route('/search',methods=['GET','POST'])
def search():
    keyword = request.form.get('keyword')
    words = request.form.get('search')
    if keyword == 'search':
        return render_template("/search.html",result={"type":None,'total':0,"search_term":"No Search terms provided","keyword":"No Keywords provided","data":None})
    table = None
    for (k,v) in filter_dict.items():
        if keyword in v:
            table = k
            column = column_dict[keyword]
            break
        print(table)
    statement = table.query.filter(column.ilike(f'%{words}%'))
    final_results = {"campaign":[],"user":[],'influencer':[]}
    if table==Campaign:
        results = statement.filter_by(private=False,status="active").all()
        for i in results:
            final_results["campaign"].append({'data':i,'progress':progress(i),"metadata":{'spam': i.is_flagged}})
        total = len(final_results["campaign"])
    elif table==Influencer:
        results = statement.all()
        for i in results:
            user=User.query.filter_by(id=Influencer.user_id).first()
            final_results["influencer"].append({'data':i,'metadata':{'influencer':i.niche,'user':user}})
        total = len(final_results["influencer"])
    else:
        results = statement.filter(table.role != "admin").all()
        for i in results:
            influencer = Influencer.query.filter_by(user_id=i.id).first()
            final_results["user"].append({'data':i,'metadata':{'influencer':influencer,'spam':i.is_flag}})
        total = len(final_results["user"])
    return render_template("/search.html",result={"type":("campaign" if len(final_results['campaign'])>0 else 'user' if len(final_results['user'])>0 else 'influencer'),'total':total,"search_term":words,"keyword":keyword,"data":final_results})