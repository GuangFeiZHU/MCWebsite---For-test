from django.shortcuts import render,HttpResponse,redirect
from app01.forms import LoginForm,RegisterForm,WorkForms,WeekReportForms
import time
import datetime
from django.db.models import Q
from app01.utlis.pagination_plugin import MyPagination
# Create your views here.
from app01 import models
import copy
def index(request):

    return render(request,'index.html')

def login_decorate(func):
    #登陆验证装饰器
    def wrap(request,subtitle,*args,**kwargs):
        if request.session.get('subtitle')==subtitle:
            res=func(request,subtitle,*args,**kwargs)
        else:
            res=redirect('/login/')
        return res
    return wrap


def login(request):
    if request.method=="GET":
        login_form=LoginForm(request)
        return render(request,'login.html',{'login_form':login_form})
    else:
        login_form=LoginForm(request,request.POST)
        if login_form.is_valid():
            print(request.POST,'用户提交的数据')
            print('------用户提交的数据')
            print(login_form.cleaned_data)
            print('-------获取session 中的验证码')
            print(request.session.get('check_code'))
            username=login_form.cleaned_data.get('username')
            subtitle=models.UserInfo.objects.filter(username=username).values('subtitle').first()['subtitle']
            print(subtitle)
            # return HttpResponse('login is working !')
            # return render(request,'main.html',{'login_form':login_form})  #如果redirect一个URL，该URL包含用户名即可
            #登录成功将用户名写入session中
            request.session['subtitle']=subtitle
            if request.POST.get('remember_status',False):
                print('----------------remember',request.POST.get('remember_status',False))
                request.session.set_expiry(24*60*60*7)  # 设置一周免登陆
            else:
                request.session.set_expiry(2 * 60 * 60)   #两个小时免登陆
            return redirect('/mainpage/%s/'%subtitle)
        return render(request,'login.html',{'login_form':login_form})
import time
def register(request):
    if request.method=="GET":
        register_form=RegisterForm(request)
        return render(request,'register.html',{'register_form':register_form})
    else:
        register_form=RegisterForm(request,request.POST,request.FILES)
        if register_form.is_valid():
            print('------用户提交的数据')
            print(register_form.cleaned_data)
            print('-------获取session 中的验证码')
            print(request.session.get('check_code'))
            #用户注册数据正确，将数据提交到数据库中
            user_info_dict=register_form.cleaned_data
            print('user_info_dict-----------',user_info_dict)
            if models.UserInfo.objects.filter(username=user_info_dict.get('username')).values('username').first() !=None:   #如果用户已经注册过
                return redirect('/please_login/')
            else:
                user_info_dict.pop('password2')
                user_info_dict.pop('check_code')
                if user_info_dict.get('avatar')==None:
                    user_info_dict.pop('avatar')
                subtitle=user_info_dict.get('email').split('@')[0]
                print(subtitle)
                user_info_dict['subtitle']=subtitle
                print(user_info_dict)
                role_obj=models.Role.objects.filter(rid=int(user_info_dict.get('role'))).first()
                department_obj = models.Department.objects.filter(did=int(user_info_dict.get('department'))).first()
                user_info_dict['role']=role_obj
                user_info_dict['department']=department_obj
                models.UserInfo.objects.create(**user_info_dict)
                return redirect('/login/')

        return render(request,'register.html',{'register_form':register_form})


from io import BytesIO
from app01.utlis.verfication_code import verfication_code

def check_code(request):
    img, codes = verfication_code(font_file='static/font/kumo.ttf', font_size=30)
    f = BytesIO()
    img.save(f, 'png')
    img_data = f.getvalue()
    print(codes)
    request.session['check_code']=codes
    return HttpResponse(img_data)


