import random

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie

from users.models import Student

from .cfService import get_recommmendations_cf
from .forms import CourseDismissForm, CourseEnrollForm
from .models import Enrollment, Subject, Lesson
from .services import get_enrolled_subjects, get_recommmendations

# Suggestions
import pandas as pd
import neattext.functions as nfx
# Load ML/Rc Pkgs
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity, linear_kernel

# Load our dataset
df = pd.read_csv('resources/subject_list.csv')

# Clean Text:stopwords,special character
df['clean_course_title'] = df['name'].apply(nfx.remove_stopwords)
df['clean_course_title'] = df['clean_course_title'].apply(
    nfx.remove_special_characters)

course_title_list = df[['name', 'clean_course_title']]

# Vectorize our Text
count_vect = CountVectorizer()
# FIt: calculate mean and std of data => calculate the frequency of each word
# Transform: create a sparse matrix
cv_mat = count_vect.fit_transform(df['clean_course_title'])
# Dense
cv_mat_dense = cv_mat.todense()
df_cv_words = pd.DataFrame(
    cv_mat_dense, columns=count_vect.get_feature_names_out())

# Cosine Similarity Matrix
cosine_sim_mat = cosine_similarity(cv_mat)

# Get courses index
course_indices = pd.Series(df.index, index=df['name']).drop_duplicates()


def recommend_course(title, num_of_rec=10):
    # ID for title
    # Course Indice
    idx = course_indices[title]
    # Search inside cosine_sim_mat
    # Scores
    scores = list(enumerate(cosine_sim_mat[idx]))
    # Sort our scores per cosine score || [1:]: remove itself
    sorted_scores = sorted(scores, key=lambda x: x[1], reverse=True)
    # Recomm
    # Contain name and scores
    selected_course_indices = [i[0] for i in sorted_scores[1:]]
    selected_course_scores = [i[1] for i in sorted_scores[1:]]
    # result = df['name'].iloc[selected_course_indices]
    # rec_df = pd.DataFrame(result)
    # rec_df['similarity_scores'] = selected_course_scores
    # return rec_df.head(num_of_rec)
    result = selected_course_indices[0: num_of_rec]
    return result


# recommend_course = recommend_course('Industrial Relations', 20)
# print(recommend_course)


def _getRecommendations(request, number):
    recommmend_list = request.session.get("recommmend_list")
    if recommmend_list is None:
        recommmend_list = get_recommmendations(request.user)
        request.session["recommmend_list"] = recommmend_list

    random_items = [
        recommmend_list[random.randrange(len(recommmend_list))]
        for item in range(number)
    ]
    return random_items


# def suggest(title):


def home(request):
    recommended_courses = _getRecommendations(request, 6)
    context = {"home_page": "active",
               "recommended_courses": recommended_courses}
    return render(request, "index.html", context)


def about(request):
    context = {"about_page": "active"}
    return render(request, "about.html", context)


def courses_list(request):
    # get filter string
    filter_str = request.POST.get("filter_str", "").strip()
    if len(filter_str) == 0:
        filter_str = request.GET.get("filter_str", "").strip()
    course_list = []
    if len(filter_str) == 0:
        course_list = list(Subject.objects.all())
        base_url = "?page="
    else:
        course_list = list(Subject.objects.filter(name__icontains=filter_str))
        base_url = "?filter_str=" + filter_str + "&page="

    # Pagination
    paginator = Paginator(course_list, 6)
    page = request.GET.get("page")
    courses = paginator.get_page(page)

    context = {
        "courses_page": "active",
        "courses": courses,
        "courses_size": course_list.__len__,
        "base_url": base_url,
        "filter_str": filter_str,
    }

    return render(request, "courses-list.html", context)


def course_watch(request, course_id, current_lesson):

    course = get_object_or_404(Subject, pk=course_id)

    # Sort lesson by order value
    lessons = Lesson.objects.filter(subject=course_id).order_by('order')

    # check if enrolled this subject if user has logined
    is_enrolled = False
    if request.user.is_authenticated:  # authenticated user
        enrolled_course_list = get_enrolled_subjects(request.user.id)
        if len(enrolled_course_list.filter(subject=course_id)) is not 0:
            is_enrolled = True

    currentLessonDetail = [x for x in lessons if x.id == current_lesson]

    context = {
        "about_watch_page": "active",
        "course": course,
        "is_enrolled": is_enrolled,
        "lessons": lessons,
        "current_lesson": currentLessonDetail[0],
        "test": 1
    }

    return render(request, "course-watch.html", context)


@cache_page(60 * 15)
@vary_on_cookie
def courses_cb(request):
    # get content-based filtering list
    recommmend_list = request.session.get("recommmend_list")
    if recommmend_list is None:
        recommmend_list = get_recommmendations(request.user)
        request.session["recommmend_list"] = recommmend_list

    # Pagination
    paginator = Paginator(recommmend_list, 6)
    page = request.GET.get("page")
    courses = paginator.get_page(page)

    context = {
        "courses_page": "active",
        "courses": courses,
        "courses_size": recommmend_list.__len__,
    }
    return render(request, "courses-cb.html", context)


