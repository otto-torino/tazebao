import logging
import re
import json
from urllib.parse import urlsplit

from django.shortcuts import render, get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.http.response import JsonResponse
from django.contrib.auth.decorators import user_passes_test
from django.contrib.sites.models import Site
from django.utils.safestring import mark_safe
from django.views.decorators.clickjacking import xframe_options_exempt
from django.template.defaultfilters import slugify, striptags
from premailer import transform
from PIL import Image, ImageDraw


from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from core.authentication import JSONWebTokenQuerystringAuthentication

from .models import Upload, Template
from .utils import html2text, extract_urllinks
from newsletter.models import Campaign, Topic

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@user_passes_test(lambda u: u.is_staff)
def index(request):
    dict = {
        'opts': Template._meta,
        'change': True,
        'is_popup': False,
        'save_as': False,
        'has_delete_permission': False,
        'has_add_permission': False,
        'has_change_permission': False,
        'site_header': mark_safe(settings.BATON.get('SITE_HEADER'))
    }
    return render(request, 'mosaico/index.html', dict)

@xframe_options_exempt
@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
@authentication_classes((JSONWebTokenQuerystringAuthentication,))
def appindex(request):
    dict = {
        'opts': Template._meta,
        'change': True,
        'is_popup': False,
        'save_as': False,
        'has_delete_permission': False,
        'has_add_permission': False,
        'has_change_permission': False,
        'site_header': mark_safe(settings.BATON.get('SITE_HEADER'))
    }
    return render(request, 'mosaico/appindex.html', dict)


@user_passes_test(lambda u: u.is_staff)
def editor(request):
    return render(request, 'mosaico/editor.html')


@xframe_options_exempt
@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
@authentication_classes((JSONWebTokenQuerystringAuthentication,))
def appeditor(request):
    id = request.GET.get('id', None)
    template = None
    if id:
        template = Template.objects.get(id=id)
    return render(request, 'mosaico/appeditor.html', {'template': template})

# mosaico views from https://github.com/voidlabs/mosaico/tree/master/backend

@csrf_exempt
def download(request):
    html = transform(request.POST['html'])
    action = request.POST['action']
    if action == 'download':
        filename = request.POST['filename']
        content_type = "text/html"
        content_disposition = "attachment; filename=%s" % filename
        response = HttpResponse(html, content_type=content_type)
        response['Content-Disposition'] = content_disposition
    elif action == 'email':
        to = request.POST['rcpt']
        subject = request.POST['subject']
        from_email = settings.DEFAULT_FROM_EMAIL
        # TODO: convert the HTML email to a plain-text message here.  That way
        # we can have both HTML and plain text.
        msg = ""
        send_mail(subject, msg, from_email, [to], html_message=html, fail_silently=False)
        # TODO: return the mail ID here
        response = HttpResponse("OK: 250 OK id=12345")
    return response


@xframe_options_exempt
@api_view(['POST'])
@permission_classes((IsAuthenticated, ))
@authentication_classes((JSONWebTokenQuerystringAuthentication,))
def appupload(request):
    if request.method == 'POST':
        file = list(request.FILES.values())[0]
        upload = Upload(
            name=file.name,
            image=file,
            client=request.user.client
        )
        upload.save()
        uploads = [upload]
    else:
        uploads = Upload.objects.filter(client__user=request.user).order_by('-id') # noqa
    data = {'files': []}
    for upload in uploads:
        data['files'].append(upload.to_json_data())
    response = HttpResponse(json.dumps(data), content_type="application/json")
    return response


@csrf_exempt
def upload(request):
    if request.method == 'POST':
        file = list(request.FILES.values())[0]
        upload = Upload(
            name=file.name,
            image=file,
            client=request.user.client
        )
        upload.save()
        uploads = [upload]
    else:
        uploads = Upload.objects.filter(client__user=request.user).order_by('-id') # noqa
    data = {'files': []}
    for upload in uploads:
        data['files'].append(upload.to_json_data())
    response = HttpResponse(json.dumps(data), content_type="application/json")
    return response