@login_decorate
def  mainpage(request,subtitle):
    # if request.method=="GET":
    print('---mainpage---')
    print(subtitle)
    main_info={}  #初始化一个传到前端的字典   {'user_department_title':user_department_title,'work_contents':[{'work_title':work_title,'status':status}]}
    # models.WorkContents.objects.filter()
    #查询今天的工作内容：获取本人所在的部门id,获取当前时间，将当前时间减去1,2,3,4,5.。。。直到获取到有值的数据所在的日期
    today=time.time()     #今天  今天的时间戳格式  1513059925.1051352
    tomorrow=today-24*60*60   #明天
    today_strftime= time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())    #今天的字符串格式 2017-12-13 14:25:25
    tomorrow_strftime=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(tomorrow))
    today_date=datetime.date.fromtimestamp(today)
    print('**************',today_date)

    #获取用户所在部门id
    user_info=models.UserInfo.objects.filter(subtitle=subtitle).values('department_id','department__title','username','avatar').first()
    user_department_id=user_info.get('department_id')    #用户部门id
    user_department_title=user_info.get('department__title')  #用户部门名称title
    main_info['user_department_title']=user_department_title
    main_info['user_info']=user_info
    print(user_department_id)
    print(user_department_title)
    user_department_obj = models.Department.objects.filter(did=user_department_id).first()      #获取用户所在的部门对象
    print(user_department_obj)
    #获取该部门下的所有同事的对象
    users_obj=models.UserInfo.objects.filter(department=user_department_obj).all()
    print(users_obj)
    #获取当天用户所在部门的所有工作对象
    #work_objs=models.WorkContents.objects.filter(main_response__in=users_obj,create_time__date=today_date,status=False).all()    #获取所有的和该用户是同级的工作对象
    work_objs = models.WorkContents.objects.filter(Q(Q(create_time__date=today_date) | Q(status=False)) & Q(main_response__in=users_obj)).all().order_by('-create_time')  #获取所有的和该用户是同级的工作对象,未完成或日期为今天的
    print('----工作对象')
    print(work_objs)
    work_contents_list=[]   #初始化一个装工作内容相关的
    for work_obj in work_objs:
        work_items={}   #初始化一个装单个工作内容的字典
        print(work_obj)
        work_title=work_obj.title
        work_create_time=work_obj.create_time
        work_main=work_obj.main_response.username
        work_status=work_obj.status
        work_details=work_obj.detailworkcontents_set.all()
        work_detail_list=[]      #初始化一个详细工作内容的列表
        for work_detail in work_details:
            work_detail_dict = {}
            work_detail_dict['work_detail_content']=work_detail.content
            work_detail_dict['work_detail_update_time']=work_detail.update_time
            work_detail_list.append(work_detail_dict)
            print('详细工作内',work_detail.content,work_detail.update_time)
        work_items['work_detail_list']=work_detail_list
        work_subresponses=models.SubResponse.objects.filter(work_id=work_obj).all()    #获取第二负责人,SubResponse对象
        work_items['work_title']=work_title
        work_items['work_create_time']=work_create_time
        work_items['work_main']=work_main
        work_items['work_status']=work_status
        sub_response_list=[]   #初始化次要负责人列表
        if work_subresponses:
            print('有第二负责人')
            #获取第二负责人的名字
            for work_subresponse in work_subresponses:
                sub_name=work_subresponse.sub_response.username
                sub_response_list.append(sub_name)
                print('subname',sub_name)
        if sub_response_list:
            sub_response_str='/'.join(sub_response_list)
        else:
            sub_response_str=''
        work_items['sub_response']=sub_response_str
        work_contents_list.append(work_items)

        # print('-------------',work_title,work_create_time,work_main,work_status,work_subresponses)
        # print('dict-----',work_items)

        #print(work_obj.objects.values('title','create_time'))
    main_info['work_contents']=work_contents_list
    print(main_info,'-----------主信息')
    print(today_strftime)
    print(tomorrow_strftime)
    return render(request,'main.html',{'subtitle':subtitle,'main_info':main_info})

@login_decorate
def  yesterday(request,subtitle):
    # if request.method=="GET":
    print('---mainpage---')
    print(subtitle)
    main_info={}  #初始化一个传到前端的字典   {'user_department_title':user_department_title,'work_contents':[{'work_title':work_title,'status':status}]}
    # models.WorkContents.objects.filter()
    #查询今天的工作内容：获取本人所在的部门id,获取当前时间，将当前时间减去1,2,3,4,5.。。。直到获取到有值的数据所在的日期
    today=time.time()     #今天  今天的时间戳格式  1513059925.1051352
    tomorrow=today-24*60*60   #明天
    today_strftime= time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())    #今天的字符串格式 2017-12-13 14:25:25
    tomorrow_strftime=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(tomorrow))
    today_date=datetime.date.fromtimestamp(today)
    print('**************',today_date)

    #获取用户所在部门id
    user_info=models.UserInfo.objects.filter(subtitle=subtitle).values('department_id','department__title','avatar','username').first()
    user_department_id=user_info.get('department_id')    #用户部门id
    user_department_title=user_info.get('department__title')  #用户部门名称title
    main_info['user_info'] = user_info
    main_info['user_department_title']=user_department_title
    print(user_department_id)
    print(user_department_title)
    user_department_obj = models.Department.objects.filter(did=user_department_id).first()      #获取用户所在的部门对象
    print(user_department_obj)
    #获取该部门下的所有同事的对象
    users_obj=models.UserInfo.objects.filter(department=user_department_obj).all()
    print(users_obj)
    #获取当天用户所在部门的所有工作对象
   #获取上一天的工作内容
    last_day=today-24*60*60
    i=0
    while True:
        i=i+1
        last_day=time.time()-i*24*60*60
        last_date=datetime.date.fromtimestamp(last_day)
        work_objs = models.WorkContents.objects.filter(Q(Q(create_time__date=last_date) | Q(status=False)) & Q(
            main_response__in=users_obj)).all().order_by('-create_time')  # 获取所有的和该用户是同级的工作对象,未完成或日期为上一天的的
        if work_objs:
            break
    print('----工作对象')
    print(work_objs)
    work_contents_list=[]   #初始化一个装工作内容相关的
    for work_obj in work_objs:
        work_items={}   #初始化一个装单个工作内容的字典
        print(work_obj)
        work_title=work_obj.title
        work_create_time=work_obj.create_time
        work_main=work_obj.main_response.username
        work_status=work_obj.status
        work_details=work_obj.detailworkcontents_set.all()
        work_detail_list=[]      #初始化一个详细工作内容的列表
        for work_detail in work_details:
            work_detail_dict = {}
            work_detail_dict['work_detail_content']=work_detail.content
            work_detail_dict['work_detail_update_time']=work_detail.update_time
            work_detail_list.append(work_detail_dict)
            print('详细工作内',work_detail.content,work_detail.update_time)
        work_items['work_detail_list']=work_detail_list
        work_subresponses=models.SubResponse.objects.filter(work_id=work_obj).all()    #获取第二负责人,SubResponse对象
        work_items['work_title']=work_title
        work_items['work_create_time']=work_create_time
        work_items['work_main']=work_main
        work_items['work_status']=work_status
        sub_response_list=[]   #初始化次要负责人列表
        if work_subresponses:
            print('有第二负责人')
            #获取第二负责人的名字
            for work_subresponse in work_subresponses:
                sub_name=work_subresponse.sub_response.username
                sub_response_list.append(sub_name)
                print('subname',sub_name)
        if sub_response_list:
            sub_response_str='/'.join(sub_response_list)
        else:
            sub_response_str=''
        work_items['sub_response']=sub_response_str
        work_contents_list.append(work_items)

        # print('-------------',work_title,work_create_time,work_main,work_status,work_subresponses)
        # print('dict-----',work_items)

        #print(work_obj.objects.values('title','create_time'))
    main_info['work_contents']=work_contents_list
    print(main_info,'-----------主信息')
    print(today_strftime)
    print(tomorrow_strftime)
    return render(request,'yesterday.html',{'subtitle':subtitle,'main_info':main_info})

