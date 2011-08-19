# -*- coding: utf-8 -*-
# 
# Nitrate is copyright 2010 Red Hat, Inc.
# 
# Nitrate is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version. This program is distributed in
# the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranties of TITLE, NON-INFRINGEMENT,
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# 
# The GPL text is available in the file COPYING that accompanies this
# distribution and at <http://www.gnu.org/licenses>.
# 
# Authors:
#   Xuqing Kuang <xkuang@redhat.com>

from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.contrib.auth.decorators import user_passes_test
from django.core.urlresolvers import reverse

@user_passes_test(lambda u: u.has_perm('management.add_testattachment'))
def upload_file(request):
    if request.FILES.get('upload_file'):
        import os
        from datetime import datetime
        
        from django.conf import settings
        from tcms.core.utils.prompt import Prompt
        from tcms.management.models import TestAttachment, TestAttachmentData
        
        try:
            upload_file = request.FILES['upload_file']
            
            now = datetime.now()
            
            stored_name = '%s-%s-%s' % (
                request.user.username,
                now,
                upload_file.name
            )
            
            stored_file_name = os.path.join(
                settings.FILE_UPLOAD_DIR, stored_name
            ).replace('\\','/')
            
            if upload_file._size > settings.MAX_UPLOAD_SIZE:
                return HttpResponse(Prompt.render(
                    request = request,
                    info_type = Prompt.Alert,
                    info = 'You upload entity is too large. \
                        Please ensure the file is less than %s bytes. \
                        ' % settings.MAX_UPLOAD_SIZE,
                    next = 'javascript:window.history.go(-1);',
                ))
            
            # Create the upload directory when it's not exist
            try:
                os.listdir(settings.FILE_UPLOAD_DIR)
            except OSError:
                os.mkdir(settings.FILE_UPLOAD_DIR)
            
            # Write to a temporary file
            try:
                open(stored_file_name, 'ro')
                return HttpResponse(Prompt.render(
                    request = request,
                    info_type = Prompt.Alert,
                    info = 'File named \'%s\' already exist in upload folder, \
                        please rename to another name for solve conflict.\
                        ' % upload_file.name,
                    next = 'javascript:window.history.go(-1);',
                ))
            except IOError:
                pass
            
            dest = open(stored_file_name, 'wb+')
            for chunk in upload_file.chunks():
                dest.write(chunk)
            dest.close()
            
            # Write the file to database
            #store_file = open(upload_file_name, 'ro')
            ta = TestAttachment.objects.create(
                submitter_id = request.user.id,
                description = request.REQUEST.get('description', None),
                file_name = upload_file.name,
                stored_name = stored_name,
                create_date = now,
                mime_type = upload_file.content_type
            )
            
            if request.REQUEST.get('to_plan_id'):
                from tcms.testplans.models import TestPlanAttachment
                
                try:
                    int(request.REQUEST['to_plan_id'])
                except ValueError, error:
                    raise
                
                TestPlanAttachment.objects.create(
                    plan_id = request.REQUEST.get('to_plan_id'),
                    attachment_id = ta.attachment_id,
                )
                
                return HttpResponseRedirect(
                    reverse('tcms.testplans.views.attachment',
                    args=[request.REQUEST['to_plan_id']])\
                )
            elif request.REQUEST.get('to_case_id'):
                from tcms.testcases.models import TestCaseAttachment
                
                try:
                    int(request.REQUEST['to_case_id'])
                except ValueError, error:
                    raise
                
                TestCaseAttachment.objects.create(
                    attachment_id = ta.attachment_id,
                    case_id = request.REQUEST['to_case_id']
                )
                
                return HttpResponseRedirect(
                    reverse('tcms.testcases.views.attachment',
                    args=[request.REQUEST['to_case_id']])
                )
        except:
            raise
    else:
        try:
            return HttpResponseRedirect(
                    reverse('tcms.testplans.views.attachment',
                    args=[request.REQUEST['to_plan_id']])\
                )
        except KeyError:
            return HttpResponseRedirect(
                    reverse('tcms.testcases.views.attachment',
                    args=[request.REQUEST['to_case_id']])
                )
    
    raise NotImplementedError

