import datetime

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Count

MAX_BOOKS_ON_SHELF = 10


class Author(models.Model):
    fio = models.CharField('Ф.И.О Автора', max_length=200)

    def __str__(self):
        return self.fio


class PublicationType(models.Model):
    name = models.CharField('Название типа публикации', max_length=100)


class Librarian(models.Model):
    fio = models.CharField('Ф.И.О.', max_length=200)

    class Meta:
        verbose_name = 'Библиотекарь'


class BookHall(models.Model):
    name = models.CharField('Имя зала', max_length=200)
    librarian = models.ForeignKey(Librarian, on_delete=models.PROTECT)

    class Meta:
        verbose_name = 'Книжный зал'


class BookCase(models.Model):
    number = models.PositiveIntegerField('Номер стеллажа')
    book_hall = models.ForeignKey(BookHall, on_delete=models.PROTECT)

    class Meta:
        verbose_name = 'Стеллаж'
        constraints = [
            models.UniqueConstraint(fields=['number', 'book_hall'],
                                    name='Номер стеллажа должен быть уникален в рамках зала')
        ]


class BookShelf(models.Model):
    number = models.PositiveIntegerField('Номер полки')
    book_case = models.ForeignKey(BookCase, on_delete=models.PROTECT)

    class Meta:
        verbose_name = 'Полка'
        constraints = [
            models.UniqueConstraint(fields=['number', 'book_case'],
                                    name='Номер полки должен быть уникален в рамках стеллажа')
        ]


class Reader(models.Model):
    fio = models.CharField('Ф.И.О.', max_length=200)

    class Meta:
        verbose_name = 'Читатель'


class Book(models.Model):
    name = models.CharField('Наименование книги', max_length=200)
    pub_date = models.DateField('Дата издания', null=True)
    author = models.ManyToManyField(Author)
    publication_type = models.ForeignKey(PublicationType, on_delete=models.SET_NULL, null=True)
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

    def GiveFirstShelfBook(self) -> BookShelf:
        return BookShelf.objects.annotate(books_count=Count('books')).filter(books_count__lt=MAX_BOOKS_ON_SHELF).first()

    def ReturnToLibrary(self, reader: Reader, librarian: Librarian):
        shelf = self.GiveFirstShelfBook()

        if shelf is None:
            raise ValidationError("Полки закончились")

        self.book_shelf = shelf
        MoveBookJournal.objects.filter(reader=reader, outside_the_library=True, book=self,
                                       returned=False).update(returned=True)
        self.save()

        MoveBookJournal.objects.create(book=self, reader=reader, to_book_shelf=shelf,
                                       date_time_move=datetime.datetime.now(),
                                       librarian=librarian, returned=True)

    def TakeOnHands(self, reader: Reader, librarian: Librarian, in_library):
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
    date_time_move = models.DateTimeField('Дата перемещения/выдачи/сдачи')
    librarian = models.ForeignKey(Librarian, verbose_name="Библиотекарь внесший перемещение/выдачу/прием книги",
                                  on_delete=models.PROTECT)
    reader = models.ForeignKey(Reader, on_delete=models.PROTECT, null=True)
    outside_the_library = models.BooleanField('Выдача на дом', default=False)
    returned = models.BooleanField('Книга возвращена', default=False)

    class Meta:
        verbose_name = 'Журнал перемещения/выдачи/приема'


def GetCountBooksByAuthor(author_fio):
    return Book.objects.filter(author__fio=author_fio).count()


def GetTopTenBooks():
    return MoveBookJournal.objects.values('book__name').annotate(book_count=Count("book")).filter(
        to_book_shelf=None).order_by('-book_count')[:10]


def CountBookOnNandsByReaders():
    return MoveBookJournal.objects.annotate(count_book=Count("reader")).values('reader__fio', 'count_book').filter(
        returned=False)