@login_decorate
def  all_works1(request,subtitle):
    # 没有分页
    print('---mainpage---')
    print(subtitle)
    main_info={}  #初始化一个传到前端的字典   {'user_department_title':user_department_title,'work_contents':[{'work_title':work_title,'status':status}]}
    # models.WorkContents.objects.filter()
    #查询今天的工作内容：获取本人所在的部门id,获取当前时间，将当前时间减去1,2,3,4,5.。。。直到获取到有值的数据所在的日期
    today=time.time()     #今天  今天的时间戳格式  1513059925.1051352
    tomorrow=today-24*60*60   #明天
    today_strftime= time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())    #今天的字符串格式 2017-12-13 14:25:25
    tomorrow_strftime=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(tomorrow))
    today_date=datetime.date.fromtimestamp(today)
    print('**************',today_date)

    #获取用户所在部门id
    user_department=models.UserInfo.objects.filter(subtitle=subtitle).values('department_id','department__title').first()
    user_department_id=user_department.get('department_id')    #用户部门id
    user_department_title=user_department.get('department__title')  #用户部门名称title
    main_info['user_department_title']=user_department_title
    print(user_department_id)
    print(user_department_title)
    user_department_obj = models.Department.objects.filter(did=user_department_id).first()      #获取用户所在的部门对象
    print(user_department_obj)
    #获取该部门下的所有同事的对象
    users_obj=models.UserInfo.objects.filter(department=user_department_obj).all()
    print(users_obj)
    #获取当天用户所在部门的所有工作对象
    #work_objs=models.WorkContents.objects.filter(main_response__in=users_obj,create_time__date=today_date,status=False).all()    #获取所有的和该用户是同级的工作对象
    work_objs = models.WorkContents.objects.filter(main_response__in=users_obj).all().order_by('-create_time')  #获取所有的和该用户是同级的工作对象,未完成或日期为今天的
    print('----工作对象')
    print(work_objs)
    work_contents_list=[]   #初始化一个装工作内容相关的
    for work_obj in work_objs:
        work_items={}   #初始化一个装单个工作内容的字典
        print(work_obj)
        work_title=work_obj.title
        work_create_time=work_obj.create_time
        work_main=work_obj.main_response.username
        work_status=work_obj.status
        work_details=work_obj.detailworkcontents_set.all()
        work_detail_list=[]      #初始化一个详细工作内容的列表
        for work_detail in work_details:
            work_detail_dict = {}
            work_detail_dict['work_detail_content']=work_detail.content
            work_detail_dict['work_detail_update_time']=work_detail.update_time
            work_detail_list.append(work_detail_dict)
            print('详细工作内',work_detail.content,work_detail.update_time)
        work_items['work_detail_list']=work_detail_list
        work_subresponses=models.SubResponse.objects.filter(work_id=work_obj).all()    #获取第二负责人,SubResponse对象
        work_items['work_title']=work_title
        work_items['work_create_time']=work_create_time
        work_items['work_main']=work_main
        work_items['work_status']=work_status
        sub_response_list=[]   #初始化次要负责人列表
        if work_subresponses:
            print('有第二负责人')
            #获取第二负责人的名字
            for work_subresponse in work_subresponses:
                sub_name=work_subresponse.sub_response.username
                sub_response_list.append(sub_name)
                print('subname',sub_name)
        if sub_response_list:
            sub_response_str='/'.join(sub_response_list)
        else:
            sub_response_str=''
        work_items['sub_response']=sub_response_str
        work_contents_list.append(work_items)

        # print('-------------',work_title,work_create_time,work_main,work_status,work_subresponses)
        # print('dict-----',work_items)

        #print(work_obj.objects.values('title','create_time'))
    main_info['work_contents']=work_contents_list
    print(main_info,'-----------主信息')
    print(today_strftime)
    print(tomorrow_strftime)
    return render(request,'all_works.html',{'subtitle':subtitle,'main_info':main_info})

