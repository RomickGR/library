import datetime

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Count, OuterRef, Subquery, Aggregate, CharField

MAX_BOOKS_ON_SHELF = 10


class Author(models.Model):
    fio = models.CharField('Ф.И.О Автора', max_length=200)

    def __str__(self):
        return self.fio


class PublicationType(models.Model):
    name = models.CharField('Название типа публикации', max_length=100)

    def __str__(self):
        return self.name


class Librarian(models.Model):
    fio = models.CharField('Ф.И.О.', max_length=200)

    class Meta:
        verbose_name = 'Библиотекарь'
        constraints = [
            models.UniqueConstraint(fields=['fio'],
                                    name='Ф.И.О. должно быть уникальным')
        ]

    def __str__(self):
        return self.fio


class BookHall(models.Model):
    name = models.CharField('Имя зала', max_length=200)
    librarian = models.ForeignKey(Librarian, on_delete=models.PROTECT, related_name='book_hall')

    class Meta:
        verbose_name = 'Книжный зал'

    @property
    def get_book_cases_names(self):
        cases = self.book_case.all()
        return ', '.join(str(cs.number) for cs in cases)


class BookCase(models.Model):
    number = models.PositiveIntegerField('Номер стеллажа')
    book_hall = models.ForeignKey(BookHall, on_delete=models.PROTECT, related_name='book_case')

    class Meta:
        verbose_name = 'Стеллаж'
        constraints = [
            models.UniqueConstraint(fields=['number', 'book_hall'],
                                    name='Номер стеллажа должен быть уникален в рамках зала')
        ]

    @property
    def get_book_shelf_names(self):
        book_shelfs = self.book_shelf.all()
        return ', '.join(str(bs.number) for bs in book_shelfs)


class BookShelf(models.Model):
    number = models.PositiveIntegerField('Номер полки')
    book_case = models.ForeignKey(BookCase, on_delete=models.PROTECT, related_name='book_shelf')

    class Meta:
        verbose_name = 'Полка'
        constraints = [
            models.UniqueConstraint(fields=['number', 'book_case'],
                                    name='Номер полки должен быть уникален в рамках стеллажа')
        ]

    def __str__(self):
        return ''.join(['Номер полки: ' + str(self.number) + ' (Стеллаж: ' + str(
            self.book_case.number) + ')' + ' (Зал: ' + str(self.book_case.book_hall.name) + ')'])


class Reader(models.Model):
    fio = models.CharField('Ф.И.О.', max_length=200)

    class Meta:
        verbose_name = 'Читатель'


class Book(models.Model):
    name = models.CharField('Наименование книги', max_length=200)
    pub_date = models.DateField('Дата издания', null=True)
    author = models.ManyToManyField(Author, related_name='books')
    publication_type = models.ForeignKey(PublicationType, on_delete=models.SET_NULL, null=True, related_name='books')
    number = models.PositiveIntegerField("Номер")
    page_count = models.PositiveSmallIntegerField('Количество страниц')
    description = models.TextField("Описание")
    book_shelf = models.ForeignKey(BookShelf,
                                   verbose_name="Книжная полка",
                                   related_name='books',
                                   on_delete=models.PROTECT,
                                   null=True)

    class Meta:
        verbose_name = 'Книга'
        constraints = [
            models.UniqueConstraint(fields=['number'], name='Номер книги должен быть уникальным')
        ]

    def __str__(self):
        return ''.join([self.name + ' (', self.publication_type.name, ')'])

    def give_first_shelf_book(self) -> BookShelf:
        return BookShelf.objects.annotate(books_count=Count('books')).filter(books_count__lt=MAX_BOOKS_ON_SHELF).first()

    def return_to_library(self, reader: Reader, librarian: Librarian):
        shelf = self.give_first_shelf_book()

        if shelf is None:
            raise ValidationError("Полки закончились")

        self.book_shelf = shelf
        MoveBookJournal.objects.filter(reader=reader, outside_the_library=True, book=self,
                                       returned=False).update(returned=True)
        self.save()

        MoveBookJournal.objects.create(book=self, reader=reader, to_book_shelf=shelf,
                                       date_time_move=datetime.datetime.now(),
                                       librarian=librarian, returned=True)

    def take_on_hands(self, reader: Reader, librarian: Librarian, in_library):
        if self.book_shelf == None:
            raise ValidationError("Невозможно выдать книгу. Книга уже выдана другому читателю.")

        if MoveBookJournal.objects.filter(reader=reader, outside_the_library=in_library, book=self,
                                          returned=False).count() > 3:
            raise ValidationError("На руках больше 3-х книг.")

        self.book_shelf = None
        self.save()

        MoveBookJournal.objects.create(book=self, reader=reader, outside_the_library=True,
                                       date_time_move=datetime.datetime.now(),
                                       librarian=librarian)


