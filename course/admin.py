from django.contrib import admin

from course.models import *

admin.site.register(Course)
admin.site.register(Subject)
admin.site.register(Category)
admin.site.register(Faculty)
admin.site.register(Enrollment)
admin.site.register(SubjectRating)
admin.site.register(Lesson)
admin.site.register(Book)