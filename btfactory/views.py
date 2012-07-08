#coding=utf-8
from django.core import serializers
from django.views.decorators.csrf import ensure_csrf_cookie
from btfactory.forms import CreateActressForm, ActressSearchForm
from btfactory.models import MovieLink, DailyLink, MonthlyLink, Actress, UserSubscribe
from django.template import loader
from django.template.context import Context, RequestContext
from django.http import HttpResponse, HttpResponseRedirect
import urllib2
import logging
from BeautifulSoup import BeautifulSoup
import re
import urlparse
from django.db.utils import IntegrityError
from urllib2 import URLError
from django.shortcuts import get_object_or_404, render_to_response
import hashlib
import datetime
import time
import cStringIO
from django.utils.encoding import smart_str
from django.contrib.auth.decorators import login_required
from tagging.models import Tag as ActressTag, TaggedItem
from django.conf import settings
from django.core.urlresolvers import reverse
import os
#import sys
#reload(sys)
#sys.setdefaultencoding('utf-8')

logger = logging.getLogger(__name__)

def get_actress_save_dir(aid):
    secNumber = str(int(aid / 1000) + 1)
    dirname = settings.MEDIA_ROOT + "images/" + secNumber + "/headers/"
    try:
        os.makedirs(dirname)
    except OSError:
        pass
    return "images/" + secNumber + "/headers/"

# 保存演员头像
def save_actress_header_file(aid, f):
    save_dir = get_actress_save_dir(aid)
    fileName, fileExtension = os.path.splitext(f.name)
    newname = save_dir + str(aid) + fileExtension
    destination = open(settings.MEDIA_ROOT + newname, 'wb+')
    for chunk in f.chunks():
        destination.write(chunk)
    destination.close()
    return newname


def save_actress_header(aid, original_location):
    opener1 = urllib2.build_opener()
    page1 = opener1.open(original_location)
    my_picture = page1.read()
    save_dir = get_actress_save_dir(aid)
    filename = save_dir + str(aid) + original_location[-4:]
    fout = open(settings.MEDIA_ROOT + filename, "wb")
    fout.write(my_picture)
    fout.close()
    return filename

#640 is iphones
def create_resized_image(image_name, original_location, xconstrain=640):
    if not original_location:
        return None

    from PIL import Image, ImageOps
    import os
    from django.conf import settings

    # Ensure a resized image doesn't already exist in the default MEDIA_ROOT/images/resized (MEDIA_ROOT is defined in Django's settings)
    month = str(datetime.date.today())[0:7]

    # 'dir' is a buildin function, so rename as 'monthly_dir'
    monthly_dir = '%simages/%s' % (settings.MEDIA_ROOT, month)
    try:
        os.makedirs(monthly_dir)
    except OSError:
        pass
    filename = '%s/%s.jpg' % (monthly_dir, image_name)
    if not os.path.exists(filename):
        # Fetch original image
        urllink = smart_str(original_location)
        imgdata = urllib2.urlopen(urllink).read()
        unsized_image = Image.open(cStringIO.StringIO(imgdata))
        # Create a resized image by fitting the original image into the constrains, and do this using proper antialiasing
        width, height = unsized_image.size
        if width > xconstrain:
            yconstrain = int(xconstrain * height / width)
        else:
            xconstrain = width
            yconstrain = height
        resized_image = ImageOps.fit(unsized_image, (xconstrain, yconstrain), Image.ANTIALIAS)
        # PIL sometimes throws errors if this isn't done
        resized_image = resized_image.convert("RGB")
        # Save the resized image as a jpeg into the MEDIA_ROOT/images/resized
        resized_image.save(filename, 'jpeg')

    urldir = '%simages/%s' % (settings.MEDIA_URL, month)
    return '%s/%s.jpg' % (urldir, image_name)

