from django.contrib import admin
from .models import (
    Journey, JourneyStep, JourneyStepProgress, Phase,
    JournalContent, LetterContent, ChoiceStoryContent,
    SpeechBubbleContent, BubblePopContent, ScaleContent,
)


@admin.register(Phase)
class PhaseAdmin(admin.ModelAdmin):
    list_display = ['title', 'order']
    ordering = ['order']


@admin.register(JourneyStep)
class JourneyStepAdmin(admin.ModelAdmin):
    list_display = ['title', 'phase', 'order', 'assignment_type', 'is_core', 'is_active']
    list_filter = ['phase', 'is_core', 'is_active', 'assignment_type']
    search_fields = ['title', 'description']
    ordering = ['phase__order', 'order']


@admin.register(Journey)
class JourneyAdmin(admin.ModelAdmin):
    list_display = ['id', 'user']
    search_fields = ['user__email']


@admin.register(JourneyStepProgress)
class JourneyStepProgressAdmin(admin.ModelAdmin):
    list_display = ['journey', 'step', 'status', 'bookmarked', 'started_at', 'completed_at']
    list_filter = ['status', 'bookmarked']
    search_fields = ['journey__user__email']


@admin.register(JournalContent)
class JournalContentAdmin(admin.ModelAdmin):
    list_display = ['id', 'title_text']


@admin.register(LetterContent)
class LetterContentAdmin(admin.ModelAdmin):
    list_display = ['id', 'title_text']


@admin.register(ChoiceStoryContent)
class ChoiceStoryContentAdmin(admin.ModelAdmin):
    list_display = ['id', 'title_text']


@admin.register(SpeechBubbleContent)
class SpeechBubbleContentAdmin(admin.ModelAdmin):
    list_display = ['id', 'title_text']


@admin.register(BubblePopContent)
class BubblePopContentAdmin(admin.ModelAdmin):
    list_display = ['id', 'title_text']


@admin.register(ScaleContent)
class ScaleContentAdmin(admin.ModelAdmin):
    list_display = ['id', 'title_text', 'left_label', 'right_label']
