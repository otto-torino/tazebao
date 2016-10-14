import json
import logging
import json
from urlparse import urlsplit

from django.shortcuts import render, get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.contrib.auth.decorators import user_passes_test
from premailer import transform
from PIL import Image, ImageDraw

from .models import Upload, Template

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
        'has_change_permission': False
    }
    return render(request, 'mosaico/index.html', dict)


@user_passes_test(lambda u: u.is_staff)
def editor(request):
    return render(request, 'mosaico/editor.html')

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


@csrf_exempt
def upload(request):
    if request.method == 'POST':
        file = request.FILES.values()[0]
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
                if upload.image.url == src:
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
        key = request.POST['key']
        html = request.POST['html']
        template_data = json.loads(request.POST['template_data'])
        meta_data = json.loads(request.POST['meta_data'])
        template, created = Template.objects.get_or_create(
            client=request.user.client,
            key=key
        )
        template.html = html
        template.template_data = template_data
        template.meta_data = meta_data
        template.save()
        response = HttpResponse("template saved", status=201)
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
    template = get_object_or_404(Template, id=template_id, client__user=request.user) # noqa
    return HttpResponse(template.html, status=200)