#从每日的新剧作页面读取剧作
def parseDailyMovie(dl):
    try:
        page = urllib2.urlopen(dl.link)
        content = page.read()
        content = content.decode('gb18030').encode('utf8')
        page.close()
    except URLError:
        raise
    logger.info("parsing daily link: " + dl.label)

    index = content.find("<div id=\"content\">") + 18
    index2 = content.find("</div>", index)
    content = content[index:index2]
    movies = content.split("<br />\r\n<br />\r\n")

    p = re.compile('<IMG class="postimg" src=".*" />', re.IGNORECASE);
    pl = re.compile('<a href=".*" target=_blank>.*\.html</a>', re.IGNORECASE);

    parseCount = 0
    for movie in movies:
        #logger.info("movie "+str(mi)+"***************************************************************")
        #mi = mi + 1
        movie = movie.strip()
        if len(movie) < 20:
            continue
            #create the movielink object
        digestkey = hashlib.sha224(movie).hexdigest()
        tIndex = movie.find("<br />")
        mTitle = movie[0:tIndex]
        #find all images        

        images = []
        for match in p.finditer(movie):
            image = str(match.group())
            iIndex = image.find('src="') + 5
            iIndex2 = image.find('"', iIndex)
            image = image[iIndex:iIndex2]
            #logger.info("movie: "+mTitle+" image:"+image)
            images.append(image)
        imagesLink = ">;<".join(images)

        dls = []
        for match in pl.finditer(movie):
            dlink = str(match.group())
            iIndex = dlink.find('href="') + 6
            iIndex2 = dlink.find('"', iIndex)
            dlink = dlink[iIndex:iIndex2]
            dls.append(dlink)
        dlLinks = ">;<".join(dls)

        result = MovieLink.objects.filter(digestkey=digestkey)
        if len(result) == 0:
            ml = MovieLink(title=mTitle, raw_desc=movie, digestkey=digestkey, daily_link=dl, images=imagesLink,
                downloadlink=dlLinks)
            ml.save()
            logger.info("movie: " + mTitle + " image:" + imagesLink)
            logger.info("movie: " + mTitle + " links:" + dlLinks)
            parseCount = parseCount + 1
        else:
            logger.info("movie already existed:...." + mTitle)
    dl.parsed = True
    dl.save()
    return parseCount

# parse daily record by the monthly link
def parseMonth(month_url):
    #logger.info("Parse Month:" + str(month_url.link))
    url = urlparse.urlsplit(month_url.link)
    servername = url[0] + "://" + url[1]
    try:
        page = urllib2.urlopen(month_url.link)
    except URLError:
        raise
    soup = BeautifulSoup(page, fromEncoding='gbk')
    #content = soup.prettify()
    links = soup.findAll('a', {'href': True, 'target': True}, True)

    count = 0
    parsed_count = 0
    reobj = re.compile(u"^★㊣最新の(日本同步|亚洲无码)(.)*♂(.)*♀$")
    #从旧的先parse
    links = links[0:10]
    links.reverse()
    for link in links:
        content = link.getText()
        match = reobj.search(content)
        if match:
            count = count + 1
            #存储日常链接            
            linkstr = servername + link.get('href', '')
            dailyLink = DailyLink(link=linkstr, monthly_link=month_url, label=content)
            try:
                dailyLink.save()
                parsed_count = parsed_count + 1
            except IntegrityError:
                logger.info(content + " Existed:...." + linkstr)
                continue
            logger.info(content)
            if count > 10:
                #only parse 2 links every time
                break
        else:
            #logger.info(content+" not match!")
            continue
    return parsed_count


def moviethumbcron(request):
    #get 1 link of not saved
    mls = MovieLink.objects.filter(images_loaded=False)[:5]
    #save image to local
    for ml in mls:
        images = ml.images.split(">;<")
        count = 0
        imageLinks = []
        for image in images:
            count = count + 1
            imgname = str(ml.digestkey) + "_" + str(count)
            try:
                link = create_resized_image(imgname, image)
                imageLinks.append(link)
            except IOError:
                continue
        ml.images = ">;<".join(imageLinks)
        ml.images_loaded = True
        ml.save()

    c = Context({'movielinks': mls})
    t = loader.get_template('btfactory/movie.html')
    return HttpResponse(t.render(c))


