from django.db import models


class Author(models.Model):
    fio = models.CharField('Ф.И.О Автора', max_length=200)


class PublicationType(models.Model):
    name = models.CharField('Название типа публикации', max_length=100)


class Book(models.Model):
    name = models.CharField('Наименование книги', max_length=200)
    pub_date = models.DateField('Дата издания')
    author = models.ManyToManyField(Author)
    publication_type = models.ForeignKey(PublicationType, on_delete=models.SET_NULL, null=True)
    number = models.PositiveIntegerField("Номер")
    page_count = models.PositiveSmallIntegerField('Количество страниц')
    description = models.TextField("Описание")

    class Meta:
        verbose_name = 'Книга'
        constraints = [
            models.UniqueConstraint(fields=['number'], name='Номер книги должен быть уникальным')
        ]


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
            models.UniqueConstraint(fields=['number', 'book_hall'], name='Номер стеллажа должен быть уникален в рамках зала')
        ]


class BookShelf(models.Model):
    number = models.PositiveIntegerField('Номер полки')
    book_case = models.ForeignKey(BookCase, on_delete=models.PROTECT)

    class Meta:
        verbose_name = 'Полка'
        constraints = [
            models.UniqueConstraint(fields=['number', 'book_case'], name='Номер полки должен быть уникален в рамках стеллажа')
        ]


class Reader(models.Model):
    fio = models.CharField('Ф.И.О.', max_length=200)

    class Meta:
        verbose_name = 'Читатель'


class MoveBookJournal(models.Model):
    book = models.ForeignKey(Book, on_delete=models.PROTECT)
    from_book_shelf = models.ForeignKey(BookShelf, verbose_name = 'Откуда переместили', on_delete=models.PROTECT, null=True, related_name = 'from_book_shelf')
    to_book_shelf = models.ForeignKey(BookShelf, verbose_name = 'Куда переместили', on_delete=models.PROTECT, null=True, related_name = 'to_book_shelf')
    date_time_move = models.DateTimeField('Дата перемещения/выдачи/сдачи')
    librarian = models.ForeignKey(Librarian, verbose_name="Библиотекарь внесший перемещение/выдачу/прием книги",
                                  on_delete=models.PROTECT)
    reader = models.ForeignKey(Reader, on_delete=models.PROTECT, null=True)
    outside_the_library = models.BooleanField('Выдача на дом', default=False)

    class Meta:
        verbose_name = 'Журнал перемещения/выдачи/приема'