class MoveBookJournal(models.Model):
    book = models.ForeignKey(Book, on_delete=models.PROTECT)
    from_book_shelf = models.ForeignKey(BookShelf, verbose_name='Откуда переместили', on_delete=models.PROTECT,
                                        null=True, related_name='from_book_shelf')
    to_book_shelf = models.ForeignKey(BookShelf, verbose_name='Куда переместили', on_delete=models.PROTECT, null=True,
                                      related_name='to_book_shelf')
    date_time_move = models.DateTimeField('Дата перемещения/выдачи/сдачи', auto_now_add=True)
    librarian = models.ForeignKey(Librarian, verbose_name="Библиотекарь внесший перемещение/выдачу/прием книги",
                                  on_delete=models.PROTECT)
    reader = models.ForeignKey(Reader, on_delete=models.PROTECT, null=True)
    outside_the_library = models.BooleanField('Выдача на дом', default=False)
    returned = models.BooleanField('Книга возвращена', default=False)

    class Meta:
        verbose_name = 'Журнал перемещения/выдачи/приема'


def get_count_books_by_author(author_fio):
    return Book.objects.filter(author__fio=author_fio).count()


def get_top_ten_books():
    return MoveBookJournal.objects.values('book__name').annotate(book_count=Count("book")).filter(
        to_book_shelf__isnull=True).order_by('-book_count')[:10]


def count_book_on_hands_by_readers():
    return MoveBookJournal.objects.annotate(count_book=Count("reader")).values('reader__fio', 'count_book').filter(
        returned=False)


class GroupConcat(Aggregate):
    function = 'GROUP_CONCAT'
    template = '%(function)s(%(distinct)s%(expressions)s)'

    def __init__(self, expression, distinct=False, **extra):
        super(GroupConcat, self).__init__(
            expression,
            distinct='DISTINCT ' if distinct else '',
            output_field=CharField(),
            **extra)


def get_halls_with_related_cases_and_shelfs():
    shelves_subquery = Subquery(BookShelf.objects.filter(book_case=OuterRef('pk')).values('book_case').annotate(
        bookShelvesNumbers=GroupConcat('number')).values('bookShelvesNumbers'))

    shelves_by_cases_subquery = Subquery(
        BookCase.objects.annotate(shelves=shelves_subquery).values('number', 'shelves', 'book_hall').filter(
            book_hall=OuterRef('pk')).values('shelves'))

    cases_subquery = Subquery(BookCase.objects.filter(book_hall=OuterRef('pk')).values('book_hall').annotate(
        bookCasesNumbers=GroupConcat('number')).values('bookCasesNumbers'))

    halls = BookHall.objects.annotate(shelves=shelves_by_cases_subquery, cases=cases_subquery).values('name', 'cases',
                                                                                                      'shelves')

    return list(halls)


# результат [{'name': 'Зал 1', 'cases': '1,2,3,4,5', 'shelves': '1,2,3,4,5,6,7,8,9,10'}, {'name': 'Зал 2', 'cases': '1,2,3,4,5', 'shelves': '1,2,3,4,5,6,7,8,9,10'}, {'name': 'Зал 3', 'cases': '1,2,3,4,5', 'shelves': '1,2,3,4,5,6,7,8,9,10'}]

def get_publications_with_books_that_not_taken():
    cnt_mov_book_subquery = Subquery(
        MoveBookJournal.objects.filter(book=OuterRef('pk')).annotate(book_count=Count("book")).filter(
            to_book_shelf__isnull=True).values('book_count'))

    books_not_taken_subquery = Subquery(
        Book.objects.filter(publication_type=OuterRef('pk')).annotate(cnt_book_move=cnt_mov_book_subquery).values(
            'name').filter(cnt_book_move__isnull=True))

    return PublicationType.objects.annotate(books_not_taken_list=books_not_taken_subquery).values('name',
                                                                                                  'books_not_taken_list')


# результат <QuerySet [{'name': 'Печатное', 'books_not_taken_list': 'Руслан и Людмила'}, {'name': 'Электронное', 'books_not_taken_list': 'Книга для примера'}]>


def get_move_book_journal_shelves_by_book():
    journal_by_shelve = MoveBookJournal.objects.values('book', 'to_book_shelf').exclude(to_book_shelf__isnull=True)

    shelves_subquery = Subquery(journal_by_shelve.filter(book=OuterRef('pk')).values('book').annotate(
        to_book_shelf_list=GroupConcat('to_book_shelf')).values('to_book_shelf_list'))

    return Book.objects.annotate(shelves_list=shelves_subquery).values(
        'name', 'shelves_list')

# <QuerySet [{'name': 'Руслан и Людмила', 'shelves_list': '3'}, {'name': 'Сборник стихов', 'shelves_list': '1,21'}, {'name': 'Книга для примера', 'shelves_list': None}]>