def  all_works(request,subtitle):
    # 采用分页


    print('---mainpage---')
    print(subtitle)
    main_info={}  #初始化一个传到前端的字典   {'user_department_title':user_department_title,'work_contents':[{'work_title':work_title,'status':status}]}
    # models.WorkContents.objects.filter()
    #查询今天的工作内容：获取本人所在的部门id,获取当前时间，将当前时间减去1,2,3,4,5.。。。直到获取到有值的数据所在的日期
    today=time.time()     #今天  今天的时间戳格式  1513059925.1051352
    tomorrow=today-24*60*60   #明天
    today_strftime= time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())    #今天的字符串格式 2017-12-13 14:25:25
    tomorrow_strftime=time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(tomorrow))
    today_date=datetime.date.fromtimestamp(today)
    print('**************',today_date)

    #获取用户所在部门id
    user_info = models.UserInfo.objects.filter(subtitle=subtitle).values('department_id', 'department__title', 'avatar',
                                                                         'username').first()
    user_department_id = user_info.get('department_id')  # 用户部门id
    user_department_title = user_info.get('department__title')  # 用户部门名称title
    main_info['user_info'] = user_info
    main_info['user_department_title']=user_department_title
    print(user_department_id)
    print(user_department_title)
    user_department_obj = models.Department.objects.filter(did=user_department_id).first()      #获取用户所在的部门对象
    print(user_department_obj)
    #获取该部门下的所有同事的对象
    users_obj=models.UserInfo.objects.filter(department=user_department_obj).all()
    print(users_obj)
    #获取当天用户所在部门的所有工作对象
    #work_objs=models.WorkContents.objects.filter(main_response__in=users_obj,create_time__date=today_date,status=False).all()    #获取所有的和该用户是同级的工作对象
    work_objs = models.WorkContents.objects.filter(main_response__in=users_obj).all().order_by('-create_time')  #获取所有的和该用户是同级的工作对象,未完成或日期为今天的
    print('----工作对象')
    print(work_objs)
    work_contents_list=[]   #初始化一个装工作内容相关的
    for work_obj in work_objs:
        work_items={}   #初始化一个装单个工作内容的字典
        print(work_obj)
        work_title=work_obj.title
        work_create_time=work_obj.create_time
        work_main=work_obj.main_response.username
        work_status=work_obj.status
        work_details=work_obj.detailworkcontents_set.all()
        work_detail_list=[]      #初始化一个详细工作内容的列表
        for work_detail in work_details:
            work_detail_dict = {}
            work_detail_dict['work_detail_content']=work_detail.content
            work_detail_dict['work_detail_update_time']=work_detail.update_time
            work_detail_list.append(work_detail_dict)
            print('详细工作内',work_detail.content,work_detail.update_time)
        work_items['work_detail_list']=work_detail_list
        work_subresponses=models.SubResponse.objects.filter(work_id=work_obj).all()    #获取第二负责人,SubResponse对象
        work_items['work_title']=work_title
        work_items['work_create_time']=work_create_time
        work_items['work_main']=work_main
        work_items['work_status']=work_status
        sub_response_list=[]   #初始化次要负责人列表
        if work_subresponses:
            print('有第二负责人')
            #获取第二负责人的名字
            for work_subresponse in work_subresponses:
                sub_name=work_subresponse.sub_response.username
                sub_response_list.append(sub_name)
                print('subname',sub_name)
        if sub_response_list:
            sub_response_str='/'.join(sub_response_list)
        else:
            sub_response_str=''
        work_items['sub_response']=sub_response_str
        work_contents_list.append(work_items)
#分页显示内容
    curren_page = request.GET.get('page')
    pager_index = MyPagination(current_page=curren_page, data_sum=len(work_contents_list), base_url='/all_works/'+subtitle+'/',
                               per_page=10, per_page_num=10)
    tags = pager_index.pager()   #分页的标签
    data_to_send = work_contents_list[pager_index.start_data():pager_index.data_end()]   #传到前端的数据

    main_info['work_contents']=data_to_send
    print(main_info,'-----------主信息')
    print(today_strftime)
    print(tomorrow_strftime)
    return render(request,'all_works.html',{'subtitle':subtitle,'main_info':main_info,'tags': tags})

@login_decorate
def add_works(request,subtitle):
    '添加工作内容'
    print('-----------add_works---')
    print(subtitle)
    # 获取用户所在部门id
    main_info={}
    user_info = models.UserInfo.objects.filter(subtitle=subtitle).values('department_id', 'department__title', 'avatar',
                                                                         'username').first()
    user_department_id = user_info.get('department_id')  # 用户部门id
    user_department_title = user_info.get('department__title')  # 用户部门名称title
    main_info['user_info'] = user_info

    main_info['user_department_title'] = user_department_title
    if request.method=="GET":
        work_form_obj=WorkForms(request,subtitle)
        return render(request, 'add_works.html', {'subtitle': subtitle,'work_form_obj':work_form_obj,'main_info':main_info})
    else:
        work_form_obj=WorkForms(request,subtitle,request.POST)
        # print(work_form_obj)
        print('----1 post')
        # print(work_form_obj.cleaned_data
        if work_form_obj.is_valid():
            print('data is ok ----------')
            print(work_form_obj.cleaned_data)
            input_data=work_form_obj.cleaned_data
            main_response_id=input_data.get('main_response')
            print(main_response_id)
            main_response_user=models.UserInfo.objects.filter(uid=main_response_id).first()   #主要负责人对象
            input_data['main_response']=main_response_user
            print(main_response_user)
            content=input_data.get('content')
            input_data.pop('content')
            sub_response_list=input_data.get('sub_response')
            input_data.pop('sub_response')
            new_id = models.WorkContents.objects.create(**input_data)  # 将数据更新到数据库,并获取刚刚写入数据库的对象
            print('newid')
            print(new_id)
            if sub_response_list:       #建立主要负责人与工作之间的关系
                for sub_id in sub_response_list:
                    sub_response_obj=models.UserInfo.objects.filter(uid=sub_id).first()
                    print('sub id')
                    print(sub_response_obj)
                    sub_dict={'work_id':new_id,'sub_response':sub_response_obj}
                    models.SubResponse.objects.create(**sub_dict)

            detail_content={'content':content,'work_id':new_id}
            models.DetailWorkContents.objects.create(**detail_content)        #将详细的工作进度写入到DetailWorkContents表中
            return redirect('/mainpage/'+subtitle)
        print('-----------2')
        print(work_form_obj)
        return render(request, 'add_works.html', {'subtitle': subtitle,'work_form_obj':work_form_obj,'main_info':main_info})
    # return render(request, 'add_works.html',{'subtitle':subtitle})