def dailycron(request):
    # get daily link from the month link
    link = MonthlyLink.objects.get(enable=True)
    parseMonth(link)
    # get movies from daily link page
    daily_lists = DailyLink.objects.filter(parsed=False).order_by('id')[:1]
    movieCount = 0
    for dl in daily_lists:
        movieCount = movieCount + parseDailyMovie(dl)
        pass

    return render_to_response('btfactory/dailycron.html', {'parsed_count': movieCount})


def parseActress(url):
    try:
        page = urllib2.urlopen(url)
        soup = BeautifulSoup(page)
        #content = content.decode('gb18030').encode('utf8')
        page.close()
    except URLError:
        raise

    body = soup.find(attrs={"class": "cssboxwhite_body2", "id": "data"})
    if not body:
        logger.info("url:" + url + " is NULL!!!!!!!!!!!!")
    else:
        names = body.contents[1].find("h4").getString().strip()
        co_index = names.find("(")
        #部分没有（)
        if co_index > 1:
            real_name = names[0:co_index]
            co_name = names[co_index + 1:-1]
            co_name_array = co_name.split(u"、")
            co_name_array.append(real_name)
            co_name = u"，".join(co_name_array)
            co_tags = ",".join(co_name_array)
        else:
            real_name = names
            co_name = names
            co_tags = names
        header = body.contents[1].find("img")
        #Get the actress from db!
        result = Actress.objects.get_or_create(name=real_name)
        actress = result[0]
        logger.info("realname:" + str(actress.id) + ">" + real_name + " coname:" + co_name)
        #create or update the actress
        actress.co_names = co_name
        actress.refer_url = url
        if header is not None:
            link = header.get('src', '')
            actress.photo = save_actress_header(actress.id, link)
        else:
            logger.info("realname:" + str(actress.id) + ">" + real_name + " no header photo!")
        dashrow = body.contents[1].find("ul", attrs={"class": "dashrow"})
        lis = dashrow.findAll('li')
        #logger.info("dashrow:"+dashrow.prettify())
        pf = []
        for content in lis:
            text = content.getText().strip()
            if text != ":::":
                pf.append(text)

        actress.profile = ";".join(pf)
        logger.info("profile:" + actress.profile)
        actress.tags = co_tags
        actress.save()
        return True

#把所有的演员资料下载本地   
#从8-650， range最后一个不包括进去的
def actresscron(request):
    urlprefix = "http://avno1.com/?action-model-name-avgirls-itemid-"
    count = 0
    for n in range(8, 651):
        url = urlprefix + str(n)
        if parseActress(url):
            count = count + 1
        time.sleep(1)

    c = Context({'count': count})
    t = loader.get_template('btfactory/actresscount.html')
    return HttpResponse(t.render(c))


def daily(request):
    parsed_daily_list = DailyLink.objects.order_by('id')[:100]
    result = []
    for daily in parsed_daily_list:
        movie_count = MovieLink.objects.filter(daily_link=daily).count()
        movie_confirm_count = MovieLink.objects.filter(daily_link=daily, parsed=True).count()
        image_loaded_count = MovieLink.objects.filter(daily_link=daily, images_loaded=True).count()
        result.append(
                {'daily': daily, 'count': movie_count, 'confirmed': movie_confirm_count, 'loaded': image_loaded_count})
    return render_to_response(u'btfactory/daily.html', {'parsed_daily_list': result},
        context_instance=RequestContext(request))

