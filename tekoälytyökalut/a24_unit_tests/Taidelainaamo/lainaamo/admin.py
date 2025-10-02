from django.contrib import admin
from lainaamo.models import Work, Artist, Loan, Tag, WorkArtist, Join_tag

class WorkArtistInline(admin.StackedInline):  # or StackedInline if you prefer
    model = Work.artists.through
    extra = 1

class JoinTagInline(admin.StackedInline):
    model = Work.tags.through
    extra = 1

@admin.register(Work)
class WorkAdmin(admin.ModelAdmin):
    list_display = ('name', 'artistStr', 'is_available')
    inlines = [WorkArtistInline, JoinTagInline]
    list_filter = ["technique", "tags"]
    search_fields = ["name"]


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    search_fields = ["name"]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ["name"]


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('user', 'work', 'loan_start', 'loan_end')
    search_fields = ['user__username']