@login_decorate
def my_works(request,subtitle):
    '查看和编辑工作内容'
    print('------my_works---')
    print(subtitle)

    print('---mainpage---')
    print(subtitle)
    main_info = {}  # 初始化一个传到前端的字典   {'user_department_title':user_department_title,'work_contents':[{'work_title':work_title,'status':status}]}
    # models.WorkContents.objects.filter()
    # 查询今天的工作内容：获取本人所在的部门id,获取当前时间，将当前时间减去1,2,3,4,5.。。。直到获取到有值的数据所在的日期
    today = time.time()  # 今天  今天的时间戳格式  1513059925.1051352
    tomorrow = today - 24 * 60 * 60  # 明天
    today_strftime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())  # 今天的字符串格式 2017-12-13 14:25:25
    tomorrow_strftime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(tomorrow))
    today_date = datetime.date.fromtimestamp(today)
    print('**************', today_date)

    # 获取用户所在部门id
    user_info = models.UserInfo.objects.filter(subtitle=subtitle).values('department_id', 'department__title', 'avatar',
                                                                         'username').first()
    user_department_id = user_info.get('department_id')  # 用户部门id
    user_department_title = user_info.get('department__title')  # 用户部门名称title
    main_info['user_info'] = user_info

    main_info['user_department_title'] = user_department_title


    print(user_department_id)
    print(user_department_title)
    user_department_obj = models.Department.objects.filter(did=user_department_id).first()  # 获取用户所在的部门对象
    print(user_department_obj)

    #获取和该用户主负责相关的，此负责相关的工作对象
    users_obj = models.UserInfo.objects.filter(subtitle=subtitle).all()
    print(users_obj)
    #获取该用户对象
    my_obj=models.UserInfo.objects.filter(subtitle=subtitle).first()
    print('my_obj 用户对象',my_obj)
    sub_response_objs = models.SubResponse.objects.filter(sub_response=my_obj).values_list('work_id')
    sub_work_id_list = []
    for sub_id in sub_response_objs:
        sub_work_id_list.append(sub_id[0])
    print('次要负责人的工作id', sub_work_id_list)
    print('次要负责人对应的SubResponse对象', sub_response_objs)

    work_objs = models.WorkContents.objects.filter(Q(Q(create_time__date=today_date) | Q(status=False)) & Q(Q(wid__in=sub_work_id_list)|Q(main_response__in=users_obj))).all().order_by('-create_time')  # 获取所有的和该用户是同级的工作对象,未完成或日期为今天的
    print('----工作对象')
    print(work_objs)
    #找次要负责人为此用户的工作对象



    work_contents_list = []  # 初始化一个装工作内容相关的
    for work_obj in work_objs:
        work_items = {}  # 初始化一个装单个工作内容的字典
        print(work_obj)
        work_title = work_obj.title
        work_id=work_obj.wid
        work_create_time = work_obj.create_time
        work_main = work_obj.main_response.username
        work_status = work_obj.status
        work_details = work_obj.detailworkcontents_set.all()
        work_detail_list = []  # 初始化一个详细工作内容的列表
        for work_detail in work_details:
            work_detail_dict = {}
            work_detail_dict['work_detail_content'] = work_detail.content
            work_detail_dict['work_detail_update_time'] = work_detail.update_time
            work_detail_dict['work_detail_id']=work_detail.did    #获取详细工作内容的id
            work_detail_list.append(work_detail_dict)
            print('详细工作内', work_detail.content, work_detail.update_time)
        work_items['work_detail_list'] = work_detail_list
        work_subresponses = models.SubResponse.objects.filter(work_id=work_obj).all()  # 获取第二负责人,SubResponse对象
        work_items['work_title'] = work_title
        work_items['work_create_time'] = work_create_time
        work_items['work_main'] = work_main
        work_items['work_status'] = work_status
        work_items['work_id']=work_id
        sub_response_list = []  # 初始化次要负责人列表
        if work_subresponses:
            print('有第二负责人')
            # 获取第二负责人的名字
            for work_subresponse in work_subresponses:
                sub_name = work_subresponse.sub_response.username
                sub_response_list.append(sub_name)
                print('subname', sub_name)
        if sub_response_list:
            sub_response_str = '/'.join(sub_response_list)
        else:
            sub_response_str = ''
        work_items['sub_response'] = sub_response_str
        work_contents_list.append(work_items)

        # print('-------------',work_title,work_create_time,work_main,work_status,work_subresponses)
        # print('dict-----',work_items)

        # print(work_obj.objects.values('title','create_time'))
    main_info['work_contents'] = work_contents_list
    print(main_info, '-----------主信息')
    print(today_strftime)
    print(tomorrow_strftime)
    return render(request, 'my_works.html', {'subtitle': subtitle, 'main_info': main_info})


@login_decorate
def upgrate_mywork(request,subtitle):
    print('---------------------------进入更新')
    data=request.POST
    print(data)
    print(data.get('work_item'))
    #将获取的数据存入数据库
    #1.获取当前工作id
    work_id=int(data.get('work_id'))
    #2.获取当前新增工作内容
    detail_work_content=data.get('detail_work_content')
    #3.获取当前工作是否办结
    status=eval(data.get('status'))
    #4.获取工作对象
    work_obj = models.WorkContents.objects.filter(wid=work_id).first()
    if detail_work_content:
        models.DetailWorkContents.objects.create(**{'content':detail_work_content,'work_id':work_obj})
        print('详细工作内容--更新',detail_work_content)
        #将工作完成状态更新到WorkContents中
    models.WorkContents.objects.filter(wid=work_id).update(**{'status':status})
    print('-----',work_id,status,type(work_id),type(status))
    return HttpResponse('it ok')