#电影和演员关联
@login_required
def confirmMovie(request, movie_id):
    ml = get_object_or_404(MovieLink, pk=movie_id)

    #create relate actress
    ml.actress_names = request.POST['actress']
    actress_names = ml.actress_names.split(";")

    for actress in actress_names:
        at = Actress.objects.get_or_create(name=actress)[0]
        at.save()
        ml.actress.add(at)

    ml.parsed = True
    ml.save()
    #refresh the daily movie link page
    return HttpResponseRedirect("/btfactory/" + str(ml.daily_link.id) + "/daily/")


@login_required
def dailymovie(request, daily_id):
    actress_form = CreateActressForm()

    #创建演员资料
    if request.POST:
        actress_form = CreateActressForm(request.POST, request.FILES)
        if actress_form.is_valid():
            actress_name = actress_form.cleaned_data['name'].strip()
            #actress_conames = actress_form.cleaned_data['conames']
            result = Actress.objects.get_or_create(name=actress_name)
            actress = result[0]
            actress.co_names = actress_name
            actress.tags = actress_name
            actress.photo = save_actress_header_file(actress.id, request.FILES['header'])
            actress.save()

    dl = get_object_or_404(DailyLink, pk=daily_id)
    movielinks = MovieLink.objects.filter(daily_link=dl).order_by('-id')[:100]
    tags = ActressTag.objects.all()
    for movielink in movielinks:
        if movielink.parsed:
            #已经确认的不进行影星比对
            continue
        movielink.suggest_actress_list = []
        #电影可能关联的影星
        for actressTag in tags:
            if movielink.raw_desc.find(actressTag.name) > 0:
                #找到对应的tag
                logger.info("Find actress " + actressTag.name + " in Movie:" + movielink.title)
                tagged_actress_list = TaggedItem.objects.get_by_model(Actress, actressTag)
                for actress in tagged_actress_list:
                    movielink.suggest_actress_list.append(actress)

    return render_to_response('btfactory/dailymovies.html',
            {'dl': dl, 'movielinks': movielinks, 'actress_form': actress_form},
        context_instance=RequestContext(request))


@login_required
def actressinfo(request, actress_id):
    actress = get_object_or_404(Actress, pk=actress_id)
    amount = len(UserSubscribe.objects.filter(actress_link__exact=actress_id))
    subscribe = UserSubscribe.objects.filter(actress_link__exact=actress_id, user_link__exact=request.user.id)
    had_subscribed = False
    if len(subscribe) > 0:
        had_subscribed = True
    return render_to_response('btfactory/actressinfo.html',
            {'actress': actress, 'subscribe_amount': amount, 'had_subscribed': had_subscribed},
        context_instance=RequestContext(request))


@login_required
def actresssubscribe(request, actress_id):
    actress = get_object_or_404(Actress, pk=actress_id)
    subscribe = UserSubscribe.objects.get_or_create(actress_link=actress, user_link=request.user)
    if subscribe[1] == False:
        subscribe[0].delete()
    return HttpResponseRedirect(reverse('actress_info', args=(actress_id,)))


def search_actress(request):
    if request.method == 'POST':
        form = ActressSearchForm(request.POST)
        if form.is_valid():
            actress = form.cleaned_data['actress']
            logger.info("search_actress:" + actress)
            actresses = Actress.objects.filter(co_names__icontains=actress)[:100]
            result = serializers.serialize('json', actresses, fields=('name', 'co_names', 'photo', 'id'))
            return HttpResponse(result)
            #缺省显示最新的10条
    actresses = Actress.objects.order_by('-id')[:100]
    result = serializers.serialize('json', actresses, fields=('name', 'co_names', 'photo', 'id'))
    return HttpResponse(result)


@ensure_csrf_cookie
def index(request):
    latest_movies_list = MovieLink.objects.all().order_by('-pub_date')[:5]
    t = loader.get_template('btfactory/index.html')
    c = Context({
        'latest_movies_list': latest_movies_list,
        })
    return HttpResponse(t.render(c))



