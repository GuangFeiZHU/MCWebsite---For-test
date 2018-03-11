from django.forms import fields, Form, widgets
from django.core.exceptions import ValidationError
from app01 import models


class LoginForm(Form):
    '用户登录'
    username = fields.CharField(max_length=32, min_length=2, required=True,
                                widget=widgets.TextInput(attrs={'class': "form-control", 'placeholder': "用户名"}))
    password1 = fields.CharField(max_length=32, min_length=2, required=True,
                                 widget=widgets.PasswordInput(attrs={'class': "form-control", 'placeholder': "密码"}))

    # check_code=fields.CharField(widget=widgets.TextInput(attrs={'class':"form-control",'placeholder':"验证码"}))
    # remember=fields.ChoiceField(widget=widgets.CheckboxInput)

    def __init__(self, request, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.request = request
        print('-------request')
        print(self.request)
        print('-------args')
        print(args)

    # def clean_check_code(self):
    #     input_code=self.cleaned_data.get('check_code').upper()
    #     session_code = self.request.session.get('check_code')
    #     print('-----form ---')
    #     print(input_code,session_code)
    #     if input_code==session_code:
    #         return input_code
    #     raise ValidationError('验证码错误')
    def clean(self):
        print('-----验证？？？？？？')
        username = self.cleaned_data.get('username')
        input_password = self.cleaned_data.get('password1')
        print('验证账密')
        print(username, input_password)
        password = None
        userinfo = models.UserInfo.objects.filter(username=username).values().first()
        print(userinfo)
        if userinfo:
            password = models.UserInfo.objects.filter(username=username).values('password').first()['password']
            print(password)
        if password:
            if password == input_password:
                return self.cleaned_data
        raise ValidationError('用户名或密码错误')


class RegisterForm(Form):
    '用户注册'
    username = fields.CharField(max_length=32, min_length=2, required=True,
                                widget=widgets.TextInput(attrs={'class': "form-control", 'placeholder': "用户名"}))
    # nickname = fields.CharField(max_length=32, min_length=2, required=True,
    #                             widget=widgets.TextInput(attrs={'class': "form-control", 'placeholder': "昵称"}))
    email = fields.EmailField(max_length=32, min_length=2, required=True,
                              widget=widgets.TextInput(attrs={'class': "form-control", 'placeholder': "邮箱"}))
    password = fields.CharField(max_length=32, min_length=2, required=True,
                                widget=widgets.PasswordInput(attrs={'class': "form-control", 'placeholder': "密码"}))
    password2 = fields.CharField(max_length=32, min_length=2, required=True,
                                 widget=widgets.PasswordInput(
                                     attrs={'class': "form-control", 'placeholder': "请再次输入密码"}))
    check_code = fields.CharField(widget=widgets.TextInput(attrs={'class': "form-control", 'placeholder': "验证码"}))
    avatar = fields.ImageField(
        widget=widgets.FileInput(attrs={'class': 'user_avatar', 'style': "position: absolute;right: -460px;opacity:0"}),
        required=False)
    role = fields.ChoiceField(widget=widgets.Select(attrs={'class': "form-control"}), initial=1)
    department = fields.ChoiceField(widget=widgets.Select(attrs={'class': "form-control"}))

    # remember=fields.ChoiceField(widget=widgets.CheckboxInput)

    def __init__(self, request, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)
        self.request = request
        self.fields['role'].choices = models.Role.objects.all().values_list('rid', 'title')
        self.fields['department'].choices = models.Department.objects.all().values_list('did', 'title')

    def clean_username(self):
        username = self.cleaned_data.get('username')
        print(username, 'username----------')
        print(self.cleaned_data, '--------------clean_username')

        username_database = models.Identify_user.objects.filter(username=username).values('username').first()
        print(username_database, '从公司数据库获取的信息')
        if username_database:
            return username
        raise ValidationError('用户不在本公司')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        print(email, 'email----------')
        print(self.cleaned_data, '--------------clean_email')

        email_database = models.Identify_user.objects.filter(email=email).values(
            'email').first()
        print(email_database, '从公司数据库获取的信息')
        if email_database:
            return email
        raise ValidationError('用户邮箱不在本公司')

    def clean_check_code(self):
        input_code = self.cleaned_data.get('check_code')
        session_code = self.request.session.get('check_code')
        print('-----form ---')
        print(self.cleaned_data)
        print(input_code, session_code)
        if input_code.upper() == session_code:
            return input_code
        raise ValidationError('验证码错误')

    def clean(self):
        password1 = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')
        # if password1==password2:
        #     print('密码一致')
        #     return self.cleaned_data
        # else:
        #     self.add_error('password2',ValidationError('密码不一致'))
        print('进入密码确认')
        username_form = self.cleaned_data.get('username')
        email_form = self.cleaned_data.get('email')
        username_database_from_email = models.Identify_user.objects.filter(email=email_form).values(
            'username').first()  # 依据用户输入的Email查找数据库中的username再与用户输入的username比对
        print('username_form', username_form, 'username_database_from_email', username_database_from_email)
        if username_database_from_email != None:
            if username_form == username_database_from_email.get('username'):
                print('用户名和Email比对正确')
                if password2 == password1:
                    return self.cleaned_data
                else:
                    self.add_error('username', ValidationError('密码不一致'))
            else:
                self.add_error('username', ValidationError('用户名和邮箱不符'))
        else:
            self.add_error('username', ValidationError('用户名或邮箱不在公司数据库'))


class WorkForms(Form):
    '工作表'
    title = fields.CharField(max_length=32, min_length=2, required=True,
                             widget=widgets.TextInput(attrs={'class': "form-control", 'placeholder': "工作项目"}))
    content = fields.CharField(max_length=255, min_length=2, required=True,
                               widget=widgets.Textarea(attrs={'class': "form-control", 'placeholder': "工作进度"}))
    main_response = fields.ChoiceField(widget=widgets.Select(attrs={'class': "form-control"}))
    sub_response = fields.MultipleChoiceField(widget=widgets.SelectMultiple(attrs={'class': "form-control"}),
                                              required=False)
    # create_time=fields.DateTimeField()
    status = fields.ChoiceField(widget=widgets.Select(attrs={'class': "form-control"}),
                                choices=((True, '是'), (False, '否'),))

    def __init__(self, request, subtitle, *args, **kwargs):
        super(WorkForms, self).__init__(*args, **kwargs)
        self.request = request
        self.subtitle = subtitle
        print('----subtitle')
        print(self.subtitle)
        print('------request')
        print(self.request)
        print('-------args')
        print(args)
        print('------kwargs')
        print(kwargs)
        role_department_id = models.UserInfo.objects.filter(subtitle=self.subtitle).values('role_id', 'department_id',
                                                                                           'uid').first()
        print('---------role_department_id')
        print(role_department_id)
        userinfo = models.UserInfo.objects.filter(role_id=role_department_id.get('role_id'),
                                                  department_id=role_department_id.get('department_id')).values('uid',
                                                                                                                'username')
        print(userinfo)
        self.fields['main_response'].choices = models.UserInfo.objects.filter \
            (role_id=role_department_id.get('role_id'),
             department_id=role_department_id.get('department_id')).values_list('uid', 'username')
        self.fields['sub_response'].choices = models.UserInfo.objects.filter \
            (role_id=role_department_id.get('role_id'),
             department_id=role_department_id.get('department_id')).values_list('uid', 'username')
        self.fields['main_response'].initial = role_department_id.get('uid')


class WeekReportForms(Form):
    '周报表单'
    import time
    create_time = fields.DateTimeField(required=True, initial=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    weekly_content = fields.CharField(min_length=2, required=True, widget=widgets.Textarea(attrs={'id': 'i1'}))
