
import httplib2
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth import logout as auth_logout
# Create your views here.
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View

from googleapiclient import discovery
from googleapiclient.errors import HttpError
from oauth2client.client import AccessTokenCredentials

from .models import Index


class GetSheetData():

    def __init__(self,sheet_id,user):
        self.sheet_id = sheet_id
        self.user = user

    def get_service(self):
        social = self.user.social_auth.get(provider='google-oauth2')
        acess_token = social.extra_data['access_token']
        credentials = AccessTokenCredentials(acess_token,user_agent='')
        http = credentials.authorize(httplib2.Http())
        discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?version=v4')
        service = discovery.build('sheets', 'v4', http=http,discoveryServiceUrl=discoveryUrl)
        return service

    def set_data(self,values):
        body = {
            'values': values
        }
        result = self.get_service().spreadsheets().values().update(spreadsheetId=self.sheet_id,
                                                                   range=settings.SHEET_NAME,
                                                                   valueInputOption="RAW",
                                                                   body=body).execute()
        print result

    def get_data(self):
        result = self.get_service().spreadsheets().values().get(spreadsheetId=self.sheet_id, range=settings.SHEET_NAME).execute()
        values = result.get('values', [])
        return values



class IndexView(View):
    template_name = 'index.html'

    def get(self, request):
        if request.user.is_authenticated():
            return HttpResponseRedirect(reverse('home'))
        else:
            return render(request, self.template_name)


class HomeView(View):
    template_name = 'home.html'
    @method_decorator(login_required(login_url="/"))
    def get(self,request):
        index,created = Index.objects.get_or_create(user=request.user)

        current = index.index if not created else 1
        try:
            values = GetSheetData(settings.DATA_SHEET_ID,request.user).get_data()
            if index.index >= len(values):
                context = {'error': 'No more data to be classified'}
                return render(request, self.template_name, context)
            if created or len(values) - 1 > index.total:
                index.total = len(values) - 1
                index.save()
            email = request.user.email
            users_exists = email in values[0]
            if users_exists:
                context = {'current_row':values[current],'index':index}
            else:
                context = {'error':'No column with your username'}
            return render(request, self.template_name,context)
        except HttpError,e:
            context = {'error': e._get_reason()}
            return render(request, self.template_name, context)

class MatchRecordView(View):
    @method_decorator(login_required(login_url="/"))
    def post(self,request,index):
        sheet = GetSheetData(settings.DATA_SHEET_ID,request.user)
        values = sheet.get_data()
        print 'Index %s'%index
        col_index = values[0].index(request.user.email)
        print 'Col Index %s'%col_index
        row = values[int(index)]
        if len(row) < col_index+1:
            values[int(index)].append(1)
        else:
            values[int(index)][col_index] = 1
        sheet.set_data(values)
        index_obj = Index.objects.filter(user=request.user).first()
        index_obj.index += 1
        index_obj.save()

        return HttpResponseRedirect(reverse('home'))

class NoMatchRecordView(View):
    @method_decorator(login_required(login_url="/"))
    def post(self,request,index):
        print 'Index %s' % index
        sheet = GetSheetData(settings.DATA_SHEET_ID,request.user)
        values = sheet.get_data()
        col_index = values[0].index(request.user.email)
        print 'Col Index %s' % values[int(index)]
        print 'Col Index %s'%col_index
        row = values[int(index)]
        if len(row) < col_index+1:
            values[int(index)].append(0)
        else:
            values[int(index)][col_index] = 0

        sheet.set_data(values)


        index_obj = Index.objects.filter(user=request.user).first()
        index_obj.index += 1
        index_obj.save()
        return HttpResponseRedirect(reverse('home'))

class LoginFailedView(View):
    template_name = 'login_error.html'
    def get(self,request):
        context = {}
        allowed_domain = settings.SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS[0]
        context['error_message'] = 'Only %s is allowed to login'%allowed_domain
        return render(request, self.template_name,context)

class LogoutView(View):
    def get(self,request):
        if request.user.is_authenticated():
            auth_logout(request)
        return HttpResponseRedirect(reverse('index'))