@login_decorate
def change_mywork(request,subtitle):
    data = request.POST
    print('---',data)
    print(data.get('work_item'))
    # 将获取的数据存入数据库
    # 1.获取当前工作id
    work_id = int(data.get('work_id'))
    # 2.获取当前更新的工作内容
    detail_work_content = data.get('detail_work_content')
    # 3.获取当前工作是否办结
    status = eval(data.get('status'))
    # 4.获取工作对象
    work_obj = models.WorkContents.objects.filter(wid=work_id).first()
    #5.获取当前更新的工作内容detail workcontent的id
    detail_work_content_id=int(data.get('detail_work_id'))

    if detail_work_content:          #如果有工作内容，将更新的内容写入数据库
        # models.DetailWorkContents.objects.update(**{'content': detail_work_content, 'work_id': work_obj})
        models.DetailWorkContents.objects.filter(did=detail_work_content_id).update(**{'content': detail_work_content})
     # 将工作完成状态更新到WorkContents中
    models.WorkContents.objects.filter(wid=work_id).update(**{'status': status})
   # print('-----', work_id, detail_work_content, status, type(work_id), type(status))
    return HttpResponse('it ok')


@login_decorate
def delete_mywork(request,subtitle):
    '删除工作项目，只能删除最新更新的一条'
    data = request.POST
    print('---', data)
    # print(data.get('work_item'))
    # # 将获取的数据存入数据库
    # # 1.获取当前工作id
    # work_id = int(data.get('work_id'))
    # # 2.获取当前更新的工作内容
    # detail_work_content = data.get('detail_work_content')
    # # 3.获取当前工作是否办结
    # status = eval(data.get('status'))
    # # 4.获取工作对象
    # work_obj = models.WorkContents.objects.filter(wid=work_id).first()
    # 5.获取当前更新的工作内容detail workcontent的id
    detail_work_content_id = int(data.get('detail_work_id'))
    print(detail_work_content_id,'详细工作id')
    models.DetailWorkContents.objects.filter(did=detail_work_content_id).delete()

    # if detail_work_content:  # 如果有工作内容，将更新的内容写入数据库
    #     # models.DetailWorkContents.objects.update(**{'content': detail_work_content, 'work_id': work_obj})
    #     models.DetailWorkContents.objects.filter(did=detail_work_content_id).update(**{'content': detail_work_content})
    #     # 将工作完成状态更新到WorkContents中
    # models.WorkContents.objects.filter(wid=work_id).update(**{'status': status})
    # print('-----', work_id, detail_work_content, status, type(work_id), type(status))
    return HttpResponse('it ok')

@login_decorate
def add_weekly_report(request,subtitle):

    #my_obj = models.UserInfo.objects.filter(subtitle=subtitle).values('department__title').first()
    main_info = {}
    #main_info['user_department_title'] = my_obj.get('department__title')

    user_info = models.UserInfo.objects.filter(subtitle=subtitle).values('department_id', 'department__title', 'avatar',
                                                                         'username').first()
    #user_department_id = user_info.get('department_id')  # 用户部门id
    user_department_title = user_info.get('department__title')  # 用户部门名称title
    main_info['user_department_title']=user_department_title
    main_info['user_info'] = user_info

    if request.method=="GET":
        weekly_obj=WeekReportForms()
        return render(request,'add_weekly_report.html',{'subtitle':subtitle,'weekly_obj':weekly_obj,'main_info':main_info})
    else:
        data = request.POST
        print(data, '-------kindeditor上传的数据')
        weekly_obj=WeekReportForms(request.POST)
        print('------subtitle',subtitle)
        if weekly_obj.is_valid():
            print('数据有效',weekly_obj.cleaned_data)
            #将数据存入到数据库中
            main_response=models.UserInfo.objects.filter(subtitle=subtitle).first()
            weekly_obj.cleaned_data['main_response']=main_response
            models.WeekReports.objects.create(**weekly_obj.cleaned_data)
            return redirect('/my_weekly_report/' + subtitle)
        return render(request,'add_weekly_report.html',{'subtitle':subtitle,'weekly_obj':weekly_obj,'main_info':main_info})

@login_decorate
def weekly_imgs(request,subtitle):
    import os,json
    print(request.POST,request.FILES)
    file_obj=request.FILES.get('imgFile')
    print(file_obj)
    print(file_obj.name)
    file_path=os.path.join('static/pictures/weekly_report_files/',(time.strftime('%Y-%m-%d %H-%M-%S',time.localtime())+file_obj.name))
    print(file_path,'文件路径')
    with open(file_path,'wb') as f:
        for chunk in file_obj.chunks():
            f.write(chunk)
    dic={
        'error':0,
        'url':'/'+file_path,        #上传的图片的url
        'message':'upload faild！'
    }
    return HttpResponse(json.dumps(dic))

@login_decorate
def my_weekly_report(request,subtitle):
    '编辑我的周报页面'
    my_weekly_report_list=models.WeekReports.objects.filter(main_response__subtitle=subtitle).all().order_by('-create_time')
    my_obj=models.UserInfo.objects.filter(subtitle=subtitle).values('department__title').first()
    main_info={}
    main_info['user_department_title']=my_obj.get('department__title')
    user_info = models.UserInfo.objects.filter(subtitle=subtitle).values('department_id', 'department__title', 'avatar',
                                                                         'username').first()
    main_info['user_info'] = user_info
    print(my_weekly_report_list)
    for item in my_weekly_report_list:
        print(item.main_response.username)

    return render(request,'my_weekly_report.html',{'my_weekly_report_list':my_weekly_report_list,'subtitle':subtitle,'main_info':main_info})