def check_file(request, file_id):
    import os
    from urllib import unquote
    from django.conf import settings
    from django.utils.http import urlquote
    from tcms.management.models import TestAttachment, TestAttachmentData
    try:
        attachment = TestAttachment.objects.get(attachment_id = file_id)
    except TestAttachment.DoesNotExist:
        raise Http404
    
    try:
        attachment = TestAttachment.objects.get(attachment_id = file_id)
        attachment_data = TestAttachmentData.objects.get(
            attachment__attachment_id = file_id
        )
        contents = attachment_data.contents
    except TestAttachmentData.DoesNotExist:
        if attachment.stored_name:
            stored_file_name = os.path.join(
                settings.FILE_UPLOAD_DIR, unquote(attachment.stored_name)
            ).replace('\\','/')
            try:
                f = open(stored_file_name, 'ro')
                contents = f.read()
            except IOError, error:
                raise Http404(error)
        else:
            stored_file_name = os.path.join(
                settings.FILE_UPLOAD_DIR, unquote(attachment.file_name)
            ).replace('\\','/')
            try:
                f = open(stored_file_name, 'ro')
                contents = f.read()
            except IOError, error:
                raise Http404(error)
    
    response = HttpResponse(contents, mimetype=str(attachment.mime_type))
    response['Content-Disposition'] = 'attachment; filename=%s' % attachment.file_name
    return response

def delete_auth(request,file_id):
    from django.contrib.auth.models import User
    from tcms.management.models import TestAttachment

    user=request.user
    if user.is_superuser:
        return True
    attach=TestAttachment.objects.all().get(attachment_id=file_id)
    submit_id=attach.submitter_id
    if user.id==submit_id:
        return True
    if request.REQUEST.get('from_plan'):
        from tcms.testplans.models import TestPlan
        
        try:
            planid=int(request.REQUEST['from_plan'])
            testplan=TestPlan.objects.all().get(plan_id=planid)
            ownerid=testplan.owner_id
            authorid=testplan.author_id
            if user.id==ownerid or user.id==authorid:
                return True
        except KeyError, TestPlan.DoesNotExist:
            raise
             
    
    elif request.REQUEST.get('from_case'):
        from tcms.testcases.models import TestCase
       
        try: 
            caseid=int(request.REQUEST['from_case'])
            ownerid=TestCase.objects.all().get(case_id=caseid).author_id
            if user.id==ownerid:
                return True
        except KeyError:
            raise
    
    return False
        
                

def delete_file(request,file_id):
    import os
    from urllib import unquote
    from django.conf import settings
    from django.utils.http import urlquote
    from django.utils import simplejson 
    
    ajax_response={'rc':0,'response':'ok'} 

    state=delete_auth(request,file_id)
    if not state:
        ajax_response['rc']=2
        ajax_response['response']='auth_failure'
        return HttpResponse(simplejson.dumps(ajax_response))
     
    if request.REQUEST.get('from_plan'):
        from tcms.testplans.models import TestPlanAttachment
        try:
            attachment=TestPlanAttachment.objects.get(attachment=file_id)
            plan_id=int(request.REQUEST['from_plan'])#attachment.plan.plan_id
            attachment.delete()
        except TestPlanAttachment.DoesNotExist:
            raise Http404
            ajax_response['rc']=1
            ajax_response['response']='failure'
        return HttpResponse(simplejson.dumps(ajax_response))
    
    elif request.REQUEST.get('from_case'):
        from tcms.testcases.models import TestCaseAttachment
        try:
            attachment=TestCaseAttachment.objects.get(attachment=file_id)
            case_id=int(request.REQUEST['from_case'])
            attachment.delete()
        except TestCaseAttachment.DoesNotExist:
            raise Http404
            ajax_response['rc']=1
            ajax_response['response']='failure'
        return HttpResponse(simplejson.dumps(ajax_response))
        #return HttpResponseRedirect(
         #       reverse('tcms.testcases.views.attachment',args=[case_id])\
        #)
    #response= HttpResponse(simplejson.dumps(ajax_response))
    #return response
