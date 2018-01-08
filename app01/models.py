from django.db import models

# Create your models here.
class UserInfo(models.Model):
    '用户表'
    uid=models.BigAutoField(primary_key=True)
    username=models.CharField(max_length=32,unique=True,verbose_name='用户名')
    password=models.CharField(max_length=32,verbose_name='用户密码')
    email=models.EmailField(unique=True,verbose_name='邮箱')
    subtitle=models.CharField(max_length=32,verbose_name='子url',unique=True)
    avatar=models.ImageField(verbose_name='头像',upload_to='avatar/',default='avatar/1.jpg')
    create_time=models.DateTimeField(auto_now_add=True,verbose_name='用户创建时间')
    role=models.ForeignKey(to='Role',to_field='rid',verbose_name='用户角色')
    department=models.ForeignKey(to='Department',to_field='did',verbose_name='用户部门')

class Role(models.Model):
    '用户角色表'
    rid=models.BigAutoField(primary_key=True)
    title=models.CharField(max_length=32,unique=True,verbose_name='用户角色名称')
class Department(models.Model):
    '用户部门表'
    did=models.BigAutoField(primary_key=True)
    title=models.CharField(max_length=32,unique=True,verbose_name='用户部门名称')

class WorkContents(models.Model):
    'daily work内容'
    wid=models.BigAutoField(primary_key=True)
    title=models.CharField(max_length=256)
    main_response=models.ForeignKey(to='UserInfo',to_field='uid',verbose_name='主要负责人')
    create_time=models.DateTimeField(auto_now_add=True,verbose_name='新增时间')
    status=models.BooleanField(default=False,verbose_name='工作是否办结')
    # content=models.ForeignKey(to='DetailWorkContents',to_field='did',verbose_name='工作进度关联外表')
    # sub_response=models.ManyToManyField(verbose_name='次要负责人',to='SubResponse',null=True,blank=True)

class DetailWorkContents(models.Model):
    '详细工作内容'
    did=models.BigAutoField(primary_key=True)
    content = models.TextField(verbose_name='详细的工作内容')
    update_time=models.DateTimeField(auto_now_add=True,verbose_name='更新时间')
    work_id=models.ForeignKey(to='WorkContents',to_field='wid',verbose_name='工作id')
    # update_person=models.ForeignKey(to='UserInfo',to_field='uid',verbose_name='更新此工作的用户')


class SubResponse(models.Model):
    '次要负责人'
    sid=models.BigAutoField(primary_key=True)
    work_id=models.ForeignKey(to='WorkContents',to_field='wid',verbose_name='工作内容id',related_name='works')
    sub_response=models.ForeignKey(to='UserInfo',to_field='uid',verbose_name='次要负责人id',related_name='subperson')

# class WC2U_subresponse(models.Model):
#     wid=models.ForeignKey(to='WorkContents',to_field='wid')
#     uid=models.ForeignKey(to='UserInfo',to_field='uid')
#     class Meta:
#         unique_together=[('wid','uid'),]


class WeekReports(models.Model):
    '周报'     #显示本周创建的内容
    wid = models.BigAutoField(primary_key=True)
    main_response = models.ForeignKey(to='UserInfo', to_field='uid')
    weekly_content=models.TextField(verbose_name='周报内容')
    create_time = models.DateTimeField(auto_now_add=True)




class JobHandover(models.Model):
    '工作交接'
    jid=models.BigAutoField(primary_key=True)
    original_response=models.ForeignKey(to='UserInfo',to_field='uid',verbose_name='原工作负责人',related_name='handover')
    hand_to=models.ForeignKey(to='UserInfo',to_field='uid',verbose_name='现工作负责人')
    job_contents=models.TextField(verbose_name='交接工作内容')

class Identify_user(models.Model):
    '验证用户邮箱和姓名'
    username=models.CharField(max_length=32,verbose_name='用户公司姓名')
    email=models.EmailField(verbose_name='用户公司邮箱')