@login_decorate
def edit_weekly_report(request,subtitle,wid):
    '编辑个人周报'
    print('edit----------')
    print(subtitle,wid)
    user_department = models.UserInfo.objects.filter(subtitle=subtitle).values('department_id',
                                                                               'department__title').first()
    user_department_title = user_department.get('department__title')  # 用户部门名称title
    main_info = {}
    main_info['user_department_title'] = user_department_title
    user_info = models.UserInfo.objects.filter(subtitle=subtitle).values('department_id', 'department__title', 'avatar',
                                                                         'username').first()
    main_info['user_info'] = user_info
    if request.method=='GET':
        weekly_obj=models.WeekReports.objects.filter(main_response__subtitle=subtitle,wid=wid).values('wid','weekly_content','create_time').first()
        print(weekly_obj)
        weekly_form_obj = WeekReportForms(weekly_obj)
        return render(request,'edit_weekly_report.html',{'weekly_form_obj':weekly_form_obj,'subtitle':subtitle,'main_info':main_info})
    else:
        weekly_form_obj=WeekReportForms(request.POST)
        print('-----------------',wid)
        if weekly_form_obj.is_valid():
            print('更新的数据',weekly_form_obj.cleaned_data)
            valiad_data=weekly_form_obj.cleaned_data
            print('valiad_data-------',valiad_data)
            models.WeekReports.objects.filter(wid=int(wid)).update(**valiad_data)
            return redirect('/my_weekly_report/'+subtitle)
        return render(request, 'my_weekly_report.html', {'weekly_form_obj': weekly_form_obj, 'subtitle': subtitle})

@login_decorate
def delete_weekly_report(request,subtitle,wid):
    '删除周报'
    print(wid,'被删除的zhoubid')
    models.WeekReports.objects.filter(wid=wid).delete()
    return redirect('/my_weekly_report/'+subtitle)

@login_decorate
def all_weekly_report(request,subtitle):
    '周报汇整，默认显示本周，按周进行筛选查看'
    today_strftime=time.strftime('%u',time.localtime())
    print('------------week time',today_strftime,type(today_strftime))
    # date_start=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()-(int(today_strftime)-1)*24*60*60))
    # date_end=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()+(7-int(today_strftime))*24*60*60))
    # print(date_start,date_end,'-------------时间起始')
    start_date=datetime.date.fromtimestamp(time.time()-(int(today_strftime)-1)*24*60*60)
    end_date=datetime.date.fromtimestamp(time.time()+(7-int(today_strftime))*24*60*60)
    print(start_date,end_date,'------------起止日期')
    #用户部门id
    user_department=models.UserInfo.objects.filter(subtitle=subtitle).values('department__did','department__title').first()
    print(user_department.get('department__did'),'userdepartment')
    # weekly_report_list=models.WeekReports.objects.filter(main_response__department__did='?',create_time_date_in=[start_date,end_date]).all()
    weekly_report_list = models.WeekReports.objects.filter(create_time__gt=start_date,create_time__lt=end_date,main_response__department__did=user_department.get('department__did')).all().order_by('-create_time')
    print(weekly_report_list)
    main_info={}
    main_info['user_department_title']=user_department.get('department__title')
    user_info = models.UserInfo.objects.filter(subtitle=subtitle).values('department_id', 'department__title', 'avatar',
                                                                         'username').first()
    main_info['user_info'] = user_info

    return render(request,'all_weekly_report.html',{'weekly_report_list':weekly_report_list,'subtitle':subtitle,'main_info':main_info})