@csrf_exempt
def image(request):
    logger.debug("request.method: %r", request.method)
    domain = Site.objects.get_current().domain
    base_url = ''.join([
        'https://' if settings.HTTPS else 'http://',
        domain
    ])
    if request.method == 'GET':
        method = request.GET['method']
        logger.debug("method: %r", method)
        params = request.GET['params'].split(',')
        logger.debug("params: %r", params)
        if method == 'placeholder':
            height, width = [size(p) for p in params]
            image = get_placeholder_image(height, width)
            response = HttpResponse(content_type="image/png")
            image.save(response, "PNG")
        elif method == 'cover':
            src = request.GET['src']
            width, height = [size(p) for p in params]
            for upload in Upload.objects.all():
                if base_url + upload.image.url == src:
                    break
            image = Image.open(upload.image.file)
            if width is not None and height is not None:
                image.thumbnail((width, height), Image.ANTIALIAS)
            response = HttpResponse(content_type="image/%s" % image.format.lower())
            image.save(response, image.format)
        elif method == 'resize':
            src = request.GET['src']
            path = urlsplit(src).path
            width, height = [size(p) for p in params]
            for upload in Upload.objects.all():
                if upload.image.url == path:
                    break
            image = Image.open(upload.image.file)
            if not width:
                width = upload.image.width
            if not height:
                height = upload.image.height
            image.thumbnail((width, height), Image.ANTIALIAS)
            response = HttpResponse(content_type="image/%s" % image.format.lower())
            image.save(response, image.format)
        return response


@csrf_exempt
@user_passes_test(lambda u: u.is_staff)
def template(request):
    action = request.POST['action']
    if action == 'save':
        key = request.POST.get('key', request.POST['name'])
        name = request.POST.get('name')
        html = request.POST['html']
        template_data = json.loads(request.POST['template_data'])
        meta_data = json.loads(request.POST['meta_data'])
        if request.user.is_superuser:
            template, created = Template.objects.get_or_create(
                key=key
            )
        else:
            template, created = Template.objects.get_or_create(
                client=request.user.client,
                key=key
            )
        template.name = template.name if template.id and template.name else name
        template.html = html
        template.template_data = template_data
        template.meta_data = meta_data
        template.save()
        response = HttpResponse("template saved", status=201)
    else:
        response = HttpResponse("unknown action", status=400)
    return response


@api_view(['POST'])
@permission_classes((IsAuthenticated, ))
@authentication_classes((JSONWebTokenQuerystringAuthentication,))
def apptemplate(request):
    action = request.POST['action']
    if action == 'save':
        id = request.POST.get('id')
        key = request.POST.get('key')  # keep it to let user edit in old mosaico baton
        name = request.POST.get('name')
        topic = request.POST.get('topic')
        subject = request.POST.get('subject')
        view_online = request.POST.get('view_online', 'false')
        view_online = True if view_online == 'true' else False
        html = request.POST['html']
        template_data = json.loads(request.POST['template_data'])
        meta_data = json.loads(request.POST['meta_data'])

        template = None
        if id:
            campaign = get_object_or_404(Campaign, id=id)
            template = campaign.template

        if not template:
            template = Template(key=key)
        if not request.user.is_superuser:
            template.client = request.user.client
        template.name = template.name if template.id and template.name else name
        template.html = html
        template.template_data = template_data
        template.meta_data = meta_data
        template.save()

        plaintext = striptags(html2text(extract_urllinks(html)))
        plaintext = re.sub(r'http://\n', 'http://', plaintext)
        plaintext = re.sub(r'\n+', '\n', plaintext)
        plaintext = re.sub(r' +', ' ', plaintext)

        if template.campaign:
            campaign = template.campaign
            campaign.name = name
            campaign.slug = slugify(name)
            campaign.topic = Topic.objects.get(id=int(topic))
            campaign.subject = subject
            campaign.html_text = html
            campaign.plain_text = plaintext
            campaign.view_online = view_online
            campaign.save()
        else:
            campaign = Campaign(
                client=request.user.client,
                name=name,
                slug=slugify(name),
                topic=Topic.objects.get(id=int(topic)),
                subject=subject,
                html_text=html,
                plain_text=plaintext,
                view_online=view_online
            )
            campaign.save()
            template.campaign = campaign
            template.save()

        response = JsonResponse({'campaign': campaign.id}, status=201)
    else:
        response = HttpResponse("unknown action", status=400)
    return response


def get_placeholder_image(width, height):
    image = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(image)
    draw.rectangle([(0, 0), (width, height)], fill=(0x70, 0x70, 0x70))
    # stripes
    x = 0
    y = 0
    size = 40
    while y < height:
        draw.polygon([(x, y), (x + size, y), (x + size*2, y + size), (x + size*2, y + size*2)], fill=(0x80, 0x80, 0x80))
        draw.polygon([(x, y + size), (x + size, y + size*2), (x, y + size*2)], fill=(0x80, 0x80, 0x80))
        x = x + size*2
        if (x > width):
            x = 0
            y = y + size*2
    return image


def size(size_txt):
    if size_txt == 'null':
        return None
    else:
        return int(size_txt)


@user_passes_test(lambda u: u.is_staff)
def template_content(request, template_id):
    if request.user.is_superuser:
        template = get_object_or_404(Template, id=template_id)
    else:
        template = get_object_or_404(Template, id=template_id, client__user=request.user) # noqa
    return HttpResponse(template.html, status=200)
