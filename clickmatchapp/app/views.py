
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
import threading
from googleapiclient import discovery
from googleapiclient.errors import HttpError
from oauth2client.client import AccessTokenCredentials

from .models import Index, DataCache


class UpdaterThread(threading.Thread):
    def __init__(self,sheet_id,user,index,value, **kwargs):
        self.sheet_id = sheet_id
        self.user = user
        self.value = value
        self.index = index
        super(UpdaterThread, self).__init__(**kwargs)
        # self.setDaemon(True)

    def run(self):
        sheet = GetSheetData(self.sheet_id, self.user)
        values = sheet.get_data()
        print 'Index %s'%self.index
        col_index = values[0].index(self.user.email)
        print 'Col Index %s'%col_index
        row = values[int(self.index)]
        if len(row) < col_index+1:
            values[int(self.index)].append(self.value)
        else:
            values[int(self.index)][col_index] = self.value
        sheet.set_data(values)


class GetSheetData():

    def __init__(self,sheet_id,user):
        self.sheet_id = sheet_id
        self.user = user
        self.get_service()

    def get_time(self):
        import time
        millis = int(round(time.time() * 1000))
        return millis

    def get_service(self):
        start = self.get_time()
        social = self.user.social_auth.get(provider='google-oauth2')
        acess_token = social.extra_data['access_token']
        credentials = AccessTokenCredentials(acess_token,user_agent='')
        http = credentials.authorize(httplib2.Http())
        discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?version=v4')
        self.service = discovery.build('sheets', 'v4', http=http,discoveryServiceUrl=discoveryUrl)
        print 'Time took to connect %s ms'%(self.get_time() - start)
        return self.service



    def set_data(self,values):
        body = {
            'values': values
        }
        start = self.get_time()
        result = self.service.spreadsheets().values().update(spreadsheetId=self.sheet_id,
                                                                   range=settings.SHEET_NAME,
                                                                   valueInputOption="RAW",
                                                                   body=body).execute()
        print 'Time took to set values %s ms' % (self.get_time() - start)
        print result

    def get_data(self):
        start = self.get_time()
        result = self.service.spreadsheets().values().get(spreadsheetId=self.sheet_id, range=settings.SHEET_NAME).execute()
        values = result.get('values', [])
        print 'Time took to get values %s ms' % (self.get_time() - start)
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
        try:
            values = [ca.row.split(',') for ca in DataCache.objects.filter(user=request.user).order_by('index').all()]
        except DataCache.DoesNotExist:
            values = []

        current = index.index if not created else 1
        try:
            if len(values) == 0:
                values = GetSheetData(settings.DATA_SHEET_ID, request.user).get_data()
                counter = 1
                for row in values:
                    ca = DataCache()
                    ca.user = request.user
                    ca.index = counter
                    ca.row = ','.join(row)
                    ca.save()
                    counter += 1
            if index.index >= len(values):
                context = {'error': 'No more data to be classified'}
                return render(request, self.template_name, context)
            if created or len(values) - 1 > index.total:
                index.total = len(values) - 1
                index.save()
            email = request.user.email
            users_exists = email in values[0]
            # print 'values[0] %s'%values[0]
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
        cache = DataCache.objects.filter(user=request.user).filter(index=index).first()
        cache.match = 1
        cache.save()
        index_obj = Index.objects.filter(user=request.user).first()
        index_obj.index += 1
        index_obj.save()

        UpdaterThread(settings.DATA_SHEET_ID, request.user, index, 1).start()

        return HttpResponseRedirect(reverse('home'))

class NoMatchRecordView(View):
    @method_decorator(login_required(login_url="/"))
    def post(self,request,index):
        # UpdaterThread(settings.DATA_SHEET_ID, request.user, index, 0).run()
        cache = DataCache.objects.filter(user=request.user).filter(index=index).first()
        cache.match = 0
        cache.save()


        index_obj = Index.objects.filter(user=request.user).first()
        index_obj.index += 1
        index_obj.save()
        UpdaterThread(settings.DATA_SHEET_ID, request.user, index, 0).start()
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