@login_decorate
def search_works(request,subtitle):
    '查询工作内容'
    user_department = models.UserInfo.objects.filter(subtitle=subtitle).values('department_id',
                                                                               'department__title').first()
    user_department_id = user_department.get('department_id')  # 用户部门id
    user_department_title = user_department.get('department__title')  # 用户部门名称title
    main_info={}
    main_info['user_department_title']=user_department_title
    user_list=models.UserInfo.objects.filter(department__title=user_department_title).all()
    main_info['user_list']=user_list
    user_info = models.UserInfo.objects.filter(subtitle=subtitle).values('department_id', 'department__title', 'avatar',
                                                                         'username').first()
    main_info['user_info'] = user_info
    print(user_list)
    for item in user_list:
        print(item.username)

    if request.method=="GET":
        data_received=request.GET
        print('------接收的数据',data_received)
        #日期转换
        start_time1=request.GET.get('start_time')
        start_time='2017/12/19'
        start_time_strf=time.strptime(start_time,'%Y/%m/%d')
        start_time_timestamp=int(time.mktime(start_time_strf))
        start_date=datetime.date.fromtimestamp(start_time_timestamp)
        print(start_time_strf,start_time_timestamp,start_date,type(start_date))
        print(request.GET.get('start_time'),type(request.GET.get('start_time')))
        #一条公式
        start_date1=datetime.date.fromtimestamp(int(time.mktime(time.strptime(start_time,'%Y/%m/%d'))))
        print(start_date1,'-----------------------------')
        return render(request,'search_works.html',{'subtitle':subtitle,'main_info':main_info})
    else:
        print('---mainpage---')
        print(subtitle)
        # 初始化一个传到前端的字典   {'user_department_title':user_department_title,'work_contents':[{'work_title':work_title,'status':status}]}
        conditions={}
        received_conditions=copy.deepcopy(request.POST)
        received_conditions.pop('csrfmiddlewaretoken')
        print('---------',received_conditions,request.POST)
        if received_conditions['create_time__gte']:
            received_conditions['create_time__gte']=datetime.date.fromtimestamp(int(time.mktime(time.strptime(request.POST.get('create_time__gte'),'%Y/%m/%d'))))
        if received_conditions['create_time__lte']:
            received_conditions['create_time__lte']=datetime.date.fromtimestamp(int(time.mktime(time.strptime(request.POST.get('create_time__lte'),'%Y/%m/%d'))))
        for k,v in received_conditions.items():
            if v:
                conditions[k]=v
        conditions['main_response__department__did']=user_department_id
        work_objs = models.WorkContents.objects.filter(**conditions).all().order_by('-create_time')         #获取工作对象
        # work_objss=models.WorkContents.objects.filter(
        #         main_response__department__did=user_department_id,main_response__username='username',
        #         works__sub_response__username='sub_username',title__contains='key_words',
        #         status='status',create_time__lt='时间最大',create_time__gt='时间最小')
        print('----工作对象')
        print(work_objs)
        work_contents_list = []  # 初始化一个装工作内容相关的
        for work_obj in work_objs:
            work_items = {}  # 初始化一个装单个工作内容的字典
            print(work_obj)
            work_title = work_obj.title
            work_create_time = work_obj.create_time
            work_main = work_obj.main_response.username
            work_status = work_obj.status
            work_details = work_obj.detailworkcontents_set.all()
            work_detail_list = []  # 初始化一个详细工作内容的列表
            for work_detail in work_details:
                work_detail_dict = {}
                work_detail_dict['work_detail_content'] = work_detail.content
                work_detail_dict['work_detail_update_time'] = work_detail.update_time
                work_detail_list.append(work_detail_dict)
                print('详细工作内', work_detail.content, work_detail.update_time)
            work_items['work_detail_list'] = work_detail_list
            work_subresponses = models.SubResponse.objects.filter(work_id=work_obj).all()  # 获取第二负责人,SubResponse对象
            work_items['work_title'] = work_title
            work_items['work_create_time'] = work_create_time
            work_items['work_main'] = work_main
            work_items['work_status'] = work_status
            sub_response_list = []  # 初始化次要负责人列表
            if work_subresponses:
                print('有第二负责人')
                # 获取第二负责人的名字
                for work_subresponse in work_subresponses:
                    sub_name = work_subresponse.sub_response.username
                    sub_response_list.append(sub_name)
                    print('subname', sub_name)
            if sub_response_list:
                sub_response_str = '/'.join(sub_response_list)
            else:
                sub_response_str = ''
            work_items['sub_response'] = sub_response_str
            work_contents_list.append(work_items)

            # print('-------------',work_title,work_create_time,work_main,work_status,work_subresponses)
            # print('dict-----',work_items)

            # print(work_obj.objects.values('title','create_time'))
        main_info['work_contents'] = work_contents_list
        print(main_info, '-----------主信息')
        return render(request, 'search_works.html', {'subtitle': subtitle, 'main_info': main_info})

@login_decorate
def search_weekly_report(request,subtitle):
    '查询周报'
    user_department = models.UserInfo.objects.filter(subtitle=subtitle).values('department_id',
                                                                               'department__title').first()
    user_department_id = user_department.get('department_id')  # 用户部门id
    user_department_title = user_department.get('department__title')  # 用户部门名称title
    main_info = {}
    main_info['user_department_title'] = user_department_title
    user_list = models.UserInfo.objects.filter(department__title=user_department_title).all()
    main_info['user_list'] = user_list
    user_info = models.UserInfo.objects.filter(subtitle=subtitle).values('department_id', 'department__title', 'avatar',
                                                                         'username').first()
    main_info['user_info'] = user_info
    if request.method=="GET":
        return render(request,'search_weekly_report.html',{'subtitle':subtitle,'main_info':main_info})
    else:
        conditions = {}
        received_conditions = copy.deepcopy(request.POST)
        received_conditions.pop('csrfmiddlewaretoken')
        print('---------', received_conditions, request.POST)
        if received_conditions['create_time__gte']:
            received_conditions['create_time__gte'] = datetime.date.fromtimestamp(
                int(time.mktime(time.strptime(request.POST.get('create_time__gte'), '%Y/%m/%d'))))
        if received_conditions['create_time__lte']:
            received_conditions['create_time__lte'] = datetime.date.fromtimestamp(
                int(time.mktime(time.strptime(request.POST.get('create_time__lte'), '%Y/%m/%d'))))
        for k, v in received_conditions.items():
            if v:
                conditions[k] = v
        conditions['main_response__department__did'] = user_department_id
        print('conditions,周报查询条件',conditions)
        weekly_report_list = models.WeekReports.objects.filter(**conditions).all().order_by(
            '-create_time')
        # weekly_report_list = models.WeekReports.objects.filter(create_time__gt=start_date, create_time__lt=end_date,
        #                                                        main_response__department__did=user_department.get(
        #                                                            'department__did'),main_response__username='username',weekly_content__contains=).all().order_by('-create_time')

        return render(request, 'search_weekly_report.html',
                      {'weekly_report_list': weekly_report_list, 'subtitle': subtitle, 'main_info': main_info})

def register_aggrement(request):
    return render(request,'register_aggrement.html')

def please_login(request):
    return render(request,'please_login.html')