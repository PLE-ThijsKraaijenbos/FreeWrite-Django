from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import (
    Journey, JourneyStep, Phase,
    JournalContent, LetterContent, ChoiceStoryContent,
    SpeechBubbleContent, BubblePopContent, ScaleContent,
)


@admin.register(Phase)
class PhaseAdmin(ModelAdmin):
    list_display = ['title', 'order']
    ordering = ['order']
    search_fields = ['title']


@admin.register(JourneyStep)
class JourneyStepAdmin(ModelAdmin):
    list_display = ['title', 'phase', 'order', 'assignment_type', 'is_core', 'is_active']
    list_filter = ['phase', 'is_core', 'is_active', 'assignment_type']
    search_fields = ['title', 'description']
    ordering = ['phase__order', 'order']
    autocomplete_fields = ['phase']
    fieldsets = (
        (None, {
            'fields': ('phase', 'order', 'title', 'description', 'banner_url', 'is_core', 'activation_rules', 'is_active'),
        }),
        ('Content', {
            'fields': (
                'assignment_type',
                'journal_content',
                'letter_content',
                'choice_story_content',
                'speech_bubble_content',
                'bubble_pop_content',
                'scale_content',
            ),
        }),
    )
    conditional_fields = {
        'journal_content': "assignment_type == 'journal'",
        'letter_content': "assignment_type == 'letter'",
        'choice_story_content': "assignment_type == 'choice_story'",
        'speech_bubble_content': "assignment_type == 'speech_bubble'",
        'bubble_pop_content': "assignment_type == 'bubble_pop'",
        'scale_content': "assignment_type == 'scale'",
    }


@admin.register(Journey)
class JourneyAdmin(ModelAdmin):
    list_display = ['user']
    search_fields = ['user__email']
    autocomplete_fields = ['user']


@admin.register(JournalContent)
class JournalContentAdmin(ModelAdmin):
    list_display = ['title_text', 'input_field_placeholder']
    search_fields = ['title_text']


@admin.register(LetterContent)
class LetterContentAdmin(ModelAdmin):
    list_display = ['title_text', 'greeting_placeholder']
    search_fields = ['title_text']


@admin.register(ChoiceStoryContent)
class ChoiceStoryContentAdmin(ModelAdmin):
    list_display = ['title_text']
    search_fields = ['title_text']


@admin.register(SpeechBubbleContent)
class SpeechBubbleContentAdmin(ModelAdmin):
    list_display = ['title_text']
    search_fields = ['title_text']


@admin.register(BubblePopContent)
class BubblePopContentAdmin(ModelAdmin):
    list_display = ['title_text']
    search_fields = ['title_text']


@admin.register(ScaleContent)
class ScaleContentAdmin(ModelAdmin):
    list_display = ['title_text', 'left_label', 'right_label']
    search_fields = ['title_text']
