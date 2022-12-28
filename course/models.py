from django.core.validators import MaxValueValidator
from django.db import models
from django.utils import timezone
from cloudinary.models import CloudinaryField
from users import models as user_models
from django.core.exceptions import ValidationError


class Faculty(models.Model):
    name = models.CharField(max_length=80, blank=True, null=True)
    faculty_describtion = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'faculty'

    def __str__(self):
        return f'Faculty {self.name}'


class Course(models.Model):
    # id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=80, blank=True, null=True)
    course_describtion = models.TextField(blank=True, null=True)
    faculty = models.ForeignKey(
        'Faculty', models.DO_NOTHING, db_column='faculty', blank=True, null=True)
    category = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'course'

    def __str__(self):
        return f'Course {self.id} | Name: {self.name}'


class Category(models.Model):
    name = models.CharField(max_length=80, blank=True, null=True)
    parent = models.ForeignKey(
        'self', models.DO_NOTHING, db_column='parent', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'category'

    def __str__(self):
        return f'Category {self.name}'


class Subject(models.Model):

    name = models.CharField(max_length=80, blank=True, null=True)
    category = models.ForeignKey(
        Category, models.DO_NOTHING, db_column='category', blank=True, null=True)
    thumb = models.CharField(max_length=100, blank=True, null=True)
    pic = models.CharField(max_length=200, blank=True, null=True)
    description = models.CharField(max_length=1000, blank=True, null=True)
    lecturer = models.ForeignKey(
        'users.Lecturer', models.DO_NOTHING, db_column='lecturer')

    # video_url = models.CharField(max_length=1000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'subject'

    def __str__(self):
        return f'Subject {self.id} | Name: {self.name}'


class SubjectRating(models.Model):
    subject = models.ForeignKey(
        Subject, models.DO_NOTHING, db_column='subject', blank=True, null=True)
    student = models.ForeignKey(
        'users.Student', models.DO_NOTHING, db_column='student', blank=True, null=True)
    rating = models.IntegerField(blank=True, null=True)
    commence = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'subject_rating'

    def __str__(self):
        return f'Subject: {self.subject.name} | Student {self.student.account.username} | Rating: {self.rating}'


class Enrollment(models.Model):
    subject = models.ForeignKey(
        'Subject', models.DO_NOTHING, db_column='subject')
    student = models.ForeignKey(
        'users.Student', models.DO_NOTHING, db_column='student')
    status = models.IntegerField(blank=True, null=True)
    lesson = models.ForeignKey(
        'Lesson', models.DO_NOTHING, db_column='lesson', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'enrollment'

    def __str__(self):
        return f'Student {self.student.account.username} | Subject: {self.subject.name}'


class Book(models.Model):
    name = models.CharField(max_length=200, blank=True, null=True)
    author = models.CharField(max_length=80, blank=True, null=True)
    publisher = models.CharField(max_length=80, blank=True, null=True)
    # type = models.ForeignKey('StylePreference', models.DO_NOTHING, db_column='type', blank=True, null=True)
    isbn = models.TextField(blank=True, null=True)
    publish_year = models.IntegerField(blank=True, null=True)
    category = models.ForeignKey(
        'Category', models.DO_NOTHING, db_column='category', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'book'

    def __str__(self):
        return f'{self.name}'


class Multimedia(models.Model):
    url = models.CharField(max_length=200, blank=True, null=True)
    name = models.CharField(max_length=80, blank=True, null=True)
    # type = models.ForeignKey('StylePreference', models.DO_NOTHING, db_column='type', blank=True, null=True)
    author = models.CharField(max_length=80, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'multimedia'

    def __str__(self):
        return f'{self.name} | Author: {self.author}'


class Lesson(models.Model):
    year = models.IntegerField(blank=True, null=True)
    name = models.CharField(max_length=80, blank=True, null=True)
    description = models.CharField(max_length=80, blank=True, null=True)
    lecturer = models.ForeignKey(
        user_models.Lecturer, models.DO_NOTHING, db_column='lecturer', blank=True, null=True)
    subject = models.ForeignKey(
        'Subject', models.DO_NOTHING, db_column='subject')
    # multimedia = models.ForeignKey(
    #     'Multimedia', models.DO_NOTHING, db_column='multimedia', blank=True, null=True)
    multimedia = models.ManyToManyField(Multimedia)
    order = models.IntegerField()
    book = models.ForeignKey(Book, models.DO_NOTHING,
                             db_column='book', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'lesson'

    def clean(self):
        current_order = self.order
        list_lesson = list(Lesson.objects.all())
        for item in list_lesson:
            if item.subject.name == self.subject.name and item.order == current_order and item.id != self.id:
                raise ValidationError("Order already exist")

    def __str__(self):
        return f'{self.name} | Subject: {self.subject.name}'