@cache_page(60 * 15)
@vary_on_cookie
def courses_cf(request):
    # get content-based filtering list
    recommmend_cf_list = request.session.get("recommmend_cf_list")
    if recommmend_cf_list is None:
        recommmend_cf_list = get_recommmendations_cf(request.user)
        request.session["recommmend_cf_list"] = recommmend_cf_list

    # Pagination
    paginator = Paginator(recommmend_cf_list, 6)
    page = request.GET.get("page")
    courses = paginator.get_page(page)

    context = {
        "courses_page": "active",
        "courses": courses,
        "courses_size": recommmend_cf_list.__len__,
    }
    return render(request, "courses-cf.html", context)


def course_single(request, course_id):
    course = get_object_or_404(Subject, pk=course_id)

    # Sort lesson by order value
    lessons = Lesson.objects.filter(subject=course_id).order_by('order')

    # check if enrolled this subject if user has logined
    is_enrolled = False
    if request.user.is_authenticated:  # authenticated user
        enrolled_course_list = get_enrolled_subjects(request.user.id)
        if len(enrolled_course_list.filter(subject=course_id)) is not 0:
            is_enrolled = True

    # get cb list
    # recommmend_list = request.session.get("recommmend_list")
    # if recommmend_list is None:
    #     recommmend_list = get_recommmendations(request.user)
    #     request.session["recommmend_list"] = recommmend_list

    # random_items = [
    #     recommmend_list[random.randrange(len(recommmend_list))] for item in range(2)
    # ]

    recommmend_ids = recommend_course(course.name, 3)
    print(recommmend_ids)
    recommend_courses = Subject.objects.filter(id__in=recommmend_ids)
    print(recommend_courses)

    context = {
        "courses_page": "active",
        "course": course,
        "recommended_courses": recommend_courses,
        "is_enrolled": is_enrolled,
        "lessons": lessons,
    }
    return render(request, "courses-single.html", context)


@login_required
def course_enroll(request):
    """
    1. Enrolling course
    2. Refreshing recommendation course list by deleting request.session['recommmend_list']
    3. Message either success or error
    """

    if request.method == "POST":
        current_student = Student.objects.get(account=request.user.id)
        print(current_student)
        form = CourseEnrollForm(request.POST)
        if form.is_valid():
            form.instance.student = current_student
            form.instance.status = 1
            print("==========form.instance=========")
            print(form.instance)
            form.save()
            _refresh_session(request)
            messages.success(request, "You have enrolled the subject.")
        else:
            messages.error(request, form.errors)

    return redirect("course-progress")


@login_required
def course_dismiss(request):
    """
    1. Dismissing course
    2. Refreshing recommendation course list by deleting request.session['recommmend_list']
    3. Message either success or error
    """
    if request.method == "POST":
        current_student = Student.objects.get(account=request.user.id)
        form = CourseDismissForm(request.POST)
        if form.is_valid():
            e = Enrollment.objects.filter(
                subject=form.instance.subject, student=current_student
            )
            e.delete()
            _refresh_session(request)
            messages.success(request, "You have dismissed the subject.")
        else:
            messages.error(request, form.errors)

    return redirect("course-progress")


def _refresh_session(request):
    del request.session["recommmend_list"]
    # del request.session["recommmend_cf_list"]


@login_required
def course_progress(request):
    """
    Display
    1. content-based filtering recommmended course list
    2. collaborative filtering recommmended course list
    2. enrolled course list
    """
    # get cb list
    recommmend_list = request.session.get("recommmend_list")
    if recommmend_list is None:
        recommmend_list = get_recommmendations(request.user)
        request.session["recommmend_list"] = recommmend_list
    recommmend_list = recommmend_list[0:4]
    # get collaborative filtering list
    # recommmend_cf_list = request.session.get("recommmend_cf_list")
    # if recommmend_cf_list is None:
    #     recommmend_cf_list = get_recommmendations_cf(request.user)
    #     request.session["recommmend_cf_list"] = recommmend_cf_list
    # recommmend_cf_list = recommmend_cf_list[0:4]

    recommmend_cf_list = _getRecommendations(request, 4)

    # get enrolled subject list
    enrolled_course_list = get_enrolled_subjects(request.user.id)

    enrolled_course0 = []
    enrolled_course1 = []
    remain_course_list = []
    has_enrolled_course0 = False
    has_enrolled_course1 = False
    has_enrolled_course_remain = False
    has_more = False
    list_size = len(enrolled_course_list)
    if list_size > 0:
        enrolled_course0 = enrolled_course_list[0]
        has_enrolled_course0 = True
    if list_size > 1:
        enrolled_course1 = enrolled_course_list[1]
        has_enrolled_course1 = True
    if list_size > 2:
        remain_course_list = enrolled_course_list[2:None]
        remain_course_list = remain_course_list[0:7]
        has_enrolled_course_remain = True
    if list_size > 9:  # show more option
        has_more = True

    context = {
        "courses_progress_page": "active",
        "recommended_courses_cb": recommmend_list,
        "recommended_courses_cf": recommmend_cf_list,
        "enrolled_course0": enrolled_course0,
        "enrolled_course1": enrolled_course1,
        "remain_course_list": remain_course_list,
        "has_enrolled_course0": has_enrolled_course0,
        "has_enrolled_course1": has_enrolled_course1,
        "has_enrolled_course_remain": has_enrolled_course_remain,
        "has_more": has_more,
    }
    return render(request, "courses-progress.html", context)

# @login_required
# only admin can access this page


@user_passes_test(lambda user: user.is_superuser)
def course_upload(request):
    context = {
        "courses_upload_page": "active",
    }
    return render(request, "course-upload.html", context)
