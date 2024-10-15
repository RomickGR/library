from rest_framework import serializers

from bookHouse.models import Book, Reader, Author, PublicationType, Librarian, BookHall, BookCase, BookShelf, \
    MoveBookJournal


class AuthorSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Author
        fields = [
            'fio',
        ]


class PublicationTypeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = PublicationType
        fields = [
            'name',
        ]


class BookSerializer(serializers.HyperlinkedModelSerializer):
    publication_type = PublicationTypeSerializer()
    author = AuthorSerializer(many=True)

    class Meta:
        model = Book
        fields = [
            'name',
            'author',
            'pub_date',
            'publication_type',
            'number',
            'page_count',
            'description',
        ]

    def create(self, validated_data):
        publications_type_data = validated_data.pop('publication_type')
        authors_data = validated_data.pop('author')
        publication_type, created = PublicationType.objects.get_or_create(name=publications_type_data['name'])

        authors = []

        for author_data in authors_data:
            author, created = Author.objects.get_or_create(fio=author_data['fio'])
            authors.append(author)

        book = Book.objects.create(
            **validated_data,
            publication_type=publication_type,
        )

        book.author.set(authors)
        return book


class ReaderSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Reader
        fields = [
            'fio',
        ]


class LibrarianSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Librarian
        fields = [
            'fio',
        ]


class BookHallSerializer(serializers.HyperlinkedModelSerializer):
    librarian = LibrarianSerializer()
    get_book_cases_names = serializers.ReadOnlyField()

    class Meta:
        model = BookHall
        fields = [
            'name',
            'librarian',
            'get_book_cases_names',
        ]

    def create(self, validated_data):
        librarian_data = validated_data.pop('librarian')
        librarian, created = Librarian.objects.get_or_create(fio=librarian_data['fio'])

        hall = BookHall.objects.create(
            **validated_data,
            librarian=librarian,
        )

        return hall


class BookCaseSerializer(serializers.HyperlinkedModelSerializer):
    book_hall = BookHallSerializer()
    get_book_shelf_names = serializers.ReadOnlyField()

    class Meta:
        model = BookCase
        fields = [
            'number',
            'book_hall',
            'get_book_shelf_names',
        ]


class BookShelfSerializer(serializers.HyperlinkedModelSerializer):
    book_case = BookCaseSerializer()

    class Meta:
        model = BookShelf
        fields = [
            'number',
            'book_case',
        ]


class MoveBookJournalSerializer(serializers.HyperlinkedModelSerializer):
    book = serializers.SlugRelatedField(queryset=Book.objects.all(), slug_field='name')
    from_book_shelf = serializers.PrimaryKeyRelatedField(queryset=BookShelf.objects.all())
    to_book_shelf = serializers.PrimaryKeyRelatedField(queryset=BookShelf.objects.all())
    librarian = serializers.SlugRelatedField(queryset=Librarian.objects.all(), slug_field='fio')

    class Meta:
        model = MoveBookJournal
        fields = [
            'book',
            'from_book_shelf',
            'to_book_shelf',
            'librarian',
        ]
