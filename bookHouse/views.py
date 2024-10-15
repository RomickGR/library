from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters

from bookHouse.models import (Book, Reader, Author, PublicationType, Librarian,
                              BookHall, BookCase, BookShelf, MoveBookJournal)
from bookHouse.serializers import (BookSerializer, ReaderSerializer, AuthorSerializer, PublicationTypeSerializer,
                                   LibrarianSerializer, BookHallSerializer, BookCaseSerializer, BookShelfSerializer,
                                   MoveBookJournalSerializer)


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['fio']
    ordering_fields = ['fio']


class PublicationTypeViewSet(viewsets.ModelViewSet):
    queryset = PublicationType.objects.all()
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    serializer_class = PublicationTypeSerializer
    filterset_fields = ['name']
    ordering_fields = ['name']


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['name', 'pub_date', 'description']
    ordering_fields = ['name', 'pub_date', 'description']


class ReaderViewSet(viewsets.ModelViewSet):
    queryset = Reader.objects.all()
    serializer_class = ReaderSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['fio']
    ordering_fields = ['fio']


class LibrarianViewSet(viewsets.ModelViewSet):
    queryset = Librarian.objects.all()
    serializer_class = LibrarianSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['fio']
    ordering_fields = ['fio']


class BookHallViewSet(viewsets.ModelViewSet):
    queryset = BookHall.objects.all()
    serializer_class = BookHallSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['name']
    ordering_fields = ['name']


class BookCaseViewSet(viewsets.ModelViewSet):
    queryset = BookCase.objects.all()
    serializer_class = BookCaseSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['name']
    ordering_fields = ['name']


class BookShelfViewSet(viewsets.ModelViewSet):
    queryset = BookShelf.objects.all()
    serializer_class = BookShelfSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['number']
    ordering_fields = ['number']


class MoveBookJournalViewSet(viewsets.ModelViewSet):
    queryset = MoveBookJournal.objects.all()
    serializer_class = MoveBookJournalSerializer
